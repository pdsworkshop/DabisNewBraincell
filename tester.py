from dotenv import load_dotenv
import asyncio
import websockets
import json
import time

load_dotenv()

SERVER_HOST = "localhost"
SERVER_PORT = 4009

# Websocket Client
async def handler(websocket):
    while True:
        try:
            message = await websocket.recv()
        except websockets.ConnectionClosedOK:
            print("Someone disconnected.")
            break
        print(message)

async def main_looper():
    pass

async def main():
    async with websockets.serve(handler, SERVER_HOST, SERVER_PORT):
        await asyncio.Future() # run forever
    
if __name__ == "__main__":
    asyncio.run(main())