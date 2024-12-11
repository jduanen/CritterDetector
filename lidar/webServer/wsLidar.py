#!/usr/bin/env python3
################################################################################
#
# YDLIDAR Lidar (T-mini Pro) Scanner Library with Web Sockets interface
# 
################################################################################

#### TODO consider using 'wss://' sockets
####  * fix exception/exit handling
####  * make version test only look at major (minor too?) value
####  * make HALT work correctly
####  * figure out how to make sending response block -- to maintain association of cmd & response

import asyncio
from enum import Enum
import json
import logging
import signal
import websockets

from ..shared import MessageTypes, Commands, COMMAND_PORT, DATA_PORT
from ..lib.lidar import Lidar

#import pdb  ## pdb.set_trace()


LOG_LEVEL = "INFO"  ## "DEBUG"

WS_LIDAR_VERSION = "1.3.0"  # N.B. Must match lidar.py library's version

HOSTNAME = "0.0.0.0"

PING = 20

scanner = None
cmdServer = dataServer = None
dataSocket = None


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
            if scanner:
                scanner.done()
            if cmdServer:
                cmdServer.close()
            if dataServer:
                dataServer.close()
            logging.info("Received Stop message, exit")
            return False
        if msg['type'] == MessageTypes.STATUS.value:
            logging.info("Received Status request message")
            status = {}
            if scanner:
                status = scanner.status()
            res = {'scanner': not scanner == None, 'status': status}
            response = {'type': MessageTypes.REPLY.value} | res
            logging.debug(f"Send Response: {response}")
            await websocket.send(json.dumps(response))
            return True
        if msg['type'] != MessageTypes.CMD.value:
            errMsg = f"Not a command, ignoring: {msg['type']}"
            logging.error(errMsg)
            response = {'type': MessageTypes.ERROR.value, 'error': errMsg}
            logging.debug(f"Send Response: {response}")
            await websocket.send(json.dumps(response))
            return True
        elif not scanner and not (msg['command'] == Commands.INIT.value):
            # not initialized and this is not a init command
            errMsg = f"Must issue initialize command first, ignoring: {msg}"
            logging.error(errMsg)
            response = {'type': MessageTypes.ERROR.value, 'error': errMsg}
            logging.debug(f"Send Response: {response}")
            await websocket.send(json.dumps(response))
            return True
        logging.info(f"Received Command message: {msg['command']}")
        if msg['command'] == Commands.INIT.value:
            if scanner:
                logging.warning("Device already initialized, ignoring Init command")
                response = {'type': MessageTypes.REPLY.value, 'version': WS_LIDAR_VERSION}
            else:
                try:
                    print(f">>>>> {msg}")
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
            if scanner.laserEnable(True):
                errMsg = "Failed to enable laser"
                logging.warning(errMsg)
                response = {'type': MessageTypes.ERROR.value, 'error': errMsg}
            else:
                points = scanner.scan(msg['names'])
                if scanner.laserEnable(False):
                    errMsg = "Failed to disable laser"
                    logging.warning(errMsg)
                    response = {'type': MessageTypes.ERROR.value, 'error': errMsg}
                else:
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
        elif msg['command'] == Commands.STREAM.value:
            if scanner.laserEnable(True):
                errMsg = "Failed to enable laser"
                logging.warning(errMsg)
                response = {'type': MessageTypes.ERROR.value, 'error': errMsg}
            else:
                response = {'type': MessageTypes.REPLY.value}
            await websocket.send(json.dumps(response))  #### TODO should I block here?

            pointsGen = scanner.stream(msg['names'])
            for points in pointsGen:
                if points:
                    response = {'type': MessageTypes.REPLY.value, 'values': points}
                    #### TODO send points on data socket -- binary or JSON????
                    await dataSocket.send(json.dumps(response))  #### TODO should I block here?
                else:
                    logging.warning("Failed to get streaming samples, continuing...")
            print("STREAM: done")
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
        await websocket.send(json.dumps(response))  #### TODO should I block here?

async def dataHandler(websocket):
    dataSocket = websocket
    print("DATA HANDLER")

async def main():
    global cmdServer, dataServer

    cmdServer = await websockets.serve(cmdHandler, HOSTNAME, COMMAND_PORT, ping_interval=PING, ping_timeout=PING)
    dataServer = await websockets.serve(dataHandler, HOSTNAME, DATA_PORT, ping_interval=PING, ping_timeout=PING)
    await asyncio.gather(cmdServer.wait_closed(), dataServer.wait_closed())
    logging.debug("Done, exiting")


if __name__ == "__main__":
    logging.basicConfig(level=LOG_LEVEL)
    logging.debug("Starting Lidar Server")

    if (Lidar.LIDAR_VERSION != WS_LIDAR_VERSION):  #### FIXME just check major(/minor?) number
        logging.error(f"Version mismatch: ({Lidar.LIDAR_VERSION} != {WS_LIDAR_VERSION})")
        exit(1)

    def signalHandler(sig, frame):
        ''' Catch SIGHUP to force a restart and SIGINT to stop.""
        '''
        if sig == signal.SIGHUP:
            logging.info("SIGHUP")
            #### TODO stop, reload, and restart everything
        elif sig == signal.SIGINT:
            logging.info("SIGINT")
            #### TODO stop everything and exit
            if scanner:
                scanner.done
                scanner = None
            exit(1)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.debug("Lidar Server manually stopped")
        exit(1)
    except Exception as ex:
        logging.error(ex)
        exit(1)
    exit(0)
