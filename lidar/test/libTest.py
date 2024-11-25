#!/usr/bin/env python3

from lidar import *

if __name__ == "__main__":
    scanner = Lidar()
    if not scanner:
        print("ERROR")

    theta, r, intensity = scanner.scanIntensity()
    thetaLen = len(theta)
    rLen = len(r)
    intensityLen = len(intensity)
    print(f"Sizes: {thetaLen}, {rLen}, {intensityLen}")
    if (thetaLen == rLen == intensityLen > 100):
        print("SUCCESS")
    else:
        print("FAILED")
