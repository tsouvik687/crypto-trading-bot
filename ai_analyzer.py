"""
Advanced Gemini AI Analyzer
- Deep Image/Chart Analysis
- Futures Trading Signals  
- Short-term Profit Stages
"""
import logging
from PIL import Image
from io import BytesIO
from config import config
from technical_analysis import TradingSignal

logger = logging.getLogger(__name__)


class AIAnalyzer:
    def __init__(self):
        try:
            from google import genai
            from google.genai import types
            self.client = genai.Client(api_key=config.GEMINI_API_KEY)
            self.types = types
            self.model = "gemini-2.5-flash-preview-05-20"
            self.available = True
            logger.info("✅ Gemini AI initialized!")
        except Exception as e:
            logger.error(f"❌ Gemini init failed: {e}")
            self.available = False

    async def analyze_chart(self, chart_bytes: bytes, symbol: str,
                            interval: str, signal: TradingSignal, ticker: dict) -> str:
        """Deep chart image analysis + futures + profit stages"""
        if not self.available:
            return self._fallback_analysis(signal, ticker, symbol)

        try:
            price = ticker['price']
            
            prompt = f"""তুমি একজন professional crypto futures trader এবং expert technical analyst।
Chart image দেখে এবং নিচের সব data বিশ্লেষণ করে সম্পূর্ণ বাংলায় বিস্তারিত trading plan দাও।

═══════════════════════════════
📊 MARKET DATA
═══════════════════════════════
🪙 Pair: {symbol} (USDT Perpetual)
⏰ Timeframe: {interval}
💰 Current Price: ${price:,.4f}
📊 24h Change: {ticker['change_24h']:+.2f}%
📈 24h High: ${ticker['high_24h']:,.4f}
📉 24h Low: ${ticker['low_24h']:,.4f}

═══════════════════════════════
📉 TECHNICAL INDICATORS
═══════════════════════════════
• RSI(14): {signal.rsi:.2f} — {"🔴 Overbought (70+)" if signal.rsi>70 else "🟢 Oversold (<30)" if signal.rsi<30 else "⚪ Neutral Zone"}
• MACD: {signal.macd_signal}
• Bollinger Bands: {signal.bb_signal}
• EMA Trend: {signal.trend}
• Key Support: ${signal.support:,.4f}
• Key Resistance: ${signal.resistance:,.4f}

═══════════════════════════════
🤖 ALGORITHM SIGNAL
═══════════════════════════════
Direction: {signal.action} | Power: {signal.strength} | Confidence: {signal.confidence}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
এখন chart image দেখে নিচের প্রতিটা section বিস্তারিক বাংলায় লেখো:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**📸 CHART IMAGE ANALYSIS**
Chart-এর candlestick pattern কী দেখছো?
- কোন specific pattern আছে? (Doji, Hammer, Engulfing, Morning Star ইত্যাদি)
- Trend কোন দিকে? Higher highs নাকি Lower lows?
- Volume কেমন? Price-এর সাথে match করছে?
- Bollinger Bands squeeze নাকি expand?
- EMA lines কোথায় আছে? Crossover হয়েছে?
- RSI divergence আছে কি?
- MACD histogram বাড়ছে নাকি কমছে?
- কোনো important support/resistance break হয়েছে?

**🎯 SPOT TRADING PLAN**
Spot market-এর জন্য:
- 🟢 BUY করবো নাকি 🔴 SELL করবো নাকি 🟡 HOLD করবো?
- Entry Price: $___
- কেন এই entry?

**📊 SHORT-TERM PROFIT STAGES (Spot)**
৩টা target stage বলো:
- 🥉 Stage 1 (Quick profit): $___  (+___%)
- 🥈 Stage 2 (Main target): $___  (+___%)  
- 🥇 Stage 3 (Maximum target): $___  (+___%)
- 🛑 Stop Loss: $___  (-___%)

**⚡ FUTURES TRADING PLAN**
Futures/Leverage trading:
- Position: LONG 📈 নাকি SHORT 📉?
- Recommended Leverage: ___x (safe)
- Entry Zone: $___  to  $___
- কেন এই position?

**💥 FUTURES PROFIT STAGES**
৪টা target stage:
- 🎯 TP1 (Take Profit 1): $___  (+___%) — এখানে ৩০% position close
- 🎯 TP2 (Take Profit 2): $___  (+___%) — এখানে ৩০% position close
- 🎯 TP3 (Take Profit 3): $___  (+___%) — এখানে ২০% position close
- 🎯 TP4 (Max Target):    $___  (+___%) — বাকি ২০% এখানে
- 🛑 Stop Loss: $___  (-___%) — এটা hit করলে সব close

**⚠️ RISK MANAGEMENT**
- Risk/Reward Ratio: ___:1
- Liquidation price (10x leverage): $___
- Maximum loss amount: ___% of capital
- Position size recommendation: মোট capital-এর ___%

**🔮 PRICE PREDICTION**
- আগামী ৪ ঘন্টায়: $___ থেকে $___ 
- আগামী ২৪ ঘন্টায়: $___ থেকে $___
- Bull scenario: কী হলে উপরে যাবে?
- Bear scenario: কী হলে নিচে যাবে?
- Key level to watch: $___

**🏆 FINAL RECOMMENDATION**
সব মিলিয়ে সবচেয়ে ভালো trade কী?
একটা সুনির্দিষ্ট action plan দাও।

সব price সংখ্যা দিয়ে বলো। Emoji দিয়ে সাজাও।"""

            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    self.types.Part.from_bytes(
                        data=chart_bytes,
                        mime_type="image/png"
                    ),
                    prompt
                ]
            )
            return response.text

        except Exception as e:
            logger.error(f"Gemini Vision error: {e}")
            return await self.get_quick_advice(symbol, signal, ticker)

    async def get_quick_advice(self, symbol: str,
                               signal: TradingSignal, ticker: dict) -> str:
        """Quick text-only analysis with futures + profit stages"""
        if not self.available:
            return self._fallback_analysis(signal, ticker, symbol)

        try:
            price = ticker['price']
            
            prompt = f"""তুমি একজন professional crypto futures trader।
নিচের data দেখে complete trading plan বাংলায় দাও।

{symbol} | ${price:,.4f} | 24h: {ticker['change_24h']:+.2f}%
High: ${ticker['high_24h']:,.4f} | Low: ${ticker['low_24h']:,.4f}
RSI: {signal.rsi:.1f} | MACD: {signal.macd_signal} | BB: {signal.bb_signal}
Trend: {signal.trend} | Support: ${signal.support:,.4f} | Resistance: ${signal.resistance:,.4f}
Signal: {signal.action} ({signal.strength}) | Confidence: {signal.confidence}%

Complete plan দাও:

**🎯 SPOT TRADING**
- Action: BUY/SELL/HOLD
- Entry: $___
- Stage 1: $___ (+___%)
- Stage 2: $___ (+___%)
- Stage 3: $___ (+___%)
- Stop Loss: $___

**⚡ FUTURES TRADING**
- Position: LONG/SHORT
- Leverage: ___x
- Entry: $___
- TP1: $___ (৩০% close)
- TP2: $___ (৩০% close)
- TP3: $___ (২০% close)
- TP4: $___ (২০% close)
- Stop Loss: $___
- Risk/Reward: ___:1

**🔮 NEXT 24H PREDICTION**
- Range: $___ - $___
- Most likely direction: UP/DOWN
- Key levels to watch: $___

Emoji দিয়ে বাংলায় বিস্তারিত।"""

            response = self.client.models.generate_content(
                model=self.model,
                contents=[prompt]
            )
            return response.text

        except Exception as e:
            logger.error(f"Gemini text error: {e}")
            return self._fallback_analysis(signal, ticker, symbol)

    async def get_futures_signal(self, symbol: str,
                                  signal: TradingSignal, ticker: dict) -> str:
        """Dedicated futures signal"""
        if not self.available:
            return self._futures_fallback(signal, ticker, symbol)

        try:
            price = ticker['price']
            
            prompt = f"""তুমি একজন expert crypto futures trader।
{symbol} এর জন্য শুধু futures trading signal দাও। বাংলায়।

Price: ${price:,.4f} | RSI: {signal.rsi:.1f} | Trend: {signal.trend}
Support: ${signal.support:,.4f} | Resistance: ${signal.resistance:,.4f}
Algorithm: {signal.action} ({signal.confidence}% confident)

এই format-এ দাও:

⚡ FUTURES SIGNAL — {symbol}

📍 Position: LONG/SHORT
📊 Leverage: ___x (recommended)
💰 Entry Zone: $___ — $___

🎯 Take Profit Levels:
• TP1: $___ (+___%) → ৩০% close করো
• TP2: $___ (+___%) → ৩০% close করো  
• TP3: $___ (+___%) → ২০% close করো
• TP4: $___ (+___%) → ২০% close করো

🛑 Stop Loss: $___ (-___%)
📊 Risk/Reward: ___:1
💥 Liquidation (10x): $___

⏰ Valid for: ৪-৮ ঘন্টা
🔥 Signal Strength: ___/10

সংক্ষেপে কেন এই signal তার ৩টা কারণ।"""

            response = self.client.models.generate_content(
                model=self.model,
                contents=[prompt]
            )
            return response.text

        except Exception as e:
            logger.error(f"Futures signal error: {e}")
            return self._futures_fallback(signal, ticker, symbol)

    async def get_market_sentiment(self, coins_data: list) -> str:
        if not self.available:
            return "⚠️ AI analysis unavailable।"
        try:
            coins_text = "\n".join(
                f"• {c['symbol']}: ${c['price']:,.4f} ({c['change_24h']:+.2f}%)"
                for c in coins_data
            )
            prompt = f"""Crypto market overview:
{coins_text}

বাংলায় বলো:
- Overall market: Bullish/Bearish/Neutral?
- Best opportunity এখন কোনটা?
- Avoid করা উচিত কোনটা?
- আজকের trading strategy কী হওয়া উচিত?
- Futures-এর জন্য সবচেয়ে ভালো coin কোনটা?

Emoji দিয়ে বিস্তারিত।"""

            response = self.client.models.generate_content(
                model=self.model, contents=[prompt]
            )
            return response.text
        except Exception as e:
            return "⚠️ Market sentiment unavailable।"

    def _futures_fallback(self, signal: TradingSignal,
                          ticker: dict, symbol: str) -> str:
        price = ticker['price']
        is_long = signal.action == "BUY"
        
        tp1 = price * (1.015 if is_long else 0.985)
        tp2 = price * (1.030 if is_long else 0.970)
        tp3 = price * (1.050 if is_long else 0.950)
        tp4 = price * (1.080 if is_long else 0.920)
        sl  = price * (0.980 if is_long else 1.020)
        
        position = "LONG 📈" if is_long else "SHORT 📉"

        return f"""⚡ **FUTURES SIGNAL — {symbol}**
━━━━━━━━━━━━━━━━━━━━

📍 Position: **{position}**
📊 Leverage: **5-10x** (safe)
💰 Entry: **${price:,.4f}**

🎯 **Take Profit Stages:**
• TP1: ${tp1:,.4f} (+1.5%) → ৩০% close
• TP2: ${tp2:,.4f} (+3.0%) → ৩০% close
• TP3: ${tp3:,.4f} (+5.0%) → ২০% close
• TP4: ${tp4:,.4f} (+8.0%) → ২০% close

🛑 **Stop Loss:** ${sl:,.4f} (-2%)
📊 **Risk/Reward:** 1:4
💪 **Signal:** {signal.strength} | {signal.confidence}%"""

    def _fallback_analysis(self, signal: TradingSignal,
                           ticker: dict, symbol: str) -> str:
        price = ticker['price']
        is_buy = signal.action == "BUY"

        sp1 = price * (1.02 if is_buy else 0.98)
        sp2 = price * (1.04 if is_buy else 0.96)
        sp3 = price * (1.07 if is_buy else 0.93)
        ssl = price * (0.97 if is_buy else 1.03)

        fp1 = price * (1.015 if is_buy else 0.985)
        fp2 = price * (1.03 if is_buy else 0.97)
        fp3 = price * (1.05 if is_buy else 0.95)
        fp4 = price * (1.08 if is_buy else 0.92)
        fsl = price * (0.98 if is_buy else 1.02)

        action = "🟢 BUY" if is_buy else "🔴 SELL" if signal.action=="SELL" else "🟡 HOLD"
        pos = "LONG 📈" if is_buy else "SHORT 📉"
        reasons = "\n".join(signal.reasons[:5])

        return f"""📊 **{symbol} Complete Analysis**
━━━━━━━━━━━━━━━━━━━━
💰 Price: ${price:,.4f} | 24h: {ticker['change_24h']:+.2f}%

**Signal:** {action} | {signal.strength} | {signal.confidence}%

**Indicators:**
{reasons}

━━━━━━━━━━━━━━━━━━━━
**🎯 SPOT TRADING**
Entry: ${price:,.4f}
• Stage 1: ${sp1:,.4f} (+2%)
• Stage 2: ${sp2:,.4f} (+4%)
• Stage 3: ${sp3:,.4f} (+7%)
• Stop Loss: ${ssl:,.4f} (-3%)

━━━━━━━━━━━━━━━━━━━━
**⚡ FUTURES TRADING**
Position: {pos} | Leverage: 5-10x
Entry: ${price:,.4f}
• TP1: ${fp1:,.4f} (+1.5%) → ৩০% close
• TP2: ${fp2:,.4f} (+3%) → ৩০% close
• TP3: ${fp3:,.4f} (+5%) → ২০% close
• TP4: ${fp4:,.4f} (+8%) → ২০% close
• Stop Loss: ${fsl:,.4f} (-2%)
• Risk/Reward: 1:4

📉 Support: ${signal.support:,.4f}
📈 Resistance: ${signal.resistance:,.4f}"""


# Singleton
ai_analyzer = AIAnalyzer()
