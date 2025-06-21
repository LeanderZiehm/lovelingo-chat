from flask import Blueprint, request, jsonify
from openai import OpenAI
import tempfile
import uuid
import subprocess
import os

transcribe_bp = Blueprint("transcribe", __name__)

# Whisper API configuration
custom_whisper_api_key = "whisper.leanderziehm.com"
custom_whisper_url = "https://whisper.leanderziehm.com/v1/"
model = "Systran/faster-whisper-tiny"

client = OpenAI(api_key=custom_whisper_api_key, base_url=custom_whisper_url)

BASE_TMP_DIR = tempfile.gettempdir()


def save_uploaded_file(file, suffix=".webm"):
    tmp_path = os.path.join(BASE_TMP_DIR, uuid.uuid4().hex + suffix)
    file.save(tmp_path)
    return tmp_path


def convert_webm_to_ogg(input_path, output_suffix=".ogg"):
    filename = uuid.uuid4().hex + output_suffix
    output_path = os.path.join(BASE_TMP_DIR, filename)

    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "webm",  # force format
        "-i",
        input_path,
        "-vn",
        "-ar",
        "16000",
        "-ac",
        "1",
        "-c:a",
        "libvorbis",
        output_path,
    ]

    result = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg conversion failed: {result.stderr.decode()}")

    return output_path


def transcribe_audio_file(file_path, model):
    with open(file_path, "rb") as f:
        response = client.audio.transcriptions.create(model=model, file=f)
        return response.text.strip()


@transcribe_bp.route("/transcribe_v1", methods=["POST"])
def transcribe():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file uploaded"}), 400

    webm_file = request.files["audio"]
    webm_path = None
    ogg_path = None

    try:
        webm_path = save_uploaded_file(webm_file)
        ogg_path = convert_webm_to_ogg(webm_path)
        text = transcribe_audio_file(ogg_path, model)
        return jsonify({"text": text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        for path in [webm_path, ogg_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass
