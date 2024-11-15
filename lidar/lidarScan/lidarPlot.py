#!/usr/bin/env python3
'''
################################################################################
#
# YDLIDAR T-mini Lidar Scanner Plotter
# 
################################################################################
'''

from functools import partial
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
from time import sleep

import lidar

import pdb


class Animator:
    def __init__(self, ax, scanner):
        self.ax = ax
        self.scanner = scanner
        self.scatter = ax.plot([], [], 'ro')[0]  # red dots

    def init(self):
        self.scatter.set_data([], [])
        return self.scatter

    def update(self, frame):
        # clear the axes and replot
        angles, distances = self.scanner.scan()
        self.ax.clear()
        self.ax.scatter(angles, distances)
        ##self.ax.plot(angles, distances, 'o-', label='Points')

        # set rmax to be slightly larger than the max distance
        self.ax.set_ylim(0, max(max(distances), 10))
        self.ax.set_title(f"Real-time Radial Plot (Frame {frame})")

def getOpts():
    def signalHandler(sig, frame):
        ''' Catch SIGHUP to force a reload/restart and SIGINT to stop all.""
        '''
        if sig == signal.SIGHUP:
            logging.info("SIGHUP")
            #### TODO stop, reload, and restart everything
        elif sig == signal.SIGINT:
            logging.info("SIGINT")
            for vin in cmdQs:
                logging.debug(f"Stopping: {vin}")
                cmdQs[vin].put("STOP")
    options = {'confs': {'numFrames': 10, 'delay': 100}}  #### FIXME
    return options

def run(options):
    scanner = lidar.Lidar()
    if scanner:
        fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
        animator = Animator(ax, scanner)
        numFrames = options['confs']['numFrames']
        delay = options['confs']['delay']

        ##pdb.set_trace()
        ani = FuncAnimation(fig, func=animator.update, init_func=animator.init,
                            frames=numFrames, interval=delay, blit=False)
        plt.show()
    scanner.done()


if __name__ == '__main__':
    opts = getOpts()
    run(opts)
