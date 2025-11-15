from flask import Flask, render_template, request, jsonify
import requests
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# Configuración de OpenRouter
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Modelo gratuito de OpenRouter
MODEL = "mistralai/mistral-nemo:free"

# Prompt del sistema para especializar el chatbot en NFL
SYSTEM_PROMPT = """Eres un asistente que SOLO responde preguntas sobre la NFL (National Football League).

Si te preguntan sobre la NFL: responde con información clara sobre equipos, jugadores, reglas, Super Bowl, estadísticas, historia, etc.

Si te preguntan sobre OTRO TEMA (política, cocina, otros deportes, películas, etc.): responde exactamente: "Lo siento, solo puedo responder preguntas sobre la NFL. Pregúntame sobre fútbol americano profesional."

Responde siempre en español de forma clara y concisa."""

def query_openrouter(user_message):
    """Consulta el modelo de OpenRouter"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5000",
        "X-Title": "Chatbot NFL"
    }
    
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"].strip()
            return "No se pudo generar respuesta"
        
        elif response.status_code == 401:
            return "Error: API Key inválida. Verifica tu configuración."
        
        elif response.status_code == 429:
            return "Límite de requests alcanzado. Espera un momento e intenta de nuevo."
        
        else:
            return f"Error al comunicarse con el modelo (código {response.status_code})"
    
    except requests.exceptions.Timeout:
        return "La solicitud tardó demasiado. Por favor intenta de nuevo."
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Mensaje vacío'}), 400
        
        # Llamar a OpenRouter
        bot_response = query_openrouter(user_message)
        
        return jsonify({'response': bot_response})
    
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

if __name__ == '__main__':
    if not OPENROUTER_API_KEY:
        print("⚠️  ERROR: No se encontró OPENROUTER_API_KEY en el archivo .env")
        print("⚠️  Crea un archivo .env con tu API key de OpenRouter")
    else:
        print("✓ Chatbot de NFL iniciado en http://localhost:5000")
        print("✓ Usando OpenRouter API con modelo gratuito")
        print(f"✓ Modelo: {MODEL}")
        app.run(debug=True, port=5000)