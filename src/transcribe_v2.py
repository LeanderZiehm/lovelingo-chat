# voice_chat.py
from flask import Blueprint, request, jsonify, render_template
from openai import OpenAI
import tempfile
import subprocess
import os
import logging
import time
from pathlib import Path


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

transcribe_bp = Blueprint("transcribe_bp", __name__)

# Whisper API configuration
CUSTOM_WHISPER_API_KEY = "whisper.leanderziehm.com"
CUSTOM_WHISPER_URL = "https://whisper.leanderziehm.com/v1/"
MODEL = "Systran/faster-whisper-tiny"

# Configuration
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB
SUPPORTED_FORMATS = {".webm", ".mp3", ".wav", ".m4a", ".ogg", ".flac"}
FFMPEG_TIMEOUT = 30  # seconds
WHISPER_TIMEOUT = 30  # seconds


# Initialize OpenAI client with error handling
try:
    client = OpenAI(api_key=CUSTOM_WHISPER_API_KEY, base_url=CUSTOM_WHISPER_URL)
    logger.info("OpenAI client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {e}")
    client = None


class TranscriptionError(Exception):
    """Custom exception for transcription errors"""

    pass


class AudioProcessor:
    """Handles audio file processing and conversion"""

    @staticmethod
    def validate_audio_file(file):
        """Validate uploaded audio file"""
        if not file:
            raise TranscriptionError("No audio file provided")

        if file.content_length and file.content_length > MAX_FILE_SIZE:
            raise TranscriptionError(
                f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
            )

        # Check file extension
        filename = file.filename or "unknown"
        file_ext = Path(filename).suffix.lower()

        if file_ext not in SUPPORTED_FORMATS:
            raise TranscriptionError(
                f"Unsupported format: {file_ext}. Supported: {', '.join(SUPPORTED_FORMATS)}"
            )

        return file_ext

    @staticmethod
    def check_ffmpeg():
        """Check if FFmpeg is available"""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"], capture_output=True, timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    @staticmethod
    def convert_to_whisper_format(input_path, output_path):
        """Convert audio to Whisper-compatible format with multiple fallback options"""

        # Primary conversion command (highest quality)
        primary_cmd = [
            "ffmpeg",
            "-y",
            "-i",
            input_path,
            "-vn",  # No video
            "-ar",
            "16000",  # 16kHz sample rate
            "-ac",
            "1",  # Mono
            "-c:a",
            "libmp3lame",  # MP3 codec
            "-b:a",
            "64k",  # 64kbps bitrate
            "-f",
            "mp3",
            output_path,
        ]

        # Fallback commands with different options
        fallback_commands = [
            # Fallback 1: Different codec
            [
                "ffmpeg",
                "-y",
                "-i",
                input_path,
                "-vn",
                "-ar",
                "16000",
                "-ac",
                "1",
                "-acodec",
                "mp3",
                "-f",
                "mp3",
                output_path,
            ],
            # Fallback 2: WAV format
            [
                "ffmpeg",
                "-y",
                "-i",
                input_path,
                "-vn",
                "-ar",
                "16000",
                "-ac",
                "1",
                "-f",
                "wav",
                output_path.replace(".mp3", ".wav"),
            ],
            # Fallback 3: Basic conversion
            ["ffmpeg", "-y", "-i", input_path, "-ar", "16000", "-ac", "1", output_path],
        ]

        commands_to_try = [primary_cmd] + fallback_commands

        for i, cmd in enumerate(commands_to_try):
            try:
                logger.info(
                    f"Attempting conversion method {i+1}: {' '.join(cmd[:5])}..."
                )

                result = subprocess.run(
                    cmd, capture_output=True, timeout=FFMPEG_TIMEOUT, text=True
                )

                if result.returncode == 0:
                    # Check if output file was created and has content
                    output_file = cmd[-1]  # Last argument is output file
                    if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                        logger.info(f"Conversion successful with method {i+1}")
                        return output_file
                    else:
                        logger.warning(
                            f"Method {i+1} completed but output file is empty or missing"
                        )
                        continue
                else:
                    logger.warning(
                        f"Method {i+1} failed with return code {result.returncode}"
                    )
                    logger.warning(f"FFmpeg stderr: {result.stderr}")
                    continue

            except subprocess.TimeoutExpired:
                logger.error(f"Method {i+1} timed out after {FFMPEG_TIMEOUT} seconds")
                continue
            except Exception as e:
                logger.error(f"Method {i+1} failed with exception: {e}")
                continue

        raise TranscriptionError(
            "All audio conversion methods failed. Please check your audio file format."
        )


