import io
import threading
import asyncio
import sounddevice as sd
import soundfile as sf
import edge_tts

VOICE = "en-US-GuyNeural"  

RATE = "+0%"     
VOLUME = "+0%"   
PITCH = "+0Hz"   

stop_speaking_flag = threading.Event()

def edge_speak(text: str, ui=None, blocking=False):
    if not text or not text.strip():
        return

    finished_event = threading.Event()

    def _thread():
        if ui:
            ui.start_speaking()

        stop_speaking_flag.clear()

        try:
            asyncio.run(_speak_async(text))
        except Exception as e:
            print("EDGE TTS ERROR:", e)
        finally:
            if ui:
                ui.stop_speaking()
            finished_event.set()

    threading.Thread(target=_thread, daemon=True).start()

    if blocking:
        finished_event.wait()

async def _speak_async(text: str):
    communicate = edge_tts.Communicate(
        text=text.strip(),
        voice=VOICE,
        rate=RATE,
        volume=VOLUME,
        pitch=PITCH,
    )

    audio_bytes = io.BytesIO()

    async for chunk in communicate.stream():
        if stop_speaking_flag.is_set():
            return

        if chunk["type"] == "audio":
            audio_bytes.write(chunk["data"])

    audio_bytes.seek(0)

    data, samplerate = sf.read(audio_bytes, dtype="float32")

    channels = data.shape[1] if len(data.shape) > 1 else 1

    with sd.OutputStream(
        samplerate=samplerate,
        channels=channels,
        dtype="float32",
    ) as stream:
        block_size = 1024
        for start in range(0, len(data), block_size):
            if stop_speaking_flag.is_set():
                break
            stream.write(data[start:start + block_size])

def stop_speaking():
    stop_speaking_flag.set()