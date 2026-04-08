# 📱 Telegram Daily Market & News Digest Bot

A 24/7 Telegram bot that delivers curated market updates and news digests at fixed times throughout the day. Covers crypto, Indian stock indices, global markets, and breaking news from top sources.

## ✨ Features

- **Automated Digests**: Daily at 8 AM, 1 PM, 7 PM IST
- **Crypto Tracking**: Real-time BTC, ETH, SOL, BNB, XRP prices (USD + INR)
- **Stock Markets**: Nifty 50, Sensex, S&P 500, NASDAQ, Gold, USD/INR
- **News Sources**: BBC, Reuters, The Hindu, Livemint, PIB, Al Jazeera, Down to Earth (10 RSS feeds)
- **Fear & Greed Index**: Market sentiment tracking
- **10 Commands**: /start, /help, /news, /market, /crypto, /stocks, /india, /cat, /morning, /evening
- **Error Handling**: Graceful fallbacks, zero crashes
- **MarkdownV2**: Clean, formatted Telegram messages

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.11+
- Telegram account & BotFather setup
- (Optional) NewsData.io API key for India news

### 2. Get Bot Token & Chat ID

**Get Bot Token:**
1. Open Telegram, search for `@BotFather`
2. Send `/newbot`, follow prompts
3. Copy the token (looks like: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

**Get Chat ID:**
1. Add your bot to a private chat
2. Send any message to the bot
3. Visit: `https://api.telegram.org/bot<BOT_TOKEN>/getUpdates`
4. Look for `"chat":{"id":<CHAT_ID>}`

### 3. Clone & Setup

```bash
# Clone repository
git clone https://github.com/yourusername/news-bot.git
cd news-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
BOT_TOKEN=your_bot_token_here
CHAT_ID=your_chat_id_here
NEWSDATA_KEY=your_newsdata_key_here
EOF

# Run locally
python bot.py
```

### 4. Test Commands

Send these to your bot in Telegram:
- `/start` - Welcome message
- `/help` - Command list
- `/crypto` - Get crypto prices now
- `/market` - Get stock update now
- `/news` - Get top news now
- `/morning` - Trigger morning digest
- `/evening` - Trigger evening digest

## 🌍 Deployment

### Option 1: Railway.app (Recommended)

**Advantages**: Free tier, easy setup, auto-restarts

**Steps:**
1. Push code to GitHub:
```bash
git add .
git commit -m "Initial commit: telegram news bot"
git push origin claude/telegram-market-digest-bot-AmiFP
```

2. Go to https://railway.app
3. Click "New Project" → "Deploy from GitHub"
4. Select your repository
5. Railway auto-detects Python
6. Go to Variables tab, add:
   - `BOT_TOKEN` = your_token
   - `CHAT_ID` = your_chat_id
   - `NEWSDATA_KEY` = your_key (optional)
7. Click Deploy
8. Bot runs 24/7 automatically

**Check Logs:**
```
Deployments tab → View logs
```

### Option 2: Render.com

**Advantages**: Free tier, simple, auto-deploy on push

**Steps:**
1. Push to GitHub (same as above)
2. Go to https://render.com
3. Click "New +" → "Web Service"
4. Connect GitHub account, select repository
5. Fill form:
   - **Name**: `telegram-news-bot`
   - **Runtime**: `Python 3.11`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
6. Add Environment Variables:
   - `BOT_TOKEN`
   - `CHAT_ID`
   - `NEWSDATA_KEY`
7. Click "Create Web Service"
8. Bot deploys and runs

**Keep Service Active:**
Go to Settings → Instance Type → Select "Standard" (prevents sleep after 15 min inactivity)

### Option 3: VPS (Advanced)

```bash
# SSH into your VPS
ssh user@your_vps_ip

# Setup
cd /home/user/
git clone https://github.com/yourusername/news-bot.git
cd news-bot

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create systemd service
sudo nano /etc/systemd/system/telegram-bot.service
```

Paste this:
```ini
[Unit]
Description=Telegram News Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/home/your_user/news-bot
Environment="BOT_TOKEN=your_token"
Environment="CHAT_ID=your_chat_id"
ExecStart=/home/your_user/news-bot/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Start service
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot

# Check status
sudo systemctl status telegram-bot
sudo journalctl -u telegram-bot -f  # View logs
```

## 📋 API Reference

### Data Sources

| Source | Data | Free? | Notes |
|--------|------|-------|-------|
| CoinGecko | Crypto | ✅ | 5 cryptos, 24h change |
| Yahoo Finance (yfinance) | Stocks | ✅ | Nifty, Sensex, S&P, NASDAQ, Gold |
| Alternative.me | F&G Index | ✅ | Market sentiment |
| RSS Feeds | News | ✅ | 10 sources, 2 articles each |
| NewsData.io | India News | ⚠️ | Optional, free tier available |

### Command Reference

```
/start          → Bot welcome message
/help           → Show all commands
/news           → Top news from all sources
/market         → Stock indices update
/crypto         → Crypto prices (BTC, ETH, SOL, BNB, XRP)
/stocks         → Detailed market indices
/india          → India breaking news (requires NEWSDATA_KEY)
/cat            → CAT GK preparation digest
/morning        → Trigger morning digest immediately
/evening        → Trigger evening digest immediately
```

### Scheduled Jobs

| Time | IST | Content |
|------|-----|---------|
| 08:00 | Morning | Crypto + Markets + News |
| 13:00 | Midday | Stock update + Crypto |
| 19:00 | Evening | Markets close + News + F&G |

## 🔧 Troubleshooting

### Bot doesn't respond
```
1. Check BOT_TOKEN is correct (BotFather)
2. Check CHAT_ID is correct (api.telegram.org/bot<TOKEN>/getUpdates)
3. Check internet connection
4. View logs: python bot.py (should show ✅ Scheduler started)
```

### RSS feeds return no articles
- Feeds tested valid ✅ on 2024-04-08
- Some feeds may be region-locked or rate-limited
- Bot auto-skips broken feeds, tries next one

### API timeouts
- CoinGecko & yfinance occasionally slow
- Bot retries with 10-second timeout
- If all fail, sends error message instead of crashing

### Deployment issues on Railway/Render
```
Check:
1. Logs tab (any Python errors?)
2. Environment variables (typo check?)
3. Free tier limits (CPU/RAM sufficient)
4. Restart deployment if stuck
```

## 📝 File Structure

```
news-bot/
├── bot.py              # Main bot code (500+ lines)
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── .env               # Local config (don't commit)
```

## 🔐 Security

- **Never commit `.env`** to GitHub
- **Never share BOT_TOKEN** or CHAT_ID
- Bot only sends to configured CHAT_ID
- All API calls use HTTPS
- Error handling prevents token leaks in logs

## 📦 Dependencies

```
python-telegram-bot==21.5   # Telegram API wrapper
feedparser==6.0.11          # RSS feed parser
requests==2.31.0            # HTTP requests
yfinance==0.2.40            # Yahoo Finance API
APScheduler==3.10.4         # Scheduled jobs
python-dotenv==1.0.0        # Environment variables
```

## 🐛 Known Issues

- Some Indian RSS feeds (PIB, Hindu) occasionally slow
- yfinance requires live market hours for realtime data
- NewsData.io free tier has 200 requests/day limit
- Telegram message size limit 4096 chars (bot truncates gracefully)

## 🚀 Future Enhancements

- [ ] User preferences (which feeds, which times)
- [ ] Database for user tracking
- [ ] Detailed crypto technical analysis
- [ ] Options pricing
- [ ] Portfolio tracking
- [ ] Web dashboard

## 📞 Support

Issues? Check:
1. Logs (`tail -f` deployment logs)
2. Environment variables (correct spelling)
3. Internet connection (can APIs be reached?)
4. GitHub Issues in repository

## 📄 License

MIT - Use freely, modify as needed

---

**Status**: ✅ Production ready | **Last Updated**: April 8, 2024 | **Tested**: Python 3.11
