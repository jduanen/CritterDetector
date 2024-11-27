#!/usr/bin/env python3
#
# WS client test
#

import asyncio
import json
import logging
import requests
import websockets


#### TODO make a shareable library that encapsulates all the client calls -- try to make a class
#### TODO turn this into an interface test


WS_LIDAR_VERSION = "1.1.0"

LOG_LEVEL = "DEBUG"

HOSTNAME = "gpuServer1"
PORTNUM = 8765

PING = 20

#### TODO move this to a common location to be shared by clients
from enum import Enum
class Commands(Enum):
    START = 'start'
    STOP = 'stop'
    SET = 'set'
    GET = 'get'
    SCAN = 'scan'
    LASER = 'laser'
    VERSION = 'version'


uri = f"ws://{HOSTNAME}:{PORTNUM}"


async def sendCmd(command):
    global uri

    async with websockets.connect(uri) as websocket:  ## , ping_interval=PING, ping_timout=PING
        await websocket.send(json.dumps(command))
        logging.debug(f"Sent command: {command}")

        rsp = await websocket.recv()
        response = json.loads(rsp)
        logging.debug(f"Received response: {response}")
        return response

async def main():
    logging.basicConfig(level=LOG_LEVEL)

    def _validateResponse(respMsg):
        if ('type' not in respMsg) or (respMsg['type'] == 'ERROR'):
            logging.error(f"Bad Response message: {response}")
            return True
        logging.debug("Response valid")
        return False

    try:
        logging.debug("Send Start command")
        #### TODO add device init options in the start command
        response = await sendCmd({'type': 'CMD', 'command': Commands.START.value})
        if _validateResponse(response):
            exit(1)
        if response['version'] == WS_LIDAR_VERSION:        #### FIXME
            logging.debug(f"Version good: {response['version']}")
        else:
            logging.error(f"Invalid Version: {response['version']} != {WS_LIDAR_VERSION}")
            exit(1)

        cliCmd = input("> ")
        while cliCmd:
            if cliCmd == 'g':
                valKeys = ['minRange', 'maxRange', 'minAngle', 'maxAngle', 'scanFreq', 'sampleRate']
                response = await sendCmd({'type': 'CMD', 'command': Commands.GET.value, 'get': valKeys})
                if _validateResponse(response):
                    break
                for k in valKeys:
                    print(f"{k}: {response['get'][k]}")
            elif cliCmd == 'S':
                options = {'minRange': 2.0, 'maxRange': 4.5, 'maxAngle': 120, 'ScanFreq': 8}
                response = await sendCmd({'type': 'CMD', 'command': Commands.START.value, 'options': options})
                if _validateResponse(response):
                    break
            elif cliCmd == 's':
                response = await sendCmd({'type': 'CMD', 'command': Commands.STOP.value})
                if _validateResponse(response):
                    break
            elif cliCmd == 'v':
                valDict = {'minRange': 2.5, 'minAngle': -90, 'maxRange': 8.5, 'scanFreq': 2}
                response = await sendCmd({'type': 'CMD', 'command': Commands.SET.value, 'set': valDict})
                if _validateResponse(response):
                    break
            elif (cliCmd == '?') or (cliCmd == 'h'):
                print("h: this message")
                print("S: start lidar device")
                print("g: get values")
                print("s: stop lidar device")
                print("v: set values")
                print("?: this message")
            else:
                logging.error(f"Invalid input: {cliCmd}")
                break
            cliCmd = input("> ")
        await sendCmd({'type': 'STOP'})
    except (websockets.ConnectionClosed, OSError) as e:
        logging.warning(f"Connection error: {e}, retrying in 5 seconds...")
        await asyncio.sleep(5)
    exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Client stopped manually")

'''
async def receiveData():
    try:
        async with websockets.connect(uri) as websocket:
            while True:
                data = await websocket.recv()
                parsedData = json.loads(data)
                print(f"Received {len(parsedData)} tuples")
                # Process your data here
    except asyncio.CancelledError:
        print("Connection was cancelled")
        raise  # Re-raise to handle it appropriately

async def main():
    while True:
        try:
            await receiveData()
        except websockets.ConnectionClosed:
            print("Connection closed, retrying in 5 seconds...")
            await asyncio.sleep(5)
'''
