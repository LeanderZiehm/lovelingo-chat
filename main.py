
import json
from flask import Flask, render_template, request, url_for, redirect

app = Flask(__name__)

# Load personas from JSON file
def load_personas():
    with open('personas.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# Route: Home - list personas
@app.route('/')
def index():
    personas = load_personas()
    return render_template('index.html', personas=personas)

# Route: Chat with selected persona\
@app.route('/chat/<persona_name>', methods=['GET', 'POST'])
def chat(persona_name):
    personas = load_personas()
    persona = next((p for p in personas if p['name'] == persona_name), None)
    if not persona:
        return redirect(url_for('index'))

    if request.method == 'POST':
        user_message = request.form.get('message')
        # Placeholder for chat handling
        response = generate_response(persona, user_message)
        return render_template('chat.html', persona=persona, user_message=user_message, response=response)

    return render_template('chat.html', persona=persona)

# Placeholder function for chatbot integration
def generate_response(persona, message):
    # TODO: implement chat logic with AI model
    pass

if __name__ == '__main__':
    app.run(debug=True, port=5010)


