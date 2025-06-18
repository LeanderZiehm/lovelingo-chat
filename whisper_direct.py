from openai import OpenAI

client = OpenAI(api_key="my-key", base_url="https://whisper.leanderziehm.com/v1/")

model = 'Systran/faster-whisper-tiny'

audio_file = open("static/voice/audio.mp3", "rb")
transcript = client.audio.transcriptions.create(
    model=model, file=audio_file
)
print(transcript.text)