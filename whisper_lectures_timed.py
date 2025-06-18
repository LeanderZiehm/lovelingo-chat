import os
import math
import subprocess
import time
from openai import OpenAI

# --- CONFIGURATION --------------------------------------------------
API_KEY   = os.getenv("OPENAI_API_KEY", "my-key")
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
    timings = {}

    # 1) Probe total duration
    t0 = time.perf_counter()
    proc = subprocess.run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        mp3_path
    ], capture_output=True, text=True, check=True)
    total_dur = float(proc.stdout.strip())
    timings['probe_duration'] = time.perf_counter() - t0

    n_chunks = math.ceil(total_dur / CHUNK_SEC)
    print(f"Total duration: {total_dur:.1f}s, splitting into {n_chunks} chunks")

    # 2) Split into WAV chunks with overlap
    chunks = []
    split_timings = []
    for i in range(n_chunks):
        split_t0 = time.perf_counter()
        start = max(0, i * CHUNK_SEC - OVERLAP)
        length = CHUNK_SEC + (OVERLAP if i > 0 else 0) + (OVERLAP if i < n_chunks - 1 else 0)
        if start + length > total_dur:
            length = total_dur - start

        out_fn   = f"{lecture_name}_chunk{i:03d}.wav"
        out_path = os.path.join(TMP_DIR, out_fn)

        subprocess.run([
            "ffmpeg", "-ss", str(start), "-t", str(length),
            "-i", mp3_path,
            "-c:a", "pcm_s16le",
            out_path
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        split_time = time.perf_counter() - split_t0
        split_timings.append(split_time)
        chunks.append(out_fn)
        print(f"  • Chunk {i+1}/{n_chunks} split in {split_time:.2f}s")
    timings['split_durations'] = split_timings

    # 3) Transcribe each chunk
    full_transcript = []
    transcribe_timings = []
    for idx, chunk_fn in enumerate(chunks, 1):
        chunk_path = os.path.join(TMP_DIR, chunk_fn)
        print(f"  • chunk {idx}/{len(chunks)} ({chunk_fn})…", end=" ")

        t0 = time.perf_counter()
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
        duration = time.perf_counter() - t0
        transcribe_timings.append(duration)
        full_transcript.append(text)

        os.remove(chunk_path)
    timings['transcribe_durations'] = transcribe_timings

    # 4) Write out assembled transcript
    t0 = time.perf_counter()
    with open(out_txt_path, "w", encoding="utf-8") as out_f:
        out_f.write("\n\n".join(full_transcript))
    timings['write_duration'] = time.perf_counter() - t0

    # 5) Print summary timings
    print("\nTiming summary:")
    print(f"  - Probe: {timings['probe_duration']:.2f}s")
    print(f"  - Splitting total: {sum(timings['split_durations']):.2f}s (avg {sum(timings['split_durations'])/len(timings['split_durations']):.2f}s each)")
    print(f"  - Transcription total: {sum(timings['transcribe_durations']):.2f}s (avg {sum(timings['transcribe_durations'])/len(timings['transcribe_durations']):.2f}s each)")
    print(f"  - Writing file: {timings['write_duration']:.2f}s")

    print(f"✔ Saved: {out_txt_path}")
