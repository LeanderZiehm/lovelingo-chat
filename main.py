# app.py
from flask import Flask, render_template
from dotenv import load_dotenv
import os

load_dotenv()

# Check required environment variables
required_env_vars = ["ELEVENLABS_API_KEY", "GROQ_API_KEY"]
for var in required_env_vars:
    assert os.getenv(
        var
    ), f"Missing required environment variable: {var}. Please create a .env file with these variables before running this script. The links to get the free api keys is in the readme in the section setup dev."

from src.chat import chat_bp
from src.transcribe_v2 import transcribe_bp  # import the voice chat blueprint


app = Flask(__name__)
app.register_blueprint(chat_bp)
app.register_blueprint(transcribe_bp)  # register the voice chat blueprint


@app.route("/")
def index():
    return render_template("chat_v2.html")


@app.route("/v1")
def v1():
    return render_template("chat_v1.html")


@app.route("/call")
def call():
    return render_template("call.html")


@app.route("/persona")
def persona():
    return render_template("persona.html")


@app.route("/voice2voice")
def voice2voice():
    return render_template("persona.html")


if __name__ == "__main__":
    app.run(debug=True)
