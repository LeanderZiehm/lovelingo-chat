from flask import Flask, render_template, request, jsonify
import os, io
from dotenv import load_dotenv
from openai import OpenAI
from pydub import AudioSegment
from tempfile import NamedTemporaryFile

# Load environment variables
load_dotenv()
custom_whisper_api_key = "whisper.leanderziehm.com"
custom_whisper_url = "https://whisper.leanderziehm.com/v1/"
model = "Systran/faster-whisper-tiny"

# Initialize custom client
client = OpenAI(api_key=custom_whisper_api_key, base_url=custom_whisper_url)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file uploaded"}), 400

    audio_file = request.files['audio']
    try:
        # Load audio from uploaded file
        audio = AudioSegment.from_file(audio_file)

        # Split into 5-second chunks (or any desired length)
        chunk_length_ms = 5 * 1000
        chunks = [audio[i:i+chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]

        full_transcript = ""
        for i, chunk in enumerate(chunks):
            with NamedTemporaryFile(suffix=".mp3", delete=True) as temp_file:
                chunk.export(temp_file.name, format="mp3")
                with open(temp_file.name, "rb") as f:
                    response = client.audio.transcriptions.create(
                        model=model,
                        file=f
                    )
                    full_transcript += response.text + " "

        return jsonify({"text": full_transcript.strip()})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
