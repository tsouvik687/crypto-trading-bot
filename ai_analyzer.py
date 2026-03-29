"""
Google Gemini AI Chart Analyzer
চার্ট দেখে বাংলায় analysis করে - সম্পূর্ণ FREE
"""
import google.generativeai as genai
import logging
from PIL import Image
from io import BytesIO
from config import config
from technical_analysis import TradingSignal

logger = logging.getLogger(__name__)


class AIAnalyzer:
    def __init__(self):
        genai.configure(api_key=config.GEMINI_API_KEY)
        # Gemini 2.0 Flash — FREE, chart দেখতে পারে
        self.vision_model = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")
        self.text_model   = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")

    async def analyze_chart(self,
                            chart_bytes: bytes,
                            symbol: str,
                            interval: str,
                            signal: TradingSignal,
                            ticker: dict) -> str:
        """Gemini Vision দিয়ে chart বিশ্লেষণ করো"""
        try:
            image = Image.open(BytesIO(chart_bytes))

            prompt = f"""
তুমি একজন expert crypto trading analyst।
নিচের chart এবং data দেখে বাংলায় বিশ্লেষণ করো।

📊 Coin: {symbol}
⏰ Timeframe: {interval}
💰 Current Price: ${ticker['price']:,.4f}
📈 24h Change: {ticker['change_24h']:+.2f}%
📊 24h High: ${ticker['high_24h']:,.4f}
📉 24h Low:  ${ticker['low_24h']:,.4f}

Technical Indicators:
• RSI(14): {signal.rsi:.1f}
• MACD: {signal.macd_signal}
• Bollinger Bands: {signal.bb_signal}
• Trend: {signal.trend}
• Support: ${signal.support:,.4f}
• Resistance: ${signal.resistance:,.4f}
• Stop Loss: ${signal.stop_loss:,.4f}
• Take Profit: ${signal.take_profit:,.4f}

Algorithm Signal: {signal.action} ({signal.strength}) — {signal.confidence}% confidence

Chart দেখে নিচের প্রশ্নের উত্তর বাংলায় দাও:

1️⃣ Candlestick Pattern কী দেখছো?
   - শেষ কয়েকটা candle কেমন?
   - কোনো বিশেষ pattern আছে?

2️⃣ এখন কী করা উচিত?
   - BUY 🟢 / SELL 🔴 / HOLD 🟡 স্পষ্টভাবে বলো
   - কেন? ৩-৪ টা কারণ বলো

3️⃣ Risk কোথায়?
   - Stop Loss কোথায় রাখবে?
   - কতটুকু loss হতে পারে?

4️⃣ Target কত?
   - Short term ও Long term target আলাদা বলো

5️⃣ Overall Sentiment:
   - Bullish নাকি Bearish?
   - কোনো warning আছে?

সহজ বাংলায়, Emoji দিয়ে, bullet points-এ লেখো।
শেষে বলো: নিজে verify করে trade করুন।
"""
            response = self.vision_model.generate_content([prompt, image])
            return response.text

        except Exception as e:
            logger.error(f"Gemini Vision error: {e}")
            return await self.get_quick_advice(symbol, signal, ticker)

    async def get_quick_advice(self,
                               symbol: str,
                               signal: TradingSignal,
                               ticker: dict) -> str:
        """Chart ছাড়া শুধু data দিয়ে quick analysis"""
        prompt = f"""
তুমি একজন expert crypto trading analyst।
নিচের data দেখে বাংলায় সংক্ষেপে advice দাও।

{symbol} Current Data:
💰 Price: ${ticker['price']:,.4f}
📊 24h Change: {ticker['change_24h']:+.2f}%
📈 High: ${ticker['high_24h']:,.4f}
📉 Low: ${ticker['low_24h']:,.4f}

Indicators:
• RSI: {signal.rsi:.1f} {"(Overbought ⚠️)" if signal.rsi>70 else "(Oversold ✅)" if signal.rsi<30 else "(Normal)"}
• MACD: {signal.macd_signal}
• BB: {signal.bb_signal}
• Trend: {signal.trend}
• Support: ${signal.support:,.4f}
• Resistance: ${signal.resistance:,.4f}

Algorithm: {signal.action} ({signal.strength}) — {signal.confidence}% confident

৫-৬ লাইনে বাংলায় বলো:
✅ BUY/SELL/HOLD — কী করবো?
✅ কেন? (২-৩ কারণ)
✅ Stop Loss ও Target কত?
✅ Risk কোথায়?

Emoji দিয়ে সহজ বাংলায় লেখো।
শেষে: নিজে verify করে trade করুন।
"""
        try:
            response = self.text_model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini text error: {e}")
            return self._fallback_analysis(signal, ticker, symbol)

    async def get_market_sentiment(self, coins_data: list) -> str:
        """Market overall sentiment analysis"""
        coins_text = "\n".join(
            f"• {c['symbol']}: ${c['price']:,.4f} ({c['change_24h']:+.2f}%)"
            for c in coins_data
        )
        prompt = f"""
নিচের crypto market data দেখে বাংলায় overall sentiment বলো:

{coins_text}

৩-৪ লাইনে বলো:
- Market এখন Bullish নাকি Bearish?
- কোন coin ভালো দেখাচ্ছে?
- কোনো warning আছে?

সহজ বাংলায় Emoji দিয়ে।
"""
        try:
            response = self.text_model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Market sentiment error: {e}")
            return "⚠️ Market sentiment analysis এখন available নেই।"

    def _fallback_analysis(self, signal: TradingSignal, ticker: dict, symbol: str) -> str:
        """API কাজ না করলে pure technical analysis response"""
        action_text = {
            "BUY":  "🟢 **BUY করার সুযোগ আছে**",
            "SELL": "🔴 **SELL করুন**",
            "HOLD": "🟡 **এখন HOLD করুন**"
        }.get(signal.action, "🟡 অপেক্ষা করুন")

        reasons_text = "\n".join(signal.reasons[:6])

        return f"""
📊 **Technical Analysis — {symbol}**
━━━━━━━━━━━━━━━━━━━━

{action_text}
💪 Strength: {signal.strength} | 🎯 Confidence: {signal.confidence}%

**Indicators বলছে:**
{reasons_text}

**Risk Management:**
🛡️ Stop Loss:   ${signal.stop_loss:,.4f}
🎯 Take Profit: ${signal.take_profit:,.4f}
📉 Support:     ${signal.support:,.4f}
📈 Resistance:  ${signal.resistance:,.4f}

⚠️ _এটি শুধু technical analysis।_
_Trade করার আগে নিজে research করুন।_
"""


# Singleton
ai_analyzer = AIAnalyzer()
