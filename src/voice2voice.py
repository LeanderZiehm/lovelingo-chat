# chat_route.py
import os
from flask import Blueprint, request, Response, render_template
from groq import Groq
from elevenlabs.client import ElevenLabs

voice2voice_bp = Blueprint("chat", __name__)


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
# print("GROQ_API_KEY:", GROQ_API_KEY)
# print(ELEVENLABS_API_KEY)


# initialize once at import
groq = Groq(api_key=GROQ_API_KEY)
eleven = ElevenLabs(api_key=ELEVENLABS_API_KEY)
VOICE_ID = "nDJIICjR9zfJExIFeSCN"
# print("groq:", groq)
# print("eleven:", eleven)


@voice2voice_bp.route("/chat", methods=["GET"])
def v2v_chat_get():
    return render_template("chat.html")


@voice2voice_bp.route("/tts", methods=["POST"])
def v2v_tts():
    data = request.get_json(silent=True) or {}
    user_msg = data.get("message")
    if not user_msg:
        return {"error": "Missing 'message' in JSON body."}, 400

    # 1️⃣ Send user message to Groq
    resp = groq.chat.completions.create(
        messages=[{"role": "user", "content": user_msg}], model="llama3-8b-8192"
    )
    reply = resp.choices[0].message.content

    # 2️⃣ Generate ElevenLabs TTS stream
    audio_stream = eleven.text_to_speech.stream(
        text=reply, voice_id=VOICE_ID, model_id="eleven_multilingual_v2"
    )

    def generate():
        for chunk in audio_stream:
            if isinstance(chunk, bytes):
                yield chunk

    headers = {"X-Reply-Text": reply.replace("\n", " ")}
    return Response(generate(), mimetype="audio/mpeg", headers=headers)


@voice2voice_bp.route("/chat", methods=["POST"])
def v2v_chat():
    data = request.get_json(silent=True) or {}
    user_msg = data.get("message")
    if not user_msg:
        return {"error": "Missing 'message' in JSON body."}, 400

    # 1️⃣ Send user message to Groq
    resp = groq.chat.completions.create(
        messages=[{"role": "user", "content": user_msg}], model="llama3-8b-8192"
    )
    reply = resp.choices[0].message.content

    # 2️⃣ Generate ElevenLabs TTS stream
    audio_stream = eleven.text_to_speech.stream(
        text=reply, voice_id=VOICE_ID, model_id="eleven_multilingual_v2"
    )

    def generate():
        for chunk in audio_stream:
            if isinstance(chunk, bytes):
                yield chunk

    headers = {"X-Reply-Text": reply.replace("\n", " ")}
    return Response(generate(), mimetype="audio/mpeg", headers=headers)
