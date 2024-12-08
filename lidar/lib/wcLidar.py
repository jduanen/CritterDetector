#!/usr/bin/env python3
################################################################################
#
# YDLIDAR T-mini Lidar Scanner Client Library with Web Sockets interface
# 
################################################################################

import asyncio
from enum import Enum
import json
import logging
import websockets

from ..shared import MessageTypes, Commands


DEF_PING = 20

DEF_SCAN_NAMES = ['angles', 'distances', 'intensities']


class LidarClient():
    WC_LIDAR_VERSION = "1.3.0"  # N.B. Must match lidar.py library's version

    def __init__(self, hostname, cmdPort, dataPort):
        self.hostname = hostname
        self.cmdPort = cmdPort
        self.dataPort = dataPort
        self.cmdURI = f"ws://{hostname}:{cmdPort}"
        self.dataURI = f"ws://{hostname}:{dataPort}"
        self.dataSocket = websockets.connect(self.dataURI, ping_interval=DEF_PING, ping_timeout=DEF_PING)
        self.inited = False
        self.streaming = False

    async def _sendHalt(self):
        try:
            async with websockets.connect(self.cmdURI, ping_interval=DEF_PING, ping_timeout=DEF_PING) as cmdSocket:
                message = {'type': MessageTypes.HALT.value}
                await cmdSocket.send(json.dumps(message))
                logging.debug(f"Sent command: {message}")

                response = json.loads(await cmdSocket.recv())
                logging.debug(f"Received response: {response}")
        except ConnectionRefusedError as ex:
            logging.error(f"Unable to connect to lidar server: {ex}")
            return True
        self.streaming = False
        return False  #### FIXME

    async def _sendCmd(self, cmd, args={}):
        try:
            async with websockets.connect(self.cmdURI, ping_interval=DEF_PING, ping_timeout=DEF_PING) as cmdSocket:
                message = {'type': MessageTypes.CMD.value, 'command': cmd} | args
                await cmdSocket.send(json.dumps(message))
                logging.debug(f"Sent command: {message}")

                response = json.loads(await cmdSocket.recv())
                logging.debug(f"Received response: {response}")
        except ConnectionRefusedError as ex:
            logging.error(f"Unable to connect to lidar server: {ex}")
            return None

        if ('type' not in response) or (response['type'] == MessageTypes.ERROR.value):
            logging.error(f"Bad Response message: {response}")
            return None
        if response['type'] == 'STOP':    #### TODO can this ever happen? how about HALT?
            logging.info("Got stop message, exiting...")
            exit(0)
        logging.debug(f"Valid Response: {response}")
        return response

    async def init(self, options={}):
        logging.info(f"INIT: {options}")
        if self.inited:
            logging.warning("Lidar is already running, so ignoring init command")
        else:
            response = await self._sendCmd(Commands.INIT.value, {'options': options})
            if response == None:
                return True
            if response['version'] == LidarClient.WC_LIDAR_VERSION:        #### FIXME semver test
                logging.debug(f"Version good: {response['version']}")
            else:
                logging.error(f"Invalid Version: {response['version']} != {LidarClient.WC_LIDAR_VERSION}")
                return True
            self.inited = True
        self.streaming = False
        return False

    async def stop(self):
        logging.info("STOP")
        response = await self._sendCmd(Commands.STOP.value)
        if response == None:
            logging.error("Failed to stop lidar")
            return True
        self.inited = False
        self.streaming = False
        return False

    async def reset(self, options={}):
        logging.info("RESET")
        if await self.stop():
            return True
        if await self.init(options):
            return True
        return False

    async def halt(self):
        logging.info("HALT")
        return await self._sendHalt()

    async def status(self):
        logging.info("STATUS")
        try:
            async with websockets.connect(self.cmdURI, ping_interval=DEF_PING, ping_timeout=DEF_PING) as websocket:
                message = {'type': MessageTypes.STATUS.value}
                await websocket.send(json.dumps(message))
                logging.debug(f"Sent command: {message}")

                response = json.loads(await websocket.recv())
                logging.debug(f"Received status response: {response}")
                if 'status' not in response:
                    response['status'] = {}
        except ConnectionRefusedError as ex:
            logging.error(f"Unable to connect to lidar server: {ex}")
            return None
        return response['status']

    async def set(self, values):
        logging.info("SET")
        if not values:
            logging.warning("No values to set, ignoring")
            return None
        response = await self._sendCmd(Commands.SET.value, {'set': values})
        if (response == None) or ('results' not in response) or all(response['results'].values()):
            return None
        return response['results']

    async def get(self, names):
        logging.info("GET")
        response = await self._sendCmd(Commands.GET.value, {'get': names})
        if (response == None) or ('values' not in response):
            return None
        return response['values']

    async def scan(self, names=DEF_SCAN_NAMES):
        logging.info("SCAN")
        response = await self._sendCmd(Commands.SCAN.value, {'names': names})
        if (response == None) or ('values' not in response):
            print("ERROR: xxx") #### TMP TMP TMP
            return None
#        print(f"SCAN: {response['values']}")
        return response['values']

    async def stream(self, names=DEF_SCAN_NAMES):
        #### FIXME
        print("XXXXXXXXXXXXXXXXXXXXXXX")
        self.streaming = True
        logging.info("STREAM")
        response = await self._sendCmd(Commands.STREAM.value, {'names': names})
        while True:
            try:
                response = await dataSocket.recv()
                print(f"STREAM: {response}")
#                yield response
                return response
            except websockets.exceptions.ConnectionClosed:
                print("DATA CONNECTION CLOSED")  #### FIXME
                self.streaming = False
                break

    async def version(self):
        logging.info("VERSION")
        response = await self._sendCmd(Commands.VERSION.value)
        if (response == None) or ('version' not in response):
            return None
        return response['version']

