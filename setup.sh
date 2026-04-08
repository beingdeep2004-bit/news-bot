#!/bin/bash

echo "=========================================="
echo "🤖 Telegram News Bot - Setup"
echo "=========================================="
echo ""
echo "Need: Bot Token from @BotFather"
echo "Need: Chat ID (get from https://api.telegram.org/bot<TOKEN>/getUpdates)"
echo ""

read -p "Enter BOT_TOKEN: " BOT_TOKEN
read -p "Enter CHAT_ID: " CHAT_ID
read -p "Enter NEWSDATA_KEY (optional, press Enter to skip): " NEWSDATA_KEY

cat > .env << ENVFILE
BOT_TOKEN=$BOT_TOKEN
CHAT_ID=$CHAT_ID
NEWSDATA_KEY=$NEWSDATA_KEY
ENVFILE

echo ""
echo "✅ Config saved to .env"
echo "Run: source venv/bin/activate && python bot.py"
