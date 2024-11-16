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
from functools import partial
import json
import logging
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
import os
import signal
import sys
from time import sleep
import yaml

import lidar

#import pdb  ## pdb.set_trace()


DEFAULTS = {
    "portPath": "/dev/ydlidar",
    "baudRate": 230400,
    "logLevel": "WARNING",
    "logFile": None,
    "configsFile": "./.lidar.yaml",
    "angleMax": 180.0,   # degrees (?)
    "angleMin": -180.0,  # degrees (?)
    "freq": 10.0,        # Hz
    "rangeMax": 16.0,    # meters
    "rangeMin": 0.02,    # meters
    "sampleRate": 4,     # K samples/sec
    "numScans": 100,     # number of scans to make before exiting
    "version": lidar.LIDAR_VERSION
}


scanner = None


def stop():
    if scanner:
        scanner.done()
    logging.debug("Stopped")
    exit(1)

def update(frame, axes, device):
    # clear the axes and replot
    angles, distances = device.scan()
    axes.clear()
    axes.plot(angles, distances, 'o-', label='Points')

    # set rmax to be slightly larger than the max distance
    axes.set_rmax(max(max(distances), 2))  #### FIXME
    axes.set_title(f"Real-time Radial Plot (Frame {frame})")

'''
lidar_polar = plt.subplot(polar=True)
lidar_polar.autoscale_view(True,True,True)
lidar_polar.grid(True)
'''

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

    usage = f"Usage: {sys.argv[0]} [-v] [-c <configsFile>] [-i] [-L <logLevel>] [-l <logFile>] [-p <portPath>] [-f <scanFreq>] [-s <sampleRate>] [-a <minAngle>] [-A <maxAngle>] [-r <minRange>] [-R <maxRange>] [-n <numScans>]"
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
    scanner = lidar.Lidar(**options)
    if scanner:
        fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
        ani = FuncAnimation(fig, update, fargs=(ax, scanner),
                            frames=options['numScans'],
                            interval=100,    #### FIXME make a function of scan frequency
                            blit=False, repeat=True)
        plt.show()
    plt.close()
    stop()


if __name__ == '__main__':
    opts = getOpts()
    run(opts)
