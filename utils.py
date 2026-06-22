import os
import re
import httpx
import logging
import urllib.parse
from groq import Groq
from dotenv import load_dotenv
import asyncio

load_dotenv()

logger = logging.getLogger("utils")

_token_cache = None

def is_chinese_word(text: str) -> bool:
    return bool(re.search(r'[\u4e00-\u9fff]', text))

async def get_token() -> str:
    global _token_cache
    if _token_cache is None:
        logger.info("Токен отсутствует в кэше, вызываем авторизацию ankiweb_login...")
        _token_cache = await ankiweb_login()
    else:
        logger.info("Используем существующий токен AnkiWeb из кэша.")
    return _token_cache

try:
    with open("system_prompt.txt", "r", encoding="utf-8") as file:
        SYSTEM_PROMPT = file.read()
    logger.info("system_prompt.txt успешно прочитан.")
except Exception as e:
    logger.error(f"Не удалось прочитать system_prompt.txt: {e}")
    SYSTEM_PROMPT = "You are a helpful assistant."

async def get_sound(word: str) -> str:
    lang = "zh-CN" if is_chinese_word(word) else "en"
    encoded_word = urllib.parse.quote(word.lower().strip())
    return f"https://translate.google.com/translate_tts?ie=UTF-8&tl={lang}&client=tw-ob&q={encoded_word}"

def parse_card(card_text: str) -> dict:
    logger.info("Парсинг сгенерированного текста карточки...")
    lines = card_text.strip().splitlines()
    result = {
        "front": "", "synonyms": "", "sentence": "", "translation": "",
        "explanation": "", "image_prompt": "",
        # Chinese-specific fields
        "pinyin": "", "sentence_translation": "", "related_words": "",
        "is_chinese": False
    }
    for line in lines:
        if line.startswith("FRONT:"):
            result["front"] = line.replace("FRONT:", "").strip()
        elif line.startswith("Synonyms:"):
            result["synonyms"] = line.replace("Synonyms:", "").strip()
        elif line.startswith("Sentence:"):
            result["sentence"] = line.replace("Sentence:", "").strip()
        elif line.startswith("Translation:"):
            result["translation"] = line.replace("Translation:", "").strip()
        elif line.startswith("Explanation:"):
            result["explanation"] = line.replace("Explanation:", "").strip()
        elif line.startswith("IMAGE_PROMPT:"):
            result["image_prompt"] = line.replace("IMAGE_PROMPT:", "").strip()
        # Chinese fields
        elif line.startswith("Pinyin:"):
            result["pinyin"] = line.replace("Pinyin:", "").strip()
            result["is_chinese"] = True
        elif line.startswith("SentenceTranslation:"):
            result["sentence_translation"] = line.replace("SentenceTranslation:", "").strip()
        elif line.startswith("RelatedWords:"):
            result["related_words"] = line.replace("RelatedWords:", "").strip()
    return result

async def get_image_url(prompt: str, fallback_word: str) -> str:
    api_key = os.getenv("PIXABAY_API_KEY")
    if not api_key:
        logger.error("Критическая ошибка: PIXABAY_API_KEY не задан в .env")
        return "https://upload.wikimedia.org/wikipedia/commons/ca/ca/1x1_placeholder.png"

    search_query = prompt if prompt else fallback_word
    encoded_query = urllib.parse.quote(search_query.lower().strip())
    url = f"https://pixabay.com/api/?key={api_key}&q={encoded_query}&image_type=photo&per_page=3&safesearch=true"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get("hits") and len(data["hits"]) > 0:
                    return data["hits"][0]["webformatURL"]
    except Exception as e:
        logger.error(f"[IMAGE SEARCH] Ошибка при запросе к Pixabay: {e}")
        
    return "https://upload.wikimedia.org/wikipedia/commons/ca/ca/1x1_placeholder.png"

def encode_varint_unsigned(value: int) -> bytes:
    result = b""
    while value > 0x7F:
        result += bytes([(value & 0x7F) | 0x80])
        value >>= 7
    result += bytes([value & 0x7F])
    return result

