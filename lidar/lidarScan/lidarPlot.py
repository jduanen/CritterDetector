#!/usr/bin/env python3
'''
################################################################################
#
# YDLIDAR T-mini Lidar Scanner Plotter
# 
################################################################################
'''

#import os

import argparse
from datetime import datetime
from functools import partial
import json
import logging
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
import os
from pytimedinput import timedInput
import signal
import sys
from time import sleep
import yaml

import lidar

import pdb  ## pdb.set_trace()


DEFAULTS = {
    "portPath": "/dev/ydlidar",
    "baudRate": 230400,
    "logLevel": "WARNING",
    "logFile": None,
    "configsFile": "./.lidar.yaml",
    "maxAngle": 180.0,   # degrees (?)
    "minAngle": -180.0,  # degrees (?)
    "scanFreq": 10.0,    # Hz
    "maxRange": 16.0,    # meters
    "minRange": 0.02,    # meters
    "sampleRate": 4,     # K samples/sec
    "numScans": None,    # number of scans to make before exiting, None=loop
    "logData": None,
    "version": lidar.LIDAR_VERSION
}


scanner = None
numFrames = 0
logDataFd = None


def stop():
    if scanner:
        scanner.done()
    if logDataFd:
        print("]", file=logDataFd)
        logDataFd.close()
    logging.debug("Stopped")
    exit(1)

def update(frame, axes, device, maxDistance):
    # clear the axes and replot
    angles, distances, intensities = device.scanIntensity()
    axes.clear()
    axes.plot(angles, distances, 'o-', label='Points')

    if logDataFd:
        if logDataFd.tell() > 2:
            print(",", file=logDataFd)
        print(f"  {{\"sampleTime\": \"{datetime.now()}\", ", file=logDataFd)
        print(f"   \"data\": {[[a, d, i] for a, d, i in zip(angles, distances, intensities)]} }}", end="", file=logDataFd)

    # set rmax to be slightly larger than the max distance
    axes.set_rmax(maxDistance)
    axes.set_title(f"Real-time Radial Plot (Frame {frame})")

def onAnimationEnd():
    global numFrames

    if numFrames > 0:
        numFrames -= 1
        if numFrames <= 0:
            inputStr, timedOut = timedInput("> ", timeout=5)
            while not timedOut and (inputStr and (inputStr[0] != 'q')):
                inputStr, timedOut = timedInput("> ", timeout=5)
            plt.close()
            stop()
            sys.exit()

def getOpts():
    global numFrames, logDataFd

    def signalHandler(sig, frame):
        ''' Catch SIGHUP to force a restart and SIGINT to stop.""
        '''
        if sig == signal.SIGHUP:
            logging.info("SIGHUP")
            logging.error("FIXME: TBD")
        elif sig == signal.SIGINT:
            logging.info("SIGINT")
            stop()
            exit(1)

    usage = f"Usage: {sys.argv[0]} [-v] [-c <configsFile>] [-i] [-L <logLevel>] [-l <logFile>] [-p <portPath>] [-f <scanFreq>] [-s <sampleRate>] [-a <minAngle>] [-A <maxAngle>] [-r <minRange>] [-R <maxRange>] [-n <numScans>] [-d <dataLogFile>]"
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-c", "--configsFile", action="store", type=str,
        help="Path to file with configuration info")
    ap.add_argument(
        "-A", "--maxAngle", action="store", type=float,
        help="Maximum scan angle (degrees)")
    ap.add_argument(
        "-a", "--minAngle", action="store", type=float,
        help="Minimum scan angle (degrees)")
    ap.add_argument(
        "-d", "--logData", action="store", type=str,
        help="Path to file into which sample data is to be written (create if doesn't exist)")
    ap.add_argument(
        "-f", "--scanFreq", action="store", type=float,
        help="Scan Frequency (Hz)")
    ap.add_argument(
        "-n", "--numScans", action="store", type=int,
        help="Number of scans (int)")
    ap.add_argument(
        "-p", "--portPath", action="store", type=str,
        help="Path to lidar device")
    ap.add_argument(
        "-R", "--maxRange", action="store", type=float,
        help="Maximum range (meters)")
    ap.add_argument(
        "-r", "--minRange", action="store", type=float,
        help="Minimum range (meters)")
    ap.add_argument(
        "-s", "--sampleRate", action="store", type=int,
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

    conf = {'version': lidar.LIDAR_VERSION, 'cli': cliOpts, 'confFile': {}, 'config': {}}
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

        if 'version' not in conf['confFile']:
            logging.error("Config file must include version")
            exit(1)
        #### FIXME this only deals with single digit major version number
        fileVersionMajor = int(conf['confFile']['version'][0])
        versionMajor = int(lidar.LIDAR_VERSION[0])
        if fileVersionMajor != versionMajor:
            logging.error(f"Config file version number incorrect ({fileVersionMajor} != {versionMajor})")
            exit(1)

    # options precedence order: cmd line -> conf file -> defaults
    #   cliOpts: cmd line options
    #   conf: conf file options
    #   DEFAULT: default options

    def _configSelect(opt):
        if (opt in conf['cli']) and (conf['cli'][opt] is not None):
            conf[opt] = conf['cli'][opt]
        elif (opt in conf['confFile']) and (conf['confFile'][opt] is not None):
            conf[opt] = conf['confFile'][opt]
        else:
            conf[opt] = DEFAULTS[opt]

    for opt in DEFAULTS.keys():
        _configSelect(opt)

    if cliOpts['verbose'] > 2:
        json.dump(conf, sys.stdout, indent=4, sort_keys=True)
        print("")

    if conf['logFile']:
        logging.basicConfig(filename=conf['logFile'], level=conf['logLevel'])
    else:
        logging.basicConfig(level=conf['logLevel'])

    if conf['logData']:
        if os.path.exists(conf['logData']):
            logging.error(f"Log data file already exists: {conf['logData']}")
            exit(1)
        logDataFd = open(conf['logData'], 'w')
        print("[", file=logDataFd)

    if conf['numScans'] is None:
        conf['numScans'] = 10000000   #### FIXME
        numFrames = 0
    else:
        numFrames = conf['numScans']

    signal.signal(signal.SIGHUP, signalHandler)
    signal.signal(signal.SIGINT, signalHandler)
    return conf

def run(options):
    scanner = lidar.Lidar(**options)
    if scanner:
        fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
        ani = FuncAnimation(fig, update, fargs=(ax, scanner, options['maxRange']),
                            frames=options['numScans'], interval=(1000 / options['scanFreq']),
                            blit=False, repeat=(options['numScans'] == 0))
        ani.event_source.add_callback(onAnimationEnd)
        plt.show()
    plt.close()
    stop()


if __name__ == '__main__':
    opts = getOpts()
    run(opts)
