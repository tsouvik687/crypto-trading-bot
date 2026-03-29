#!/usr/bin/env python3
"""
🤖 Advanced AI Crypto Trading Telegram Bot
Uses: Binance API (Free) + Claude AI + Telegram Bot API
"""

import logging
import asyncio
from telegram_bot import CryptoTradingBot

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    print("""
    ╔══════════════════════════════════════════╗
    ║   🚀 AI Crypto Trading Bot Starting...   ║
    ║   📊 Powered by Claude AI + Binance      ║
    ╚══════════════════════════════════════════╝
    """)
    
    bot = CryptoTradingBot()
    bot.run()

if __name__ == '__main__':
    main()
