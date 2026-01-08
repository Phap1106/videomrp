from .core.config import settings
import httpx

async def translate(text: str, target_lang: str, source_lang: str = "auto") -> str:
    if not text.strip():
        return text

    if settings.translate_provider.lower() == "libretranslate":
        payload = {"q": text, "source": source_lang, "target": target_lang, "format": "text"}
        if settings.libretranslate_api_key:
            payload["api_key"] = settings.libretranslate_api_key

        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(settings.libretranslate_url, data=payload)
            r.raise_for_status()
            data = r.json()
            return data.get("translatedText", text)

    # fallback: no-op
    return text
