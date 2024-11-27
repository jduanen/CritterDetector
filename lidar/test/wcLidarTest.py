#!/usr/bin/env python3
#
# Lidar Web Client Library test
#

import asyncio
import json
import logging
import websockets

from wcLidar import LidarClient


LOG_LEVEL = "WARNING"

HOSTNAME = "gpuServer1.lan"
PORT_NUM = 8765


async def ainput(prompt=""):
    return await asyncio.to_thread(input, prompt)

# Test code
async def cli(lidar):
    try:
        cliCmd = input("> ")
        while cliCmd:
            '''
            if cliCmd == 'L':
                response = await lidar.laser(True)
                print(f"LASER ON: {response}")
            elif cliCmd == 'l':
                response = await lidar.laser(False)
                print(f"LASER OFF: {response}")
            '''
            if cliCmd == 'r':
                names = ['minRange', 'maxRange', 'minAngle', 'maxAngle', 'scanFreq', 'sampleRate']
                response = await lidar.get(names)
                print(f"GET: {response}")
            elif cliCmd == 's':
                opts = {}
                response = await lidar.start(opts)
                print(f"START: {response}")
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
                #print("L: turn laser on")
                #print("l: turn laser off")
                print("q: quit")
                print("r: read values")
                print("s: start lidar device")
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
    lidar = LidarClient(HOSTNAME, PORT_NUM)
    if await lidar.start():
        return True
    return await cli(lidar)


if __name__ == "__main__":
    logging.basicConfig(level=LOG_LEVEL)
    logging.info("Start")

    if asyncio.run(main()):
        exit(1)
    logging.info("Done")
    exit(0)

'''
    # run asynchronous methods
    await lidar.run_tasks()
    logging.info("Done")
'''

