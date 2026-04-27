import re
import json
import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient, events

load_dotenv()

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")

client = TelegramClient("session_bot", api_id, api_hash)

# ==========================
# CONFIG
# ==========================
def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)


# ==========================
# EXTRAIR PREÇOS (ROBUSTO)
# ==========================
def extrair_precos(texto):
    padrao = r"r\$\s?\d{1,3}(?:\.\d{3})*(?:,\d{2})?|r\$\s?\d+"
    matches = re.findall(padrao, texto.lower())

    valores = []
    for m in matches:
        num = m.replace("r$", "").strip()
        num = num.replace(".", "").replace(",", ".")
        try:
            valores.append(float(num))
        except:
            continue

    return valores


# ==========================
# OBTER NOME DO GRUPO
# ==========================
def get_origem(event):
    try:
        if event.is_group or event.is_channel:
            return event.chat.title
        return "Privado"
    except:
        return "Desconhecido"


# ==========================
# HANDLER
# ==========================
@client.on(events.NewMessage)
async def handler(event):
    try:
        texto_original = event.raw_text
        texto = texto_original.lower()

        config = load_config()
        filtros = config["filtros"]

        for filtro in filtros:
            nome = filtro["nome"]
            keywords = filtro["keywords"]
            min_price = filtro["min"]
            max_price = filtro["max"]

            # keyword match (case insensitive)
            if not any(k.lower() in texto for k in keywords):
                continue

            precos = extrair_precos(texto_original)

            if not precos:
                continue

            dentro_faixa = [
                p for p in precos if min_price <= p <= max_price
            ]

            if not dentro_faixa:
                continue

            origem = get_origem(event)

            link = ""
            if event.chat and getattr(event.chat, "username", None):
                link = f"https://t.me/{event.chat.username}/{event.id}"

            mensagem = f"""
🚨 OFERTA DETECTADA

📍 Origem: {origem}
🎯 Filtro: {nome}
💰 Faixa definida: ({min_price}, {max_price})

💬 {texto_original}

💰 Preços encontrados: {', '.join([f'R$ {p:.2f}' for p in precos])}

🔗 {link}
"""

            print(mensagem)

            # envia pra você mesmo
            await client.send_message("me", mensagem)

            # anti-spam / anti-ban
            await asyncio.sleep(2)

    except Exception as e:
        print("Erro:", e)


# ==========================
# START
# ==========================
async def main():
    print("🚀 Bot rodando com proteção anti-ban...")
    await client.start()
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())