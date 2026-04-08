# 🚂 Railway.app Quick Start (5 Minutes)

Your bot is **100% ready to deploy**. Follow these exact steps:

## Step 1: Go to Railway.app
Visit: https://railway.app

## Step 2: Sign Up (if needed)
- Click "Sign Up"
- Use GitHub account (easiest)
- Authorize Railway

## Step 3: New Project
Click **"New Project"** → **"Deploy from GitHub"**

## Step 4: Connect GitHub
- Click "Configure GitHub App"
- Select `beingdeep2004-bit/news-bot` repository
- Click "Install"

## Step 5: Select Repository
- Choose: `beingdeep2004-bit/news-bot`
- Branch: `claude/telegram-market-digest-bot-AmiFP`
- Click "Deploy"

## Step 6: Configure Variables
Railway auto-detects Python. Wait for build to start, then:

1. Click **"Variables"** tab
2. Add these 3 variables:

| Key | Value |
|-----|-------|
| `BOT_TOKEN` | `8758611475:AAGh5Ek0RNADWP3Gbw2DC8S0wQmFCT_dWts` |
| `CHAT_ID` | `1285910479` |
| `NEWSDATA_KEY` | (leave empty) |

3. Click "Add variable" for each one
4. Click **"Deploy"**

## Step 7: Wait for Deployment
Railway builds your bot. You'll see:
```
✅ Build successful
✅ Bot started
```

Check **Logs** tab - should show:
```
✅ Scheduler started - Jobs scheduled at 8 AM, 1 PM, 7 PM IST
🤖 Bot is running... Press Ctrl+C to stop.
```

## ✅ Done!

Your bot is now **live 24/7**!

Test in Telegram:
- `/start` - Should get welcome message
- `/help` - Should get command list
- `/crypto` - Should get crypto prices
- `/market` - Should get stock prices

---

## Digests Sent Automatically

The bot will send digests at:
- **8:00 AM IST** - Morning (crypto + markets + news)
- **1:00 PM IST** - Midday (stocks + crypto)
- **7:00 PM IST** - Evening (markets + news + fear & greed)

No manual work needed!

---

## View Logs Anytime

Go to **Deployments** → Select deployment → **Logs**

Look for:
- ✅ "Sent successfully" = Digest delivered
- ❌ "Error" = Check what failed
- "Job triggered" = Scheduled task ran

---

## Make Changes & Redeploy

If you change bot.py:
1. Push to GitHub:
   ```bash
   git add bot.py
   git commit -m "Update bot"
   git push origin claude/telegram-market-digest-bot-AmiFP
   ```

2. Railway auto-redeploys (watch Deployments tab)

---

## Common Issues

| Problem | Solution |
|---------|----------|
| Bot doesn't respond | Check logs, verify BOT_TOKEN |
| No digests at 8 AM | Check logs around 08:00, verify CHAT_ID |
| "Error connecting" | Restart deployment (Deployments → Restart) |
| Need to update token | Settings → Variables → Edit BOT_TOKEN → Restart |

---

## That's It!

You have a **production-grade Telegram bot running 24/7** ✅

Need help? Check `README.md` or `DEPLOYMENT.md` for more details.
