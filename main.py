# app.py
from flask import Flask, render_template
from dotenv import load_dotenv
from openai import OpenAI
import os
load_dotenv()

from src.chat import chat_bp
from src.transcribe import transcribe_bp  # import the blueprint

# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
# print("222 GROQ_API_KEY:", GROQ_API_KEY)
# print(ELEVENLABS_API_KEY)


app = Flask(__name__)
app.register_blueprint(chat_bp)
app.register_blueprint(transcribe_bp)  # register the blueprint

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
