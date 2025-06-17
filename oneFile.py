from openai import OpenAI

client = OpenAI(api_key="my-key", base_url="http://localhost:8888/v1/")

model = 'Systran/faster-whisper-tiny'

audio_file = open("audio.mp3", "rb")
transcript = client.audio.transcriptions.create(
    model=model, file=audio_file
)
print(transcript.text)