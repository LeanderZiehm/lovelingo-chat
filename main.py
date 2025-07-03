# app.py
from flask import Flask, render_template,send_from_directory
from dotenv import load_dotenv
import os

load_dotenv()

from src.chat import chat_bp
from src.transcribe_v2 import transcribe_bp  # import the voice chat blueprint
from src.key_management import key_bp  # Add this line

app = Flask(__name__)
app.register_blueprint(chat_bp)
app.register_blueprint(transcribe_bp)  # register the voice chat blueprint
app.register_blueprint(key_bp)  # Register the key management blueprint



@app.route("/")
def index():
    return render_template("chat_v2.html")

@app.route("/key")
def key_management1():
    return render_template("key_management.html")


@app.route("/keys")
def key_management2():
    return render_template("key_management.html")

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

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        app.static_folder, 'favicon.ico', mimetype='image/vnd.microsoft.icon'
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(debug=True, port=port)
