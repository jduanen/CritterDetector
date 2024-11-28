#!/usr/bin/env python3
'''
################################################################################
#
# YDLIDAR Lidar (T-mini Pro) Scanner Library with Web Sockets interface
#
# WS Interface:
#  * send dicts serialized to json (with json.dumps())
#  * receive serialized json strings and deserialize to dicts (with json.loads())
#  * message formats
#    - halt: {'type': 'HALT'}
#    - command: {'type': 'CMD', 'command': <cmd>, ????: <KVs>}
#    - response: {'type': 'REPLY', ????: <returnKVs>}
#    - error: {'type': 'ERROR', 'error': <errMsg>}
#  * commands/responses
#    - Start
#      * {'type': 'CMD', 'command': 'options': {'start', 'port': <path>", 'baud': <int>,
#          'scanFreq': <Hz>, 'sampleRate': <KHz>, 'minAngle': <degrees>,
#          'maxAngle': <degrees>, 'minRange': <meters>, 'maxRange': <meters>,
#          'zeroFilter': <bool>}}
#      * {'type': 'REPLY', 'version': <str>}
#      * {'type': 'ERROR', 'error': <errMsg>}
#    - Stop
#      * {'type': 'CMD', 'command': 'stop'}
#      * {'type': 'REPLY'}
#      * {'type': 'ERROR', 'error': <errMsg>}
#    - Set values
#      * {'type': 'CMD', 'command': 'set', 'set': {'scanFreq': <KHz>, 'sampleRate': <Hz>,
#          'minAngle': <deg>, 'maxAngle': <deg>, 'minRange': <m>, 'maxRange': <m>}
#      * {'type': 'REPLY', 'results': {'scanFreq': <bool>,
#          'sampleRate': <bool>, 'minAngle': <bool>, 'maxAngle': <bool>,
#          'minRange': <bool>, 'maxRange': <bool>}
#      * {'type': 'ERROR', 'error': <errMsg>}
#    - Get value(s)
#      * {'type': 'CMD', 'command': 'get', 'get': ['scanFreq', 'sampleRate',
#          'minAngle', 'maxAngle', 'minRange', 'maxRange']}
#      * {'type': 'REPLY', 'values': {'scanFreq': <Hz>, 'sampleRate': <KHz>,
#          'minAngle': <degrees>, 'maxAngle': <degrees>,
#          'minRange': <meters>, 'maxRange': <meters>}}
#      * {'type': 'ERROR', 'error': <errMsg>}
#    - Scan
#      * {'type': 'CMD', 'command': 'scan', 'names': ['angles', 'distances', 'intensities']}
#      * {'type': 'REPLY', 'values': {'angles': <floatList>, 'distances': <intList>, 'intensities': <intList>}}
#      * {'type': 'ERROR', 'error': <errMsg>}
#    - Laser on/off
#      * {'type': 'CMD', 'command': 'laser', 'enable': <bool>}
#      * {'type': 'REPLY'}
#      * {'type': 'ERROR', 'error': <errMsg>}
#    - Version
#      * {'type': 'CMD', 'command': 'version'}
#      * {'type': 'REPLY', 'version': <str>}
#      * {'type': 'ERROR', 'error': <errMsg>}
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

from ..shared import MessageTypes, Commands
from ..lib.lidar import Lidar

#import pdb  ## pdb.set_trace()

#### TODO consider using 'wss://' sockets
#### TODO fix exception/exit handling
#### TODO make version test only look at major (minor too?) value

LOG_LEVEL = "DEBUG"

WS_LIDAR_VERSION = "1.2.0"  # N.B. Must match lidar.py library's version

HOSTNAME = "0.0.0.0"
PORTNUM = 8765

PING = 20

scanner = None


async def cmdHandler(websocket):
    global scanner

    async for message in websocket:
        msg = json.loads(message)
        if not 'type' in msg:
            errMsg = f"No message type field: {msg}"
            logging.error(errMsg)
            response = {'type': MessageTypes.ERROR.value, 'error': errMsg}
            logging.debug(f"Send Response: {response}")
            await websocket.send(json.dumps(response))
            return True
        if msg['type'] == MessageTypes.HALT.value:
            scanner.done()
            scanner = None
            logging.info("Received Stop message, exit")
            return False
        if msg['type'] != MessageTypes.CMD.value:
            errMsg = f"Not a command, ignoring: {msg['type']}"
            logging.warning(errMsg)
            response = {'type': MessageTypes.ERROR.value, 'error': errMsg}
        elif not scanner or (msg['command'] != 'Commands.START.value'):
            errMsg = f"Must issue start command first, ignoring: {msg}"
            logging.warning(errMsg)
            response = {'type': MessageTypes.ERROR.value, 'error': errMsg}
        if msg['command'] == Commands.START.value:
            if scanner:
                logging.warning("Device already started, ignoring Start command")
                response = {'type': MessageTypes.REPLY.value, 'version': WS_LIDAR_VERSION}
            else:
                try:
                    if ('options' in msg) and msg['options']:
                        scanner = Lidar(**msg['options'])
                    else:
                        scanner = Lidar()
                except Exception as ex:
                    logging.error(f"Failed to attach to lidar: {ex}")
                    return True
                if scanner:
                    response = {'type': MessageTypes.REPLY.value, 'version': WS_LIDAR_VERSION}
                else:
                    errMsg = "Failed to initialize the lidar device"
                    logging.warning(errMsg)
                    response = {'type': MessageTypes.ERROR.value, 'error': errMsg}
        elif msg['command'] == Commands.STOP.value:
            if scanner.done():
                scanner = None
                response = {'type': MessageTypes.REPLY.value}
            else:
                errMsg = "Failed to shutdown the lidar"
                logging.warning(errMsg)
                response = {'type': MessageTypes.ERROR.value, 'error': errMsg}
        elif msg['command'] == Commands.SET.value:
            if ('set' not in msg) or (msg['set'] is None):
                errMsg = "No values to set"
                logging.warning(errMsg)
                response = {'type': MessageTypes.ERROR.value, 'error': errMsg}
            else:
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
                response = {'type': MessageTypes.REPLY.value, 'results': results}
        elif msg['command'] == Commands.GET.value:
            if ('get' not in msg) or (msg['get'] is None):
                errMsg = "No values to get"
                logging.warning(errMsg)
                response = {'type': MessageTypes.ERROR.value, 'error': errMsg}
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
                response = {'type': MessageTypes.REPLY.value, 'values': vals}
        elif msg['command'] == Commands.SCAN.value:
            points = scanner.scan(msg['names'])
            if points:
                response = {'type': MessageTypes.REPLY.value, 'values': points}
            else:
                errMsg = "Failed to get requested samples"
                logging.warning(errMsg)
                response = {'type': MessageTypes.ERROR.value, 'error': errMsg}
        elif msg['command'] == Commands.LASER.value:
            if scanner.laserEnable(msg['enable']):
                response = {'type': MessageTypes.REPLY.value}
            else:
                errMsg = "Failed to turn laser on/off"
                logging.warning(errMsg)
                response = {'type': MessageTypes.ERROR.value, 'error': errMsg}
        elif msg['command'] == Commands.VERSION.value:
            version = scanner.getVersion()
            if version:
                response = {'type': MessageTypes.REPLY.value, 'version': version}
            else:
                errMsg = "Failed to get lidar library version"
                logging.warning(errMsg)
                response = {'type': MessageTypes.ERROR.value, 'error': errMsg}
        else:
            errMsg = f"Unknown command: {msg['command']}"
            logging.warning(errMsg)
            response = {'type': MessageTypes.ERROR.value, 'error': errMsg}
        logging.debug(f"Send Response: {response}")
        await websocket.send(json.dumps(response))

async def main():
    try:
        # loop forever
        async with websockets.serve(cmdHandler, HOSTNAME, PORTNUM, ping_interval=PING, ping_timeout=PING):
            future = asyncio.get_running_loop().create_future()
            await future
    except asyncio.CancelledError:
        logging.error("Future was cancelled, exiting...")
        # Perform any necessary cleanup here
        #### FIXME
    except Exception as ex:
        logging.error(ex)


if __name__ == "__main__":
    logging.basicConfig(level=LOG_LEVEL)
    logging.debug("Starting Lidar Server")

    if (Lidar.LIDAR_VERSION != WS_LIDAR_VERSION):  #### FIXME just check major(/minor?) number
        logging.error(f"Version mismatch: ({Lidar.LIDAR_VERSION} != {WS_LIDAR_VERSION})")
        exit(1)

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logging.debug("Lidar Server manually stopped")
        exit(1)
    except Exception as ex:
        logging.error(ex)
        exit(1)
    exit(0)
