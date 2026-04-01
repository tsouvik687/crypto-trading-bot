"""
Global Stock Market Client
Yahoo Finance (FREE) — No API Key needed!
US, India NSE/BSE, UK, Japan, Germany, Index Futures
"""
import aiohttp
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# ═══ Symbol Reference ═══
POPULAR_STOCKS = {
    # 🇺🇸 US Stocks
    "AAPL": "Apple Inc",
    "TSLA": "Tesla Inc",
    "GOOGL": "Alphabet (Google)",
    "MSFT": "Microsoft",
    "AMZN": "Amazon",
    "NVDA": "NVIDIA",
    "META": "Meta (Facebook)",
    "NFLX": "Netflix",
    "AMD": "AMD",
    "BABA": "Alibaba",

    # 🇮🇳 India NSE
    "RELIANCE.NS": "Reliance Industries",
    "TCS.NS": "Tata Consultancy Services",
    "INFY.NS": "Infosys",
    "HDFCBANK.NS": "HDFC Bank",
    "ICICIBANK.NS": "ICICI Bank",
    "SBIN.NS": "State Bank of India",
    "WIPRO.NS": "Wipro",
    "TATAMOTORS.NS": "Tata Motors",
    "ADANIENT.NS": "Adani Enterprises",
    "BAJFINANCE.NS": "Bajaj Finance",

    # 🌍 Global
    "HSBA.L": "HSBC (London)",
    "BP.L": "BP (London)",
    "VOW3.DE": "Volkswagen (Germany)",
    "SAP.DE": "SAP (Germany)",
    "7203.T": "Toyota (Japan)",
    "9984.T": "SoftBank (Japan)",

    # 📈 Index Futures
    "^NSEI": "Nifty 50",
    "^BSESN": "BSE Sensex",
    "^GSPC": "S&P 500",
    "^DJI": "Dow Jones",
    "^IXIC": "NASDAQ",
    "^FTSE": "FTSE 100 (UK)",
    "^N225": "Nikkei 225 (Japan)",
    "^GDAXI": "DAX (Germany)",
}

INTERVAL_MAP = {
    "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
    "1h": "60m", "4h": "1h", "1d": "1d", "1w": "1wk"
}

PERIOD_MAP = {
    "1m": "1d", "5m": "5d", "15m": "5d", "30m": "1mo",
    "1h": "1mo", "4h": "3mo", "1d": "1y", "1w": "2y"
}

