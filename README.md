# Love Lingo

<img width="1920" height="5039" alt="image" src="https://github.com/user-attachments/assets/e6a41857-c6e4-4260-a354-f59d5bca5b42" />

<img width="1920" height="1080" alt="Screenshot From 2025-08-31 19-30-49" src="https://github.com/user-attachments/assets/400caefc-28c0-424f-9d6d-a1aa90a948d4" />


<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/7d89ac7d-00cb-4a34-b445-69dfbcf030d8" />


# Project Setup & Development Guide

## 🚀 Setup

```bash
pip install -r requirements.txt  
python main.py  
```

Open in browser: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🔑 Environment Variables

Create a `.env` file with your API keys:

* [ElevenLabs API Keys](https://elevenlabs.io/app/settings/api-keys)
* [Groq API Keys](https://console.groq.com/keys)

---

## 👤 Personas

To add more personas:

1. Add the persona details to `personas.json`
2. Place the corresponding image in `static/persona_images/`

---

## 🎙️ Speech & Transcription

### Whisper (Transcription)

We use [faster-whisper-server](https://github.com/etalab-ia/faster-whisper-server).

Run via Docker:

```bash
# GPU version
docker run --gpus=all -p 8000:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  fedirz/faster-whisper-server:latest-cuda

# CPU version
docker run -p 8000:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  fedirz/faster-whisper-server:latest-cpu
```

### TTS (Voice Generation)

#### Coqui TTS

[Coqui TTS](https://github.com/coqui-ai/TTS) example:

```bash
docker run --rm -it -p 5002:5002 \
  --entrypoint /bin/bash ghcr.io/coqui-ai/tts-cpu  

# Inside container:
python3 TTS/server/server.py --list_models       # List available models  
python3 TTS/server/server.py --model_name tts_models/en/vctk/vits  # Start server
```

Other TTS options:

* [kokoro-tts](https://github.com/nazdridoy/kokoro-tts)
* [Chatterbox-TTS-Server](https://github.com/devnen/Chatterbox-TTS-Server)

---

## 🔗 Useful Links

* [Whisper CPU](https://whisper_cpu.leanderziehm.com/)
* [Whisper](https://whisper.leanderziehm.com/)
* [TTS](https://tts.leanderziehm.com/)

---

## 🛠️ Development Notes

* Add a **chat icon** (similar to WhatsApp/ChatGPT).
* Enable **voice functionality** with **fullscreen persona images**.

---

## 📑 Presentation / Paper Generation

Generate slides and PDFs:

```bash
pandoc -s -o presentation.pdf presentation.md  
pandoc -t beamer -o presentation2.pdf presentation.md  
marp presentation.md --pdf  
pdflatex personal_paper.tex  
```

