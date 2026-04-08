# 🚀 DEPLOYMENT GUIDE

Your Telegram bot is ready to deploy! Choose your platform below.

---

## **Option 1: Railway.app (Recommended - Simplest)**

**Why Railway?**
- Free tier includes 500 hours/month (24/7 bot runs ~720 hours)
- Auto-restarts if bot crashes
- Easy GitHub integration
- Instant logs access

**Steps:**

### 1. Push to GitHub
```bash
# Already done! Your code is on:
# https://github.com/beingdeep2004-bit/news-bot
# Branch: claude/telegram-market-digest-bot-AmiFP
```

### 2. Go to Railway.app
```
https://railway.app
```

### 3. Create New Project
- Click "New Project" → "Deploy from GitHub"
- Select your repository: `beingdeep2004-bit/news-bot`
- Authorize Railway to access GitHub
- Select branch: `claude/telegram-market-digest-bot-AmiFP`

### 4. Configure Environment Variables
Railway should auto-detect Python. Go to **Variables** tab and add:

```
BOT_TOKEN=8758611475:AAGh5Ek0RNADWP3Gbw2DC8S0wQmFCT_dWts
CHAT_ID=1285910479
NEWSDATA_KEY=
```

### 5. Deploy
- Click "Deploy"
- Railway builds and starts your bot automatically
- Monitor in Deployments tab

**Check if running:**
```
Logs tab → Should show:
✅ Scheduler started - Jobs scheduled at 8 AM, 1 PM, 7 PM IST
🤖 Bot is running... Press Ctrl+C to stop.
```

**View logs:**
- Deployments → Select latest → View Logs
- Look for any errors (none expected)

**Cost:** Free (500 hrs/month covers 24/7 usage)

---

## **Option 2: Render.com**

**Why Render?**
- Free tier (with some limitations)
- Simple deployment from GitHub
- Auto-deploys on every push
- Good uptime

**Steps:**

### 1. Go to Render.com
```
https://render.com
```

### 2. Create Web Service
- Click "New +" → "Web Service"
- Connect GitHub (authorize if first time)
- Select repository: `beingdeep2004-bit/news-bot`
- Select branch: `claude/telegram-market-digest-bot-AmiFP`

### 3. Fill Configuration
```
Name:              telegram-news-bot
Environment:       Python 3
Build Command:     pip install -r requirements.txt
Start Command:     python bot.py
Instance Type:     Free (or Starter for 24/7 - $7/month)
```

### 4. Add Environment Variables
Go to **Environment** tab:

```
BOT_TOKEN = 8758611475:AAGh5Ek0RNADWP3Gbw2DC8S0wQmFCT_dWts
CHAT_ID = 1285910479
NEWSDATA_KEY = (leave empty)
```

### 5. Deploy
- Click "Create Web Service"
- Render builds and deploys
- Monitor in Logs

**Keep Running 24/7:**
- Settings → Instance Type → Select **Starter** ($7/month)
- Free tier sleeps after 15 min inactivity

**View logs:**
- Logs section shows real-time output

---

## **Option 3: Self-Hosted VPS**

**Why self-host?**
- Full control
- Cheapest long-term ($5-15/month VPS)
- No free tier limitations

**Steps:**

### 1. SSH into your server
```bash
ssh root@your_vps_ip
```

### 2. Clone and setup
```bash
cd /root
git clone https://github.com/beingdeep2004-bit/news-bot.git
cd news-bot

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure .env
```bash
nano .env
```
Add:
```
BOT_TOKEN=8758611475:AAGh5Ek0RNADWP3Gbw2DC8S0wQmFCT_dWts
CHAT_ID=1285910479
NEWSDATA_KEY=
```

Save: `Ctrl+X` → `Y` → `Enter`

### 4. Create systemd service
```bash
sudo nano /etc/systemd/system/telegram-bot.service
```

Paste:
```ini
[Unit]
Description=Telegram News Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/news-bot
Environment="BOT_TOKEN=8758611475:AAGh5Ek0RNADWP3Gbw2DC8S0wQmFCT_dWts"
Environment="CHAT_ID=1285910479"
ExecStart=/root/news-bot/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Save: `Ctrl+X` → `Y` → `Enter`

### 5. Start bot
```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
```

### 6. Check status
```bash
sudo systemctl status telegram-bot
sudo journalctl -u telegram-bot -f  # View live logs
```

**Stop bot:**
```bash
sudo systemctl stop telegram-bot
```

**Restart after changes:**
```bash
sudo systemctl restart telegram-bot
```

---

## **Testing Commands (Any Platform)**

Once deployed, test these commands in Telegram:

```
/start          → Welcome message
/help           → Command list
/news           → Top news now
/market         → Stock update now
/crypto         → Crypto prices now
/stocks         → Market indices
/morning        → Morning digest now
/evening        → Evening digest now
```

---

## **Auto-Scheduled Digests**

Bot automatically sends:

| Time   | Content |
|--------|---------|
| 8 AM IST (02:30 UTC)  | Crypto + Markets + Top News |
| 1 PM IST (07:30 UTC)  | Stock Update + Crypto |
| 7 PM IST (13:30 UTC)  | Markets Close + News + F&G |

No manual work needed! Bot runs 24/7.

---

## **Troubleshooting**

### Bot doesn't respond to commands
```
1. Check Deployments logs for errors
2. Verify BOT_TOKEN is correct (20+ char alphanumeric)
3. Verify CHAT_ID is correct (numeric, no @)
4. Ensure bot is added to the chat/channel
5. Restart deployment
```

### No digests at scheduled times
```
1. Check logs around 8:00, 13:00, 19:00 IST
2. Ensure server timezone is correct
3. Verify internet connection (check API call logs)
4. Restart bot
```

### RSS feeds not working
```
- Some feeds block requests at certain times
- Bot auto-skips broken feeds, tries next one
- Check logs for which feeds succeeded
```

### API timeouts
```
- CoinGecko & yfinance may be slow during market hours
- Bot has 10-second timeout, retries gracefully
- Check logs for "Timeout" errors
```

---

## **Monitoring (Optional)**

### Railway
- Deployments tab shows real-time status
- Auto-restarts on failure
- Check memory/CPU usage

### Render
- Logs show all activity
- Metrics tab for CPU/memory
- Email alerts (Settings)

### VPS
```bash
# Check bot is running
ps aux | grep "python bot.py"

# View recent logs (last 50 lines)
sudo journalctl -u telegram-bot -n 50

# View logs since last restart
sudo journalctl -u telegram-bot --since "2 hours ago"

# Check disk space
df -h

# Check memory
free -h
```

---

## **Summary**

| Platform | Cost | Uptime | Setup Time | Recommendation |
|----------|------|--------|------------|-----------------|
| **Railway** | Free | 99.9% | 5 min | ⭐ Best for beginners |
| **Render** | $0-7 | 95% | 5 min | Good alternative |
| **VPS** | $5-15 | 99%+ | 15 min | Best for control |

**Next Step:** Choose a platform and deploy!

Questions? Check the main README.md for more details.
