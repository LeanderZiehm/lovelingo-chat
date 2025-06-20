import os
import math
import subprocess
from openai import OpenAI

# --- CONFIGURATION --------------------------------------------------

API_KEY   = "my-key"
BASE_URL  = "https://whisper.leanderziehm.com/v1/"
MODEL     = "Systran/faster-whisper-tiny"
CHUNK_SEC = 30           # length of each chunk in seconds (new content per chunk)
OVERLAP   = 5            # seconds of overlap between consecutive chunks
TMP_DIR   = "/tmp/whisper_chunks"

# --- PATHS ----------------------------------------------------------

audio_dir      = "static/lecture_recordings"
transcript_dir = os.path.join(audio_dir, "transcripts")
os.makedirs(transcript_dir, exist_ok=True)
os.makedirs(TMP_DIR, exist_ok=True)

# --- INITIALIZE CLIENT ---------------------------------------------

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# --- PROCESS EACH MP3 ----------------------------------------------

for fn in os.listdir(audio_dir):
    if not fn.lower().endswith(".mp3"):
        continue

    lecture_name = os.path.splitext(fn)[0]
    mp3_path     = os.path.join(audio_dir, fn)
    out_txt_path = os.path.join(transcript_dir, lecture_name + ".txt")

    print(f"\n--- Transcribing «{fn}» → {out_txt_path}")

    # --- 1) Probe total duration with ffprobe ----------------------
    proc = subprocess.run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        mp3_path
    ], capture_output=True, text=True, check=True)
    total_dur = float(proc.stdout.strip())
    n_chunks  = math.ceil(total_dur / CHUNK_SEC)

    # --- 2) Split into WAV chunks with overlap ----------------------
    chunks = []
    for i in range(n_chunks):
        # compute start time (with overlap)
        start = max(0, i * CHUNK_SEC - OVERLAP)
        # compute length: CHUNK_SEC of new + overlaps (but trim at file end)
        length = CHUNK_SEC
        if i > 0:
            length += OVERLAP
        if i < n_chunks - 1:
            length += OVERLAP
        if start + length > total_dur:
            length = total_dur - start

        out_fn   = f"{lecture_name}_chunk{i:03d}.wav"
        out_path = os.path.join(TMP_DIR, out_fn)

        cmd = [
            "ffmpeg",
            "-ss", str(start),
            "-t",  str(length),
            "-i",  mp3_path,
            "-c:a","pcm_s16le",
            out_path
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        chunks.append(out_fn)

    # --- 3) Transcribe each chunk in order --------------------------
    full_transcript = []
    for idx, chunk_fn in enumerate(chunks, 1):
        chunk_path = os.path.join(TMP_DIR, chunk_fn)
        print(f"  • chunk {idx}/{len(chunks)} ({chunk_fn})…", end=" ")

        with open(chunk_path, "rb") as fh:
            try:
                resp = client.audio.transcriptions.create(
                    model=MODEL,
                    file=fh
                )
                text = resp.text.strip()
                print("OK")
            except Exception as e:
                text = f"[ERROR chunk {idx}: {e}]\n"
                print("FAILED")

        full_transcript.append(text)
        os.remove(chunk_path)

    # --- 4) Write out assembled transcript ---------------------------
    with open(out_txt_path, "w", encoding="utf-8") as out_f:
        out_f.write("\n\n".join(full_transcript))

    print(f"✔ Saved: {out_txt_path}")
