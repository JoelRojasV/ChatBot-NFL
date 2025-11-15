import requests
import json

response = requests.post(
    "http://localhost:11435/api/generate",
    json={"model": "mistral", "prompt": "¿Qué es un sismo?", "stream": False}
)

print(response.json()["response"])