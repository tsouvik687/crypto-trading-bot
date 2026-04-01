"""
India Options & Futures Client
NSE Free API — No paid subscription needed!
Nifty, BankNifty, Sensex Options Chain + Futures
"""
import aiohttp
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)

# NSE Headers (required to bypass bot detection)
NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.nseindia.com/",
    "Connection": "keep-alive",
}

# Popular symbols
INDEX_SYMBOLS = {
    "NIFTY": "NIFTY 50",
    "BANKNIFTY": "NIFTY BANK",
    "FINNIFTY": "NIFTY FIN SERVICE",
    "MIDCPNIFTY": "NIFTY MIDCAP SELECT",
    "SENSEX": "BSE SENSEX",
}

EQUITY_OPTIONS = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK",
    "SBIN", "WIPRO", "TATAMOTORS", "BAJFINANCE", "ADANIENT",
    "HINDUNILVR", "KOTAKBANK", "LT", "AXISBANK", "MARUTI"
]


class IndiaOptionsClient:
    def __init__(self):
        self.nse_base = "https://www.nseindia.com"
        self.session = None
        self._session_initialized = False

    async def _get_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(headers=NSE_HEADERS)
            # Initialize NSE session (required!)
            try:
                async with self.session.get(
                    f"{self.nse_base}/",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    pass
                self._session_initialized = True
            except:
                pass
        return self.session

    async def get_options_chain(self, symbol: str) -> dict:
        """NSE Options Chain — Complete OI, IV, Greeks"""
        session = await self._get_session()
        symbol = symbol.upper().strip()

        # Determine if index or equity
        if symbol in INDEX_SYMBOLS:
            url = f"{self.nse_base}/api/option-chain-indices?symbol={symbol}"
        else:
            url = f"{self.nse_base}/api/option-chain-equities?symbol={symbol}"

        try:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"NSE API Error: {resp.status}")
                data = await resp.json(content_type=None)

            return self._parse_options_chain(data, symbol)

        except Exception as e:
            logger.error(f"Options chain error: {e}")
            # Fallback to alternative
            return await self._get_options_fallback(symbol)

    def _parse_options_chain(self, data: dict, symbol: str) -> dict:
        """Parse NSE options chain data"""
        records = data.get("records", {})
        filtered = data.get("filtered", {})

        # Current price
        underlying_value = records.get("underlyingValue", 0)
        expiry_dates = records.get("expiryDates", [])
        data_list = records.get("data", [])

        # Organize by expiry
        options_by_expiry = {}
        total_call_oi = 0
        total_put_oi = 0
        max_call_oi = {"strike": 0, "oi": 0}
        max_put_oi = {"strike": 0, "oi": 0}

        for item in data_list:
            expiry = item.get("expiryDate", "")
            strike = item.get("strikePrice", 0)

            if expiry not in options_by_expiry:
                options_by_expiry[expiry] = []

            ce = item.get("CE", {})
            pe = item.get("PE", {})

            row = {
                "strike": strike,
                "ce_oi": ce.get("openInterest", 0),
                "ce_chg_oi": ce.get("changeinOpenInterest", 0),
                "ce_volume": ce.get("totalTradedVolume", 0),
                "ce_iv": ce.get("impliedVolatility", 0),
                "ce_ltp": ce.get("lastPrice", 0),
                "ce_bid": ce.get("bidprice", 0),
                "ce_ask": ce.get("askPrice", 0),
                "pe_oi": pe.get("openInterest", 0),
                "pe_chg_oi": pe.get("changeinOpenInterest", 0),
                "pe_volume": pe.get("totalTradedVolume", 0),
                "pe_iv": pe.get("impliedVolatility", 0),
                "pe_ltp": pe.get("lastPrice", 0),
                "pe_bid": pe.get("bidprice", 0),
                "pe_ask": pe.get("askPrice", 0),
            }

            options_by_expiry[expiry].append(row)

            # Track max OI for support/resistance
            if ce.get("openInterest", 0) > max_call_oi["oi"]:
                max_call_oi = {"strike": strike, "oi": ce.get("openInterest", 0)}
            if pe.get("openInterest", 0) > max_put_oi["oi"]:
                max_put_oi = {"strike": strike, "oi": pe.get("openInterest", 0)}

            total_call_oi += ce.get("openInterest", 0)
            total_put_oi += pe.get("openInterest", 0)

        # PCR calculation
        pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 0

        # ATM strike
        atm_strike = round(underlying_value / 50) * 50 if underlying_value > 1000 else round(underlying_value / 100) * 100

        return {
            "symbol": symbol,
            "underlying_value": underlying_value,
            "expiry_dates": expiry_dates[:6],  # Next 6 expiries
            "options": options_by_expiry,
            "pcr": pcr,
            "total_call_oi": total_call_oi,
            "total_put_oi": total_put_oi,
            "max_call_oi_strike": max_call_oi["strike"],  # Resistance
            "max_put_oi_strike": max_put_oi["strike"],    # Support
            "atm_strike": atm_strike,
        }

    async def _get_options_fallback(self, symbol: str) -> dict:
        """Fallback using Yahoo Finance options data"""
        try:
            # Map NSE symbol to Yahoo
            yf_map = {
                "NIFTY": "^NSEI",
                "BANKNIFTY": "^NSEBANK",
                "SENSEX": "^BSESN",
            }
            yf_sym = yf_map.get(symbol, f"{symbol}.NS")

            session = await self._get_session()
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yf_sym}"
            params = {"interval": "1d", "range": "1d"}

            async with session.get(url, params=params) as resp:
                data = await resp.json()

            meta = data["chart"]["result"][0]["meta"]
            price = float(meta.get("regularMarketPrice", 0))

            # Generate synthetic options data for analysis
            return {
                "symbol": symbol,
                "underlying_value": price,
                "expiry_dates": [],
                "options": {},
                "pcr": 1.0,
                "total_call_oi": 0,
                "total_put_oi": 0,
                "max_call_oi_strike": price * 1.02,
                "max_put_oi_strike": price * 0.98,
                "atm_strike": round(price / 50) * 50,
                "note": "Fallback data — NSE API unavailable"
            }
        except Exception as e:
            raise Exception(f"Options data unavailable: {e}")

    async def get_nse_market_status(self) -> dict:
        """NSE Market status + indices"""
        session = await self._get_session()

        try:
            url = f"{self.nse_base}/api/allIndices"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json(content_type=None)

            indices = {}
            for item in data.get("data", []):
                name = item.get("indexSymbol", "")
                if name in ["NIFTY 50", "NIFTY BANK", "NIFTY IT", "NIFTY PHARMA",
                            "NIFTY AUTO", "NIFTY FMCG", "NIFTY METAL", "INDIA VIX"]:
                    indices[name] = {
                        "last": item.get("last", 0),
                        "change": item.get("change", 0),
                        "pChange": item.get("pChange", 0),
                        "high": item.get("high", 0),
                        "low": item.get("low", 0),
                        "open": item.get("open", 0),
                    }

            return indices

        except Exception as e:
            logger.error(f"NSE status error: {e}")
            return {}

    async def get_india_vix(self) -> dict:
        """India VIX — Fear/Greed index"""
        indices = await self.get_nse_market_status()
        vix_data = indices.get("INDIA VIX", {})

        vix = vix_data.get("last", 0)
        vix_change = vix_data.get("pChange", 0)

        if vix > 0:
            if vix < 12:
                sentiment = "😴 Extremely Low Fear — Market Complacent"
                market_outlook = "BULLISH"
            elif vix < 16:
                sentiment = "😊 Low Volatility — Stable Market"
                market_outlook = "BULLISH"
            elif vix < 20:
                sentiment = "😐 Normal — Watch carefully"
                market_outlook = "NEUTRAL"
            elif vix < 25:
                sentiment = "😟 Elevated Fear — Volatile market"
                market_outlook = "BEARISH"
            elif vix < 35:
                sentiment = "😨 High Fear — Market Stressed"
                market_outlook = "BEARISH"
            else:
                sentiment = "😱 Extreme Fear — PANIC!"
                market_outlook = "VERY BEARISH"
        else:
            sentiment = "Data unavailable"
            market_outlook = "NEUTRAL"

        return {
            "vix": vix,
            "change": vix_change,
            "sentiment": sentiment,
            "market_outlook": market_outlook
        }

    def calculate_options_greeks(self, spot, strike, expiry_days, iv, option_type="CE", rate=0.065):
        """Black-Scholes Greeks Calculator"""
        try:
            import math

            S = spot      # Current price
            K = strike    # Strike price
            T = expiry_days / 365  # Time to expiry
            r = rate      # Risk-free rate
            sigma = iv / 100  # IV as decimal

            if T <= 0 or sigma <= 0:
                return {}

            # d1, d2
            d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
            d2 = d1 - sigma * math.sqrt(T)

            # Normal CDF
            def norm_cdf(x):
                return 0.5 * (1 + math.erf(x / math.sqrt(2)))

            def norm_pdf(x):
                return math.exp(-0.5 * x**2) / math.sqrt(2 * math.pi)

            if option_type == "CE":
                # Call option
                delta = norm_cdf(d1)
                theta = (-(S * norm_pdf(d1) * sigma) / (2 * math.sqrt(T)) -
                         r * K * math.exp(-r * T) * norm_cdf(d2)) / 365
                price = S * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2)
            else:
                # Put option
                delta = norm_cdf(d1) - 1
                theta = (-(S * norm_pdf(d1) * sigma) / (2 * math.sqrt(T)) +
                         r * K * math.exp(-r * T) * norm_cdf(-d2)) / 365
                price = K * math.exp(-r * T) * norm_cdf(-d2) - S * norm_cdf(-d1)

            gamma = norm_pdf(d1) / (S * sigma * math.sqrt(T))
            vega = S * norm_pdf(d1) * math.sqrt(T) / 100
            rho = (K * T * math.exp(-r * T) * norm_cdf(d2) / 100
                   if option_type == "CE"
                   else -K * T * math.exp(-r * T) * norm_cdf(-d2) / 100)

            return {
                "theoretical_price": round(price, 2),
                "delta": round(delta, 4),
                "gamma": round(gamma, 6),
                "theta": round(theta, 2),
                "vega": round(vega, 2),
                "rho": round(rho, 4),
                "d1": round(d1, 4),
                "d2": round(d2, 4),
            }
        except Exception as e:
            logger.error(f"Greeks calc error: {e}")
            return {}

    def analyze_options_chain(self, chain_data: dict) -> dict:
        """Analyze options chain for trading signals"""
        if not chain_data.get("options"):
            return {}

        underlying = chain_data["underlying_value"]
        pcr = chain_data["pcr"]
        max_call_strike = chain_data["max_call_oi_strike"]
        max_put_strike = chain_data["max_put_oi_strike"]
        atm = chain_data["atm_strike"]

        # PCR Analysis
        if pcr > 1.3:
            pcr_signal = "🟢 BULLISH — Excessive Put writing, market may go UP"
            pcr_bias = "BULLISH"
        elif pcr > 1.0:
            pcr_signal = "🟡 MILDLY BULLISH — Put OI > Call OI"
            pcr_bias = "MILDLY BULLISH"
        elif pcr > 0.7:
            pcr_signal = "🟡 NEUTRAL — Balanced market"
            pcr_bias = "NEUTRAL"
        elif pcr > 0.5:
            pcr_signal = "🔴 MILDLY BEARISH — Call OI > Put OI"
            pcr_bias = "MILDLY BEARISH"
        else:
            pcr_signal = "🔴 BEARISH — Excessive Call writing, market may go DOWN"
            pcr_bias = "BEARISH"

        # Options strategy recommendation
        if pcr_bias in ["BULLISH", "MILDLY BULLISH"]:
            strategies = [
                "✅ Bull Call Spread",
                "✅ Cash-secured Put sell",
                "✅ CE Buy (ATM or slightly OTM)",
            ]
        elif pcr_bias == "NEUTRAL":
            strategies = [
                "✅ Iron Condor (Range bound)",
                "✅ Short Straddle (if low IV)",
                "✅ Short Strangle",
            ]
        else:
            strategies = [
                "✅ Bear Put Spread",
                "✅ Covered Call write",
                "✅ PE Buy (ATM or slightly OTM)",
            ]

        return {
            "pcr": pcr,
            "pcr_signal": pcr_signal,
            "pcr_bias": pcr_bias,
            "max_pain": atm,
            "resistance": max_call_strike,
            "support": max_put_strike,
            "strategies": strategies,
            "atm_strike": atm,
        }

    async def get_futures_data(self, symbol: str) -> dict:
        """NSE Futures data"""
        session = await self._get_session()

        try:
            if symbol in INDEX_SYMBOLS:
                url = f"{self.nse_base}/api/equity-derivatives-market-summary-data?type=index-futures"
            else:
                url = f"{self.nse_base}/api/quote-derivative?symbol={symbol}"

            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    return data
        except Exception as e:
            logger.error(f"Futures data error: {e}")

        return {}

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()


# Singleton
india_options = IndiaOptionsClient()
