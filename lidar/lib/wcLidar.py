#!/usr/bin/env python3
'''
################################################################################
#
# YDLIDAR T-mini Lidar Scanner Client Library with Web Sockets interface
#
# 
################################################################################
'''

import asyncio
from enum import Enum
import json
import logging
import websockets

from ..shared import MessageTypes, Commands


LOG_LEVEL = "DEBUG"

DEF_PING = 20


class LidarClient():
    WC_LIDAR_VERSION = "1.3.0"  # N.B. Must match lidar.py library's version

    def __init__(self, hostname, portNum):
        self.hostname = hostname
        self.portNum = portNum
        self.uri = f"ws://{hostname}:{portNum}"
        self.inited = False

    async def _sendHalt(self):
        try:
            async with websockets.connect(self.uri, ping_interval=DEF_PING, ping_timeout=DEF_PING) as websocket:
                message = {'type': MessageTypes.HALT.value}
                await websocket.send(json.dumps(message))
                logging.debug(f"Sent command: {message}")

                response = json.loads(await websocket.recv())
                logging.debug(f"Received response: {response}")
        except ConnectionRefusedError as ex:
            logging.error(f"Unable to connect to lidar server: {ex}")
            return True
        return False  #### FIXME

    async def _sendCmd(self, cmd, args={}):
        try:
            async with websockets.connect(self.uri, ping_interval=DEF_PING, ping_timeout=DEF_PING) as websocket:
                message = {'type': MessageTypes.CMD.value, 'command': cmd} | args
                await websocket.send(json.dumps(message))
                logging.debug(f"Sent command: {message}")

                response = json.loads(await websocket.recv())
                logging.debug(f"Received response: {response}")
        except ConnectionRefusedError as ex:
            logging.error(f"Unable to connect to lidar server: {ex}")
            return None

        if ('type' not in response) or (response['type'] == MessageTypes.ERROR.value):
            logging.error(f"Bad Response message: {response}")
            return None
        if response['type'] == 'STOP':    #### TODO can this ever happen?
            logging.info("Got stop message, exiting...")
            exit(0)
        logging.debug(f"Valid Response: {response}")
        return response

    async def init(self, options={}):
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
        return False

    async def stop(self):
        response = await self._sendCmd(Commands.STOP.value)
        if response == None:
            return True
        self.inited = False
        return False

    async def halt(self):
        return await self._sendHalt()

    async def status(self):
        try:
            async with websockets.connect(self.uri, ping_interval=DEF_PING, ping_timeout=DEF_PING) as websocket:
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
        if not values:
            logging.warning("No values to set, ignoring")
            return None
        response = await self._sendCmd(Commands.SET.value, {'set': values})
        if (response == None) or ('results' not in response) or all(response['results'].values()):
            return None
        return response['results']

    async def get(self, names):
        response = await self._sendCmd(Commands.GET.value, {'get': names})
        if (response == None) or ('values' not in response):
            return None
        return response['values']

    async def scan(self, names):
        response = await self._sendCmd(Commands.SCAN.value, {'names': names})
        if (response == None) or ('values' not in response):
            return None
        return response['values']

    async def version(self):
        response = await self._sendCmd(Commands.VERSION.value)
        if (response == None) or ('version' not in response):
            return None
        return response['version']

