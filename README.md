# Love Lingo

<img width="1920" height="5039" alt="image" src="https://github.com/user-attachments/assets/e6a41857-c6e4-4260-a354-f59d5bca5b42" />

<img width="1920" height="1080" alt="Screenshot From 2025-08-31 19-30-49" src="https://github.com/user-attachments/assets/400caefc-28c0-424f-9d6d-a1aa90a948d4" />


<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/7d89ac7d-00cb-4a34-b445-69dfbcf030d8" />


# setup

pip install -r requirements.txt

python main.py

open

http://127.0.0.1:5000

# dev

create .env for groq, elevanlabs

https://elevenlabs.io/app/settings/api-keys
https://console.groq.com/keys

to add more personas add to personas.json and iamge under static/persona_images

# links

https://whisper_cpu.leanderziehm.com/
https://whisper.leanderziehm.com/
https://tts.leanderziehm.com/

# todo

add a chat icon like whatsapp call or chatgpt and have voice unctionality that shows image full screen.

# References

We used for transcriptino whisper based on this git repo:
https://github.com/etalab-ia/faster-whisper-server

```
docker run --gpus=all --publish 8000:8000 --volume ~/.cache/huggingface:/root/.cache/huggingface fedirz/faster-whisper-server:latest-cuda
# or
docker run --publish 8000:8000 --volume ~/.cache/huggingface:/root/.cache/huggingface fedirz/faster-whisper-server:latest-cpu
```

for voice generation we use https://github.com/coqui-ai/TTS?tab=readme-ov-file

```
docker run --rm -it -p 5002:5002 --entrypoint /bin/bash ghcr.io/coqui-ai/tts-cpu
python3 TTS/server/server.py --list_models #To get the list of available models
python3 TTS/server/server.py --model_name tts_models/en/vctk/vits # To start a server
```

# Love Lingo

![image](https://github.com/user-attachments/assets/e21d944d-9c7b-4915-a5d9-e7cd9fb65649)
![image](https://github.com/user-attachments/assets/b8db8097-e479-49bc-84dd-fa4da335440e)

# setup

pip install -r requirements.txt

python main.py

open

http://127.0.0.1:5000

# dev

to add more personas add to personas.json and iamge under static/persona_images

# links

https://whisper_cpu.leanderziehm.com/
https://whisper.leanderziehm.com/
https://tts.leanderziehm.com/

# todo

add a chat icon like whatsapp call or chatgpt and have voice unctionality that shows image full screen.

# References

We used for transcriptino whisper based on this git repo:
https://github.com/etalab-ia/faster-whisper-server

```
docker run --gpus=all --publish 8000:8000 --volume ~/.cache/huggingface:/root/.cache/huggingface fedirz/faster-whisper-server:latest-cuda
# or
docker run --publish 8000:8000 --volume ~/.cache/huggingface:/root/.cache/huggingface fedirz/faster-whisper-server:latest-cpu
```

for voice generation we use https://github.com/coqui-ai/TTS?tab=readme-ov-file

```
docker run --rm -it -p 5002:5002 --entrypoint /bin/bash ghcr.io/coqui-ai/tts-cpu
python3 TTS/server/server.py --list_models #To get the list of available models
python3 TTS/server/server.py --model_name tts_models/en/vctk/vits # To start a server
```

https://github.com/nazdridoy/kokoro-tts

https://github.com/devnen/Chatterbox-TTS-Server






# Presentation PDF generation

pandoc -s -o presentation.pdf presentation.md
pandoc -t beamer -o presentation2.pdf presentation.md
marp presentation.md --pdf



pdflatex personal_paper.tex
