import asyncio
import datetime
import random
import websockets
Count=0

async def time(websocket, path):
    global Count
    Count+=1
    while True:
        try:
            await websocket.send(str(Count))
        except websockets.exceptions.ConnectionClosed:
            print("Client disconnected.  Do cleanup")
            Count-=1
            break             

async def main():
    async with websockets.serve(time, "localhost", 5678):
        await asyncio.Future()