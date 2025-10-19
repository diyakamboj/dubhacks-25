# Backend/nlp_engine/gemini_pipeline.py
import os, threading, time, subprocess, sys
from dotenv import load_dotenv

# -------- Gemini client (optional but preferred) --------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

try:
    from google import genai
    _gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
except Exception:
    _gemini_client = None

def _gai(prompt: str) -> str:
    """Ask Gemini with a short, safe prompt. Fallback to rule-based text."""
    if not _gemini_client:
        # Fallback text that's still useful for demo
        return "Continue high-quality chest compressions at about 110 per minute. I’ll keep the beat."
    try:
        r = _gemini_client.models.generate_content(
            model="models/gemini-2.0-pro-exp-02-05",
            contents=prompt
        )
        return (r.text or "").strip() or "Continue compressions at 110/min. I’ll keep time."
    except Exception as e:
        return f"Continue compressions at 110/min. (Gemini error: {e})"

# --------- TTS (plays on macOS for real) ----------
def speak(text: str, rate_wpm: int = 180):
    """
    Uses macOS 'say' for real-time speech and also prints to console for AR overlay.
    Keeps it simple and reliable for hackathon.
    """
    print(f"🖥️  DISPLAY: {text}")
    try:
        # macOS 'say' is the most reliable low-latency TTS we can use quickly
        subprocess.Popen(["say", "-r", str(rate_wpm), text])
    except Exception:
        # fallback: pyttsx3 (will speak, but can be slower)
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty('rate', rate_wpm)
            engine.setProperty('volume', 0.9)
            engine.say(text)
            engine.runAndWait()
        except Exception:
            print(f"🔇 [TTS would say]: {text}")

