import asyncio
import websockets

async def hello():
    uri = "ws://localhost:5678"
    stop=False
    async with websockets.connect(uri) as websocket:
        greeting = await websocket.recv()
    return greeting
