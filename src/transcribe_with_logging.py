import logging
import traceback
from flask import Blueprint, request, jsonify
from openai import OpenAI
from tempfile import NamedTemporaryFile
import subprocess
import os
import time

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('transcribe.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

transcribe_bp = Blueprint('transcribe', __name__)

# Whisper API configuration
custom_whisper_api_key = "whisper.leanderziehm.com"
custom_whisper_url = "https://whisper.leanderziehm.com/v1/"
model = "Systran/faster-whisper-tiny"

client = OpenAI(api_key=custom_whisper_api_key, base_url=custom_whisper_url)

@transcribe_bp.route('/transcribe', methods=['POST'])
def transcribe():
    request_id = f"req_{int(time.time())}"
    logger.info(f"[{request_id}] Starting transcription request")
    
    webm_path = None
    mp3_path = None
    
    try:
        # Check if audio file is present
        if 'audio' not in request.files:
            logger.error(f"[{request_id}] No audio file in request")
            return jsonify({"error": "No audio file uploaded"}), 400

        webm_file = request.files['audio']
        logger.info(f"[{request_id}] Audio file received: {webm_file.filename}, size: {webm_file.content_length if hasattr(webm_file, 'content_length') else 'unknown'}")

        # Create temporary WebM file
        try:
            with NamedTemporaryFile(suffix=".webm", delete=False) as source_temp:
                webm_path = source_temp.name
                logger.debug(f"[{request_id}] Created temp WebM file: {webm_path}")
                webm_file.save(webm_path)
                logger.info(f"[{request_id}] Saved WebM file, size: {os.path.getsize(webm_path)} bytes")
        except Exception as e:
            logger.error(f"[{request_id}] Failed to create/save WebM temp file: {str(e)}")
            logger.error(f"[{request_id}] Traceback: {traceback.format_exc()}")
            return jsonify({"error": f"Failed to save uploaded file: {str(e)}"}), 500

        # Create temporary MP3 file
        try:
            with NamedTemporaryFile(suffix=".mp3", delete=False) as target_temp:
                mp3_path = target_temp.name
                logger.debug(f"[{request_id}] Created temp MP3 file: {mp3_path}")
        except Exception as e:
            logger.error(f"[{request_id}] Failed to create MP3 temp file: {str(e)}")
            return jsonify({"error": f"Failed to create temporary file: {str(e)}"}), 500

        # FFmpeg conversion
        logger.info(f"[{request_id}] Starting FFmpeg conversion")
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", webm_path,
            "-vn",
            "-ar", "16000",
            "-ac", "1",
            "-f", "mp3",
            mp3_path
        ]
        
        logger.debug(f"[{request_id}] FFmpeg command: {' '.join(ffmpeg_cmd)}")
        
        try:
            start_time = time.time()
            ffmpeg_result = subprocess.run(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30  # 30 second timeout
            )
            conversion_time = time.time() - start_time
            
            logger.info(f"[{request_id}] FFmpeg completed in {conversion_time:.2f}s, return code: {ffmpeg_result.returncode}")
            
            if ffmpeg_result.stdout:
                logger.debug(f"[{request_id}] FFmpeg stdout: {ffmpeg_result.stdout.decode()}")
            if ffmpeg_result.stderr:
                logger.debug(f"[{request_id}] FFmpeg stderr: {ffmpeg_result.stderr.decode()}")

            if ffmpeg_result.returncode != 0:
                error_output = ffmpeg_result.stderr.decode()
                logger.error(f"[{request_id}] FFmpeg conversion failed with code {ffmpeg_result.returncode}")
                logger.error(f"[{request_id}] FFmpeg error output: {error_output}")
                return jsonify({
                    "error": "FFmpeg conversion failed",
                    "return_code": ffmpeg_result.returncode,
                    "ffmpeg_stderr": error_output,
                    "ffmpeg_stdout": ffmpeg_result.stdout.decode() if ffmpeg_result.stdout else ""
                }), 500

        except subprocess.TimeoutExpired:
            logger.error(f"[{request_id}] FFmpeg conversion timed out")
            return jsonify({"error": "FFmpeg conversion timed out"}), 500
        except Exception as e:
            logger.error(f"[{request_id}] FFmpeg subprocess error: {str(e)}")
            logger.error(f"[{request_id}] Traceback: {traceback.format_exc()}")
            return jsonify({"error": f"FFmpeg execution failed: {str(e)}"}), 500

        # Check if MP3 file was created successfully
        if not os.path.exists(mp3_path):
            logger.error(f"[{request_id}] MP3 file was not created: {mp3_path}")
            return jsonify({"error": "MP3 file was not created by FFmpeg"}), 500
        
        mp3_size = os.path.getsize(mp3_path)
        logger.info(f"[{request_id}] MP3 file created successfully, size: {mp3_size} bytes")
        
        if mp3_size == 0:
            logger.error(f"[{request_id}] MP3 file is empty")
            return jsonify({"error": "Generated MP3 file is empty"}), 500

        # Transcription with OpenAI/Whisper API
        logger.info(f"[{request_id}] Starting transcription with Whisper API")
        try:
            with open(mp3_path, "rb") as f:
                logger.debug(f"[{request_id}] Opened MP3 file for reading")
                
                start_time = time.time()
                response = client.audio.transcriptions.create(
                    model=model,
                    file=f
                )
                transcription_time = time.time() - start_time
                
                logger.info(f"[{request_id}] Transcription completed in {transcription_time:.2f}s")
                logger.debug(f"[{request_id}] Transcription response type: {type(response)}")
                
                if hasattr(response, 'text'):
                    transcribed_text = response.text.strip()
                    logger.info(f"[{request_id}] Transcription successful, text length: {len(transcribed_text)}")
                    logger.debug(f"[{request_id}] Transcribed text preview: {transcribed_text[:100]}...")
                    
                    return jsonify({
                        "text": transcribed_text,
                        "processing_time": {
                            "conversion": conversion_time,
                            "transcription": transcription_time,
                            "total": conversion_time + transcription_time
                        }
                    })
                else:
                    logger.error(f"[{request_id}] Unexpected response format from Whisper API: {response}")
                    return jsonify({"error": "Unexpected response format from transcription service"}), 500
                    
        except Exception as e:
            logger.error(f"[{request_id}] Transcription API error: {str(e)}")
            logger.error(f"[{request_id}] Traceback: {traceback.format_exc()}")
            
            # Check if it's a network/API issue
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                return jsonify({"error": f"Connection error to transcription service: {str(e)}"}), 503
            elif "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
                return jsonify({"error": f"Authentication error with transcription service: {str(e)}"}), 401
            else:
                return jsonify({"error": f"Transcription service error: {str(e)}"}), 500

    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error in transcribe function: {str(e)}")
        logger.error(f"[{request_id}] Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

    finally:
        # Cleanup temporary files
        cleanup_errors = []
        
        if webm_path:
            try:
                if os.path.exists(webm_path):
                    os.remove(webm_path)
                    logger.debug(f"[{request_id}] Cleaned up WebM file: {webm_path}")
                else:
                    logger.warning(f"[{request_id}] WebM file not found for cleanup: {webm_path}")
            except Exception as e:
                cleanup_errors.append(f"WebM cleanup failed: {str(e)}")
                logger.error(f"[{request_id}] Failed to cleanup WebM file {webm_path}: {str(e)}")
        
        if mp3_path:
            try:
                if os.path.exists(mp3_path):
                    os.remove(mp3_path)
                    logger.debug(f"[{request_id}] Cleaned up MP3 file: {mp3_path}")
                else:
                    logger.warning(f"[{request_id}] MP3 file not found for cleanup: {mp3_path}")
            except Exception as e:
                cleanup_errors.append(f"MP3 cleanup failed: {str(e)}")
                logger.error(f"[{request_id}] Failed to cleanup MP3 file {mp3_path}: {str(e)}")
        
        if cleanup_errors:
            logger.warning(f"[{request_id}] Cleanup errors: {'; '.join(cleanup_errors)}")
        
        logger.info(f"[{request_id}] Request completed")

# Health check endpoint for debugging
@transcribe_bp.route('/health', methods=['GET'])
def health_check():
    try:
        # Test FFmpeg availability
        ffmpeg_result = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        ffmpeg_available = ffmpeg_result.returncode == 0
        
        # Test API connectivity (without actually making a request)
        api_config = {
            "base_url": custom_whisper_url,
            "model": model
        }
        
        return jsonify({
            "status": "healthy",
            "ffmpeg_available": ffmpeg_available,
            "api_config": api_config,
            "temp_dir": os.path.dirname(NamedTemporaryFile().name)
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500