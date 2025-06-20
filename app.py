from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI
from tempfile import NamedTemporaryFile
import subprocess
import os

# Load environment variables (if using .env)
load_dotenv()

# Whisper API configuration
custom_whisper_api_key = "whisper.leanderziehm.com"
custom_whisper_url = "https://whisper.leanderziehm.com/v1/"
model = "Systran/faster-whisper-tiny"

# Initialize OpenAI client
client = OpenAI(api_key=custom_whisper_api_key, base_url=custom_whisper_url)

# Flask setup
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file uploaded"}), 400

    webm_file = request.files['audio']

    # Save uploaded webm audio to temp file
    with NamedTemporaryFile(suffix=".webm", delete=False) as source_temp:
        webm_path = source_temp.name
        webm_file.save(webm_path)

    # Convert webm to mp3 using ffmpeg
    with NamedTemporaryFile(suffix=".mp3", delete=False) as target_temp:
        mp3_path = target_temp.name

    try:
        # Convert using ffmpeg
        ffmpeg_cmd = [
            "ffmpeg", "-y",          # overwrite output
            "-i", webm_path,         # input file
            "-vn",                   # no video
            "-ar", "16000",          # audio sample rate
            "-ac", "1",              # mono audio
            "-f", "mp3",             # output format
            mp3_path
        ]

        ffmpeg_result = subprocess.run(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if ffmpeg_result.returncode != 0:
            error_output = ffmpeg_result.stderr.decode()
            return jsonify({
                "error": "FFmpeg conversion failed",
                "ffmpeg_output": error_output
            }), 500

        # Send mp3 to Whisper
        with open(mp3_path, "rb") as f:
            response = client.audio.transcriptions.create(
                model=model,
                file=f
            )
            return jsonify({"text": response.text.strip()})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        # Clean up temp files
        try:
            os.remove(webm_path)
            os.remove(mp3_path)
        except:
            pass

if __name__ == '__main__':
    app.run(debug=True)
