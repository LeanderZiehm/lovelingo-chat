import pydub
from tempfile import NamedTemporaryFile
from openai import OpenAI
import os

whisper_url="https://whisper.leanderziehm.com/v1/"
client = OpenAI(api_key="my-key", base_url=whisper_url)

filename = "audio2.mp3"
audio_path = f"static/voice/{filename}"
model = "Systran/faster-whisper-tiny"

# Load audio
audio = pydub.AudioSegment.from_file(audio_path)


# Split into 10-second chunks
chunk_length_ms = 5 * 1000
chunks = [audio[i:i+chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]


for i, chunk in enumerate(chunks):
    with NamedTemporaryFile(suffix=".mp3") as temp_file:
        chunk.export(temp_file.name, format="mp3")
        with open(temp_file.name, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model=model, file=audio_file
            )
            print(f"[Chunk {i}]: {response.text}")