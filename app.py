#!/usr/bin/env python

import asyncio
import json
import websockets

import random

OPEN_MOUTH = {
    "type": "updateMouth",
    "size": 1,
    "message": "This is a message"
}
CLOSE_MOUTH = {
    "type": "updateMouth",
    "size": 2,
    "message": "This is a different message"
}

async def generate_messages():
    # Generator that yields messages to be send over the WebSocket.
    # Things placed in the 'yield' will be placed 'next' thanks to the 'with' keyword.
    while True:
        await asyncio.sleep(1)
        roll = random.random()
        if roll < 0.5:
            yield json.dumps(OPEN_MOUTH)
        else:
            yield json.dumps(CLOSE_MOUTH)

async def send_msg(websocket):
    try:
        async for message in generate_messages():
            await websocket.send(message)
    except websockets.ConnectionClosed:
        print("Connection closed")


async def main():
    async with websockets.serve(send_msg, "", 8001):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())