class WhisperTranscriber:
    """Handles Whisper API transcription with fallbacks"""

    def __init__(self, client):
        self.client = client

    def transcribe_audio(self, audio_path, language=None):
        """Transcribe audio with multiple attempts and error handling"""

        if not self.client:
            raise TranscriptionError("Whisper client not initialized")

        if not os.path.exists(audio_path):
            raise TranscriptionError(f"Audio file not found: {audio_path}")

        file_size = os.path.getsize(audio_path)
        if file_size == 0:
            raise TranscriptionError("Audio file is empty")

        logger.info(f"Transcribing audio file: {audio_path} ({file_size} bytes)")

        # Multiple transcription attempts with different parameters
        transcription_configs = [
            {"temperature": 0.0, "language": language},
            {"temperature": 0.2, "language": language},
            {"temperature": 0.0},  # Auto-detect language
            {"temperature": 0.5},  # Higher temperature for difficult audio
        ]

        for i, config in enumerate(transcription_configs):
            try:
                logger.info(f"Transcription attempt {i+1} with config: {config}")

                with open(audio_path, "rb") as audio_file:
                    response = self.client.audio.transcriptions.create(
                        model=MODEL, file=audio_file, **config
                    )

                if hasattr(response, "text") and response.text:
                    text = response.text.strip()
                    if len(text) > 0:
                        logger.info(
                            f"Transcription successful on attempt {i+1}: '{text[:50]}...'"
                        )

                        # Try to extract confidence if available
                        confidence = getattr(response, "confidence", None)
                        if confidence is None:
                            # Estimate confidence based on text length and attempt number
                            confidence = max(
                                0.5, 1.0 - (i * 0.1) - (1.0 / max(1, len(text.split())))
                            )

                        return {
                            "text": text,
                            "confidence": confidence,
                            "language": getattr(response, "language", "unknown"),
                            "attempt": i + 1,
                        }
                else:
                    logger.warning(f"Attempt {i+1} returned empty transcription")

            except Exception as e:
                logger.error(f"Transcription attempt {i+1} failed: {e}")
                if i == len(transcription_configs) - 1:  # Last attempt
                    raise TranscriptionError(
                        f"All transcription attempts failed. Last error: {str(e)}"
                    )
                continue

        raise TranscriptionError("Failed to transcribe audio after all attempts")


# Global instances
audio_processor = AudioProcessor()
transcriber = WhisperTranscriber(client) if client else None


@transcribe_bp.route("/transcribe", methods=["POST"])
def transcribe():
    """Main transcription endpoint with comprehensive error handling"""

    start_time = time.time()
    webm_path = None
    converted_path = None

    try:
        # Check if Whisper client is available
        if not transcriber:
            return (
                jsonify(
                    {
                        "error": "Whisper service unavailable",
                        "details": "Failed to initialize Whisper client. Check API configuration.",
                        "fix": "Verify CUSTOM_WHISPER_API_KEY and CUSTOM_WHISPER_URL settings",
                    }
                ),
                503,
            )

        # Check if FFmpeg is available
        if not audio_processor.check_ffmpeg():
            return (
                jsonify(
                    {
                        "error": "FFmpeg not available",
                        "details": "FFmpeg is required for audio processing",
                        "fix": "Install FFmpeg: apt-get install ffmpeg (Ubuntu) or brew install ffmpeg (macOS)",
                    }
                ),
                500,
            )

        # Validate request
        if "audio" not in request.files:
            return (
                jsonify(
                    {
                        "error": "No audio file in request",
                        "details": "Request must include 'audio' file field",
                        "fix": "Ensure FormData includes audio file with key 'audio'",
                    }
                ),
                400,
            )

        audio_file = request.files["audio"]

        # Validate audio file
        try:
            file_ext = audio_processor.validate_audio_file(audio_file)
            logger.info(f"Processing {file_ext} file: {audio_file.filename}")
        except TranscriptionError as e:
            return (
                jsonify(
                    {
                        "error": "Invalid audio file",
                        "details": str(e),
                        "fix": "Use supported audio formats: "
                        + ", ".join(SUPPORTED_FORMATS),
                    }
                ),
                400,
            )

        # Save uploaded file
        try:
            with tempfile.NamedTemporaryFile(
                suffix=file_ext, delete=False
            ) as temp_file:
                webm_path = temp_file.name
                audio_file.save(webm_path)
                logger.info(f"Audio file saved to: {webm_path}")
        except Exception as e:
            return (
                jsonify(
                    {
                        "error": "Failed to save uploaded file",
                        "details": str(e),
                        "fix": "Check server disk space and permissions",
                    }
                ),
                500,
            )

        # Convert audio to Whisper-compatible format
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                converted_path = temp_file.name

            final_audio_path = audio_processor.convert_to_whisper_format(
                webm_path, converted_path
            )
            logger.info(f"Audio converted to: {final_audio_path}")

        except TranscriptionError as e:
            return (
                jsonify(
                    {
                        "error": "Audio conversion failed",
                        "details": str(e),
                        "fix": "Try a different audio format or check if the file is corrupted",
                    }
                ),
                500,
            )
        except Exception as e:
            return (
                jsonify(
                    {
                        "error": "Unexpected conversion error",
                        "details": str(e),
                        "fix": "Check FFmpeg installation and audio file integrity",
                    }
                ),
                500,
            )

        # Transcribe audio
        try:
            result = transcriber.transcribe_audio(final_audio_path)

            processing_time = time.time() - start_time
            logger.info(f"Transcription completed in {processing_time:.2f} seconds")

            return jsonify(
                {
                    "text": result["text"],
                    "confidence": result["confidence"],
                    "language": result["language"],
                    "processing_time": round(processing_time, 2),
                    "attempt": result["attempt"],
                }
            )

        except TranscriptionError as e:
            return (
                jsonify(
                    {
                        "error": "Transcription failed",
                        "details": str(e),
                        "fix": "Try recording in a quieter environment or speak more clearly",
                    }
                ),
                500,
            )
        except Exception as e:
            return (
                jsonify(
                    {
                        "error": "Unexpected transcription error",
                        "details": str(e),
                        "fix": "Check Whisper API configuration and network connectivity",
                    }
                ),
                500,
            )

    except Exception as e:
        logger.error(f"Unexpected error in transcribe endpoint: {e}")
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "details": str(e),
                    "fix": "Check server logs for more details",
                }
            ),
            500,
        )

    finally:
        # Clean up temporary files
        for temp_path in [webm_path, converted_path]:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                    logger.info(f"Cleaned up temporary file: {temp_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up {temp_path}: {e}")
