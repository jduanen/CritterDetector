#!/usr/bin/env python3
#
# WS client test
#

import asyncio
import json
import requests
import websockets


HOSTNAME = "gpuServer1"
PORTNUM = 8765

async def receive_data():
    uri = f"ws://{HOSTNAME}:{PORTNUM}"
    try:
        async with websockets.connect(uri) as websocket:
            while True:
                data = await websocket.recv()
                parsed_data = json.loads(data)
                print(f"Received {len(parsed_data)} tuples")
                # Process your data here
    except asyncio.CancelledError:
        print("Connection was cancelled")
        raise  # Re-raise to handle it appropriately

async def main():
    while True:
        try:
            await receive_data()
        except websockets.ConnectionClosed:
            print("Connection closed, retrying in 5 seconds...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Client stopped manually")