def encode_field(field_num: int, value: bytes) -> bytes:
    tag = (field_num << 3) | 2
    return encode_varint_unsigned(tag) + encode_varint_unsigned(len(value)) + value

def encode_string_field(field_num: int, value: str) -> bytes:
    return encode_field(field_num, value.encode("utf-8"))

async def ankiweb_login() -> str:
    email = os.getenv("ANKIWEB_EMAIL")
    password = os.getenv("ANKIWEB_PASSWORD")
    if not email or not password:
        logger.error("ANKIWEB_EMAIL или ANKIWEB_PASSWORD отсутствуют в .env")
        raise Exception("Credentials missing")

    body = encode_string_field(1, email) + encode_string_field(2, password)
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.post(
            "https://ankiuser.net/svc/account/login",
            content=body,
            headers={"Content-Type": "application/octet-stream"}
        )
        token = client.cookies.get("ankiweb")
        if not token:
            raise Exception("ankiweb cookie not found")
        return token

async def ankiweb_add_card(card_text: str, audio_url: str) -> bool:
    token = await get_token()
    
    # 1. Парсим текст от нейросети
    parsed = parse_card(card_text)
    
    # 2. Получаем картинку
    image_url = await get_image_url(parsed["image_prompt"], parsed["front"])
    
    if parsed["is_chinese"]:
        # ── CHINESE FRONT ──────────────────────────────────────────────
        front_html = f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 360px; margin: 0 auto; padding: 16px; background: #ffffff; border-radius: 20px; box-shadow: 0 8px 24px rgba(0,0,0,0.08); text-align: center; border: 1px solid #f0f0f0;">
    <div style="font-size: 14px; color: #8e8e93; font-weight: 500; margin-bottom: 4px; letter-spacing: 1px;">{parsed["pinyin"]}</div>
    <h1 style="font-size: 48px; font-weight: 800; color: #1d1d1f; margin: 0 0 16px 0;">{parsed["front"]}</h1>
    <div style="overflow: hidden; border-radius: 14px; margin-bottom: 8px; line-height: 0;">
        <img src="{image_url}" style="width: 100%; height: auto; object-fit: cover;">
    </div>
</div>
"""
        # ── CHINESE BACK ───────────────────────────────────────────────
        # Build related words block
        related_items = []
        for item in parsed["related_words"].split(";"):
            item = item.strip()
            if item:
                related_items.append(f'<div style="font-size: 14px; color: #3a3a3c; padding: 4px 0; border-bottom: 1px solid #f0f0f0;">{item}</div>')
        related_html = "".join(related_items)

        back_html = f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 360px; margin: 12px auto 0 auto; padding: 20px; background: #f9f9fb; border-radius: 20px; border: 1px solid #e5e5ea; box-shadow: 0 4px 16px rgba(0,0,0,0.04); text-align: left;">
    <div style="background: #d62b2b; color: white; display: inline-block; padding: 6px 14px; border-radius: 100px; font-size: 16px; font-weight: 600; margin-bottom: 16px;">
        {parsed["translation"]}
    </div>

    <div style="margin-bottom: 16px;">
        <div style="font-size: 12px; text-transform: uppercase; color: #8e8e93; font-weight: 700; margin-bottom: 4px; letter-spacing: 0.5px;">Example</div>
        <p style="font-size: 18px; color: #1d1d1f; margin: 0 0 4px 0; line-height: 1.4;">{parsed["sentence"]}</p>
        <p style="font-size: 13px; color: #8e8e93; margin: 0; font-style: italic;">{parsed["sentence_translation"]}</p>
    </div>

    <div style="margin-bottom: 4px;">
        <div style="font-size: 12px; text-transform: uppercase; color: #8e8e93; font-weight: 700; margin-bottom: 8px; letter-spacing: 0.5px;">Related Words</div>
        {related_html}
    </div>
</div>
"""
    else:
        # ── ENGLISH FRONT ──────────────────────────────────────────────
        front_html = f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 360px; margin: 0 auto; padding: 16px; background: #ffffff; border-radius: 20px; box-shadow: 0 8px 24px rgba(0,0,0,0.08); text-align: center; border: 1px solid #f0f0f0;">
    <h1 style="font-size: 32px; font-weight: 800; color: #1d1d1f; margin: 0 0 16px 0; letter-spacing: -0.5px;">{parsed["front"]}</h1>
    <div style="overflow: hidden; border-radius: 14px; margin-bottom: 8px; line-height: 0;">
        <img src="{image_url}" style="width: 100%; height: auto; object-fit: cover;">
    </div>
