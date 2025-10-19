import asyncio, websockets, json

async def handle_message(websocket):
    async for msg in websocket:
        try:
            data = json.loads(msg)
            print(f"🧠 Received event: {data['type']} "
                  f"(conf: {data['confidence']}, priority: {data['priority']})")
        except Exception as e:
            print("⚠️ Bad message:", msg, e)

async def main():
    print("🎧 Mock Listener running on ws://localhost:8765 ...")
    async with websockets.serve(handle_message, "localhost", 8765):
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
