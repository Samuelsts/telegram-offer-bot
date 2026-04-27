from telethon import TelegramClient, events
from dotenv import load_dotenv
import os
import re
import time
import asyncio
import random
from collections import deque

# ==========================
# CONFIG
# ==========================

load_dotenv()

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")

client = TelegramClient("session_bot", api_id, api_hash)

# 🔎 Palavras-chave
KEYWORDS = [
    "notebook",
    "ssd",
    "monitor",
    "ryzen",
    "iphone",
    "teclado"
]

# 🚫 Palavras a ignorar
NEGATIVE = [
    "usado",
    "capinha",
    "cabo"
]

# 💰 Faixa de preço
PRICE_RULES = {
    "teclado": (60, 120),
    "ssd": (100, 400),
    "notebook": (1500, 3000),
    "monitor": (500, 900),
    "iphone": (1000, 5000)
}

# 🧠 Controle
seen_messages = set()

# 🔐 Anti-ban
LAST_SENT = 0
MIN_INTERVAL = 15  # segundos entre mensagens

message_queue = deque(maxlen=20)
TIME_WINDOW = 60  # janela de tempo
MAX_MSG = 5       # máximo por minuto

# ==========================
# FUNÇÕES
# ==========================

def normalize(text):
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.lower().strip()

def extract_prices(text):
    matches = re.findall(r'R\$\s*([\d\.]+,\d{2}|[\d\.]+)', text, re.IGNORECASE)

    prices = []
    for m in matches:
        try:
            clean = m.replace(".", "").replace(",", ".")
            prices.append(float(clean))
        except:
            continue

    return prices

def keyword_match(text):
    return any(re.search(rf"\b{k}\b", text) for k in KEYWORDS)

def negative_match(text):
    return any(n in text for n in NEGATIVE)

def can_send():
    now = time.time()
    message_queue.append(now)
    recent = [t for t in message_queue if now - t < TIME_WINDOW]
    return len(recent) <= MAX_MSG

def get_price_match_info(text):
    prices = extract_prices(text)

    if not prices:
        return False, None, []

    for keyword, (min_price, max_price) in PRICE_RULES.items():
        if keyword in text:
            for price in prices:
                if min_price <= price <= max_price:
                    return True, (min_price, max_price), prices
            return False, (min_price, max_price), prices

    return False, None, prices

async def safe_send(client, message):
    global LAST_SENT

    now = time.time()
    diff = now - LAST_SENT

    if diff < MIN_INTERVAL:
        wait = MIN_INTERVAL - diff
        print(f"⏳ Aguardando {wait:.1f}s...")
        await asyncio.sleep(wait)

    if not can_send():
        print("🚫 Limite de mensagens por minuto atingido")
        return

    await asyncio.sleep(random.uniform(1, 3))  # delay humano

    try:
        await client.send_message("me", message)
        LAST_SENT = time.time()
    except Exception as e:
        print("❌ Erro ao enviar:", e)

# ==========================
# EVENTO
# ==========================

@client.on(events.NewMessage)
async def handler(event):
    raw_text = event.raw_text or ""
    text = normalize(raw_text)

    if not text:
        return

    chat_name = event.chat.title if event.chat else "Privado"

    print(f"📩 [{chat_name}] {text}")

    if text in seen_messages:
        return

    if keyword_match(text) and not negative_match(text):
        valid, faixa, prices = get_price_match_info(text)

        if not valid:
            return

        seen_messages.add(text)

        # 🔗 Link
        link = ""
        try:
            if hasattr(event.chat, "username") and event.chat.username:
                link = f"https://t.me/{event.chat.username}/{event.id}"
            else:
                link = f"https://t.me/c/{event.chat_id}/{event.id}"
        except:
            link = ""

        # 🎯 Faixa
        faixa_str = f"🎯 Faixa considerada: R$ {faixa[0]} - R$ {faixa[1]}"

        # 💰 Preços
        prices_str = ", ".join([f"R$ {p:.2f}" for p in prices])

        msg = f"""
🚨 OFERTA DETECTADA

📍 Origem: {chat_name}
{faixa_str}

💬 {raw_text[:300]}

💰 Preços encontrados: {prices_str}
"""

        if link:
            msg += f"\n🔗 Link: {link}"

        await safe_send(client, msg)

# ==========================
# START
# ==========================

print("🚀 Bot rodando com proteção anti-ban...")
client.start()
client.run_until_disconnected()