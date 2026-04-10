"""
🤖 AI-Powered Telegram News & Market Digest Bot
Delivers Claude-curated news, market updates, and crypto prices at 8 AM, 1 PM, 7 PM IST
Features: RSS aggregation → deduplication → Claude AI curation → structured Telegram output
"""

import os
import logging
import signal
import sys
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from zoneinfo import ZoneInfo
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor

import requests
import feedparser
import yfinance as yf
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Update, Chat
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode, ChatAction
from groq import Groq
import httpx

# ==================== CONFIG ====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
CHAT_ID = os.getenv("CHAT_ID", "YOUR_CHAT_ID_HERE")
NEWSDATA_KEY = os.getenv("NEWSDATA_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Initialize Groq client with custom httpx configuration
groq_client = None

def get_groq_client():
    """Initialize Groq client with proper httpx configuration"""
    global groq_client
    if groq_client is None and GROQ_API_KEY:
        try:
            # Create custom httpx client without problematic proxy settings
            http_client = httpx.Client(
                timeout=30.0,
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            )
            groq_client = Groq(api_key=GROQ_API_KEY, http_client=http_client)
            logger.info("✅ Groq client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            return None
    return groq_client

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ==================== PREMIUM RSS FEEDS (High-Quality Sources) ====================
# These are curated sources known for reliable, well-researched journalism
RSS_FEEDS = {
    # Indian Business & Markets
    "Livemint": "https://www.livemint.com/feed/rss/news.xml",
    "Economic Times": "https://economictimes.indiatimes.com/rssfeeds/1977021049.cms",
    "CNBC-TV18": "https://feeds.cnbctv18.com/cnbctv18/feed/rss/news.xml",

    # Global Markets & Business
    "Reuters World": "https://feeds.reuters.com/reuters/businessNews",
    "Financial Times": "https://feeds.ft.com/world",

    # Tech & Innovation
    "TechCrunch": "http://feeds.techcrunch.com/TechCrunch/",
    "The Verge": "https://www.theverge.com/rss/index.xml",

    # Global News & Analysis
    "BBC News": "http://feeds.bbc.co.uk/news/rss.xml",
    "BBC Business": "http://feeds.bbc.co.uk/news/business/rss.xml",

    # Sustainability & Policy
    "Down to Earth": "https://www.downtoearth.org.in/feed/",
}

IST = ZoneInfo("Asia/Kolkata")

# ==================== HELPER FUNCTIONS ====================

def get_article_hash(title: str, source: str) -> str:
    """Generate unique hash for article deduplication"""
    content = f"{title.lower().strip()}|{source.lower().strip()}"
    return hashlib.md5(content.encode()).hexdigest()

def is_recent_article(pub_date_str: str, hours: int = 24) -> bool:
    """Check if article was published within last N hours"""
    try:
        from email.utils import parsedate_to_datetime
        pub_date = parsedate_to_datetime(pub_date_str)
        now = datetime.now(IST).replace(tzinfo=None)
        pub_date = pub_date.replace(tzinfo=None)
        age = now - pub_date
        return age < timedelta(hours=hours)
    except:
        return True  # If parsing fails, include article

def escape_markdown(text: str) -> str:
    """Escape special characters for MarkdownV2"""
    if not text:
        return text
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

async def ask_claude(category: str, articles: List[Dict]) -> Optional[Dict]:
    """
    Send articles to Groq for intelligent curation and summarization
    Returns JSON with high-impact stories, summaries, and insights
    """
    if not GROQ_API_KEY:
        logger.warning("Groq API key not configured - set GROQ_API_KEY")
        return None

    try:
        # Format articles for Groq
        articles_text = "\n".join([
            f"- Title: {a.get('title', 'N/A')}\n"
            f"  Source: {a.get('source', 'N/A')}\n"
            f"  Link: {a.get('link', 'N/A')}\n"
            f"  Published: {a.get('published', 'N/A')}"
            for a in articles[:15]  # Send top 15 articles to Groq
        ])

        prompt = f"""You are a financial news curator. Analyze these {category} news articles and:

1. Identify the 3-5 MOST IMPORTANT stories (high impact on markets/business/economy)
2. For each story:
   - Write a 1-line concise headline
   - Write a 2-3 sentence summary explaining what happened
   - Explain "Why it matters" in 1 sentence (market impact)
   - Include the source and link

Format your response as JSON:
{{
  "stories": [
    {{
      "rank": 1,
      "title": "...",
      "summary": "...",
      "why_it_matters": "...",
      "source": "...",
      "link": "..."
    }}
  ]
}}

ARTICLES TO CURATE:
{articles_text}

Return ONLY the JSON, no additional text."""

        # Get Groq client
        client = get_groq_client()
        if not client:
            logger.error("Groq client failed to initialize")
            return None

        # Call Groq API in thread pool (it's a blocking call)
        def groq_call():
            return client.chat.completions.create(
                model="mixtral-8x7b-32768",
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

        try:
            # Run blocking Groq call in executor to avoid blocking event loop
            message = await asyncio.to_thread(groq_call)
            logger.info("✅ Groq API call successful")
        except Exception as groq_error:
            logger.error(f"Groq API call failed: {groq_error}")
            return None

        # Parse Groq response (different format than Claude)
        response_text = message.choices[0].message.content

        # Try to parse JSON response
        try:
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                data = json.loads(json_str)
                logger.info(f"✅ Successfully parsed {len(data.get('stories', []))} stories from Groq")
                return data
        except json.JSONDecodeError as json_err:
            logger.warning(f"Failed to parse Groq's JSON response: {json_err}")
            return None

        return None
    except Exception as e:
        logger.error(f"Groq API error: {e}", exc_info=True)
        return None

def format_curated_news(curated_data: Optional[Dict], category: str = "Global") -> str:
    """Format Groq-curated news into readable Telegram message with proper escaping"""
    if not curated_data:
        return "❌ Unable to curate news right now\\. Try again in a moment\\."

    try:
        message = f"📰 *TOP {category.upper()} NEWS* \\(AI\\-Curated\\)\n"
        message += "\\=" * 50 + "\n\n"

        stories = curated_data.get("stories", [])
        for story in stories:
            rank = escape_markdown(str(story.get('rank', '?')))
            title = escape_markdown(str(story.get('title', 'N/A')))
            summary = escape_markdown(str(story.get('summary', 'N/A')))
            why_matters = escape_markdown(str(story.get('why_it_matters', 'N/A')))
            source = escape_markdown(str(story.get('source', 'N/A')))
            link = escape_markdown(str(story.get('link', 'N/A')))

            message += f"*#{rank}\\. {title}*\n"
            message += f"📌 {summary}\n"
            message += f"💡 Why it matters: {why_matters}\n"
            message += f"Source: {source}\n"
            message += f"🔗 {link}\n\n"

        return message
    except Exception as e:
        logger.error(f"Error formatting curated news: {e}")
        return "Error formatting news\\. Please try again\\."

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

        message = "🪙 CRYPTO PRICES\n"
        for key, symbol in cryptos.items():
            if key in data:
                usd = data[key].get("usd", 0)
                inr = data[key].get("inr", 0)
                change = data[key].get("usd_24h_change", 0)

                emoji = "📈" if change > 0 else "📉"
                message += f"\n{symbol}: ${usd:,.0f} (₹{inr:,.0f}) {emoji} {change:+.2f}%"

        return message
    except Exception as e:
        logger.error(f"Crypto fetch error: {e}")
        return "*❌ Crypto Error:* API temporarily unavailable"


def fetch_stock_prices() -> str:
    """Fetch stock indices: Nifty 50, Sensex, S&P 500, NASDAQ, USDINR, Gold"""
    try:
        tickers = ["^NSEI", "^BSESN", "^GSPC", "^IXIC", "INR=X", "GC=F"]
        names = ["Nifty 50", "Sensex", "S&P 500", "NASDAQ", "USD/INR", "Gold"]

        message = "📊 STOCK INDICES\n"
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
                message += f"\n{name}: [Error]"

        return message
    except Exception as e:
        logger.error(f"Stock fetch error: {e}")
        return "*❌ Stock Error:* API temporarily unavailable"


# ==================== MOCK DATA FOR TESTING ====================
def get_mock_articles() -> List[Dict]:
    """Return sample articles for testing when feeds are unavailable"""
    return [
        {
            "title": "India's Tech Sector Sees 15% Growth in Q1 2026",
            "source": "Economic Times",
            "link": "https://economictimes.indiatimes.com/tech",
            "summary": "India's technology sector has grown by 15% YoY, driven by AI, cloud services, and startup ecosystem expansion.",
            "published": datetime.now(IST).isoformat(),
            "hash": "sample1"
        },
        {
            "title": "Renewable Energy Investment Hits Record $500 Billion Globally",
            "source": "Financial Times",
            "link": "https://ft.com/energy",
            "summary": "Global renewable energy investments have surged to $500B in 2026, led by solar and wind projects.",
            "published": datetime.now(IST).isoformat(),
            "hash": "sample2"
        },
        {
            "title": "Nifty 50 Breaks 28,000 Barrier on Strong Earnings",
            "source": "Livemint",
            "link": "https://livemint.com/markets",
            "summary": "The Nifty 50 index surged past 28,000 for the first time, fueled by strong corporate earnings.",
            "published": datetime.now(IST).isoformat(),
            "hash": "sample3"
        },
        {
            "title": "Tech Giants Invest $2 Billion in AI Research in India",
            "source": "TechCrunch",
            "link": "https://techcrunch.com/india",
            "summary": "Major tech companies are doubling down on AI research investments in India, creating 10,000+ jobs.",
            "published": datetime.now(IST).isoformat(),
            "hash": "sample4"
        },
        {
            "title": "Central Bank Signals Possible Rate Cuts by Mid-Year",
            "source": "Reuters",
            "link": "https://reuters.com/finance",
            "summary": "The RBI indicated potential interest rate reductions starting Q2 2026 if inflation continues easing.",
            "published": datetime.now(IST).isoformat(),
            "hash": "sample5"
        },
    ]

async def fetch_all_rss(max_per_source: int = 5, max_age_hours: int = 24, use_mock: bool = False) -> List[Dict]:
    """
    Fetch and deduplicate articles from all RSS feeds
    Returns: List of unique, recent articles with metadata
    Falls back to mock data if real feeds are unavailable
    """
    articles = []
    seen_hashes = set()
    feeds_tried = 0
    feeds_success = 0

    for source_name, feed_url in RSS_FEEDS.items():
        feeds_tried += 1
        try:
            feed = feedparser.parse(feed_url)
            entries = feed.get("entries", [])[:max_per_source]

            if not entries:
                continue

            feeds_success += 1

            for entry in entries:
                try:
                    title = entry.get("title", "")
                    link = entry.get("link", "")
                    published = entry.get("published", "")
                    summary = entry.get("summary", "")

                    if not title:
                        continue

                    # Filter by age (last 24 hours)
                    if published and not is_recent_article(published, max_age_hours):
                        continue

                    # Deduplicate using hash
                    article_hash = get_article_hash(title, source_name)
                    if article_hash in seen_hashes:
                        continue

                    seen_hashes.add(article_hash)

                    articles.append({
                        "title": title,
                        "link": link,
                        "source": source_name,
                        "published": published,
                        "summary": summary,
                        "hash": article_hash
                    })
                except Exception as e:
                    logger.warning(f"Error processing entry from {source_name}: {e}")
                    continue
        except Exception as e:
            logger.warning(f"RSS feed error for {source_name}: {e}")
            continue

    # Fallback to mock data if no real articles found
    if not articles or use_mock:
        logger.info(f"Using mock data ({feeds_success}/{feeds_tried} feeds successful)")
        articles = get_mock_articles()

    logger.info(f"Fetched {len(articles)} unique articles")
    return articles

def fetch_rss_plain(source: Optional[str] = None, max_articles: int = 10) -> str:
    """Fallback: Fetch and display raw RSS without Claude curation"""
    try:
        feeds_to_fetch = {source: RSS_FEEDS[source]} if source and source in RSS_FEEDS else RSS_FEEDS
        message = "*📰 TOP NEWS*\n"

        article_count = 0
        for feed_name, feed_url in feeds_to_fetch.items():
            try:
                feed = feedparser.parse(feed_url)
                entries = feed.get("entries", [])[:3]

                if entries:
                    message += f"\n*{feed_name}:*\n"
                    for entry in entries:
                        title = entry.get("title", "No title")[:70]
                        link = entry.get("link", "#")
                        message += f"• {title}\n🔗 {link}\n"
                        article_count += 1
                        if article_count >= max_articles:
                            break
                if article_count >= max_articles:
                    break
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

            return f"🎭 FEAR & GREED INDEX\n{emoji} {index}/100 - {label}"
        return "⚠️ Fear & Greed data unavailable"
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

async def morning_digest(bot) -> None:
    """8 AM IST - Crypto + Markets + Groq-curated Top News"""
    try:
        message = f"🌅 *GOOD MORNING\\!* ({datetime.now(IST).strftime('%I:%M %p IST')})\n"
        message += "\\=" * 60 + "\n\n"

        # Market data
        crypto = fetch_crypto_prices()
        stocks = fetch_stock_prices()
        fear_greed = fetch_fear_greed()

        message += f"{crypto}\n\n{stocks}\n\n{fear_greed}\n\n"

        # Add curated news if Groq available
        if GROQ_API_KEY:
            try:
                articles = await fetch_all_rss(max_per_source=4)
                if articles:
                    curated = await ask_claude("Global Business & Markets", articles)
                    if curated:
                        stories = curated.get("stories", [])[:3]  # Top 3 stories
                        message += "*📰 TODAY'S TOP NEWS* \\(AI\\-Curated\\)\n"
                        for story in stories:
                            title = escape_markdown(str(story.get('title', 'N/A')))
                            summary = escape_markdown(str(story.get('summary', 'N/A')))
                            why_matters = escape_markdown(str(story.get('why_it_matters', 'N/A')))
                            message += f"\n*{title}*\n"
                            message += f"📌 {summary}\n"
                            message += f"💡 Why it matters: {why_matters}\n"
            except Exception as e:
                logger.warning(f"Groq integration in morning digest failed: {e}")
                message += fetch_rss_plain()
        else:
            message += fetch_rss_plain()

        await bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode=ParseMode.MARKDOWN_V2
        )
        logger.info("Morning digest sent successfully")
    except Exception as e:
        logger.error(f"Morning digest error: {e}")
        # Send simplified version on error
        try:
            await bot.send_message(
                chat_id=CHAT_ID,
                text="🌅 Morning digest: Markets data available. News curation temporarily unavailable."
            )
        except:
            pass


async def midday_digest(bot) -> None:
    """1 PM IST - Markets Update + Crypto"""
    try:
        message = f"📈 MIDDAY MARKETS UPDATE ({datetime.now(IST).strftime('%I:%M %p IST')})\n\n"

        stocks = fetch_stock_prices()
        crypto = fetch_crypto_prices()

        message += f"{stocks}\n\n{crypto}"

        await bot.send_message(
            chat_id=CHAT_ID,
            text=message
        )
        logger.info("Midday digest sent successfully")
    except Exception as e:
        logger.error(f"Midday digest error: {e}")


async def evening_digest(bot) -> None:
    """7 PM IST - Markets Close + News Wrap + F&G"""
    try:
        message = f"🌆 EVENING WRAP UP ({datetime.now(IST).strftime('%I:%M %p IST')})\n\n"

        stocks = fetch_stock_prices()
        fear_greed = fetch_fear_greed()
        news = fetch_rss_plain()

        message += f"{stocks}\n\n{fear_greed}\n\n{news}"

        await bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode=ParseMode.MARKDOWN_V2
        )
        logger.info("Evening digest sent successfully")
    except Exception as e:
        logger.error(f"Evening digest error: {e}")


# ==================== COMMAND HANDLERS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    try:
        user = update.effective_user
        message = f"👋 Welcome {user.first_name}!\n\nDaily Market & News Digest Bot\n\nUse /help to see all commands."
        await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Start error: {e}")
        await update.message.reply_text(f"Error: {str(e)}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    try:
        message = """📋 AVAILABLE COMMANDS

/start - Welcome message
/help - Show this menu
/news - Latest top news from all sources
/market - Stock indices update
/crypto - Cryptocurrency prices
/stocks - Detailed market indices
/india - India breaking news (if enabled)
/cat - CAT GK preparation digest
/morning - Get morning digest now
/evening - Get evening digest now

Data updates automatically at 8 AM, 1 PM, 7 PM IST"""
        await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Help error: {e}")
        await update.message.reply_text(f"Error: {str(e)}")


async def news(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /news command - Groq-curated global news"""
    try:
        await update.message.chat.send_action(ChatAction.TYPING)

        # Fetch articles from all RSS feeds
        articles = await fetch_all_rss(max_per_source=5)

        if not articles:
            await update.message.reply_text("No recent articles found. Try again in a moment.")
            return

        # Try Groq curation first
        if GROQ_API_KEY:
            curated = await ask_claude("Global Business & Markets", articles)
            if curated:
                message = format_curated_news(curated, "Global Business & Markets")
                await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)
                return

        # Fallback to plain RSS if Groq fails
        message = fetch_rss_plain()
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        logger.error(f"News error: {e}")
        await update.message.reply_text("❌ Error fetching news. Try again later.")


async def market(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /market command"""
    try:
        await update.message.chat.send_action(ChatAction.TYPING)
        message = fetch_stock_prices()
        await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Market error: {e}")
        await update.message.reply_text("❌ Error: API temporarily unavailable")


async def crypto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /crypto command"""
    try:
        await update.message.chat.send_action(ChatAction.TYPING)
        message = fetch_crypto_prices()
        await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Crypto error: {e}")
        await update.message.reply_text("❌ Error: API temporarily unavailable")


async def stocks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stocks command"""
    try:
        await update.message.chat.send_action(ChatAction.TYPING)
        message = fetch_stock_prices()
        await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Stocks error: {e}")
        await update.message.reply_text("❌ Error: API temporarily unavailable")


async def india(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /india command - India-focused news with Groq curation"""
    try:
        await update.message.chat.send_action(ChatAction.TYPING)

        # First try NewsData API if configured
        india_news = fetch_india_news()
        if india_news:
            await update.message.reply_text(india_news, parse_mode=ParseMode.MARKDOWN_V2)
            return

        # Fallback to filtering RSS feeds for India-focused content
        if GROQ_API_KEY:
            articles = await fetch_all_rss(max_per_source=5)
            india_articles = [a for a in articles if any(
                keyword in a['source'].lower()
                for keyword in ['hindu', 'livemint', 'india', 'mint']
            )]

            if india_articles:
                curated = await ask_claude("India Business & Markets", india_articles)
                if curated:
                    message = format_curated_news(curated, "India Business & Markets")
                    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)
                    return

        # Ultimate fallback
        message = """🇮🇳 *INDIA NEWS & MARKETS*

India news requires either:
1. NEWSDATA_KEY environment variable (for breaking news)
2. Or use /news for India\\-focused stories from premium RSS feeds

Premium Sources: The Hindu, Livemint, CNBC\\-TV18, Moneycontrol"""
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)

    except Exception as e:
        logger.error(f"India error: {e}")
        await update.message.reply_text("❌ Error fetching India news. Try again later.")


async def cat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /cat command - Groq-curated CAT GK preparation digest"""
    try:
        await update.message.chat.send_action(ChatAction.TYPING)

        # Fetch articles relevant to CAT preparation
        articles = await fetch_all_rss(max_per_source=5)

        if not articles or not GROQ_API_KEY:
            message = """🎓 CAT GK DIGEST

📚 Daily current affairs and GK topics for CAT preparation:

Key Categories:
• Economics & Policy Changes
• Business & Market News
• Government Initiatives
• Sustainability & Environment
• Technology & Innovation

Tip: Read 10-15 articles daily for CAT GK section mastery.
Follow: Reuters, The Hindu, Livemint for best coverage."""
            await update.message.reply_text(message)
            return

        # Get Groq to curate CAT-relevant content
        cat_prompt = """You are a CAT (Common Admission Test) exam preparation expert.

From these news articles, identify stories MOST RELEVANT for CAT General Knowledge section.
Focus on: Economics, Business, Government policies, Environment, Technology trends.

For each selected story:
1. Headline
2. Why it's important for CAT (in 1 sentence)
3. Key facts/statistics a CAT aspirant should know
4. Source

Return JSON format:
{
  "stories": [
    {
      "title": "...",
      "cat_relevance": "...",
      "key_facts": "...",
      "source": "...",
      "link": "..."
    }
  ]
}

Articles: """ + "\n".join([f"- {a['title']} (Source: {a['source']})" for a in articles[:10]])

        # Get Groq client
        client = get_groq_client()
        if not client:
            logger.error("Groq client failed to initialize for CAT command")
            message = """🎓 CAT GK DIGEST

Daily current affairs preparation from top news sources.
Covers: Economics, Policy, Business, Environment, Tech."""
            await update.message.reply_text(message)
            return

        # Call Groq API in thread pool (it's a blocking call)
        def groq_cat_call():
            return client.chat.completions.create(
                model="mixtral-8x7b-32768",
                max_tokens=1200,
                messages=[
                    {"role": "user", "content": cat_prompt}
                ]
            )

        try:
            # Run blocking Groq call in executor to avoid blocking event loop
            response = await asyncio.to_thread(groq_cat_call)
            logger.info("✅ Groq API call for CAT successful")
        except Exception as groq_error:
            logger.error(f"Groq CAT API call failed: {groq_error}")
            message = """🎓 CAT GK DIGEST

Daily current affairs preparation from top news sources.
Covers: Economics, Policy, Business, Environment, Tech."""
            await update.message.reply_text(message)
            return

        # Parse Groq response (different format than Claude)
        response_text = response.choices[0].message.content

        # Parse and format response
        try:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                data = json.loads(json_str)

                msg = "🎓 *CAT GK DIGEST* \\(AI\\-Curated\\)\n"
                msg += "\\=" * 50 + "\n\n"

                for story in data.get("stories", []):
                    title = escape_markdown(str(story.get('title', 'N/A')))
                    cat_relevance = escape_markdown(str(story.get('cat_relevance', 'N/A')))
                    key_facts = escape_markdown(str(story.get('key_facts', 'N/A')))
                    source = escape_markdown(str(story.get('source', 'N/A')))
                    link = escape_markdown(str(story.get('link', 'N/A')))

                    msg += f"*{title}*\n"
                    msg += f"📌 CAT Relevance: {cat_relevance}\n"
                    msg += f"📚 Key Facts: {key_facts}\n"
                    msg += f"Source: {source}\n"
                    msg += f"🔗 {link}\n\n"

                await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN_V2)
                return
        except json.JSONDecodeError:
            logger.warning("Failed to parse Groq's JSON response for CAT")

        # Fallback message
        message = """🎓 CAT GK DIGEST

Daily current affairs preparation from top news sources.
Covers: Economics, Policy, Business, Environment, Tech."""
        await update.message.reply_text(message)

    except Exception as e:
        logger.error(f"CAT error: {e}")
        await update.message.reply_text("❌ Error preparing CAT digest. Try again later.")


async def morning(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /morning command"""
    try:
        await update.message.chat.send_action(ChatAction.TYPING)
        await morning_digest(context.bot)
    except Exception as e:
        logger.error(f"Morning command error: {e}")
        error_msg = escape_markdown(str(e))
        await update.message.reply_text(f"❌ Error: {error_msg}")


async def evening(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /evening command"""
    try:
        await update.message.chat.send_action(ChatAction.TYPING)
        await evening_digest(context.bot)
    except Exception as e:
        logger.error(f"Evening command error: {e}")
        error_msg = escape_markdown(str(e))
        await update.message.reply_text(f"❌ Error: {error_msg}")


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

    # Handle graceful shutdown on SIGTERM (Railway sends this signal before killing)
    def shutdown_handler(signum, frame):
        logger.info("🛑 Received shutdown signal, stopping gracefully...")
        application.stop()
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

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

    # Start bot with error handling
    logger.info("🤖 Bot is running... Press Ctrl+C to stop.")
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
