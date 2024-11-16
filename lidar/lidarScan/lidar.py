#!/usr/bin/env python3
'''
################################################################################
#
# YDLIDAR T-mini Lidar Scanner Library
# 
################################################################################
'''

import logging

import ydlidar

#import pdb  ## pdb.set_trace()

LIDAR_VERSION = "1.0.0"

DEF_LOG_LEVEL = "WARNING"

DEF_CONFIGS_FILE = "./.lidar.yaml"
DEF_PORT_PATH = "/dev/ydlidar"
DEF_BAUD_RATE = 230400
DEF_MAX_ANGLE = 180.0   # degrees
DEF_MIN_ANGLE = -180.0  # degrees
DEF_SCAN_FREQ = 10.0    # ????
DEF_MAX_RANGE = 16.0    # ????
DEF_MIN_RANGE = 0.02    # ????
DEF_SCAN_RATE = 4       # ????


class Lidar():
    def __init__(self, **kwargs):
        self.port = kwargs.get('port', None)
        self.baud = kwargs.get('baud', DEF_BAUD_RATE)
        self.scanFreq = kwargs.get('scanFreq', DEF_SCAN_FREQ)
        self.sampleRate = kwargs.get('sampleRate', DEF_SCAN_RATE)
        self.maxAngle = kwargs.get('maxAngle', DEF_MAX_ANGLE)
        self.minAngle = kwargs.get('minAngle', DEF_MIN_ANGLE)
        self.maxRange = kwargs.get('maxRange', DEF_MAX_RANGE)
        self.minRange = kwargs.get('minRange', DEF_MIN_RANGE)
        self.laserScan = None

        ydlidar.os_init()

        if not self.port:
            ports = ydlidar.lidarPortList()
            self.port = DEF_PORT_PATH
            for key, value in ports.items():
                self.port = value
        logging.debug(f"Port: {self.port}")

        self.laser = ydlidar.CYdLidar()
        self.laser.setlidaropt(ydlidar.LidarPropSerialPort, self.port)
        self.laser.setlidaropt(ydlidar.LidarPropSerialBaudrate, self.baud)
        self.laser.setlidaropt(ydlidar.LidarPropLidarType, ydlidar.TYPE_TRIANGLE)
        self.laser.setlidaropt(ydlidar.LidarPropDeviceType, ydlidar.YDLIDAR_TYPE_SERIAL)
        self.laser.setlidaropt(ydlidar.LidarPropScanFrequency, self.scanFreq)
        self.laser.setlidaropt(ydlidar.LidarPropSampleRate, self.sampleRate)
        self.laser.setlidaropt(ydlidar.LidarPropSingleChannel, False)
        self.laser.setlidaropt(ydlidar.LidarPropMaxAngle, self.minAngle)
        self.laser.setlidaropt(ydlidar.LidarPropMinAngle, self.maxAngle)
        self.laser.setlidaropt(ydlidar.LidarPropMaxRange, self.maxRange)
        self.laser.setlidaropt(ydlidar.LidarPropMinRange, self.minRange)
        self.laser.setlidaropt(ydlidar.LidarPropIntenstiy, True)

        if not self.laser.initialize():
            self.laser = None
            logging.error("Failed to initalize laser")
        if not self.laser.turnOn():
            self.laser = None
            logging.error("Failed to turn laser on")
        if not ydlidar.os_isOk():
            self.laser = None
            logger.error("Laser is not OK")
        if not self.laser:
            exit(1)

    def scan(self):
        self.laserScan = ydlidar.LaserScan()
        if not self.laser.doProcessSimple(self.laserScan):
            logging.error("Scan processing failed")
            return None
        if not self.laser.turnOn(): 
            logging.error("Laser failed to turn on")
            return None
        if not ydlidar.os_isOk():
            logging.error("Laser not OK")
            return None
        angles, distances = zip(*[(p.angle, p.range) for p in self.laserScan.points])
        return angles, distances

    '''
    def info(self):
        if not self.laser:
            logging.error("Lidar not initialized")
            return None
        r = self.laser.getDeviceInfo(????)
        print(f"INFO: {r}")
        return(r)
    '''

    def done(self):
        self.laser.turnOff()
        self.laser.disconnecting()

