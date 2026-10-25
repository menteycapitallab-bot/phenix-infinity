import asyncio
from config import config
from google import genai
from google.genai import types

def test_genai_audio():
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    
    # Probar con un buffer de audio corto
    dummy_bytes = b"OggS\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00" + b"\x00" * 100
    
    try:
        res = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[
                types.Part.from_bytes(
                    data=dummy_bytes,
                    mime_type="audio/ogg"
                ),
                "Escucha este audio y responde brevemente en español."
            ]
        )
        print("AUDIO SUCCESS RESPONSE:", res.text)
    except Exception as e:
        print("AUDIO EXCEPTION:", type(e), e)

if __name__ == "__main__":
    test_genai_audio()
