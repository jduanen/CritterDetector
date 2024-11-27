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

import lidar

#### FIXME get this from a common location
from enum import Enum, unique

@unique
class MessageTypes(Enum):
    CMD = 'command'
    REPLY = 'reply'
    ERROR = 'error'
    HALT = 'halt'

@unique
class Commands(Enum):
    START = 'start'
    STOP = 'stop'
    SET = 'set'
    GET = 'get'
    SCAN = 'scan'
    LASER = 'laser'
    VERSION = 'version'

WC_LIDAR_VERSION = "1.1.0"  # N.B. Must match lidar.py library's version

LOG_LEVEL = "DEBUG"

DEF_PING = 20

class LidarClient():
    def __init__(self, hostname, portNum):
        self.hostname = hostname
        self.portNum = portNum
        self.uri = f"ws://{hostname}:{portNum}"
        self.started = False

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

        if ('type' not in response) or (response['type'] == 'ERROR'):
            logging.error(f"Bad Response message: {response}")
            return None
        if response['type'] == 'STOP':    #### TODO can this ever happen?
            logging.info("Got stop message, exiting...")
            exit(0)
        logging.debug(f"Valid Response: {response}")
        return response

    async def start(self, options={}):
        if self.started:
            logging.warning("Lidar is already running, so ignoring start command")
        else:
            response = await self._sendCmd(Commands.START.value, {'options': options})
            if response == None:
                return True
            if response['version'] == WC_LIDAR_VERSION:        #### FIXME semver test
                logging.debug(f"Version good: {response['version']}")
            else:
                logging.error(f"Invalid Version: {response['version']} != {WC_LIDAR_VERSION}")
                return True
            self.started = True
        return False

    async def stop(self):
        response = await self._sendCmd(Commands.STOP.value)
        if response == None:
            return True
        self.started = False
        return False

    async def halt(self):
        return await self._sendHalt()

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
        #### FIXME
        return False

    async def laser(self, enable):
        #### FIXME
        return False

    async def version(self):
        #### FIXME
        return False

