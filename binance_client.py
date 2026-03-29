"""
Binance Free API Client
No API key required for public market data!
"""
import aiohttp
import asyncio
import pandas as pd
from datetime import datetime
from config import config
import logging

logger = logging.getLogger(__name__)

class BinanceClient:
    def __init__(self):
        self.base_url = config.BINANCE_BASE_URL
        self.session = None

    async def _get_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def get_klines(self, symbol: str, interval: str = "1h", limit: int = 100) -> pd.DataFrame:
        """Candlestick/OHLCV data fetch করো (FREE)"""
        session = await self._get_session()
        url = f"{self.base_url}/api/v3/klines"
        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": limit
        }
        
        async with session.get(url, params=params) as resp:
            if resp.status != 200:
                raise Exception(f"Binance API Error: {resp.status}")
            data = await resp.json()
        
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        df.set_index('timestamp', inplace=True)
        return df[['open', 'high', 'low', 'close', 'volume']]

    async def get_ticker(self, symbol: str) -> dict:
        """Live price + 24h stats (FREE)"""
        session = await self._get_session()
        url = f"{self.base_url}/api/v3/ticker/24hr"
        params = {"symbol": symbol.upper()}
        
        async with session.get(url, params=params) as resp:
            if resp.status != 200:
                raise Exception(f"Symbol '{symbol}' পাওয়া যায়নি!")
            data = await resp.json()
        
        return {
            "symbol": data["symbol"],
            "price": float(data["lastPrice"]),
            "change_24h": float(data["priceChangePercent"]),
            "high_24h": float(data["highPrice"]),
            "low_24h": float(data["lowPrice"]),
            "volume_24h": float(data["volume"]),
            "quote_volume": float(data["quoteVolume"]),
        }

    async def get_orderbook(self, symbol: str, limit: int = 5) -> dict:
        """Order book data (FREE)"""
        session = await self._get_session()
        url = f"{self.base_url}/api/v3/depth"
        params = {"symbol": symbol.upper(), "limit": limit}
        
        async with session.get(url, params=params) as resp:
            data = await resp.json()
        
        return {
            "bids": [(float(p), float(q)) for p, q in data["bids"]],
            "asks": [(float(p), float(q)) for p, q in data["asks"]]
        }

    async def get_recent_trades(self, symbol: str, limit: int = 10) -> list:
        """সাম্প্রতিক trades (FREE)"""
        session = await self._get_session()
        url = f"{self.base_url}/api/v3/trades"
        params = {"symbol": symbol.upper(), "limit": limit}
        
        async with session.get(url, params=params) as resp:
            data = await resp.json()
        
        return data

    async def validate_symbol(self, symbol: str) -> bool:
        """Symbol valid কিনা চেক করো"""
        try:
            await self.get_ticker(symbol)
            return True
        except:
            return False

    async def get_top_movers(self) -> list:
        """Top gainers/losers"""
        session = await self._get_session()
        url = f"{self.base_url}/api/v3/ticker/24hr"
        
        async with session.get(url) as resp:
            data = await resp.json()
        
        usdt_pairs = [
            d for d in data 
            if d["symbol"].endswith("USDT") and float(d["quoteVolume"]) > 1000000
        ]
        
        sorted_by_change = sorted(
            usdt_pairs, 
            key=lambda x: float(x["priceChangePercent"]), 
            reverse=True
        )
        
        gainers = sorted_by_change[:5]
        losers = sorted_by_change[-5:]
        
        return gainers, losers


# Singleton instance
binance = BinanceClient()
