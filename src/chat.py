# chat_route.py
import os
from flask import Blueprint, request, Response, render_template
from groq import Groq
from elevenlabs.client import ElevenLabs
import requests
from src.key_management import get_groq_api_key, get_elevenlabs_api_key

chat_bp = Blueprint("chat", __name__)



# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
# print("GROQ_API_KEY:", GROQ_API_KEY)
# print(ELEVENLABS_API_KEY)

GOOGLE_DOC_TXT_URL = "https://docs.google.com/document/d/1qz-3McunkpMIeKfoipANVMW4iZzZWHSVdAA1nhfa8lE/export?format=txt"

def fetch_system_prompt():
    try:
        response = requests.get(GOOGLE_DOC_TXT_URL)
        if response.status_code == 200:
            return response.text.strip()
        else:
            return "Du bist ein Deutschlehrer."  # Fallback minimal prompt
    except Exception:
        return "Du bist ein Deutschlehrer."  # Fallback minimal prompt



# initialize once at import

# eleven = ElevenLabs(api_key=ELEVENLABS_API_KEY)
VOICE_ID = "nDJIICjR9zfJExIFeSCN"


def get_groq():
    return Groq(api_key=get_groq_api_key())
    
def get_elevenlabs():
    return ElevenLabs(api_key=get_elevenlabs_api_key())


@chat_bp.route("/chat", methods=["GET"])
def chat_get():
    return render_template("chat.html")

# todo add cashing of audo files if same text is requested
@chat_bp.route("/tts", methods=["POST"])
def tts():
    data = request.get_json(silent=True) or {}
    text = data.get("text")
    if not text:
        return {"error": "Missing 'text' in JSON body."}, 400
    
    # Generate ElevenLabs TTS stream
    audio_stream = get_elevenlabs().text_to_speech.stream(
        text=text, voice_id=VOICE_ID, model_id="eleven_multilingual_v2"
    )

    def generate():
        for chunk in audio_stream:
            if isinstance(chunk, bytes):
                yield chunk

    headers = {"X-Reply-Text": text.replace("\n", " ")}
    return Response(generate(), mimetype="audio/mpeg", headers=headers)



@chat_bp.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    user_msg = data.get("message")
    if not user_msg:
        return {"error": "Missing 'message' in JSON body."}, 400

    system_prompt = fetch_system_prompt()

    # 1️⃣ Send user message to Groq
    resp = get_groq().chat.completions.create(
        messages=[{"role":"system","content":system_prompt}, {"role": "user", "content": user_msg}], model="llama-3.3-70b-versatile"
    )
    reply = resp.choices[0].message.content

    # 2️⃣ Generate ElevenLabs TTS stream
    audio_stream = get_elevenlabs().text_to_speech.stream(
        text=reply, voice_id=VOICE_ID, model_id="eleven_multilingual_v2"
    )

    def generate():
        for chunk in audio_stream:
            if isinstance(chunk, bytes):
                yield chunk

    headers = {"X-Reply-Text": reply.replace("\n", " ")}
    return Response(generate(), mimetype="audio/mpeg", headers=headers)
