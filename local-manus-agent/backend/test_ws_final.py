import asyncio
import websockets
import json

async def test():
    uri = "ws://127.0.0.1:8000/ws/agent"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            await websocket.send(json.dumps({"type": "task", "content": "hello"}))
            response = await websocket.recv()
            print(f"Received: {response}")
    except Exception as e:
        print(f"Failed: {e}")

asyncio.run(test())
