#!/usr/bin/env python3
#
# WS client test
#

import asyncio
import json
import logging
import requests
import websockets


WS_LIDAR_VERSION = "0.1.0"

LOG_LEVEL = "DEBUG"

HOSTNAME = "gpuServer1"
PORTNUM = 8765

uri = f"ws://{HOSTNAME}:{PORTNUM}"
i = 0

async def sendCmd():
    global uri

    async with websockets.connect(uri) as websocket:
        command = {'cmd': 'foo', 'arg': i}
        await websocket.send(json.dumps(command))
        logging.debug(f"Sent command: {command}")

        rsp = await websocket.recv()
        response = json.loads(rsp)
        logging.debug(f"Received response: {response}")
        return response

async def main():
    global i

    logging.basicConfig(level=LOG_LEVEL)
    while True:
        try:
            logging.debug("Send command")
            response = await sendCmd()
            logging.debug(f"Received response: {response}")
            i = response['data']
            await asyncio.sleep(10) # delay
        except (websockets.ConnectionClosed, OSError) as e:
            logging.warning(f"Connection error: {e}, retrying in 5 seconds...")
            await asyncio.sleep(5)


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
