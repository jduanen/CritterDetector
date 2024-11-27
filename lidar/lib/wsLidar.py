#!/usr/bin/env python3
'''
################################################################################
#
# YDLIDAR T-mini Lidar Scanner Library (T-mini Pro) with Web Sockets interface
#
# WS Interface:
#  * send dicts serialized to json (with json.dumps())
#  * receive serialized json strings and deserialize to dicts (with json.loads())
#  * message formats
#    - stop: {'type': 'STOP'}
#    - command: {'type': 'CMD', 'command': <cmd>, <**argKVs>}
#    - response: {'type': 'RESP', 'cmd': <cmd>, <returnKVs>}
#  * commands/responses
#    - Start
#      * {'type': 'CMD', 'command':'start', 'port': <path>", 'baud': <int>,
#          'scanFreq': <Hz>, 'sampleRate': <KHz>, 'minAngle': <degrees>,
#          'maxAngle': <degrees>, 'minRange': <meters>, 'maxRange': <meters>,
#          'zeroFilter': <bool>}
#      * {'type': 'RESP', 'success': <bool>, 'version': <str>}
#    - Stop
#      * {'type': 'CMD', 'command': 'stop'}
#      * {'type': 'RESP', 'success': <bool>}
#    - Set value(s)
#      * {'type': 'CMD', 'command': 'set', {'scanFreq': <KHz>, 'sampleRate': <Hz>,
#          'minAngle': <deg>, 'maxAngle': <deg>, 'minRange': <m>, 'maxRange': <m>}
#      * {'type': 'RESP', 'success': <bool>, 'results': {'scanFreq': <bool>,
#          'sampleRate': <bool>, 'minAngle': <bool>, 'maxAngle': <bool>,
#          'minRange': <bool>, 'maxRange': <bool>}
#    - Get value(s)
#      * {'type': 'CMD', 'command': 'get', ['scanFreq', 'sampleRate',
#          'minAngle', 'maxAngle', 'minRange', 'maxRange']}
#      * {'type': 'RESP', 'success': <bool>, 'values': ['scanFreq': <Hz>,
#          'sampleRate': <KHz>, 'minAngle': <degrees>, 'maxAngle': <degrees>,
#          'minRange': <meters>, 'maxRange': <meters>]}
#    - Scan
#      * {'type': 'CMD', 'command': 'scan', 'values': ['angles', 'distances', 'intensities']}
#      * {'type': 'RESP', 'success': <bool>, 'values': {'angles': <floatList>,
#          'distances': <intList>, 'intensities': <intList>}}
#    - Laser on/off
#      * {'type': 'CMD', 'command': 'laser', 'enable': <bool>}
#      * {'type': 'RESP', 'success': <bool>}
#    - Version
#      * {'type': 'CMD', 'command': 'version'}
#      * {'type': 'RESP', 'success': <bool>, 'version': <str>}
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
from enum import Enum
import json
import logging
import websockets

import lidar

#import pdb  ## pdb.set_trace()

#### TODO consider using 'wss://' sockets
#### TODO fix exception/exit handling
#### TODO make version test only look at major (minor too?) value


WS_LIDAR_VERSION = "1.1.0"  # N.B. Must match lidar.py library's version

LOG_LEVEL = "DEBUG"

HOSTNAME = "0.0.0.0"
PORTNUM = 8765

PING = 20


#### TODO move this to a common location to be shared by clients
class Commands(Enum):
    START = 'start'
    STOP = 'stop'
    SET = 'set'
    GET = 'get'
    SCAN = 'scan'
    LASER = 'laser'
    VERSION = 'version'

scanner = None

async def cmdHandler(websocket):
    global scanner

    async for message in websocket:
        msg = json.loads(message)
        if not 'type' in msg:
            logging.error(f"No message type: {msg}")
            response = {'type': 'ERROR'}
            logging.debug(f"Sending Error Response: {response}")
            await websocket.send(json.dumps(response))
            exit(1)
        if msg['type'] == 'STOP':
            scanner.done()
            scanner = None
            exit(0)
        if msg['type'] != 'CMD':
            logging.warning(f"Not a command, ignoring: {msg['type']}")
            response = {'type': 'RESP', 'success': False}
        elif msg['command'] == Commands.START.value:
            if ('options' in msg) and msg['options']:
                scanner = lidar.Lidar(**msg['options'])
            else:
                scanner = lidar.Lidar()
            if scanner:
                response = {'type': 'RESP', 'success': True, 'version': WS_LIDAR_VERSION}
            else:
                response = {'type': 'RESP', 'success': False, 'version': WS_LIDAR_VERSION}
        elif msg['command'] == Commands.STOP.value:
            if scanner.done():
                scanner = None
                response = {'type': 'RESP', 'success': True}
            else:
                response = {'type': 'RESP', 'success': False}
        elif msg['command'] == Commands.SET.value:
            results = {}
            for k in msg['set']:
                if k == 'scanFreq':
                    results['scanFreq'] = scanner.setScanFreq(msg['set']['scanFreq'])
                elif k == 'sampleRate':
                    results['sampleRate'] = scanner.setSampleRate(msg['set']['sampleRate'])
                elif k == 'minAngle':
                    results['minAngle'] = scanner.setMinAngle(msg['set']['minAngle'])
                elif k == 'maxAngle':
                    results['maxAngle'] = scanner.setMaxAngle(msg['set']['maxAngle'])
                elif k == 'minRange':
                    results['minRange'] = scanner.setMinRange(msg['set']['minRange'])
                elif k == 'maxRange':
                    results['maxRange'] = scanner.setMaxRange(msg['set']['maxRange'])
            response = {'type': 'RESP', 'success': True, 'results': results}
        elif msg['command'] == Commands.GET.value:
            if ('get' not in msg) or (msg['get'] is None):
                response = {'type': 'RESP', 'success': False}
            else:
                GETTERS = {'minAngle': scanner.getAngles, 'maxAngle': scanner.getAngles,
                           'minRange': scanner.getRanges, 'maxRange': scanner.getRanges,
                           'scanFreq': scanner.getScanFreq, 'sampleRate': scanner.getSampleRate}
                vals = {}
                for k in msg['get']:
                    v = GETTERS[k]()
                    if k == 'minAngle':
                        vals[k] = v[0]
                    elif k == 'maxAngle':
                        vals[k] = v[1]
                    elif k == 'minRange':
                        vals[k] = v[0]
                    elif k == 'maxRange':
                        vals[k] = v[1]
                    elif k in ['scanFreq', 'sampleRate']:
                        vals[k] = v
                if vals:
                    response = {'type': 'RESP', 'success': True, 'get': vals}
                else:
                    response = {'type': 'RESP', 'success': False, 'get': None}
        elif msg['command'] == Commands.SCAN.value:
            points = scanner.scan(msg['values'])
            if points:
                response = {'type': 'RESP', 'success': True, 'values': points}
            else:
                response = {'type': 'RESP', 'success': False, 'values': None}
        elif msg['command'] == Commands.LASER.value:
            if scanner.laserEnable(msg['enable']):
                response = {'type': 'RESP', 'success': True}
            else:
                response = {'type': 'RESP', 'success': False}
        elif msg['command'] == Commands.VERSION.value:
            version = scanner.getVersion()
            if version:
                response = {'type': 'RESP', 'success': True, 'version': version}
            else:
                response = {'type': 'RESP', 'success': False, 'version': None}
        else:
            logging.warning(f"Unknown command: {msg['command']}")
            response = {'type': 'RESP', 'success': False}
        logging.debug(f"Send Response: {response}")
        await websocket.send(json.dumps(response))

async def main():
    try:
        # loop forever
        async with websockets.serve(cmdHandler, HOSTNAME, PORTNUM, ping_interval=PING, ping_timeout=PING):
            future = asyncio.get_running_loop().create_future()
            await future
    except asyncio.CancelledError:
        print("Future was cancelled, exiting...")
        # Perform any necessary cleanup here


if __name__ == "__main__":
    logging.basicConfig(level=LOG_LEVEL)
    logging.debug("Starting Lidar Server")

    if (lidar.LIDAR_VERSION != WS_LIDAR_VERSION):  #### FIXME just check major(/minor?) number
        logging.error(f"Version mismatch: ({lidar.LIDAR_VERSION} != {WS_LIDAR_VERSION})")
        exit(1)

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logging.debug("Lidar Server stopped")
