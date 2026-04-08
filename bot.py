"""
Telegram Daily Market & News Digest Bot
Delivers crypto, stock market, and curated news at 8 AM, 1 PM, 7 PM IST
"""

import os
import logging
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

import requests
import feedparser
import yfinance as yf
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Update, Chat
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode, ChatAction

# ==================== CONFIG ====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
CHAT_ID = os.getenv("CHAT_ID", "YOUR_CHAT_ID_HERE")
NEWSDATA_KEY = os.getenv("NEWSDATA_KEY", "")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ==================== RSS FEEDS ====================
RSS_FEEDS = {
    "BBC World": "http://feeds.bbc.co.uk/news/rss.xml",
    "BBC Business": "http://feeds.bbc.co.uk/news/business/rss.xml",
    "The Hindu": "https://www.thehindu.com/news/national/feed",
    "Livemint": "https://www.livemint.com/feed/rss/news.xml",
    "PIB": "https://pib.gov.in/rss/default.aspx",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "BBC Science": "http://feeds.bbc.co.uk/news/science_and_environment/rss.xml",
    "Down to Earth": "https://www.downtoearth.org.in/feed/",
    "BBC Sport": "http://feeds.bbc.co.uk/sport/rss.xml",
    "India Times": "https://feeds.hindustantimes.com/rss/topnews.xml",
}

IST = ZoneInfo("Asia/Kolkata")

# ==================== HELPER FUNCTIONS ====================

