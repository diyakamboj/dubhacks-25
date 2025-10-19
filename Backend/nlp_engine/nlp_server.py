import asyncio, websockets, json, os
from flask import Flask, request, jsonify
from gemini_pipeline import (
    start_emergency_guidance,
    process_user_response,
    handle_cv_trigger
)
from stt_handler import start_voice_thread

app = Flask(__name__)

# ----------- Flask route: text/audio from user -----------
@app.route("/nlp", methods=["POST"])
def nlp_endpoint():
    """
    Handles input from Unity or user mic (text or audio).
    Example JSON:
      { "text": "next" }
      or
      { "audio": "<base64_audio>" }
    """
    data = request.json
    user_text = data.get("text")

    if not user_text and data.get("audio"):
        user_text = transcribe_audio(data.get("audio"))

    if not user_text:
        return jsonify({"intent": "no_input", "response": "No speech detected."})

    # Send to CPR NLP engine
    result = process_user_response(user_text)
    print(f"👤 User: {user_text}")
    print(f"🤖 Gemini: {result['response']}")
    return jsonify(result)


# ----------- WebSocket: receives CV model triggers -----------
async def cv_listener(websocket):
    """
    Receives events from cv_server.py like:
      {"type": "unresponsive", "confidence": 0.83}
    Starts CPR when unresponsive is detected.
    """
    print("🌐 Waiting for CV input...")
    async for message in websocket:
        try:
            event = json.loads(message)
            evt_type = event.get("type", "")
            conf = event.get("confidence", 0)

            print(f"📥 Received from CV: {evt_type} (conf={conf:.2f})")

            # Only respond to 'unresponsive'
            if evt_type == "unresponsive":
                result = handle_cv_trigger(evt_type, conf)
                print(f"🤖 Gemini: {result['response']}")
        except Exception as e:
            print(f"⚠️ Error handling CV message: {e}")

# ----------- Run both Flask + WebSocket servers -----------
async def main():
    # Run websocket + flask concurrently
    ws_server = await websockets.serve(cv_listener, "localhost", 8765)
    print("🤖 Gemini WebSocket server running at ws://localhost:8765")

    loop = asyncio.get_event_loop()
    flask_future = loop.run_in_executor(None, lambda: app.run(host="0.0.0.0", port=5001))
    await asyncio.Future()  # run forever

if __name__ == "__main__":
    start_voice_thread();
    asyncio.run(main())
