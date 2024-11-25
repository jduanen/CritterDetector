#!/usr/bin/env python3
'''
################################################################################
#
# YDLIDAR T-mini Lidar Scanner Library (T-mini Pro) with Web Sockets interface
#
# WS Interface:
#
# Specs:
# * Laser wavelength: 895-915nm (905nm typ)
# * Laser power: 16W (max) Class I
# * Supply power: 5V
# * Current:
#   - startup: 1A (peak), .84A (typ)
#   - working: 340mA (typ), 480mA (peak)
#   - sleeping: 45mA (max)
# * Angle reference: 0 degs is direction of arrow on top (right side, connector down)
# * Operating temperature: -10C (min), 40C (max)
# 
################################################################################
'''

import asyncio
import json
import logging
import websockets

import lidar

#import pdb  ## pdb.set_trace()


WS_LIDAR_VERSION = "0.1.0"

DEF_LOG_LEVEL = "WARNING"

HOSTNAME = "0.0.0.0"
PORTNUM = 8765


async def sendData(websocket):
    while True:
        data = [(i, float(i)) for i in range(400)]  #### FIXME
        await websocket.send(json.dumps(data))
        await asyncio.sleep(10)  # Send data every 60 seconds

async def main():
    async with websockets.serve(sendData, HOSTNAME, PORTNUM):
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    asyncio.run(main())