def escape_markdown(text: str) -> str:
    """Escape special characters for MarkdownV2"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

# ==================== API FUNCTIONS ====================

def fetch_crypto_prices() -> str:
    """Fetch BTC, ETH, SOL, BNB, XRP prices from CoinGecko (free API)"""
    try:
        crypto_ids = "bitcoin,ethereum,solana,binancecoin,ripple"
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_ids}&vs_currencies=usd,inr&include_24hr_change=true"

        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        cryptos = {
            "bitcoin": "₿ BTC",
            "ethereum": "Ξ ETH",
            "solana": "SOL",
            "binancecoin": "BNB",
            "ripple": "XRP"
        }

        message = "*🪙 CRYPTO PRICES*\n"
        for key, symbol in cryptos.items():
            if key in data:
                usd = data[key].get("usd", 0)
                inr = data[key].get("inr", 0)
                change = data[key].get("usd_24h_change", 0)

                emoji = "📈" if change > 0 else "📉"
                message += f"\n{symbol}: ${usd:,.0f} (₹{inr:,.0f}) {emoji} {change:.2f}%"

        return message
    except Exception as e:
        logger.error(f"Crypto fetch error: {e}")
        return "*❌ Crypto Error:* API temporarily unavailable"


def fetch_stock_prices() -> str:
    """Fetch stock indices: Nifty 50, Sensex, S&P 500, NASDAQ, USDINR, Gold"""
    try:
        tickers = ["^NSEI", "^BSESN", "^GSPC", "^IXIC", "INR=X", "GC=F"]
        names = ["Nifty 50", "Sensex", "S&P 500", "NASDAQ", "USD/INR", "Gold"]

        message = "*📊 STOCK INDICES*\n"
        for ticker, name in zip(tickers, names):
            try:
                data = yf.Ticker(ticker)
                hist = data.history(period="1d")

                if not hist.empty:
                    current = hist["Close"].iloc[-1]
                    prev = hist["Open"].iloc[0]
                    change = ((current - prev) / prev * 100) if prev != 0 else 0

                    emoji = "📈" if change > 0 else "📉"

                    if name == "USD/INR":
                        message += f"\n{name}: ₹{current:.2f} {emoji} {change:+.2f}%"
                    elif name == "Gold":
                        message += f"\n{name}: ${current:,.2f}/oz {emoji} {change:+.2f}%"
                    else:
                        message += f"\n{name}: {current:,.0f} {emoji} {change:+.2f}%"
            except Exception as e:
                logger.warning(f"Error fetching {name}: {e}")
                message += f"\n{name}: ⚠️ Error"

        return message
    except Exception as e:
        logger.error(f"Stock fetch error: {e}")
        return "*❌ Stock Error:* API temporarily unavailable"


def fetch_rss(source: Optional[str] = None) -> str:
    """Fetch news from RSS feeds"""
    try:
        feeds_to_fetch = {source: RSS_FEEDS[source]} if source and source in RSS_FEEDS else RSS_FEEDS
        message = "*📰 TOP NEWS*\n"

        article_count = 0
        for feed_name, feed_url in feeds_to_fetch.items():
            try:
                feed = feedparser.parse(feed_url)
                entries = feed.get("entries", [])[:2]  # Get 2 articles per feed

                if entries:
                    message += f"\n*{feed_name}:*\n"
                    for entry in entries:
                        title = entry.get("title", "No title")[:60]
                        link = entry.get("link", "#")
                        message += f"• [{title}]({link})\n"
                        article_count += 1
            except Exception as e:
                logger.warning(f"RSS feed error for {feed_name}: {e}")

        if article_count == 0:
            return "*⚠️ No articles found*"

        return message
    except Exception as e:
        logger.error(f"RSS fetch error: {e}")
        return "*❌ News Error:* API temporarily unavailable"


def fetch_fear_greed() -> str:
    """Fetch Fear & Greed index from alternative.me"""
    try:
        url = "https://api.alternative.me/fng/?limit=1"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data["data"]:
            index = int(data["data"][0]["value"])
            label = data["data"][0]["value_classification"]

            # Emotion emoji based on index
            if index < 25:
                emoji = "😱"
            elif index < 50:
                emoji = "😟"
            elif index < 75:
                emoji = "😊"
            else:
                emoji = "🤑"

            return f"*🎭 FEAR & GREED INDEX*\n{emoji} {index}/100 - {label}"
        return "*⚠️ Fear & Greed data unavailable*"
    except Exception as e:
        logger.error(f"Fear & Greed error: {e}")
        return "*❌ F&G Error:* API temporarily unavailable"


def fetch_india_news() -> str:
    """Fetch India breaking news from NewsData.io (optional)"""
    if not NEWSDATA_KEY or NEWSDATA_KEY == "":
        return None

    try:
        url = f"https://newsdata.io/api/1/latest?q=India&country=in&apikey={NEWSDATA_KEY}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        message = "*🇮🇳 INDIA BREAKING NEWS*\n"
        for article in data.get("results", [])[:3]:
            title = article.get("title", "")[:60]
            link = article.get("link", "#")
            message += f"• [{title}]({link})\n"

        return message
    except Exception as e:
        logger.warning(f"India news error: {e}")
        return None


# ==================== DIGEST MESSAGES ====================

async def morning_digest(context: ContextTypes.DEFAULT_TYPE) -> None:
    """8 AM IST - Crypto + Markets + Top News"""
    try:
        message = f"*🌅 GOOD MORNING! ({datetime.now(IST).strftime('%I:%M %p IST')})*\n\n"

        crypto = fetch_crypto_prices()
        stocks = fetch_stock_prices()
        fear_greed = fetch_fear_greed()
        news = fetch_rss()

        message += f"{crypto}\n\n{stocks}\n\n{fear_greed}\n\n{news}"

        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode=ParseMode.MARKDOWN_V2,
            disable_web_page_preview=True
        )
        logger.info("Morning digest sent successfully")
    except Exception as e:
        logger.error(f"Morning digest error: {e}")


async def midday_digest(context: ContextTypes.DEFAULT_TYPE) -> None:
    """1 PM IST - Markets Update + Crypto"""
    try:
        message = f"*📈 MIDDAY MARKETS UPDATE ({datetime.now(IST).strftime('%I:%M %p IST')})*\n\n"

        stocks = fetch_stock_prices()
        crypto = fetch_crypto_prices()

        message += f"{stocks}\n\n{crypto}"

        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode=ParseMode.MARKDOWN_V2,
            disable_web_page_preview=True
        )
        logger.info("Midday digest sent successfully")
    except Exception as e:
        logger.error(f"Midday digest error: {e}")


async def evening_digest(context: ContextTypes.DEFAULT_TYPE) -> None:
    """7 PM IST - Markets Close + News Wrap + F&G"""
    try:
        message = f"*🌆 EVENING WRAP UP ({datetime.now(IST).strftime('%I:%M %p IST')})*\n\n"

        stocks = fetch_stock_prices()
        fear_greed = fetch_fear_greed()
        news = fetch_rss()

        message += f"{stocks}\n\n{fear_greed}\n\n{news}"

        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode=ParseMode.MARKDOWN_V2,
            disable_web_page_preview=True
        )
        logger.info("Evening digest sent successfully")
    except Exception as e:
        logger.error(f"Evening digest error: {e}")


# ==================== COMMAND HANDLERS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    try:
        user = update.effective_user
        message = f"👋 *Welcome {user.first_name}\\!*\n\n_Daily Market & News Digest Bot_\n\nUse /help to see all commands\\."
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        logger.error(f"Start error: {e}")
        await update.message.reply_text(f"Error: {str(e)}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    try:
        message = """*📋 AVAILABLE COMMANDS*

/start \\- Welcome message
/help \\- Show this menu
/news \\- Latest top news from all sources
/market \\- Stock indices update
/crypto \\- Cryptocurrency prices
/stocks \\- Detailed market indices
/india \\- India breaking news \\(if enabled\\)
/cat \\- CAT GK preparation digest
/morning \\- Get morning digest now
/evening \\- Get evening digest now

_Data updates automatically at 8 AM, 1 PM, 7 PM IST_"""
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        logger.error(f"Help error: {e}")
        await update.message.reply_text(f"Error: {str(e)}")


async def news(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /news command"""
    try:
        await update.message.chat.send_action(ChatAction.TYPING)
        message = fetch_rss()
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"News error: {e}")
        error_msg = escape_markdown(str(e))
        await update.message.reply_text(f"*❌ Error:* {error_msg}", parse_mode=ParseMode.MARKDOWN_V2)


