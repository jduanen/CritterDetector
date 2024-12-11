#!/usr/bin/env python3
################################################################################
#
# YDLIDAR (T-mini Pro) Lidar Scanner Library
# 
################################################################################

import logging

from ..shared import (MIN_ANGLE, MAX_ANGLE, MIN_SAMPLE_RATE, MAX_SAMPLE_RATE,
                      MIN_SCAN_FREQ, MAX_SCAN_FREQ)

import ydlidar

#import pdb  ## pdb.set_trace()


#### TODO
####  * laser: setAutoIntensity, enableGlassNoise, enableSunNoise, getDeviceInfo, getUserVersion
####  * use asyncio and add streaming option
####    - keep sending points until get END message
####    - while in STREAM mode can handle: HALT and STATUS messages, as well as GET and VERSION commands
####    - exit STREAM mode when get: INIT, STOP, SET, SCAN, LASER
####    - N.B. lidar calls are blocking, so be careful with async
####  * make this error out properly if the device isn't found in /dev/tty????


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


class Lidar():
    LIDAR_VERSION = "1.3.0"

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
        self.numScans = None

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
        if not self.laser.turnOff():
            logging.error("Failed to turn laser off")
            exit(1)
        self.laserScan = ydlidar.LaserScan()
        self.streaming = False

    def laserEnable(self, enable):
        if enable:
            if not self.laser.turnOn():
                logging.error("Failed to turn laser on")
                return True
            self.laserScan = ydlidar.LaserScan()
        else:
            if not self.laser.turnOff():
                logging.error("Failed to turn laser off")
                return True
            self.streaming = False
        return False

    def scan(self, names=['angles', 'distances', 'intensities']):
        print("SCAN:::::::::")
        self.streaming = False
        ret = self.laser.doProcessSimple(self.laserScan)
        print(f"> {ret}, {ydlidar.os_isOk()}, {self.laserScan.points}")
        while not (ret and ydlidar.os_isOk() and self.laserScan.points):
            self.laser.turnOn()
            self.laserScan = ydlidar.LaserScan()
            self.laser.turnOff()
            ret = self.laser.doProcessSimple(self.laserScan)
            print(f">> {ret}, {ydlidar.os_isOk()}, {self.laserScan.points}")

        angles, distances, intensities = zip(*[(p.angle, p.range, int(p.intensity)) for p in self.laserScan.points if not (self.zeroFilter and (p.range <= 0))])

        results = {}
        if 'angles' in names:
            results['angles'] = angles
        if 'distances' in names:
            results['distances'] = distances
        if 'intensities' in names:
            results['intensities'] = intensities
        return results

    def stream(self, names):
        print("STREAM!!!!!!!!!!!!!!!!!!!!!")
        self.streaming = True
        self.numScans = 0
        while self.streaming:
            self.numScans += 1
            ret = self.laser.doProcessSimple(self.laserScan)
            print(f"::::: {ret}, {ydlidar.os_isOk()}, {self.laserScan.points}")
            if not (ret and ydlidar.os_isOk() and self.laserScan.points):
                print("^")
                yield None
            results = {name: [] for name in names}
            for p in self.laserScan.points:
                if self.zeroFilter and (p.range <= 0):
                    #### TODO add info here?
                    continue
                if 'angles' in names:
                    results['angles'].append(p.angle)
                if 'distances' in names:
                    results['distances'].append(p.range)
                if 'intensities' in names:
                    results['intensities'].append(int(p.intensity))
            print("TTTTTT")
            yield results

    '''
    def info(self):
        if not self.laser:
            logging.error("Lidar not initialized")
            return None
        r = self.laser.getDeviceInfo(????)
        print(f"INFO: {r}")
        return(r)
    '''

    def status(self):
        stat = {'laser': None, 'ok': ydlidar.os_isOk(), 'scanning': None,
                'streaming': self.streaming, 'numScans': self.numScans,
                'minAngle': self.minAngle, 'maxAngle': self.maxAngle, 
                'minRange': self.minRange, 'maxRange': self.maxRange,
                'scanFreq': self.scanFreq, 'sampleRate': self.sampleRate}
        if self.laser:
            stat['laser'] = True
            stat['scanning'] = self.laser.isScanning()
        return stat

    def setAngles(self, minAngle, maxAngle):
        if minAngle >= maxAngle:
            logging.error(f"Invalid minAngle and maxAngle pair ({minAngle} >= {maxAngle}))")
            return True
        return self.setMinAngle(minAngle) or self.setMaxAngle(maxAngle)

    def setMinAngle(self, angle):
        if (angle > MAX_ANGLE) or (angle < MIN_ANGLE):
            logging.error(f"Invalid minAngle ({angle})")
            return True
        self.minAngle = angle
        return not self.laser.setlidaropt(ydlidar.LidarPropMinAngle, self.minAngle)

    def setMaxAngle(self, angle):
        if (angle > 180.0) or (angle < -180.0):
            logging.error(f"Invalid maxAngle ({angle})")
            return True
        self.maxAngle = angle
        return not self.laser.setlidaropt(ydlidar.LidarPropMaxAngle, self.maxAngle)

    def getAngles(self):
        return self.maxAngle, self.minAngle

    def setRanges(self, minRange, maxRange):
        if minRange >= maxRange:
            logging.error(f"Invalid minRange and maxRange pair ({minRange} >= {maxRange}))")
            return True
        return self.setMinRange(minRange) or self.setMaxRange(maxRange)

    def setMinRange(self, range):
        if (range > 1000) or (range <= 0):    #### FIXME
            logging.error(f"Invalid minRange ({range})")
            return True
        self.minRange = range
        return not self.laser.setlidaropt(ydlidar.LidarPropMinRange, self.minRange)

    def setMaxRange(self, range):
        if (range > 1000) or (range < 0):    #### FIXME
            logging.error(f"Invalid maxRange ({range})")
            return True
        self.maxRange = range
        return not self.laser.setlidaropt(ydlidar.LidarPropMaxRange, self.maxRange)

    def getRanges(self):
        return self.maxRange, self.minRange

    def setScanFreq(self, scanFreq):
        if (scanFreq > MAX_SCAN_FREQ) or (scanFreq < MIN_SCAN_FREQ):
            logging.error(f"Invalid scan frequency ({scanFreq})")
            return True
        self.scanFreq = scanFreq
        return not self.laser.setlidaropt(ydlidar.LidarPropScanFrequency, self.scanFreq)

    def getScanFreq(self):
        return self.scanFreq

    def setSampleRate(self, sampleRate):
        if (sampleRate > MAX_SAMPLE_RATE) or (sampleRate < MIN_SAMPLE_RATE):
            logging.error(f"Invalid sample rate ({sampleRate})")
            return True
        self.sampleRate = sampleRate
        return not self.laser.setlidaropt(ydlidar.LidarPropSampleRate, self.sampleRate)

    def getSampleRate(self):
        return self.sampleRate

    def getVersion(self):
        return Lidar.LIDAR_VERSION

    def done(self):
        self.streaming = False
        ydlidar.os_shutdown()
        res = (not self.laser.turnOff()) or (not self.laser.disconnecting())
        self.laser = None
        self.laserScan = None
        self.laserEnable = False
        return res

