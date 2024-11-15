#!/usr/bin/env python3
'''
################################################################################
#
# YDLIDAR T-mini Lidar Scanner Library
# 
################################################################################
'''

import argparse
import logging
import os
import signal
import sys
import time

import ydlidar


DEF_LOG_LEVEL = "WARNING"

DEF_CONFIGS_FILE = "./.lidar.yaml"
DEF_PORT_NAME = "/dev/ydlidar"
DEF_BAUD_RATE = 230400
DEF_MAX_ANGLE = 180.0   # ????
DEF_MIN_ANGLE = -180.0  # ????
DEF_SCAN_FREQ = 10.0    # ????
DEF_MAX_RANGE = 16.0    # ????
DEF_MIN_RANGE = 0.02    # ????
DEF_SCAN_RATE = 4       # ????


class Lidar():
    '''????
    '''

    def __init__(self, port=None, baud=DEF_BAUD_RATE, scanFreq=DEF_SCAN_FREQ,
                 sampleRate=DEF_SCAN_RATE, maxAngle=DEF_MAX_ANGLE, minAngle=DEF_MIN_ANGLE,
                 maxRange=DEF_MAX_RANGE, minRange=DEF_MIN_RANGE):
        '''????
        '''
        self.laserScan = None
        ydlidar.os_init()

        if not port:
            ports = ydlidar.lidarPortList()
            port = "/dev/ydlidar"
            for key, value in ports.items():
                port = value
        logging.debug(f"Port: {port}")

        self.laser = ydlidar.CYdLidar()
        self.laser.setlidaropt(ydlidar.LidarPropSerialPort, port)
        self.laser.setlidaropt(ydlidar.LidarPropSerialBaudrate, baud)
        self.laser.setlidaropt(ydlidar.LidarPropLidarType, ydlidar.TYPE_TRIANGLE)
        self.laser.setlidaropt(ydlidar.LidarPropDeviceType, ydlidar.YDLIDAR_TYPE_SERIAL)
        self.laser.setlidaropt(ydlidar.LidarPropScanFrequency, scanFreq)
        self.laser.setlidaropt(ydlidar.LidarPropSampleRate, sampleRate)
        self.laser.setlidaropt(ydlidar.LidarPropSingleChannel, False)
        self.laser.setlidaropt(ydlidar.LidarPropMaxAngle, minAngle)
        self.laser.setlidaropt(ydlidar.LidarPropMinAngle, maxAngle)
        self.laser.setlidaropt(ydlidar.LidarPropMaxRange, maxRange)
        self.laser.setlidaropt(ydlidar.LidarPropMinRange, minRange)
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

    def done(self):
        '''????
        '''
        self.laser.turnOff()
        self.laser.disconnecting()

    def scan(self):
        '''????
        '''
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


def getOps():
    def signalHandler(sig, frame):
        ''' Catch SIGHUP to force a restart and SIGINT to stop.""
        '''
        if sig == signal.SIGHUP:
            logging.info("SIGHUP")
            #### TODO stop, reload, and restart everything
        elif sig == signal.SIGINT:
            logging.info("SIGINT")
            #### TODO stop everything and exit

    usage = f"Usage: {sys.argv[0]} [-v] [-c <configsFile>] [-i] [-L <logLevel>] [-l <logFile>] [-p <portName>] [-f <scanFreq>] [-s <scanRate>] [-a <minAngle>] [-A <maxAngle>] [-r <minRange>] [-R <maxRange>] [-n <numScans>]"
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-c", "--configsFile", action="store", type=str,
        default=DEF_CONFIGS_FILE, help="Path to file with configuration info")
    ap.add_argument(
        "-A", "--angleMax", action="store", type=float, default=DEF_MAX_ANGLE,
        help="Maximum scan angle (degrees)")
    ap.add_argument(
        "-a", "--angleMin", action="store", type=float, default=DEF_MIN_ANGLE,
        help="Minimum scan angle (degrees)")
    ap.add_argument(
        "-f", "--freq", action="store", type=float, default=DEF_SCAN_FREQ,
        help="Scan Frequency (Hz)")
    ap.add_argument(
        "-n", "--numScans", action="store", type=int, help="Number of scans (int)")
    ap.add_argument(
        "-p", "--portPath", action="store", type=str, default=DEF_PORT_NAME,
        help="Path to lidar device")
    ap.add_argument(
        "-R", "--rangeMax", action="store", type=float, default=DEF_MAX_RANGE,
        help="Maximum range (meters)")
    ap.add_argument(
        "-r", "--rangeMin", action="store", type=float, default=DEF_MIN_RANGE,
        help="Minimum range (meters)")
    ap.add_argument(
        "-s", "--scanRate", action="store", type=int, default=DEF_SCAN_RATE,
        help="???? (int)")
    ap.add_argument(
        "-L", "--logLevel", action="store", type=str, default=DEF_LOG_LEVEL,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level")
    ap.add_argument(
        "-l", "--logFile", action="store", type=str,
       help="Path to location of logfile (create it if it doesn't exist)")
    ap.add_argument(
        "-v", "--verbose", action="count", default=0, help="print debug info")
    opts = ap.parse_args()

    if opts.configsFile and opts.configsFile != '-':
        if not os.path.exists(opts.configsFile):
            logging.error(f"Invalid configuration file: {opts.configsFile}")
            exit(1)
        with open(opts.configsFile, "r") as confsFile:
            confs = list(yaml.load_all(confsFile, Loader=yaml.Loader))[0]
        if opts.verbose > 3:
            json.dump(confs, sys.stdout, indent=4, sort_keys=True)    #### TMP TMP TMP
        print("")
    else:
        confs = {'config': []}

    #### FIXME
    '''
    if opts.logLevel:
        confs['config']['logLevel'] = opts.logLevel
    else:
        if 'logLevel' not in confs['config']:
            confs['config']['logLevel'] = DEF_LOG_LEVEL
    logLevel = confs['config']['logLevel']
    '''
    logLevel = DEF_LOG_LEVEL
    l = getattr(logging, logLevel, None)
    if not isinstance(l, int):
        fatalError(f"Invalid log level: {logLevel}")

    '''
    if opts.logFile:
        confs['config']['logFile'] = opts.logFile
    logFile = confs['config'].get('logFile')
    '''
    ####logFile = "lidar.log"
    if opts.verbose:
        print(f"Logging to: {logFile}")
    if logFile:
        logging.basicConfig(filename=logFile, level=l)
    else:
        logging.basicConfig(level=l)

    signal.signal(signal.SIGHUP, signalHandler)
    signal.signal(signal.SIGINT, signalHandler)

    opts.confs = confs
    return opts

def run(options):
    lidar = Lidar()
    while options.numScans is None or options.numScans > 0:
        scan = lidar.scan()
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
    lidar.done()


if __name__ == '__main__':
    opts = getOpts()
    run(opts)
