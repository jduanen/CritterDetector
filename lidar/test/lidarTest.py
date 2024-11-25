#!/home/jdn/.virtualenvs/LIDAR/bin/python3

import os
import ydlidar
import time


def lidarInit():
    ydlidar.os_init()

    ports = ydlidar.lidarPortList()
    port = "/dev/ydlidar"
    for key, value in ports.items():
        port = value
        print(port)  ## TMP TMP TMP

    laser = ydlidar.CYdLidar()
    laser.setlidaropt(ydlidar.LidarPropSerialPort, port)
    laser.setlidaropt(ydlidar.LidarPropSerialBaudrate, 230400)
    laser.setlidaropt(ydlidar.LidarPropLidarType, ydlidar.TYPE_TRIANGLE)
    laser.setlidaropt(ydlidar.LidarPropDeviceType, ydlidar.YDLIDAR_TYPE_SERIAL)
    laser.setlidaropt(ydlidar.LidarPropScanFrequency, 10.0)
    laser.setlidaropt(ydlidar.LidarPropSampleRate, 4)
    laser.setlidaropt(ydlidar.LidarPropSingleChannel, False)
    laser.setlidaropt(ydlidar.LidarPropMaxAngle, 180.0)
    laser.setlidaropt(ydlidar.LidarPropMinAngle, -180.0)
    laser.setlidaropt(ydlidar.LidarPropMaxRange, 16.0)
    laser.setlidaropt(ydlidar.LidarPropMinRange, 0.02)
    laser.setlidaropt(ydlidar.LidarPropIntenstiy, True)

    if not laser.initialize() or not laser.turnOn() or not ydlidar.os_isOk():
        laser = None
    return laser

def lidarDone():
    laser.turnOff()
    laser.disconnecting()

def getScan():
    scan = ydlidar.LaserScan()
    if not laser.doProcessSimple(scan) or not laser.turnOn() or not ydlidar.os_isOk():
        print(f"Failed to get lidar data: {r}")
        scan = None
    return scan

if __name__ == "__main__":
    laser = lidarInit()
    if laser:
        i = 0
        while True:
            scan = getScan()
            if scan:
                print(f"Scan [{scan.stamp}]: #points={scan.points.size()}, timeFromLastScan=[{scan.config.scan_time}]")
                j = 0
                for pt in scan.points:
                    print(f"{pt.angle}, {pt.range}")
                    j += 1
                    if j > 10:
                        break
                i += 1
                if i > 10:
                    break
            else:
                time.sleep(0.05)
    lidarDone()
