#!/usr/bin/env python3
'''
################################################################################
#
# YDLIDAR T-mini Lidar Scanner Library (T-mini Pro)
#
# Specs:
# * Laser wavelength: 895-915nm (905nm typ)
# * Laser power: 16W (max) Class I
# * Supply power: 5V
# * Current:
#   - startup: 1A (peak), .84A (typ)
#   - working: 340mA (typ), 480mA (peak)
#   - sleeping: 45mA (max)
# * Angle reference: 0 degs is direction of arrow on top (right side, connector down)
# * Operating temperature: -10C (min), 40C (max)
# 
################################################################################
'''

import logging

import ydlidar

#import pdb  ## pdb.set_trace()


LIDAR_VERSION = "1.1.0"

DEF_LOG_LEVEL = "WARNING"

DEF_CONFIGS_FILE = "./.lidar.yaml"
DEF_PORT_PATH = "/dev/ydlidar"
DEF_BAUD_RATE = 230400
DEF_MAX_ANGLE = 180.0   # degrees
DEF_MIN_ANGLE = -180.0  # degrees
DEF_SCAN_FREQ = 10.0    # Hz
DEF_MAX_RANGE = 8.0     # meters
DEF_MIN_RANGE = 0.02    # meters
DEF_SAMPLE_RATE = 4     # KHz

MIN_ANGLE = -180.0
MAX_ANGLE = 180.0
MIN_RANGE = 0.02      # meters
MAX_RANGE = 12.0      # meters
MIN_SCAN_FREQ = 6.0   # Hz
MAX_SCAN_FREQ = 12.0  # Hz
MIN_SAMPLE_RATE = 1   # KHz ????
MAX_SAMPLE_RATE = 4   # KHz ????

MIN_ANGLE_RESOLUTION = 0.54  # degrees

MIN_TILT_ANGLE = 0.0   # degrees
DEF_TILT_ANGLE = 0.75  # degrees
MAX_TILT_ANGLE = 1.5   # degrees


