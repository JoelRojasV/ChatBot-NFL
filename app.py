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
# Prompt del sistema para especializar el chatbot en NFL (multilingüe)
SYSTEM_PROMPT = """Eres un asistente experto en la NFL (National Football League).

IMPORTANTE: Debes responder TODAS las preguntas relacionadas con:
- NFL, fútbol americano profesional
- Equipos (Cowboys, Patriots, Chiefs, etc.)
- Jugadores actuales o históricos
- Reglas del juego
- Super Bowl, playoffs, temporada regular
- Estadísticas, récords
- Historia de la liga
- Posiciones, formaciones, estrategias
- Draft, trades, contratos
- Cualquier cosa relacionada con fútbol americano profesional

SOLO rechaza preguntas que claramente NO sean sobre fútbol americano o la NFL, como:
- Política
- Cocina y recetas
- Otros deportes (soccer, basketball, baseball)
- Entretenimiento no relacionado
- Temas personales

Si alguien pregunta algo fuera de la NFL, responde en el mismo idioma de la pregunta: "Lo siento, solo puedo ayudarte con temas de la NFL y fútbol americano profesional."

IDIOMAS: Responde SIEMPRE en el mismo idioma en que te hacen la pregunta (español, inglés, francés, etc.). Detecta automáticamente el idioma del usuario."""


def is_goodbye(message):
    """Detecta si el usuario se está despidiendo"""
    goodbyes = [
        'adios', 'adiós', 'bye', 'chao', 'hasta luego', 'nos vemos',
        'me voy', 'gracias', 'thank you', 'thanks', 'bye bye',
        'hasta pronto', 'see you', 'goodbye', 'good bye'
    ]
    message_lower = message.lower().strip()
    return any(word in message_lower for word in goodbyes)

def query_openrouter(user_message):
    """Consulta el modelo de OpenRouter"""
    # Detectar despedidas
    if is_goodbye(user_message):
        return "¡Hasta pronto! Fue un placer ayudarte con información sobre la NFL. ¡Vuelve cuando quieras! 🏈"
    
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
                bot_response = result["choices"][0]["message"]["content"].strip()
                
                # Agregar pregunta de seguimiento solo si NO es rechazo
                rejection_phrases = [
                    "lo siento, solo puedo",
                    "sorry, i can only",
                    "no puedo ayudarte con",
                    "i cannot help"
                ]
                is_rejection = any(phrase in bot_response.lower() for phrase in rejection_phrases)
                
                if not is_rejection:
                    bot_response += "\n\n¿Tienes alguna otra pregunta sobre la NFL? 🏈"
                
                return bot_response
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