# --------- Metronome (110 BPM) ----------
class Metronome:
    def __init__(self, bpm=110):
        self.bpm = bpm
        self._running = False
        self._th = None

    def _beat(self):
        interval = 60.0 / float(self.bpm)
        # macOS system sound to avoid extra deps
        sound = "/System/Library/Sounds/Pop.aiff"
        while self._running:
            try:
                # non-blocking-ish; Pop is short
                subprocess.Popen(["afplay", sound], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
            time.sleep(interval)

    def start(self):
        if self._running:
            return
        self._running = True
        self._th = threading.Thread(target=self._beat, daemon=True)
        self._th.start()

    def stop(self):
        self._running = False

_metronome = Metronome(bpm=110)

# --------- Emergency/CPR State Machine ----------
emergency_context = None  # dict or None
conversation_memory = []

CPR_STEPS = [
    # step_index starts at 0
    "Tap the shoulders and shout. No response? Shout for help and ask someone to call 911 and bring an AED.",
    "Place the heel of your hand on the center of the chest. Put your other hand on top. Lock your elbows.",
    "Start chest compressions at ~110 per minute, depth ~2 inches. I’ll give you the beat.",
    "After 30 compressions, if trained, give 2 rescue breaths. Otherwise continue compressions.",
    "Keep cycles going. Tell me if they’re breathing, an AED arrives, or help arrives."
]

def _reset_context():
    global emergency_context, conversation_memory
    emergency_context = None
    conversation_memory = []

def start_emergency_guidance(emergency_type: str):
    """
    Entry point: call when CV detects prolonged unresponsiveness.
    Returns payload your nlp_server can emit to Unity/quest (text + flags).
    """
    _reset_context()
    if emergency_type != "cardiac_arrest":
        # For this hackathon scope, we only run CPR flow
        emergency_type = "cardiac_arrest"

    # Build context
    global emergency_context
    emergency_context = {
        "type": emergency_type,
        "step_index": 0,
        "compressions_running": False,
        "aed_present": False,
        "help_arrived": False,
        "breathing_restored": False
    }

    intro = "Unresponsive detected. Start CPR. I’ll guide you. First—ensure someone is calling 911 now."
    # Short Gemini opener (optional)
    ai = _gai("Give one short sentence to begin CPR for an unresponsive adult.")
    speak(intro)
    if ai:
        speak(ai)

    first = CPR_STEPS[0]
    speak(first)

    return {
        "intent": "emergency_started",
        "emergency_type": emergency_type,
        "response": f"{intro} {ai} {first}",
        "metronome": False
    }

def _advance_step():
    """Internal: move to next CPR step and speak it. Starts metronome on compression step."""
    if not emergency_context:
        return {"response": "No active emergency."}

    si = emergency_context["step_index"]
    si = min(si + 1, len(CPR_STEPS) - 1)
    emergency_context["step_index"] = si
    text = CPR_STEPS[si]
    speak(text)

    # Start metronome exactly when we hit compression instruction (step index 2)
    if si == 2 and not emergency_context["compressions_running"]:
        _metronome.start()
        emergency_context["compressions_running"] = True
        speak("Follow the beat: compress — release — compress — release.")

    return {"response": text, "metronome": emergency_context["compressions_running"]}

def _repeat_step():
    if not emergency_context:
        return {"response": "No active emergency."}
    text = CPR_STEPS[emergency_context["step_index"]]
    speak(f"Repeating: {text}")
    return {"response": text, "metronome": emergency_context["compressions_running"]}

def _stop_all(reason=""):
    """Finish the emergency flow gracefully."""
    if emergency_context and emergency_context.get("compressions_running"):
        _metronome.stop()
    msg = "Stopping assistance. " + (reason or "Stay with the person until help arrives.")
    speak(msg)
    _reset_context()
    return {"response": msg, "metronome": False, "done": True}

def process_user_response(user_text: str):
    """
    Main NLP handler: called by your /nlp endpoint.
    Very simple NLU + optional Gemini paraphrase to keep it robust.
    """
    if not user_text:
        return {"intent": "no_input", "response": "I didn’t catch that. Keep compressions going at this beat."}

    if not emergency_context:
        # If user speaks before CV trigger (or after reset)
        speak("No active emergency. Say 'Aura help' or wait for detection.")
        return {"intent": "no_emergency", "response": "No active emergency."}

    t = user_text.lower().strip()

    # ---- Quick intents (low-latency) ----
    if any(k in t for k in ["help arrived", "paramedics", "ems here", "they're here", "they are here"]):
        return _stop_all("Emergency services have arrived. Great job.")

    if any(k in t for k in ["they're breathing", "they are breathing", "breathing restored", "started breathing"]):
        return _stop_all("They are breathing. Roll to recovery position if safe, and monitor until help arrives.")

    if "pause metronome" in t or "stop metronome" in t:
        _metronome.stop()
        if emergency_context:
            emergency_context["compressions_running"] = False
        speak("Metronome paused. Resume compressions at the same rhythm.")
        return {"intent": "metronome_paused", "response": "Metronome paused.", "metronome": False}

    if "resume metronome" in t or "start metronome" in t:
        _metronome.start()
        if emergency_context:
            emergency_context["compressions_running"] = True
        speak("Metronome resumed.")
        return {"intent": "metronome_resumed", "response": "Metronome resumed.", "metronome": True}

    if "repeat" in t:
        return {"intent": "repeat", **_repeat_step()}

    if "next" in t:
        res = _advance_step()
        return {"intent": "next_step", **res}

    if "aed" in t:
        emergency_context["aed_present"] = True
        speak("Turn on the AED and follow its voice prompts immediately, while minimizing interruptions to compressions.")
        return {"intent": "aed", "response": "Use the AED now. Follow its prompts.", "metronome": emergency_context["compressions_running"]}

    # If user asks “am I doing it right?” / “how deep?” etc → short Gemini tip
    if any(k in t for k in ["right", "correct", "how deep", "how fast", "am i doing"]):
        tip = _gai("Give one sentence with CPR quality tips: depth about 2 inches, full recoil, hard and fast, minimal pauses.")
        speak(tip)
        return {"intent": "quality_tip", "response": tip, "metronome": emergency_context["compressions_running"]}

    # Default: contextual short guidance from Gemini
    ctx = f"CPR step now: {CPR_STEPS[emergency_context['step_index']]}"
    prompt = (
        "You are a calm CPR assistant. "
        "User said: '" + user_text + "'. "
        f"Context: {ctx}. "
        "Reply in under 2 sentences with practical guidance. "
        "If compressions are ongoing, remind them to keep pace with the beat."
    )
    ai = _gai(prompt)
    speak(ai)
    return {"intent": "guidance", "response": ai, "metronome": emergency_context["compressions_running"]}

# -------- Optional: let CV trigger start the CPR flow ----------
def handle_cv_trigger(event_type: str, confidence: float = 1.0):
    """
    If your nlp_server routes CV events here, we start CPR only on 'unresponsive' events.
    """
    if event_type != "unresponsive":
        return {"ignored": True}
    return start_emergency_guidance("cardiac_arrest")
