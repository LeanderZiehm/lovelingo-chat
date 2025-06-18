import subprocess
from openai import OpenAI
import numpy as np
import threading
import queue
import io, wave


# Parameters
CHUNK_SECONDS = 4       # chunk size in seconds
OVERLAP_SECONDS = 1     # overlap between chunks in seconds
SAMPLE_RATE = 16000     # Whisper expects 16kHz audio
AUDIO_CHANNELS = 1
AUDIO_FORMAT = 's16le'  # 16-bit PCM
DEVICE = 'default'      # Change to your microphone device if needed


API_KEY   = "my-key"
BASE_URL  = "https://whisper.leanderziehm.com/v1/"

class WhisperModels:
    BASE = "Systran/faster-whisper-base"
    LARGE_V3 = "Systran/faster-whisper-large-v3"
    LARGE_V2 = "Systran/faster-whisper-large-v2"
    TINY = "Systran/faster-whisper-tiny"
    SMALL = "Systran/faster-whisper-small"
    BASE_EN = "Systran/faster-whisper-base.en"
    SMALL_EN = "Systran/faster-whisper-small.en"
    MEDIUM = "Systran/faster-whisper-medium"
    MEDIUM_EN = "Systran/faster-whisper-medium.en"
    TINY_EN = "Systran/faster-whisper-tiny.en"



# MODEL = "Systran/faster-whisper-tiny"
MODEL = WhisperModels.TINY_EN

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# Thread-safe queue for audio data
audio_queue = queue.Queue()

def make_wav_bytes(chunk: np.ndarray, sample_rate=16000):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(chunk.tobytes())
    buf.seek(0)
    return buf

def record_audio():
    """Continuously records audio in chunks with overlap using FFmpeg."""
    chunk_samples = CHUNK_SECONDS * SAMPLE_RATE
    overlap_samples = OVERLAP_SECONDS * SAMPLE_RATE
    buffer = np.zeros(0, dtype=np.int16)

    ffmpeg_cmd = [
        "ffmpeg",
        "-f", "alsa",  # For Linux; use "avfoundation" (Mac) or "dshow" (Windows)
        "-i", DEVICE,
        "-ac", str(AUDIO_CHANNELS),
        "-ar", str(SAMPLE_RATE),
        "-f", AUDIO_FORMAT,
        "-"
    ]
    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    bytes_per_sample = 2  # s16le = 2 bytes per sample

    while True:
        # Read enough bytes for chunk
        chunk_bytes = chunk_samples * bytes_per_sample
        audio_bytes = process.stdout.read(chunk_bytes)
        if not audio_bytes:
            break
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
        # Concatenate overlap from previous buffer
        buffer = np.concatenate([buffer[-overlap_samples:], audio_array])
        audio_queue.put(buffer.copy())

def transcribe_loop():
    """Continuously transcribes audio chunks with overlap and compares results."""
    prev_text = ""
    prev_chunk = None

    while True:
        chunk = audio_queue.get()
        if chunk is None:
            break
        # print(chunk)
 
        wav_buffer = make_wav_bytes(chunk, SAMPLE_RATE)
        resp = client.audio.transcriptions.create(model=MODEL,file=("chunk.wav", wav_buffer, "audio/wav"))
        text = resp.text.strip()

        # Compare with previous text for overlap region
        if prev_chunk is not None:
            # Compare only the overlapping region
            overlap_text = text[:len(prev_text)]
            if overlap_text != prev_text:
                print(f"Updated transcript (context improved): {text}")
            else:
                print(f"Transcript: {text}")
        else:
            print(f"Transcript: {text}")

        prev_text = text
        prev_chunk = chunk

def main():
    # Start recording and transcription threads
    threading.Thread(target=record_audio, daemon=True).start()
    transcribe_loop()

if __name__ == "__main__":
    main()
