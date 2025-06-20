# transcribe.py
from flask import Blueprint, request, jsonify
import requests
import os
from tempfile import NamedTemporaryFile

transcribe_bp = Blueprint('transcribe', __name__)

# Whisper API configuration
WHISPER_API_KEY = "whisper.leanderziehm.com"
WHISPER_API_URL = "https://whisper.leanderziehm.com/v1/audio/transcriptions"
MODEL = "Systran/faster-whisper-tiny"

@transcribe_bp.route('/transcribe', methods=['POST'])
def transcribe():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file uploaded"}), 400

    audio_file = request.files['audio']

    if not audio_file.filename.endswith('.ogg'):
        return jsonify({"error": "Only .ogg files are supported"}), 400

    with NamedTemporaryFile(suffix=".ogg", delete=False) as temp_file:
        temp_path = temp_file.name
        audio_file.save(temp_path)

    try:
        with open(temp_path, 'rb') as f:
            files = {'file': f}
            data = {'model': MODEL}
            headers = {'Authorization': f'Bearer {WHISPER_API_KEY}'}

            response = requests.post(WHISPER_API_URL, headers=headers, files=files, data=data)

            if response.status_code != 200:
                return jsonify({
                    "error": "Transcription failed",
                    "details": response.text
                }), response.status_code

            result = response.json()
            return jsonify({"text": result.get("text", "").strip()})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        try:
            os.remove(temp_path)
        except Exception:
            pass
