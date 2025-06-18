import requests

# Replace with your TTS server address
url = "https://coqui.leanderziehm.com/api/tts"

# The text you want to convert to speech
text = "Hello, how are you today?"


data = {
    "text": text,
    "speaker-id": "p376",  # Example speaker ID
    "language-id": "en"    # Example language code
}
response = requests.post(url, data=data)

print("Response status code:", response.status_code)
# print("Response headers:", response.headers)
print("Response content type:", response.content)

# Save the audio to a file
with open("output.wav", "wb") as f:
    f.write(response.content)

print("Audio saved to output.wav")


# # Send POST request
# response = requests.post(url, json={"text": text})

# # Check for successful response
# if response.status_code == 200:
#     # Save the resulting audio
#     with open("coqui.wav", "wb") as f:
#         f.write(response.content)
#     print("Audio saved as output.wav")
# else:
#     print("Failed to get audio:", response.status_code, response.text)


# # curl -X POST https://coqui.leanderziehm.com//api/tts -H "Content-Type: application/json" -d '{"text":"Hello world"}' --output output.wav
