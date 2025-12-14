import asyncio
import websockets
import json

RELAY = "ws://146.190.89.166:8765/relay"

async def main():
    print("Connecting...")
    ws = await websockets.connect(RELAY)
    print("OPEN")

    sub = {
        "op": "subscribe",
        "args": ["tickers.BTCUSDT"]
    }

    await ws.send(json.dumps(sub))
    print("SUB SENT")

    while True:
        msg = await ws.recv()
        print("MSG:", msg)

asyncio.run(main())
