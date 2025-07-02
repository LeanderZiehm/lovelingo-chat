import os
from flask import Blueprint, request, jsonify

key_bp = Blueprint("key_management", __name__)

# Global variables to store API keys and clients
_current_groq_key = os.getenv("GROQ_API_KEY")
_current_elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")


def get_current_keys_half_hidden():
    """Get current API keys without revealing the actual keys"""
    return {
        "groq_set": _current_groq_key[:8] + "****" if _current_groq_key else False,
        "elevenlabs_set": _current_elevenlabs_key[:8] + "****" if _current_elevenlabs_key else False
    }

@key_bp.route("/api/keys", methods=["GET"])
def get_key_status():
    """Get current key status (without revealing the actual keys)"""
    return jsonify(get_current_keys_half_hidden())

@key_bp.route("/api/keys", methods=["POST"])
def update_keys():
    """Update API keys"""
    global _current_groq_key, _current_elevenlabs_key
    
    data = request.get_json(silent=True) or {}
    groq_key = data.get("groq_key", "").strip()
    elevenlabs_key = data.get("elevenlabs_key", "").strip()
    
    updated = False
    
    if groq_key:
        _current_groq_key = groq_key
        updated = True
    
    if elevenlabs_key:
        _current_elevenlabs_key = elevenlabs_key
        updated = True
    
    return jsonify({
        "success": True,
        "message": "API keys updated successfully" if updated else "No keys provided",
        "groq_set": bool(_current_groq_key),
        "elevenlabs_set": bool(_current_elevenlabs_key)
    })

def get_groq_api_key():
    """Get the current Groq API key"""
    return _current_groq_key

def get_elevenlabs_api_key():
    """Get the current ElevenLabs API key"""
    return _current_elevenlabs_key
