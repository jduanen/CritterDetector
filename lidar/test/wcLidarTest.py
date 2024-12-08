#!/usr/bin/env python3
################################################################################
#
# Lidar Web Client Library test
#
################################################################################

import asyncio
import json
import logging
import websockets

from ..shared import COMMAND_PORT, DATA_PORT
from ..lib.wcLidar import LidarClient


LOG_LEVEL = "DEBUG"

HOSTNAME = "bookworm.lan" # "gpuServer1.lan" # 


async def ainput(prompt=""):
    return await asyncio.to_thread(input, prompt)

# Test code
async def cli(lidar):
    try:
        cliCmd = input("> ")
        while cliCmd:
            if cliCmd == 'i':
                opts = {}
                response = await lidar.init(opts)
                print(f"INIT: {response}")
            elif cliCmd == 'm':
                #### FIXME
                names = ['intensities']
                for i in range(3):
                    response = await lidar.stream(names)
                    print(f"STREAM ({i}): {response}")
            elif cliCmd == 'p':
                names = ['angles', 'distances', 'intensities']
                response = await lidar.scan(names)
                print(f"SCAN: {response}")
            elif cliCmd == 'r':
                names = ['minRange', 'maxRange', 'minAngle', 'maxAngle', 'scanFreq', 'sampleRate']
                response = await lidar.get(names)
                print(f"GET: {response}")
            elif cliCmd == 'R':
                response = await lidar.reset()
                print(f"RESET: {response}")
            elif cliCmd == 's':
                response = await lidar.status()
                print(f"STATUS: {response}")
            elif cliCmd == 'S':
                response = await lidar.stop()
                print(f"STOP: {response}")
            elif cliCmd == 'v':
                response = await lidar.version()
                print(f"VERSION: {response}")
            elif cliCmd == 'w':
                vals = {'minRange': 2.5, 'minAngle': -90, 'maxRange': 8.5, 'scanFreq': 2}
                response = await lidar.set(vals)
                print(f"SET: {response}")
            elif cliCmd == 'X':
                response = await lidar.halt()
                print(f"HALT: {response}")
            elif (cliCmd == '?') or (cliCmd == 'h'):
                print("h: this message")
                print("i: init lidar device")
                print("m: stream")
                print("p: get sample points")
                print("q: quit")
                print("r: read values")
                print("R: reset lidar device")
                print("s: status")
                print("S: stop lidar device")
                print("v: get version")
                print("w: write values")
                print("X: shutdown server")
                print("?: this message")
            elif cliCmd in ['q', 'Q']:
                break
            else:
                logging.error(f"Invalid input: {cliCmd}")
            cliCmd = input("> ")
        await lidar.stop()
    except (websockets.ConnectionClosed, OSError) as e:
        logging.warning(f"Connection error: {e}")
        return True
    return False

async def main():
    global lidar

##    # create an instance using the asynchronous class method
##    lidar = await LidarClient.create("LidarClientInterface")
    lidar = LidarClient(HOSTNAME, COMMAND_PORT, DATA_PORT)
    if await lidar.init():
        return True
    return await cli(lidar)


if __name__ == "__main__":
    logging.basicConfig(level=LOG_LEVEL)
    logging.info("Starting Web Client")

    if asyncio.run(main()):
        exit(1)
    logging.info("Web Client Done")
    exit(0)

'''
    # run asynchronous methods
    await lidar.run_tasks()
    logging.info("Done")
'''

