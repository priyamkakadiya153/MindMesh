import asyncio
import httpx
import os

from app.core.config import settings
from app.ai.llm.gemini import GeminiProvider, HARDCODED_DEV_GEMINI_KEY

async def test_direct_gemini_call():
    key = getattr(settings, "GEMINI_API_KEY", None) or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or HARDCODED_DEV_GEMINI_KEY
    print(f"[AI DIAGNOSTIC] API key present: {bool(key)}")
    print(f"[AI DIAGNOSTIC] API key length: {len(key) if key else 0}")
    print(f"[AI DIAGNOSTIC] API key snippet: {key[:6]}...{key[-4:]}" if key else "None")

    models_to_test = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp", "gemini-2.0-flash"]

    async with httpx.AsyncClient(timeout=15.0) as client:
        for model in models_to_test:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": "Say hello in one short sentence."}]
                    }
                ]
            }
            print(f"\n[AI DIAGNOSTIC] Testing POST to {url}...")
            try:
                res = await client.post(url, json=payload)
                print(f"[AI DIAGNOSTIC] Model: '{model}' -> Status: {res.status_code}")
                if res.status_code == 200:
                    print(f"[AI DIAGNOSTIC] SUCCESS! Response text: {res.json()['candidates'][0]['content']['parts'][0]['text']}")
                    break
                else:
                    print(f"[AI DIAGNOSTIC] Error response: {res.text}")
            except Exception as e:
                print(f"[AI DIAGNOSTIC] Exception for model '{model}': {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_direct_gemini_call())
