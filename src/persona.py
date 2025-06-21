from flask import Blueprint, request, jsonify, send_file, abort
import os
import json
from threading import Lock

persona_bp = Blueprint("persona", __name__)

# Constants for file paths
PERSONA_JSON_PATH = os.path.join(os.path.dirname(__file__), "personas.json")
CHATHISTORY_JSON_PATH = os.path.join(os.path.dirname(__file__), "chat_history.json")

# Lock for thread-safe file writes
file_lock = Lock()


def _load_json(path):
    """Helper to load JSON from file."""
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _write_json(path, data):
    """Helper to write JSON to file in a thread-safe way."""
    with file_lock:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


@persona_bp.route("/get_persona_image", methods=["GET"])
def get_persona_image():
    """
    Query Params:
      - name: persona name to fetch image for
    Returns the image file for the given persona.
    """
    name = request.args.get("name")
    if not name:
        return jsonify({"error": "Missing persona name parameter"}), 400

    personas = _load_json(PERSONA_JSON_PATH)
    # Ensure personas is a list of dicts
    if not isinstance(personas, list):
        return jsonify({"error": "Invalid persona file format"}), 500

    persona = next((p for p in personas if p.get("name") == name), None)
    if not persona:
        return jsonify({"error": "Persona not found"}), 404

    image_path = persona.get("image")
    if not image_path:
        return jsonify({"error": "Persona image not configured"}), 404

    abs_path = os.path.join(os.path.dirname(__file__), image_path)
    if not os.path.exists(abs_path):
        return jsonify({"error": "Image file does not exist"}), 404

    # Send the image file
    return send_file(abs_path, mimetype="image/png")


@persona_bp.route("/chat_history", methods=["GET"])
def get_persona_chat_history():
    """
    Query Params:
      - name: persona name whose chat history to fetch
    Returns JSON array of messages for the persona.
    """
    name = request.args.get("name")
    if not name:
        return jsonify({"error": "Missing persona name parameter"}), 400

    history = _load_json(CHATHISTORY_JSON_PATH)
    # history expected as dict: { persona_name: [ {role, message, timestamp}, ... ] }
    persona_history = history.get(name, [])
    return jsonify({"name": name, "history": persona_history})


@persona_bp.route("/set_chat_hisotry", methods=["POST"])
def set_persona_chat_history():
    """
    Body JSON:
      - name: persona name
      - role: 'user' or 'assistant'
      - message: text of the message
    Appends a new entry to the chat history and returns updated history.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    name = data.get("name")
    role = data.get("role")
    message = data.get("message")

    if not all([name, role, message]):
        return jsonify({"error": "Missing one of name, role, or message"}), 400

    history = _load_json(CHATHISTORY_JSON_PATH)
    if not isinstance(history, dict):
        history = {}

    # Initialize list if new persona
    persona_history = history.setdefault(name, [])

    # Create entry with optional timestamp
    entry = {
        "role": role,
        "message": message,
        "timestamp": request.headers.get(
            "X-Timestamp"
        ),  # clients can include timestamp header
    }

    persona_history.append(entry)
    # Write back to file
    _write_json(CHATHISTORY_JSON_PATH, history)

    return jsonify({"name": name, "history": persona_history}), 201
