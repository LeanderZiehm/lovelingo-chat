# transcribe.py
from flask import Blueprint, request, jsonify
from openai import OpenAI
from tempfile import NamedTemporaryFile
import subprocess
import os

transcribe_bp = Blueprint('transcribe', __name__)

# Whisper API configuration
custom_whisper_api_key = "whisper.leanderziehm.com"
custom_whisper_url = "https://whisper.leanderziehm.com/v1/"
model = "Systran/faster-whisper-tiny"

client = OpenAI(api_key=custom_whisper_api_key, base_url=custom_whisper_url)

@transcribe_bp.route('/transcribe', methods=['POST'])
def transcribe():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file uploaded"}), 400

    webm_file = request.files['audio']

    with NamedTemporaryFile(suffix=".webm", delete=False) as source_temp:
        webm_path = source_temp.name
        webm_file.save(webm_path)

    with NamedTemporaryFile(suffix=".mp3", delete=False) as target_temp:
        mp3_path = target_temp.name

    try:
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", webm_path,
            "-vn",
            "-ar", "16000",
            "-ac", "1",
            "-f", "mp3",
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

        with open(mp3_path, "rb") as f:
            response = client.audio.transcriptions.create(
                model=model,
                file=f
            )
            return jsonify({"text": response.text.strip()})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        try:
            os.remove(webm_path)
            os.remove(mp3_path)
        except:
            pass
