import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from shapely import union_all
from shapely.geometry import Polygon, MultiPolygon
import numpy as np
import lidar


fig = None
ax = None
scanner = None
points = None
refArea = 0

def init():
    global scanner
    scanner = lidar.Lidar(zeroFilter=True)

def polarToCartesian(theta, r):
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    return x, y

def scan():
    angles, distances, intensities = scanner.scanIntensity()
    polarCoords = [[theta, r] for theta, r in zip(angles, distances)]
    cartCoords = [polarToCartesian(theta, r) for theta, r in zip(angles, distances)]
    return polarCoords, cartCoords

def polarPlot(polarCoords, color):
    global fig, ax
    angles, distances = zip(*polarCoords)
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
    ax.plot(angles, distances, 'o-', color=color)
    ax.fill(angles, distances, alpha=0.3, color=color)

def cartPlot(cartCoords, color):
    global fig, ax
    x, y = zip(*cartCoords)
    fig, ax = plt.subplots()
    ax.plot(x, y, 'o-', color=color)
    ax.fill(x, y, alpha=0.3, color=color)

def plotScan(polar = False, color = 'red'):
    polarCoords, cartCoords = scan()
    if (polar):
        polarPlot(polarCoords, color)
    else:
        cartPlot(cartCoords, color)
    plt.show()
    return polarCoords, cartCoords

def stack():
    COLORS = ['red', 'green', 'blue', 'cyan', 'magenta', 'yellow']
    fig, ax = plt.subplots()
    for i in range(100):
        c = COLORS[i % len(COLORS)]
        polarCoords, cartCoords = scan()
        x, y = zip(*cartCoords)
        ax.plot(x, y, 'o-', color=c)
        ax.fill(x, y, alpha=0.3, color='gray')

    plt.show()

def shrink(poly):
    #### FIXME
    return poly

def intersect(num=1):
    poly = None
    for i in range(num):
        polarCoords, cartCoords = scan()
        if poly:
            p = Polygon(cartCoords)
            poly = union_all([poly, p])
        else:
            poly = Polygon(cartCoords)
        break
    return poly

def stop():
    if scanner:
        scanner.done()
    print("Stopped")
    exit(1)

def update(frame, ax, foo):
    polarCoords, cartCoords = scan()
    x, y = zip(*cartCoords)
    ax.plot(list(x), list(y), 'o', color='cyan')

def plot(tol, num):
    fig, ax = plt.subplots()

    # plot a raw snapshot
    polarCoords, cartCoords = scan()
    x, y = zip(*cartCoords)
    print(f"Snapshot: {len(x)}")
    ax.plot(x, y, 'o-', color='red')

    # intersect num scans and plot
    poly = intersect(num)
    xy = poly.exterior.coords
    x, y = zip(*xy)
    print(f"Intersect: {len(x)}")
    ax.plot(x, y, 'o-', color='green')
    ax.fill(x, y, alpha=0.3, color='gray')

    # simplify the intersected scans
    poly = poly.simplify(tolerance=tol)
    xy = poly.exterior.coords
    x, y = zip(*xy)
    print(f"Simplified: {len(x)}")
    ax.plot(x, y, 'o-', color='blue')
    ax.fill(x, y, alpha=0.3, color='gray')

    # show realtime scans
    ani = FuncAnimation(fig, update, fargs=(ax, 1), frames=10000000,
                        interval=(1000 / scanner.scanFreq),
                        blit=False, repeat=True)
    plt.show()

minDiff = 10000
maxDiff = 0
avgDiff = 0

def updateDots(frame, ax, foo):
    global points
    global minDiff, maxDiff, avgDiff
    angles, distances, intensities = scanner.scanIntensity()
    cartCoords = [polarToCartesian(theta, r) for theta, r in zip(angles, distances)]
    poly = Polygon(cartCoords)
    polyArea = poly.area
    areaDiff = refArea - polyArea
    if abs(areaDiff) < abs(minDiff):
        minDiff = areaDiff
    if abs(areaDiff) > abs(maxDiff):
        maxDiff = areaDiff
    avgDiff = (avgDiff + areaDiff) / 2
    print(f"minDiff: {minDiff}, avgDiff: {avgDiff}, maxDiff: {maxDiff}\r", end="")
    xy = poly.exterior.coords
    x, y = zip(*xy)
    if points:
        points.remove()
    points = ax.scatter(x, y, marker='o', c='blue')

def detect(margin=-0.0025, tol=0.02, num=50):
    global refArea
    fig, ax = plt.subplots()

    # get reference area and plot it
    refPoly = MultiPolygon()
    while refPoly.geom_type != 'Polygon':
        poly = intersect(num)
        if tol:
            poly = poly.simplify(tolerance=tol)
        refPoly = poly.buffer(margin)
    refArea = refPoly.area
    print(f"Ref Area: {refArea}")
    xy = refPoly.exterior.coords
    x, y = zip(*xy)
    ax.plot(x, y, 'o-', color='green')
    ax.fill(x, y, alpha=0.3, color='gray')

    # get scans, plot them, and compare their area
    ani = FuncAnimation(fig, updateDots, fargs=(ax, 1), frames=1000,
                        interval=(1000 / scanner.scanFreq),
                        blit=False, repeat=True)
    plt.show()

'''
+def getRef(tol=0.02, num=50):
+    poly = intersect(num)
+    if tol:
+        poly = poly.simplify(tolerance=tol)
+    return poly
'''

TEST = 1


if __name__ == '__main__':
    init()
    if TEST == 0:
        plot(0.02, 50)
    elif TEST == 1:
        detect(-0.01, 0.02, 50)
    stop()