class Lidar():
    def __init__(self, **kwargs):
        self.port = kwargs.get('port', None)
        self.baud = kwargs.get('baud', DEF_BAUD_RATE)
        self.scanFreq = kwargs.get('scanFreq', DEF_SCAN_FREQ)
        self.sampleRate = kwargs.get('sampleRate', DEF_SAMPLE_RATE)
        self.maxAngle = kwargs.get('maxAngle', DEF_MAX_ANGLE)
        self.minAngle = kwargs.get('minAngle', DEF_MIN_ANGLE)
        self.maxRange = kwargs.get('maxRange', DEF_MAX_RANGE)
        self.minRange = kwargs.get('minRange', DEF_MIN_RANGE)
        self.zeroFilter = kwargs.get('zeroFilter', True)
        self.laserScan = None

        ydlidar.os_init()

        if not self.port:
            ports = ydlidar.lidarPortList()
            self.port = DEF_PORT_PATH
            for key, value in ports.items():
                self.port = value
        logging.debug(f"Port: {self.port}")

        self.laser = ydlidar.CYdLidar()
        if not self.laser:
            logging.error("Unable to initialize lidar")
            exit(1)
        self.laser.setlidaropt(ydlidar.LidarPropSerialPort, self.port)
        self.laser.setlidaropt(ydlidar.LidarPropSerialBaudrate, self.baud)
        self.laser.setlidaropt(ydlidar.LidarPropLidarType, ydlidar.TYPE_TRIANGLE)
        self.laser.setlidaropt(ydlidar.LidarPropDeviceType, ydlidar.YDLIDAR_TYPE_SERIAL)
        self.laser.setlidaropt(ydlidar.LidarPropSingleChannel, False)
        self.laser.setlidaropt(ydlidar.LidarPropIntenstiy, True)
        self.setScanFreq(self.scanFreq)
        self.setSampleRate(self.sampleRate)
        self.setAngles(self.minAngle, self.maxAngle)
        self.setRanges(self.minRange, self.maxRange)

        if not self.laser.initialize():
            logging.error("Failed to initalize laser")
            exit(1)
        if not self.laser.turnOn():
            logging.error("Failed to turn laser on")
            exit(1)
        if not ydlidar.os_isOk():
            logger.error("Laser is not OK")
            exit(1)
        self.laserScan = ydlidar.LaserScan()

    def laserOn(self):
        if not self.laser.turnOn():
            logging.error("Failed to turn laser on")
            return True
        if not ydlidar.os_isOk():
            logging.error("Laser not OK")
            return True
        self.laserScan = ydlidar.LaserScan()
        return False

    def laserOff(self):
        if not self.laser.turnOff():
            logging.error("Failed to turn laser off")
            return True
        return False

    def rescan(self):
        self.laser.turnOn()
        self.laserScan = ydlidar.LaserScan()

    def _scan(self):
        ret = self.laser.doProcessSimple(self.laserScan)
        while not (ret and ydlidar.os_isOk() and self.laserScan.points):
            self.laser.turnOn()
            self.laserScan = ydlidar.LaserScan()
            ret = self.laser.doProcessSimple(self.laserScan)
        print("...")

    #### TODO replace scan() and scanIntensity() with scan(vals)
    def scan(self):
        self._scan()
        angles, distances = zip(*[(p.angle, p.range) for p in self.laserScan.points if not ((self.zeroFilter) and (p.range <= 0))])
        return angles, distances

    def scanIntensity(self):
        self._scan()
        angles, distances, intensity = zip(*[(p.angle, p.range, int(p.intensity)) for p in self.laserScan.points if not ((self.zeroFilter) and (p.range <= 0))])
        return angles, distances, intensity

    '''
    def info(self):
        if not self.laser:
            logging.error("Lidar not initialized")
            return None
        r = self.laser.getDeviceInfo(????)
        print(f"INFO: {r}")
        return(r)
    '''

    def setAngles(self, minAngle, maxAngle):
        if (minAngle > MAX_ANGLE) or (minAngle < MIN_ANGLE):
            logging.error(f"Invalid minAngle ({minAngle})")
            return
        if (maxAngle > 180.0) or (maxAngle < -180.0):
            logging.error(f"Invalid maxAngle ({maxAngle})")
            return
        if minAngle >= maxAngle:
            logging.error(f"Invalid minAngle and maxAngle pair ({minAngle} >= {maxAngle}))")
            return
        self.minAngle = minAngle
        self.maxAngle = maxAngle
        self.laser.setlidaropt(ydlidar.LidarPropMinAngle, self.minAngle)
        self.laser.setlidaropt(ydlidar.LidarPropMaxAngle, self.maxAngle)

    def getAngles(self):
        return self.maxAngle, self.minAngle

    def setRanges(self, minRange, maxRange):
        if (minRange > 1000) or (minRange <= 0):    #### FIXME
            logging.error(f"Invalid minRange ({minRange})")
            return
        if (maxRange > 1000) or (maxRange < 0):    #### FIXME
            logging.error(f"Invalid maxRange ({maxRange})")
            return
        if minRange >= maxRange:
            logging.error(f"Invalid minRange and maxRange pair ({minRange} >= {maxRange}))")
            return
        self.minRange = minRange
        self.maxRange = maxRange
        self.laser.setlidaropt(ydlidar.LidarPropMinRange, self.minRange)
        self.laser.setlidaropt(ydlidar.LidarPropMaxRange, self.maxRange)

    def getRanges(self):
        return self.maxRange, self.minRange

    def setScanFreq(self, scanFreq):
        if (scanFreq > MAX_SCAN_FREQ) or (scanFreq < MIN_SCAN_FREQ):
            logging.error(f"Invalid scan frequency ({scanFreq})")
            return
        self.scanFreq = scanFreq
        self.laser.setlidaropt(ydlidar.LidarPropScanFrequency, self.scanFreq)

    def getScanFreq(self):
        return self.scanFreq

    def setSampleRate(self, sampleRate):
        if (sampleRate > MAX_SAMPLE_RATE) or (sampleRate < MIN_SAMPLE_RATE):
            logging.error(f"Invalid sample rate ({sampleRate})")
            return
        self.sampleRate = sampleRate
        self.laser.setlidaropt(ydlidar.LidarPropSampleRate, self.sampleRate)

    def getSampleRate(self):
        return self.sampleRate

    def getVersion(self):
        return LIDAR_VERSION

    def done(self):
        return (not self.laser.turnOff()) or (not self.laser.disconnecting())

