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
#    - command: {'type': 'CMD', 'command': <cmd>, <**argKVs>}
#    - response: {'type': 'RESP', 'cmd': <cmd>, <returnKVs>}
#  * commands/responses
#    - Initialize
#      * {'type': 'CMD', 'command':'init', 'port': <path>", 'baud': <int>,
#          'scanFreq': <Hz>, 'sampleRate': <KHz>, 'minAngle': <degrees>,
#          'maxAngle': <degrees>, 'minRange': <meters>, 'maxRange': <meters>,
#          'zeroFilter': <bool>}
#      * {'type': 'RESP', 'success': <bool>}
#    - Stop
#      * {'type': 'CMD', 'command': 'stop'}
#      * {'type': 'RESP', 'success': <bool>}
#    - Set value(s)
#      * {'type': 'CMD', 'command': 'set', ['port', 'baud', 'scanFreq', 'sampleRate',
#          'minAngle', 'maxAngle', 'minRange', 'maxRange', 'zeroFilter']}
#      * {'type': 'RESP', 'success': <bool>}
#    - Get value(s)
#      * {'type': 'CMD', 'command': 'get', ['port', 'baud', 'scanFreq', 'sampleRate',
#          'minAngle', 'maxAngle', 'minRange', 'maxRange', 'zeroFilter']}
#      * {'type': 'RESP', 'success': <bool>, 'values': ['port': <str>, 'baud': <int>,
#          'scanFreq': <Hz>, 'sampleRate': <KHz>, 'minAngle': <degrees>,
#          'maxAngle': <degrees>, 'minRange': <meters>, 'maxRange': <meters>,
#          'zeroFilter': <bool>]}
#    - Scan
#      * {'type': 'CMD', 'command': 'scan', 'values': ['angles', 'distances', 'intensities']}
#      * {'type': 'RESP', 'success': <bool>, 'values': ['angles': <floatList>,
#          'distances': <intList>, 'intensities': <intList>]}
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
    INIT = 'init'
    STOP = 'stop'
    SET = 'set'
    GET = 'get'
    SCAN = 'scan'
    LASER = 'laser'
    VERSION = 'version'

scanner = None


async def cmdHandler(websocket):
    async for message in websocket:
        msg = json.loads(message)
        if not 'type' in msg:
            logging.error(f"No message type: {msg}")
            response = {'type': 'ERROR'}
            logging.debug(f"Sending Error Response: {response}")
            await websocket.send(json.dumps(response))
            exit(1)
        if msg['type'] != 'CMD':
            logging.warning(f"Not a command, ignoring: {msg['type']}")
            response = {'type': 'RESP', 'success': False}
        elif msg['command'] == Commands.INIT.value:
            print(f"INIT: {msg}")
#    - Initialize
#      * {'type': 'CMD', 'command':'init', 'port': <path>", 'baud': <int>,
#          'scanFreq': <Hz>, 'sampleRate': <KHz>, 'minAngle': <degrees>,
#          'maxAngle': <degrees>, 'minRange': <meters>, 'maxRange': <meters>,
#          'zeroFilter': <bool>}
            if True:  #### FIXME
                response = {'type': 'RESP', 'success': True}
            else:
                response = {'type': 'RESP', 'success': False}
        elif msg['command'] == Commands.STOP.value:
            print(f"STOP: {msg}")
#    - Stop
#      * {'type': 'CMD', 'command': 'stop'}
#      * {'type': 'RESP', 'success': <bool>}
            if scanner.done():
                response = {'type': 'RESP', 'success': True}
            else:
                response = {'type': 'RESP', 'success': False}
        elif msg['command'] == Commands.SET.value:
            print(f"SET: {msg}")
#    - Set value(s)
#      * {'type': 'CMD', 'command': 'set', ['port', 'baud', 'scanFreq', 'sampleRate',
#          'minAngle', 'maxAngle', 'minRange', 'maxRange', 'zeroFilter']}
#      * {'type': 'RESP', 'success': <bool>}
            if True:  #### FIXME
                response = {'type': 'RESP', 'success': True}
            else:
                response = {'type': 'RESP', 'success': False}
        elif msg['command'] == Commands.GET.value:
            print(f"GET: {msg}")
#    - Get value(s)
#      * {'type': 'CMD', 'command': 'get', ['port', 'baud', 'scanFreq', 'sampleRate',
#          'minAngle', 'maxAngle', 'minRange', 'maxRange', 'zeroFilter']}
#      * {'type': 'RESP', 'success': <bool>, 'values': ['port': <str>, 'baud': <int>,
#          'scanFreq': <Hz>, 'sampleRate': <KHz>, 'minAngle': <degrees>,
#          'maxAngle': <degrees>, 'minRange': <meters>, 'maxRange': <meters>,
#          'zeroFilter': <bool>]}
            if True:  #### FIXME
                response = {'type': 'RESP', 'success': True}
            else:
                response = {'type': 'RESP', 'success': False}
        elif msg['command'] == Commands.SCAN.value:
            print(f"SCAN: {msg}")
#    - Scan
#      * {'type': 'CMD', 'command': 'scan', 'values': ['angles', 'distances', 'intensities']}
#      * {'type': 'RESP', 'success': <bool>, 'values': ['angles': <floatList>,
#          'distances': <intList>, 'intensities': <intList>]}
            if True:  #### FIXME
                response = {'type': 'RESP', 'success': True}
            else:
                response = {'type': 'RESP', 'success': False}
        elif msg['command'] == Commands.LASER.value:
            print(f"LASER: {msg}")
#    - Laser on/off
#      * {'type': 'CMD', 'command': 'laser', 'enable': <bool>}
#      * {'type': 'RESP', 'success': <bool>}
            if True:  #### FIXME
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
        async with websockets.serve(cmdHandler, HOSTNAME, PORTNUM, ping_interval=PING, ping_timeout=PING):
            future = asyncio.get_running_loop().create_future()
            await future
#            await asyncio.Future()  # Run forever
    except asyncio.CancelledError:
        print("Future was cancelled, exiting...")
        # Perform any necessary cleanup here


if __name__ == "__main__":
    logging.basicConfig(level=LOG_LEVEL)
    logging.debug("Starting Lidar Server")

    scanner = lidar.Lidar()

    #### TODO get version and make sure it's consistent with this code

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logging.debug("Lidar Server stopped")

'''
async def sendData(websocket):
    while True:
        data = [(i, float(i)) for i in range(400)]  #### FIXME
        await websocket.send(json.dumps(data))
        await asyncio.sleep(10)  # Send data every 60 seconds
'''