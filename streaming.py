import pydub
from tempfile import NamedTemporaryFile
from openai import OpenAI

client = OpenAI(api_key="my-key", base_url="http://localhost:8888/v1/")

filename = "audio2.mp3"
model = "Systran/faster-whisper-tiny"

# Load audio
audio = pydub.AudioSegment.from_file(filename)


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
