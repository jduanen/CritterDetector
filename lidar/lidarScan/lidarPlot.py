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
    def __init__(self):
        plt.ion()
        self.fig, self.ax = plt.subplots(subplot_kw={'projection': 'polar'})
        plt.show
        self.frameNum = 0

    def update(self, angles, distances):
        print(f"a: {angles[0]}, {len(angles)}")  #### TMP TMP TMP
        print(f"d: {distances[0]}, {len(distances)}")  #### TMP TMP TMP

        # clear the axes and replot
        self.ax.clear()
        self.ax.scatter(angles, distances)
        #self.scatter.set_offsets(np.column_stack((angles, distances)))
        #self.ax.plot(angles, distances, 'o-', label='Points')

        # set rmax to be slightly larger than the max distance
        self.ax.set_ylim(0, max(max(distances), 10))
        self.ax.set_title(f"Real-time Radial Plot (Frame {self.frameNum})")
        plt.draw()
        self.frameNum += 1

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
    options = {'confs': {'numFrames': 10, 'delay': 1}}  #### FIXME
    return options

def run(options):
    scanner = lidar.Lidar()
    if scanner:
        animator = Animator()
        ##pdb.set_trace()
        numFrames = options['confs']['numFrames']
        delay = options['confs']['delay']
        while numFrames > 0:
            angles, distances = scanner.scan()
            animator.update(angles, distances)
            numFrames -= 1
            sleep(delay)
    scanner.done()

        # TODO add init_func to draw initial perimeter
#        ani = FuncAnimation(fig, partial(update, axes=ax, device=scanner),
#                            frames=options['confs']['numFrames'],
#                            interval=options['confs']['delay'], repeat=False)
#        plt.show()

if __name__ == '__main__':
    opts = getOpts()
    run(opts)