class StockClient:
    def __init__(self):
        self.base_url = "https://query1.finance.yahoo.com"
        self.session = None

    async def _get_session(self):
        if self.session is None or self.session.closed:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    def _format_symbol(self, symbol: str) -> str:
        """Symbol format করো"""
        symbol = symbol.upper().strip()
        # India NSE — .NS যোগ করো যদি না থাকে এবং Indian stock মনে হয়
        return symbol

    async def get_klines(self, symbol: str, interval: str = "1h", limit: int = 100) -> pd.DataFrame:
        """OHLCV data from Yahoo Finance"""
        session = await self._get_session()
        symbol = self._format_symbol(symbol)

        yf_interval = INTERVAL_MAP.get(interval, "60m")
        yf_period = PERIOD_MAP.get(interval, "1mo")

        url = f"{self.base_url}/v8/finance/chart/{symbol}"
        params = {
            "interval": yf_interval,
            "range": yf_period,
            "includePrePost": "false"
        }

        async with session.get(url, params=params) as resp:
            if resp.status != 200:
                raise Exception(f"Symbol '{symbol}' পাওয়া যায়নি! Status: {resp.status}")
            data = await resp.json()

        result = data.get("chart", {}).get("result", [])
        if not result:
            raise Exception(f"'{symbol}' এর data নেই!")

        chart = result[0]
        timestamps = chart["timestamp"]
        ohlcv = chart["indicators"]["quote"][0]

        df = pd.DataFrame({
            "timestamp": pd.to_datetime(timestamps, unit="s"),
            "open":   [float(x) if x else None for x in ohlcv.get("open", [])],
            "high":   [float(x) if x else None for x in ohlcv.get("high", [])],
            "low":    [float(x) if x else None for x in ohlcv.get("low", [])],
            "close":  [float(x) if x else None for x in ohlcv.get("close", [])],
            "volume": [float(x) if x else 0 for x in ohlcv.get("volume", [])],
        })

        df.dropna(subset=["open", "high", "low", "close"], inplace=True)
        df.set_index("timestamp", inplace=True)
        return df[["open", "high", "low", "close", "volume"]].tail(limit)

    async def get_ticker(self, symbol: str) -> dict:
        """Live stock price & stats"""
        session = await self._get_session()
        symbol = self._format_symbol(symbol)

        url = f"{self.base_url}/v8/finance/chart/{symbol}"
        params = {"interval": "1d", "range": "5d"}

        async with session.get(url, params=params) as resp:
            if resp.status != 200:
                raise Exception(f"Symbol '{symbol}' পাওয়া যায়নি!")
            data = await resp.json()

        result = data.get("chart", {}).get("result", [])
        if not result:
            raise Exception(f"'{symbol}' এর data নেই!")

        meta = result[0].get("meta", {})
        price = float(meta.get("regularMarketPrice", 0))
        prev_close = float(meta.get("chartPreviousClose", price))
        change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0
        currency = meta.get("currency", "USD")

        # High/Low from recent data
        quotes = result[0]["indicators"]["quote"][0]
        highs = [x for x in quotes.get("high", []) if x]
        lows = [x for x in quotes.get("low", []) if x]
        volumes = [x for x in quotes.get("volume", []) if x]

        return {
            "symbol": symbol,
            "name": POPULAR_STOCKS.get(symbol, symbol),
            "price": price,
            "prev_close": prev_close,
            "change_24h": change_pct,
            "high_24h": max(highs[-1:]) if highs else price,
            "low_24h": min(lows[-1:]) if lows else price,
            "volume_24h": sum(volumes[-1:]) if volumes else 0,
            "quote_volume": price * sum(volumes[-1:]) if volumes else 0,
            "currency": currency,
            "market": self._detect_market(symbol),
            "exchange": meta.get("exchangeName", "Unknown"),
        }

    def _detect_market(self, symbol: str) -> str:
        if symbol.endswith(".NS") or symbol.endswith(".BO"):
            return "🇮🇳 India"
        elif symbol.endswith(".L"):
            return "🇬🇧 London"
        elif symbol.endswith(".DE"):
            return "🇩🇪 Germany"
        elif symbol.endswith(".T"):
            return "🇯🇵 Japan"
        elif symbol.startswith("^"):
            return "📈 Index"
        else:
            return "🇺🇸 US"

    async def get_orderbook(self, symbol: str, limit: int = 5) -> dict:
        """Approximate orderbook from price"""
        ticker = await self.get_ticker(symbol)
        price = ticker['price']
        return {
            "bids": [(price * (1 - i*0.001), 100) for i in range(1, limit+1)],
            "asks": [(price * (1 + i*0.001), 100) for i in range(1, limit+1)],
        }

    async def validate_symbol(self, symbol: str) -> bool:
        try:
            await self.get_ticker(symbol)
            return True
        except:
            return False

    async def get_market_overview(self) -> dict:
        """Major indices overview"""
        indices = {
            "🇮🇳 Nifty 50": "^NSEI",
            "🇮🇳 Sensex": "^BSESN",
            "🇺🇸 S&P 500": "^GSPC",
            "🇺🇸 NASDAQ": "^IXIC",
            "🇺🇸 Dow Jones": "^DJI",
            "🇬🇧 FTSE 100": "^FTSE",
            "🇯🇵 Nikkei": "^N225",
            "🇩🇪 DAX": "^GDAXI",
        }

        results = {}
        for name, sym in indices.items():
            try:
                ticker = await self.get_ticker(sym)
                results[name] = ticker
                await asyncio.sleep(0.3)  # Rate limit
            except Exception as e:
                logger.error(f"Index error {sym}: {e}")

        return results

    async def get_top_movers(self) -> tuple:
        """Top gainers/losers from popular stocks"""
        movers = []
        all_stocks = list(POPULAR_STOCKS.keys())[:20]

        for sym in all_stocks:
            try:
                ticker = await self.get_ticker(sym)
                movers.append(ticker)
                await asyncio.sleep(0.2)
            except:
                pass

        movers.sort(key=lambda x: x['change_24h'], reverse=True)
        gainers = movers[:5]
        losers = movers[-5:]

        # Format for compatibility
        def fmt(t):
            return {
                "symbol": t['symbol'],
                "lastPrice": str(t['price']),
                "priceChangePercent": str(t['change_24h']),
                "quoteVolume": str(t['quote_volume']),
                "name": t.get('name', t['symbol']),
                "market": t.get('market', ''),
            }

        return [fmt(g) for g in gainers], [fmt(l) for l in losers]


# Singleton
stock_client = StockClient()