async def market(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /market command"""
    try:
        await update.message.chat.send_action(ChatAction.TYPING)
        message = fetch_stock_prices()
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        logger.error(f"Market error: {e}")
        error_msg = escape_markdown(str(e))
        await update.message.reply_text(f"*❌ Error:* {error_msg}", parse_mode=ParseMode.MARKDOWN_V2)


async def crypto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /crypto command"""
    try:
        await update.message.chat.send_action(ChatAction.TYPING)
        message = fetch_crypto_prices()
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        logger.error(f"Crypto error: {e}")
        error_msg = escape_markdown(str(e))
        await update.message.reply_text(f"*❌ Error:* {error_msg}", parse_mode=ParseMode.MARKDOWN_V2)


async def stocks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stocks command"""
    try:
        await update.message.chat.send_action(ChatAction.TYPING)
        message = fetch_stock_prices()
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        logger.error(f"Stocks error: {e}")
        error_msg = escape_markdown(str(e))
        await update.message.reply_text(f"*❌ Error:* {error_msg}", parse_mode=ParseMode.MARKDOWN_V2)


async def india(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /india command"""
    try:
        await update.message.chat.send_action(ChatAction.TYPING)
        message = fetch_india_news()

        if message is None:
            message = "_India news requires NEWSDATA_KEY environment variable\\._"
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)
        else:
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"India error: {e}")
        error_msg = escape_markdown(str(e))
        await update.message.reply_text(f"*❌ Error:* {error_msg}", parse_mode=ParseMode.MARKDOWN_V2)


async def cat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /cat command - CAT GK preparation"""
    try:
        message = """*🎓 CAT GK DIGEST*

_Coming Soon\\!_

This section will include:
\\- Current Affairs
\\- Economic News
\\- Business Headlines
\\- Government Policies
\\- Stock Market Insights

Check back for daily updates\\."""
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        logger.error(f"CAT error: {e}")
        error_msg = escape_markdown(str(e))
        await update.message.reply_text(f"*❌ Error:* {error_msg}", parse_mode=ParseMode.MARKDOWN_V2)


async def morning(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /morning command"""
    try:
        await update.message.chat.send_action(ChatAction.TYPING)
        await morning_digest(context)
    except Exception as e:
        logger.error(f"Morning command error: {e}")
        error_msg = escape_markdown(str(e))
        await update.message.reply_text(f"*❌ Error:* {error_msg}", parse_mode=ParseMode.MARKDOWN_V2)


async def evening(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /evening command"""
    try:
        await update.message.chat.send_action(ChatAction.TYPING)
        await evening_digest(context)
    except Exception as e:
        logger.error(f"Evening command error: {e}")
        error_msg = escape_markdown(str(e))
        await update.message.reply_text(f"*❌ Error:* {error_msg}", parse_mode=ParseMode.MARKDOWN_V2)


# ==================== MAIN ====================

def main():
    """Start the bot"""
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or CHAT_ID == "YOUR_CHAT_ID_HERE":
        logger.error("❌ BOT_TOKEN or CHAT_ID not configured. Set environment variables.")
        print("Please set:")
        print("  export BOT_TOKEN='your_token_here'")
        print("  export CHAT_ID='your_chat_id_here'")
        return

    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("news", news))
    application.add_handler(CommandHandler("market", market))
    application.add_handler(CommandHandler("crypto", crypto))
    application.add_handler(CommandHandler("stocks", stocks))
    application.add_handler(CommandHandler("india", india))
    application.add_handler(CommandHandler("cat", cat))
    application.add_handler(CommandHandler("morning", morning))
    application.add_handler(CommandHandler("evening", evening))

    # Set up scheduler for digests
    scheduler = BackgroundScheduler(timezone="Asia/Kolkata")

    # 8 AM IST
    scheduler.add_job(
        morning_digest,
        CronTrigger(hour=8, minute=0, timezone="Asia/Kolkata"),
        args=[application.bot],
        id="morning_digest",
        name="Morning Digest"
    )

    # 1 PM IST (13:00)
    scheduler.add_job(
        midday_digest,
        CronTrigger(hour=13, minute=0, timezone="Asia/Kolkata"),
        args=[application.bot],
        id="midday_digest",
        name="Midday Digest"
    )

    # 7 PM IST (19:00)
    scheduler.add_job(
        evening_digest,
        CronTrigger(hour=19, minute=0, timezone="Asia/Kolkata"),
        args=[application.bot],
        id="evening_digest",
        name="Evening Digest"
    )

    scheduler.start()
    logger.info("✅ Scheduler started - Jobs scheduled at 8 AM, 1 PM, 7 PM IST")

    # Start bot
    logger.info("🤖 Bot is running... Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
