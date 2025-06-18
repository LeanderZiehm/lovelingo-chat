import os
import subprocess
from openai import OpenAI

# --- CONFIGURATION --------------------------------------------------

API_KEY   = "my-key"
BASE_URL  = "https://whisper.leanderziehm.com/v1/"
MODEL     = "Systran/faster-whisper-tiny"
CHUNK_SEC = 30           # length of each chunk in seconds
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

    # --- 1) Use ffmpeg to split into WAV chunks ----------------------
    # e.g. /tmp/whisper_chunks/chunk000.wav, chunk001.wav, ...
    cmd = [
        "ffmpeg",
        "-i", mp3_path,
        "-f", "segment",
        "-segment_time", str(CHUNK_SEC),
        "-c:a", "pcm_s16le",
        os.path.join(TMP_DIR, lecture_name + "_chunk%03d.wav")
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # --- 2) Transcribe each chunk in order --------------------------
    full_transcript = []
    # find all chunk files, sorted by index
    chunks = sorted([
        f for f in os.listdir(TMP_DIR)
        if f.startswith(lecture_name + "_chunk") and f.endswith(".wav")
    ])

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

    # --- 3) Write out assembled transcript ---------------------------
    with open(out_txt_path, "w", encoding="utf-8") as out_f:
        out_f.write("\n\n".join(full_transcript))

    print(f"✔ Saved: {out_txt_path}")
