# nlp_server.py
from flask import Flask, request, jsonify
from gemini_pipeline import process_text
from stt_handler import transcribe_audio
import os

app = Flask(__name__)

@app.route("/nlp", methods=["POST"])
def nlp_endpoint():
    """
    Receives JSON from Unity or Voice input.
    Expects JSON: { "text": "..." } or { "audio": "..." }
    Returns JSON: { "intent": "...", "text": "...", "audio_file": "..." }
    """
    data = request.json
    # Simulate STT
    text = data.get("text") or transcribe_audio(data.get("audio"))
    # AI reasoning
    result = process_text(text)
    
    # Simulate TTS
    if result["intent"] == "call_911":
        audio_file = "AI_911/call911_1.wav"  # pre-recorded placeholder
        display_text = "Calling 911 now. Please stay calm."
    else:
        audio_file = None
        display_text = "No action needed."
    
    return jsonify({
        "intent": result["intent"],
        "text": display_text,
        "audio_file": audio_file
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
