"""
Configuration Management
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ═══ Telegram ═══
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # ═══ Google Gemini API ═══
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    # ═══ Binance (FREE - No API key needed for public data) ═══
    BINANCE_BASE_URL = "https://api.binance.com"
    BINANCE_WS_URL = "wss://stream.binance.com:9443/ws"
    
    # ═══ Default Settings ═══
    DEFAULT_INTERVAL = "1h"
    DEFAULT_LIMIT = 100  # candles
    
    INTERVALS = {
        "1m": "1 মিনিট", "5m": "5 মিনিট", "15m": "15 মিনিট",
        "30m": "30 মিনিট", "1h": "1 ঘন্টা", "4h": "4 ঘন্টা",
        "1d": "1 দিন", "1w": "1 সপ্তাহ"
    }
    
    # ═══ Alert Check Interval (seconds) ═══
    ALERT_CHECK_INTERVAL = 30
    LIVE_MONITOR_INTERVAL = 60  # 1 minute
    
    # ═══ Popular Coins ═══
    POPULAR_PAIRS = [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT",
        "ADAUSDT", "DOGEUSDT", "XRPUSDT", "DOTUSDT"
    ]

config = Config()
