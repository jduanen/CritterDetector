#!/usr/bin/env python3
'''
################################################################################
#
# YDLIDAR T-mini Lidar Scanner Plotter
# 
################################################################################
'''

from functools import partial
import logging
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
import signal
from time import sleep

import lidar

#import pdb  ## pdb.set_trace()

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
    axes.set_rmax(4)  #### FIXME
    axes.set_title(f"Real-time Radial Plot (Frame {frame})")

'''
lidar_polar = plt.subplot(polar=True)
lidar_polar.autoscale_view(True,True,True)
lidar_polar.grid(True)
'''

def getOpts():
    def signalHandler(sig, frame):
        ''' Catch SIGHUP to force a reload/restart and SIGINT to stop all.""
        '''
        if sig == signal.SIGHUP:
            logging.info("SIGHUP")
            #### TODO stop, reload, and restart everything
        elif sig == signal.SIGINT:
            logging.info("SIGINT")
            stop()

    signal.signal(signal.SIGHUP, signalHandler)
    signal.signal(signal.SIGINT, signalHandler)

    options = {'confs': {'numFrames': 25, 'delay': 100}}  #### FIXME
    return options

def run(options):
    scanner = lidar.Lidar()
    if scanner:
        fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
        numFrames = options['confs']['numFrames']
        delay = options['confs']['delay']
        ani = FuncAnimation(fig, update, fargs=(ax, scanner),
                            frames=numFrames, interval=delay,
                            blit=False, repeat=True)
        plt.show()
    plt.close()
    stop()


if __name__ == '__main__':
    opts = getOpts()
    run(opts)
