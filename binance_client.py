"""
CoinGecko Free API Client
কোনো block নেই - সব দেশে কাজ করে!
"""
import aiohttp
import asyncio
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# CoinGecko symbol map
SYMBOL_MAP = {
    "BTCUSDT": "bitcoin",
    "ETHUSDT": "ethereum",
    "BNBUSDT": "binancecoin",
    "SOLUSDT": "solana",
    "ADAUSDT": "cardano",
    "DOGEUSDT": "dogecoin",
    "XRPUSDT": "ripple",
    "DOTUSDT": "polkadot",
    "MATICUSDT": "matic-network",
    "LTCUSDT": "litecoin",
    "AVAXUSDT": "avalanche-2",
    "LINKUSDT": "chainlink",
    "UNIUSDT": "uniswap",
    "ATOMUSDT": "cosmos",
    "TRXUSDT": "tron",
}

INTERVAL_MAP = {
    "1m": 1, "5m": 1, "15m": 1, "30m": 1,
    "1h": 1, "4h": 7, "1d": 30, "1w": 90
}

class BinanceClient:
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.session = None

    def _get_coin_id(self, symbol: str) -> str:
        symbol = symbol.upper().replace("USDT", "") + "USDT"
        if symbol in SYMBOL_MAP:
            return SYMBOL_MAP[symbol]
        # Try direct match
        base = symbol.upper().replace("USDT", "").lower()
        return base

    async def _get_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def get_klines(self, symbol: str, interval: str = "1h", limit: int = 100) -> pd.DataFrame:
        """OHLCV candlestick data from CoinGecko"""
        session = await self._get_session()
        coin_id = self._get_coin_id(symbol)
        days = INTERVAL_MAP.get(interval, 1)

        url = f"{self.base_url}/coins/{coin_id}/ohlc"
        params = {"vs_currency": "usd", "days": days}

        async with session.get(url, params=params) as resp:
            if resp.status == 404:
                raise Exception(f"Symbol '{symbol}' পাওয়া যায়নি!")
            if resp.status != 200:
                raise Exception(f"CoinGecko API Error: {resp.status}")
            data = await resp.json()

        if not data:
            raise Exception(f"কোনো data পাওয়া যায়নি!")

        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['volume'] = df['close'] * 1000  # approximate
        for col in ['open', 'high', 'low', 'close']:
            df[col] = df[col].astype(float)
        df.set_index('timestamp', inplace=True)

        return df[['open', 'high', 'low', 'close', 'volume']].tail(limit)

    async def get_ticker(self, symbol: str) -> dict:
        """Live price from CoinGecko"""
        session = await self._get_session()
        coin_id = self._get_coin_id(symbol)

        url = f"{self.base_url}/coins/{coin_id}"
        params = {"localization": "false", "tickers": "false", "community_data": "false"}

        async with session.get(url, params=params) as resp:
            if resp.status == 404:
                raise Exception(f"Symbol '{symbol}' পাওয়া যায়নি!")
            data = await resp.json()

        market = data.get("market_data", {})
        return {
            "symbol": symbol.upper(),
            "price": float(market.get("current_price", {}).get("usd", 0)),
            "change_24h": float(market.get("price_change_percentage_24h", 0) or 0),
            "high_24h": float(market.get("high_24h", {}).get("usd", 0)),
            "low_24h": float(market.get("low_24h", {}).get("usd", 0)),
            "volume_24h": float(market.get("total_volume", {}).get("usd", 0)),
            "quote_volume": float(market.get("total_volume", {}).get("usd", 0)),
        }

    async def get_orderbook(self, symbol: str, limit: int = 5) -> dict:
        """Approximate orderbook"""
        ticker = await self.get_ticker(symbol)
        price = ticker['price']
        return {
            "bids": [(price * (1 - i*0.001), 1.0) for i in range(1, limit+1)],
            "asks": [(price * (1 + i*0.001), 1.0) for i in range(1, limit+1)],
        }

    async def validate_symbol(self, symbol: str) -> bool:
        try:
            await self.get_ticker(symbol)
            return True
        except:
            return False

    async def get_top_movers(self) -> tuple:
        """Top gainers and losers"""
        session = await self._get_session()
        url = f"{self.base_url}/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 50,
            "page": 1,
            "price_change_percentage": "24h"
        }

        async with session.get(url, params=params) as resp:
            data = await resp.json()

        sorted_data = sorted(
            data,
            key=lambda x: x.get("price_change_percentage_24h") or 0,
            reverse=True
        )

        gainers_raw = sorted_data[:5]
        losers_raw = sorted_data[-5:]

        def format_coin(c):
            return {
                "symbol": c["symbol"].upper() + "USDT",
                "lastPrice": str(c.get("current_price", 0)),
                "priceChangePercent": str(c.get("price_change_percentage_24h", 0) or 0),
                "quoteVolume": str(c.get("total_volume", 0) or 0),
            }

        gainers = [format_coin(c) for c in gainers_raw]
        losers = [format_coin(c) for c in losers_raw]

        return gainers, losers

    async def get_recent_trades(self, symbol: str, limit: int = 10) -> list:
        return []


# Singleton
binance = BinanceClient()