</div>
"""
        # ── ENGLISH BACK ───────────────────────────────────────────────
        synonyms_block = f'''
<div style="border-top: 1px solid #e5e5ea; padding-top: 12px;">
    <div style="font-size: 12px; text-transform: uppercase; color: #8e8e93; font-weight: 700; margin-bottom: 4px; letter-spacing: 0.5px;">Synonyms</div>
    <div style="font-size: 14px; color: #48484a; font-weight: 500;">{parsed["synonyms"]}</div>
</div>
''' if parsed["synonyms"] else ''

        back_html = f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 360px; margin: 12px auto 0 auto; padding: 20px; background: #f9f9fb; border-radius: 20px; border: 1px solid #e5e5ea; box-shadow: 0 4px 16px rgba(0,0,0,0.04); text-align: left;">
    <div style="background: #4361ee; color: white; display: inline-block; padding: 6px 14px; border-radius: 100px; font-size: 16px; font-weight: 600; margin-bottom: 16px;">
        {parsed["translation"]}
    </div>
    
    <div style="margin-bottom: 16px;">
        <div style="font-size: 12px; text-transform: uppercase; color: #8e8e93; font-weight: 700; margin-bottom: 4px; letter-spacing: 0.5px;">Example</div>
        <p style="font-size: 16px; color: #3a3a3c; margin: 0; line-height: 1.4; font-style: italic;">"{parsed["sentence"]}"</p>
    </div>

    <div style="margin-bottom: 16px;">
        <div style="font-size: 12px; text-transform: uppercase; color: #8e8e93; font-weight: 700; margin-bottom: 4px; letter-spacing: 0.5px;">Explanation</div>
        <p style="font-size: 14px; color: #48484a; margin: 0; line-height: 1.4;">{parsed["explanation"]}</p>
    </div>
    
    {synonyms_block}
</div>
"""

    audio_field = f"[sound:{audio_url}]"
    INNER_BYTES = bytes.fromhex("08d0c6e6eee93310d9c6e6eee933")
    
    # Собираем запрос с чистым HTML
    body = (
        encode_string_field(1, front_html) + 
        encode_string_field(1, back_html) + 
        encode_string_field(1, audio_field) + 
        encode_field(3, INNER_BYTES)
    )
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://ankiuser.net/svc/editor/add-or-update",
            content=body,
            headers={
                "Content-Type": "application/octet-stream",
                "Cookie": f"ankiweb={token}",
                "Origin": "https://ankiuser.net",
                "Referer": "https://ankiuser.net/add"
            }
        )
        
        if response.status_code == 401:
            global _token_cache
            _token_cache = None
            token = await get_token()
            response = await client.post(
                "https://ankiuser.net/svc/editor/add-or-update",
                content=body,
                headers={
                    "Content-Type": "application/octet-stream",
                    "Cookie": f"ankiweb={token}",
                    "Origin": "https://ankiuser.net",
                    "Referer": "https://ankiuser.net/add"
                }
            )
        return response.status_code == 200

async def sync_to_ankiweb(card_text: str, audio_url: str) -> bool:
    try:
        return await ankiweb_add_card(card_text, audio_url)
    except Exception as e:
        logger.error(f"AnkiWeb sync failed: {e}")
        return False