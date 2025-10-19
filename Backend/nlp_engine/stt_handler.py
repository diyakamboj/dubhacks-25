# Backend/nlp_engine/stt_handler.py

import speech_recognition as sr
import pvporcupine
import pyaudio
import struct
import threading
import time
from gemini_pipeline import process_text

# ---------------- Wake Word Path ----------------
wakeword_path = "wakewords/porcupine_mac_x86_64_aura_help.ppn"
print("Using wake word:", wakeword_path)

# ---------------- VoiceTrigger Class ----------------
class VoiceTrigger:
    def __init__(self):
        self.is_listening = False
        try:
            # Initialize Porcupine with macOS wake word
            self.porcupine = pvporcupine.create(
                keyword_paths=[wakeword_path]
            )
            self.recognizer = sr.Recognizer()
            self.mic = sr.Microphone()
            
            # Adjust for ambient noise
            with self.mic as source:
                self.recognizer.adjust_for_ambient_noise(source)
            print("✅ Voice trigger initialized")
        except Exception as e:
            print(f"❌ Voice trigger init failed: {e}")
            self.porcupine = None

    def listen_for_wake_word(self):
        """Continuously listen for wake word in background"""
        if not self.porcupine:
            return
        
        pa = pyaudio.PyAudio()
        audio_stream = pa.open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.porcupine.frame_length
        )
        
        print("🎤 Listening for wake word...")
        while True:
            pcm = audio_stream.read(self.porcupine.frame_length)
            pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
            
            keyword_index = self.porcupine.process(pcm)
            if keyword_index >= 0:
                print("🔔 Wake word detected!")
                self.capture_emergency_phrase()
                
    def capture_emergency_phrase(self):
        """After wake word, listen for emergency phrases"""
        try:
            print("🎤 Listening for emergency command...")
            with self.mic as source:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=3)
            
            text = self.recognizer.recognize_google(audio).lower()
            print(f"🎯 Heard: {text}")
            
            # Send to Gemini for intent analysis
            result = process_text(text)
            print(f"🤖 Processed result: {result}")
            return result
            
        except sr.WaitTimeoutError:
            print("⏰ No speech detected after wake word")
        except sr.UnknownValueError:
            print("🔇 Could not understand speech")
        except Exception as e:
            print(f"❌ STT Error: {e}")
        return {"intent": "none"}

# ---------------- Helper to Start Monitoring ----------------
def start_voice_monitoring():
    """Start the voice trigger in background thread"""
    trigger = VoiceTrigger()
    voice_thread = threading.Thread(target=trigger.listen_for_wake_word)
    voice_thread.daemon = True
    voice_thread.start()
    return trigger

# ---------------- Quick Test ----------------
if __name__ == "__main__":
    trigger = start_voice_monitoring()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping voice monitoring...")
