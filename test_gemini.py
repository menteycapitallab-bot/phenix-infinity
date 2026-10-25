import asyncio
import httpx
from config import config

async def test_gemini():
    api_key = config.GEMINI_API_KEY
    print(f"Testing API Key prefix: {api_key[:10]}... Length: {len(api_key)}")
    
    # Probar endpoint v1beta con gemini-1.5-flash y gemini-2.0-flash
    urls = [
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}",
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}"
    ]

    
    payload = {
        "contents": [{"parts": [{"text": "Hola, responde brevemente en español."}]}]
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        for url in urls:
            try:
                res = await client.post(url, json=payload)
                print(f"URL: {url.split('?')[0]} | Status: {res.status_code}")
                if res.status_code == 200:
                    data = res.json()
                    print("SUCCESS RESPONSE:", data["candidates"][0]["content"]["parts"][0]["text"])
                    return
                else:
                    print("ERROR BODY:", res.text)
            except Exception as e:
                print("EXCEPTION:", e)

if __name__ == "__main__":
    asyncio.run(test_gemini())
