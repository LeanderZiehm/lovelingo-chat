import os
import math
import subprocess
import time
from functools import wraps
from dataclasses import dataclass
from typing import List, Tuple
from openai import OpenAI

# --- CONFIGURATION --------------------------------------------------

@dataclass
class Config:
    API_KEY: str = "my-key"
    BASE_URL: str = "https://whisper.leanderziehm.com/v1/"
    MODEL: str = "Systran/faster-whisper-tiny"
    CHUNK_SEC: int = 30
    OVERLAP: int = 5
    TMP_DIR: str = "/tmp/whisper_chunks"
    AUDIO_DIR: str = "static/lecture_recordings"

# --- TIMING DECORATOR -----------------------------------------------

def timer(func):
    """Decorator to time function execution with detailed info"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        print(f"🚀 Starting {func.__name__}...")
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"✅ {func.__name__} completed in {end_time - start_time:.2f} seconds")
        return result
    return wrapper

# --- CORE FUNCTIONS -------------------------------------------------

@timer
def get_audio_duration(mp3_path: str) -> float:
    """Get the duration of an audio file using ffprobe"""
    proc = subprocess.run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        mp3_path
    ], capture_output=True, text=True, check=True)
    return float(proc.stdout.strip())

def calculate_chunk_params(total_duration: float, chunk_sec: int, overlap: int) -> List[Tuple[float, float, int]]:
    """Calculate start time, length, and chunk index for each audio chunk"""
    n_chunks = math.ceil(total_duration / chunk_sec)
    chunks = []
    
    for i in range(n_chunks):
        # Compute start time (with overlap)
        start = max(0, i * chunk_sec - overlap)
        
        # Compute length: CHUNK_SEC of new + overlaps (but trim at file end)
        length = chunk_sec
        if i > 0:
            length += overlap
        if i < n_chunks - 1:
            length += overlap
        if start + length > total_duration:
            length = total_duration - start
        
        chunks.append((start, length, i))
    
    return chunks

@timer
def create_audio_chunk(mp3_path: str, start: float, length: float, chunk_idx: int, 
                      lecture_name: str, tmp_dir: str) -> str:
    """Create a single audio chunk from the original file"""
    out_fn = f"{lecture_name}_chunk{chunk_idx:03d}.wav"
    out_path = os.path.join(tmp_dir, out_fn)
    
    cmd = [
        "ffmpeg",
        "-ss", str(start),
        "-t", str(length),
        "-i", mp3_path,
        "-c:a", "pcm_s16le",
        out_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out_fn

@timer
def create_all_chunks(mp3_path: str, chunk_params: List[Tuple[float, float, int]], 
                     lecture_name: str, tmp_dir: str) -> List[str]:
    """Create all audio chunks sequentially"""
    chunks = []
    for start, length, idx in chunk_params:
        chunk_fn = create_audio_chunk(mp3_path, start, length, idx, lecture_name, tmp_dir)
        chunks.append(chunk_fn)
    return chunks

def transcribe_chunk(chunk_path: str, chunk_idx: int, total_chunks: int, 
                    client: OpenAI, model: str) -> str:
    """Transcribe a single audio chunk"""
    chunk_fn = os.path.basename(chunk_path)
    print(f"  • chunk {chunk_idx + 1}/{total_chunks} ({chunk_fn})…", end=" ")
    
    try:
        with open(chunk_path, "rb") as fh:
            resp = client.audio.transcriptions.create(
                model=model,
                file=fh
            )
            text = resp.text.strip()
            print("OK")
            return text
    except Exception as e:
        text = f"[ERROR chunk {chunk_idx + 1}: {e}]\n"
        print("FAILED")
        return text
    finally:
        # Clean up chunk file
        if os.path.exists(chunk_path):
            os.remove(chunk_path)

@timer
def transcribe_chunks_sequential(chunk_files: List[str], tmp_dir: str, client: OpenAI, model: str) -> List[str]:
    """Transcribe all chunks sequentially"""
    transcripts = []
    for idx, chunk_fn in enumerate(chunk_files):
        chunk_path = os.path.join(tmp_dir, chunk_fn)
        text = transcribe_chunk(chunk_path, idx, len(chunk_files), client, model)
        transcripts.append(text)
    return transcripts

@timer
def save_transcript(transcript_parts: List[str], output_path: str) -> None:
    """Save the assembled transcript to file"""
    with open(output_path, "w", encoding="utf-8") as out_f:
        out_f.write("\n\n".join(transcript_parts))

@timer
def process_single_file(mp3_path: str, lecture_name: str, config: Config, client: OpenAI) -> None:
    """Process a single MP3 file from start to finish"""
    transcript_dir = os.path.join(config.AUDIO_DIR, "transcripts")
    out_txt_path = os.path.join(transcript_dir, lecture_name + ".txt")
    
    print(f"\n--- Transcribing «{os.path.basename(mp3_path)}» → {out_txt_path}")
    
    # Get audio duration
    total_duration = get_audio_duration(mp3_path)
    
    # Calculate chunk parameters
    chunk_params = calculate_chunk_params(total_duration, config.CHUNK_SEC, config.OVERLAP)
    
    # Create audio chunks
    chunk_files = create_all_chunks(mp3_path, chunk_params, lecture_name, config.TMP_DIR)
    
    # Transcribe chunks sequentially
    transcripts = transcribe_chunks_sequential(chunk_files, config.TMP_DIR, client, config.MODEL)
    
    # Save transcript
    save_transcript(transcripts, out_txt_path)
    print(f"✔ Saved: {out_txt_path}")

def setup_directories(config: Config) -> str:
    """Setup required directories and return transcript directory path"""
    transcript_dir = os.path.join(config.AUDIO_DIR, "transcripts")
    os.makedirs(transcript_dir, exist_ok=True)
    os.makedirs(config.TMP_DIR, exist_ok=True)
    return transcript_dir

def get_mp3_files(audio_dir: str) -> List[Tuple[str, str]]:
    """Get list of MP3 files and their corresponding lecture names"""
    mp3_files = []
    for fn in os.listdir(audio_dir):
        if fn.lower().endswith(".mp3"):
            lecture_name = os.path.splitext(fn)[0]
            mp3_path = os.path.join(audio_dir, fn)
            mp3_files.append((mp3_path, lecture_name))
    return mp3_files

# --- MAIN EXECUTION -------------------------------------------------

@timer
def main():
    """Main execution function"""
    config = Config()
    
    # Setup directories
    setup_directories(config)
    
    # Initialize OpenAI client
    client = OpenAI(api_key=config.API_KEY, base_url=config.BASE_URL)
    
    # Get all MP3 files
    mp3_files = get_mp3_files(config.AUDIO_DIR)
    
    if not mp3_files:
        print("No MP3 files found in the audio directory.")
        return
    
    print(f"Found {len(mp3_files)} MP3 file(s) to process")
    
    # Process each file
    for mp3_path, lecture_name in mp3_files:
        try:
            process_single_file(mp3_path, lecture_name, config, client)
        except Exception as e:
            print(f"❌ Failed to process {lecture_name}: {e}")
            continue
    
    print("\n🎉 All files processed!")

if __name__ == "__main__":
    main()
