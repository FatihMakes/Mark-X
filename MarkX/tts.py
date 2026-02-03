import io
import threading
import requests
import sounddevice as sd
import soundfile as sf
import os

#Take the API key from ElevenLabs

ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"

stop_speaking_flag = threading.Event()

def edge_speak(text: str, ui=None, blocking=False):
    if not text.strip():
        return
    

    finished_event = threading.Event()

    def _thread():
        if ui:
            ui.start_speaking()
        stop_speaking_flag.clear()

        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
            headers = {
                "xi-api-key": ELEVEN_API_KEY,
                "Content-Type": "application/json"
            }
            payload = {
                "text": text.strip(),
                "voice_settings": {
                    "stability": 0.55,
                    "similarity_boost": 0.85
                }
            }

            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()

            audio_data = io.BytesIO(response.content)
            data, samplerate = sf.read(audio_data, dtype="float32")

            channels = data.shape[1] if len(data.shape) > 1 else 1
            with sd.OutputStream(
                samplerate=samplerate,
                channels=channels,
                dtype="float32"
            ) as stream:
                block_size = 1024
                for start in range(0, len(data), block_size):
                    if stop_speaking_flag.is_set():
                        break
                    stream.write(data[start:start + block_size])

        except Exception as e:
            print("VOICE ERROR:", e)
        finally:
            if ui:
                ui.stop_speaking()
            finished_event.set()

    threading.Thread(target=_thread, daemon=True).start()

    if blocking:
        finished_event.wait()

def stop_speaking():
    stop_speaking_flag.set()
