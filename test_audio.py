import asyncio
import base64
import httpx
from config import config

async def test_audio():
    api_key = config.GEMINI_API_KEY
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}"
    
    # Crear un dummy de datos base64 para probar la sintaxis del esquema
    dummy_audio = base64.b64encode(b"RIFF....WAVEfmt ....data....").decode('utf-8')
    
    payload = {
        "contents": [{
            "parts": [
                {
                    "inlineData": {
                        "mimeType": "audio/ogg",
                        "data": dummy_audio
                    }
                },
                {
                    "text": "Prueba de audio: ¿Puedes responder 'Audio recibido OK'?"
                }
            ]
        }]
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.post(url, json=payload)
        print("Status code:", res.status_code)
        print("Response:", res.text)

if __name__ == "__main__":
    asyncio.run(test_audio())
