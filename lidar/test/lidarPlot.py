#!/home/jdn/.virtualenvs/LIDAR/bin/python3

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from functools import partial

from lidarTest import *


laser = None


def XgetScanX():
    scan = [((np.random.uniform(0, 2*np.pi)), (np.random.uniform(0, 10))) for i in range(10)]
    print(f"S: {len(scan)}; {scan}")
    return scan

def update(frame):
    angles, distances = zip(*[(p[0], p[1]) for p in getScan()])
    print(f"a: {angles[0]}, {len(angles)}")
    print(f"d: {distances[0]}, {len(distances)}")

    # Clear the axis and replot
    ax.clear()
    ax.scatter(angles, distances)
    
    # Set the rmax to be slightly larger than the max distance
    ax.set_ylim(0, max(max(distances), 10))
    
    # Add title
    ax.set_title(f"Real-time Radial Plot (Frame {frame})")


if __name__ == "__main__":
    laser = lidarInit()
    if laser:
        fig, ax = plt.subplots(subplot_kw=dict(projection='polar'))

        # TODO add init_func to draw initial perimeter
        ani = FuncAnimation(fig, update, frames=20, interval=100, repeat=False)
        plt.show()
    lidarDone()
