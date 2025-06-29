import requests
# models = ['gemma3','gemma3:12b','gemma3:27b','llama3.1:8b','mistral:7b']
class Models:
    GEMMA3 = 'gemma3'
    GEMMA3_12B = 'gemma3:12b'
    GEMMA3_27B = 'gemma3:27b'
    LLAMA3_8B = 'llama3.1:8b'
    MISTRAL_7B = 'mistral:7b'



def generate_text(prompt,model = Models.MISTRAL_7B):
    OLLAMA_BASE_URL = 'https://ollama.leanderziehm.com'
    url = OLLAMA_BASE_URL + '/api/generate'
    headers = {
        'Content-Type': 'application/json'
    }
    payload = {
        'model': model,
        'prompt': prompt,
        'stream': False
    }
    response = requests.post(url, json=payload, headers=headers)
    if not response.ok:
        print(f"Failed to generate text: {response.status_code} {response.reason}")
        return {"error": response.reason, "status_code": response.status_code}
    result = response.json()
    return result
    # print('Response:', result.get('response'))


prompt = 'Why is 1+1?'
response = generate_text(prompt)
responseText = response['response']

json_prompt = f'RAW_TEXT: {responseText}\n From this text extract the answer to the question "{prompt}" and return it as a json object with key "answer". JSON:'
response_json = generate_text(json_prompt)
responseText_json = response_json['response']
print(responseText_json)
