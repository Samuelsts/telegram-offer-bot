#!/bin/bash

echo "🚀 Iniciando deploy..."

# Ir para pasta do projeto
cd ~/telegram-offer-bot || { echo "❌ Pasta não encontrada"; exit 1; }

echo "📥 Atualizando código..."
git pull

echo "🐍 Ativando ambiente virtual..."
source venv/bin/activate

echo "📦 Instalando dependências..."
pip install -r requirements.txt > /dev/null 2>&1

echo "🔍 Validando config.json..."
python3 -m json.tool config.json > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo "❌ ERRO: config.json inválido!"
    echo "👉 Corrija antes de continuar."
    exit 1
fi

echo "🔁 Reiniciando bot..."
sudo systemctl restart telegram-bot

sleep 2

echo "📊 Status do bot:"
sudo systemctl status telegram-bot --no-pager

echo ""
echo "📜 Últimos logs:"
tail -n 10 /home/ubuntu/telegram-bot.log

echo ""
echo "✅ Deploy finalizado!"