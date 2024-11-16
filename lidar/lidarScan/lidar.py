#!/usr/bin/env python3
'''
################################################################################
#
# YDLIDAR T-mini Lidar Scanner Library
# 
################################################################################
'''

import argparse
import json
import logging
import os
import signal
import sys
import time
import yaml

import ydlidar

import pdb  ## pdb.set_trace()


DEFAULTS = {
    "portPath": "/dev/ydlidar",
    "baudRate": 230400,
    "logLevel": "WARNING",
    "logFile": None,
    "configsFile": "./.lidar.yaml",
    "angleMax": 180.0,   # degrees (?)
    "angleMin": -180.0,  # degrees (?)
    "freq": 10.0,        # ????
    "rangeMax": 16.0,    # ????
    "rangeMin": 0.02,    # ????
    "scanRate": 4,       # ????
    "numScans": 100,     # ????
    "version": "1.0.0"
}


_lidar = None


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
            self.port = "/dev/ydlidar"
            for key, value in ports.items():
                self.port = value
        logging.debug(f"Port: {self.port}")  #### TMP TMP TMP

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

    def done(self):
        self.laser.turnOff()
        self.laser.disconnecting()


def getOpts():
    def signalHandler(sig, frame):
        ''' Catch SIGHUP to force a restart and SIGINT to stop.""
        '''
        if sig == signal.SIGHUP:
            logging.info("SIGHUP")
            logging.error("FIXME: TBD")
        elif sig == signal.SIGINT:
            logging.info("SIGINT")
            if _lidar:
                _lidar.done()
            exit(1)

    usage = f"Usage: {sys.argv[0]} [-v] [-c <configsFile>] [-i] [-L <logLevel>] [-l <logFile>] [-p <portPath>] [-f <scanFreq>] [-s <scanRate>] [-a <minAngle>] [-A <maxAngle>] [-r <minRange>] [-R <maxRange>] [-n <numScans>]"
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-c", "--configsFile", action="store", type=str,
        help="Path to file with configuration info")
    ap.add_argument(
        "-A", "--angleMax", action="store", type=float,
        help="Maximum scan angle (degrees)")
    ap.add_argument(
        "-a", "--angleMin", action="store", type=float,
        help="Minimum scan angle (degrees)")
    ap.add_argument(
        "-f", "--freq", action="store", type=float,
        help="Scan Frequency (Hz)")
    ap.add_argument(
        "-n", "--numScans", action="store", type=int,
        help="Number of scans (int)")
    ap.add_argument(
        "-p", "--portPath", action="store", type=str,
        help="Path to lidar device")
    ap.add_argument(
        "-R", "--rangeMax", action="store", type=float,
        help="Maximum range (meters)")
    ap.add_argument(
        "-r", "--rangeMin", action="store", type=float,
        help="Minimum range (meters)")
    ap.add_argument(
        "-s", "--scanRate", action="store", type=int,
        help="???? (int)")
    ap.add_argument(
        "-L", "--logLevel", action="store", type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level")
    ap.add_argument(
        "-l", "--logFile", action="store", type=str,
       help="Path to location of logfile (create it if it doesn't exist)")
    ap.add_argument(
        "-v", "--verbose", action="count", default=0,
        help="print debug info")
    cliOpts = ap.parse_args().__dict__

    conf = {'version': '1.0.0', 'cli': cliOpts, 'confFile': {}, 'config': {}}
    if cliOpts['configsFile']:
        if not os.path.exists(cliOpts['configsFile']):
            logging.error(f"Invalid configuration file: {cliOpts['configsFile']}")
            exit(1)
        with open(cliOpts['configsFile'], "r") as confsFile:
            confs = list(yaml.load_all(confsFile, Loader=yaml.Loader))
            if len(confs) >= 1:
                conf['confFile'] = confs[0]
                if len(confs) > 1:
                    logging.warning(f"Multiple config docs in file. Using the first one")

    # options precedence order: cmd line -> conf file -> defaults
    #   cliOpts: cmd line options
    #   conf: conf file options
    #   DEFAULT: default options

    def _configSelect(opt):
        if opt in conf['cli'] and conf['cli'][opt]:
            conf[opt] = conf['cli'][opt]
        elif opt in conf['confFile'] and conf['confFile'][opt]:
            conf[opt] = conf['confFile'][opt]
        else:
            conf[opt] = DEFAULTS[opt]

    for opt in DEFAULTS.keys():
        _configSelect(opt)

    if cliOpts['verbose'] > 2:
        print("CONF2")
        json.dump(conf, sys.stdout, indent=4, sort_keys=True)
        print("")

    if conf['logFile']:
        logging.basicConfig(filename=conf['logFile'], level=conf['logLevel'])
    else:
        logging.basicConfig(level=conf['logLevel'])

    signal.signal(signal.SIGHUP, signalHandler)
    signal.signal(signal.SIGINT, signalHandler)
    return conf


def run(options):
    _lidar = Lidar()
    while options.numScans is None or options.numScans > 0:
        scan = _lidar.scan()
        if scan:
            print(f"Scan [{scan.stamp}]: #points={scan.points.size()}, timeFromLastScan=[{scan.config.scan_time}]")
            j = 0
            for pt in scan.points:
                print(f"{pt.angle}, {pt.range}")
                j += 1
                if j > 10:
                    break
            if options.numScans:
                options.numScans -= 1
        else:
            time.sleep(0.05)
    _lidar.done()
    _lidar = None


if __name__ == '__main__':
    opts = getOpts()
    run(opts)
