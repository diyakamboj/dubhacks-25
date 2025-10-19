# stt_handler.py
import os, pvporcupine, pyaudio, struct, threading, time
from gemini_pipeline import start_emergency_guidance
from dotenv import load_dotenv

load_dotenv()
WAKEWORD_PATH = os.path.join(os.path.dirname(__file__), "wakewords/Aura-help_en_mac_v3_0_0.ppn")
ACCESS_KEY = os.getenv("PICO_VOICE_API_KEY")  # make sure this exists in your .env

class AuraVoiceTrigger:
    def __init__(self):
        try:
            # Pass the access key here
            self.porcupine = pvporcupine.create(
                access_key=ACCESS_KEY,
                keyword_paths=[WAKEWORD_PATH]
            )
            self.pa = pyaudio.PyAudio()
            self.stream = self.pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )
            print("🎙️ Aura voice trigger ready — say 'Aura help'")
        except Exception as e:
            print(f"❌ Voice init failed: {e}")

    def listen_loop(self):
        if not hasattr(self, "stream"):
            print("⚠️ Audio stream not initialized, cannot listen.")
            return
        print("🕵️ Listening for 'Aura help'...")
        while True:
            pcm = self.stream.read(self.porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
            keyword_index = self.porcupine.process(pcm)
            if keyword_index >= 0:
                print("🩺 Wake word detected! Starting CPR guidance...")
                start_emergency_guidance("cardiac_arrest")

def start_voice_thread():
    trigger = AuraVoiceTrigger()
    t = threading.Thread(target=trigger.listen_loop)
    t.daemon = True
    t.start()

if __name__ == "__main__":
    start_voice_thread()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("🛑 Exiting voice trigger.")
