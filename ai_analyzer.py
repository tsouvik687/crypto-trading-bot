"""
Ultra Advanced Gemini AI Analyzer
Maximum Detail - Professional Grade
"""
import logging
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

    def _build_chart_prompt(self, symbol, interval, signal, ticker):
        price = ticker['price']
        return f"""তুমি একজন Wall Street-level professional crypto trader, technical analyst এবং market strategist।
তোমার কাছে একটি real-time crypto chart আছে। এই chart এবং সব data দেখে সম্পূর্ণ professional trading report বাংলায় তৈরি করো।

╔══════════════════════════════════════╗
║         MARKET SNAPSHOT              ║
╚══════════════════════════════════════╝
🪙 Asset: {symbol} (USDT Perpetual)
⏰ Timeframe: {interval}
💰 Current Price: ${price:,.6f}
📊 24h Change: {ticker['change_24h']:+.2f}%
📈 24h High: ${ticker['high_24h']:,.6f}
📉 24h Low: ${ticker['low_24h']:,.6f}
📦 Volume: ${ticker['volume_24h']:,.0f}

╔══════════════════════════════════════╗
║      TECHNICAL INDICATORS            ║
╚══════════════════════════════════════╝
• RSI(14): {signal.rsi:.2f} → {"🔴 OVERBOUGHT — Selling pressure শুরু হতে পারে" if signal.rsi>70 else "🟢 OVERSOLD — Buying opportunity তৈরি হচ্ছে" if signal.rsi<30 else "⚪ NEUTRAL ZONE — Momentum দেখে সিদ্ধান্ত নাও"}
• MACD Signal: {signal.macd_signal}
• Bollinger Bands: {signal.bb_signal}
• EMA Trend: {signal.trend}
• Support Zone: ${signal.support:,.6f}
• Resistance Zone: ${signal.resistance:,.6f}
• Algorithm: {signal.action} | {signal.strength} | {signal.confidence}% confident

╔══════════════════════════════════════╗
║    COMPLETE ANALYSIS REQUIRED        ║
╚══════════════════════════════════════╝

Chart দেখে নিচের প্রতিটা section সম্পূর্ণ বিস্তারিতভাবে বাংলায় লেখো।
প্রতিটা price সংখ্যা দিয়ে বলো। কোনো section skip করবে না।

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📸 SECTION 1: DEEP CHART ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Chart image-এ যা দেখছো তার সম্পূর্ণ বিশ্লেষণ:

🕯️ CANDLESTICK ANALYSIS:
- শেষ ৫টা candle কেমন? Color, size, wick কেমন?
- কোনো specific pattern আছে? (Doji, Hammer, Shooting Star, Engulfing, Harami, Morning/Evening Star, Three Soldiers/Crows, Spinning Top ইত্যাদি)
- এই pattern কী signal দিচ্ছে?
- Candle bodies কি বড় নাকি ছোট? কী বোঝায়?

📐 TREND STRUCTURE:
- Overall trend কোন direction-এ? (Uptrend/Downtrend/Sideways)
- Higher Highs Higher Lows আছে? নাকি Lower Highs Lower Lows?
- Trend কি strong নাকি weak? কীভাবে বুঝলে?
- কোনো trend reversal sign আছে?

📊 VOLUME ANALYSIS:
- Volume কি বাড়ছে নাকি কমছে?
- Price movement-এর সাথে volume match করছে?
- Volume spike কোথায় দেখা যাচ্ছে?
- Low volume consolidation আছে কি?

🎯 KEY LEVELS:
- Strong support levels কোথায়? (Price দিয়ে বলো)
- Strong resistance levels কোথায়? (Price দিয়ে বলো)
- কোনো important breakout বা breakdown হয়েছে?
- Previous high/low কোথায়?

📉 INDICATOR DEEP ANALYSIS:
- RSI: Overbought/Oversold? Divergence আছে? Hidden divergence আছে?
- MACD: Crossover হয়েছে? Histogram বাড়ছে নাকি কমছে? Zero line cross হয়েছে?
- Bollinger Bands: Squeeze হচ্ছে? Price কোন band-এ? Band walk করছে?
- EMA: কোন EMA-গুলো price-এর উপরে/নিচে? Crossover হয়েছে?
- Stochastic: কোথায় আছে? Overbought/Oversold?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 SECTION 2: SPOT TRADING PLAN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Spot market-এর জন্য complete plan:

📍 TRADE DIRECTION: BUY 🟢 / SELL 🔴 / HOLD 🟡 / WAIT ⏳
(স্পষ্ট বলো কোনটা এবং কেন — ৫টা কারণ দাও)

💰 ENTRY STRATEGY:
- Ideal Entry Price: $___
- Entry Zone: $___ থেকে $___
- কখন entry নেবো? (কী condition দেখলে)
- DCA করলে কোথায়? (২-৩টা level)

📊 SPOT PROFIT STAGES:
🥉 Stage 1 — Quick Scalp:
   • Target: $___ (+___%)
   • এখানে কতটুকু sell করবো: ৩০%
   • কেন এই target?

🥈 Stage 2 — Main Target:
   • Target: $___ (+___%)
   • এখানে কতটুকু sell করবো: ৪০%
   • কেন এই target?

🥇 Stage 3 — Extended Target:
   • Target: $___ (+___%)
   • এখানে কতটুকু sell করবো: ২০%
   • কেন এই target?

🏆 Stage 4 — Moon Target:
   • Target: $___ (+___%)
   • এখানে বাকি ১০% sell
   • এটা কতটা realistic?

🛑 STOP LOSS:
   • Hard Stop: $___ (-___%)
   • Soft Stop (mental): $___
   • কেন এখানে stop?
   • Stop hit হলে re-entry কোথায়?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ SECTION 3: FUTURES TRADING PLAN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Professional futures plan:

📍 POSITION TYPE: LONG 📈 / SHORT 📉
(কেন এই position? ৪টা কারণ)

⚖️ LEVERAGE RECOMMENDATION:
• Conservative (Safe): ___x
• Moderate (Balanced): ___x
• Aggressive (High Risk): ___x
• কোনটা recommend করছো এবং কেন?

💰 ENTRY PLAN:
• Primary Entry: $___
• Entry Zone: $___ — $___
• Limit order নাকি Market order?
• Confirmation কী দেখলে entry নেবো?

🎯 FUTURES PROFIT STAGES (Partial Close Strategy):
━━━━━━━━━━━━━━━━━━━━
🎯 TP1 — First Target:
   • Price: $___ (+___%)
   • Position-এর ২৫% close করো
   • Rationale: কেন এখানে?

🎯 TP2 — Second Target:
   • Price: $___ (+___%)
   • Position-এর ২৫% close করো
   • Rationale: কেন এখানে?

🎯 TP3 — Third Target:
   • Price: $___ (+___%)
   • Position-এর ২৫% close করো
   • Rationale: কেন এখানে?

🎯 TP4 — Final Target:
   • Price: $___ (+___%)
   • বাকি ২৫% close করো
   • Rationale: কেন এখানে?

🛑 FUTURES STOP LOSS:
   • Stop Loss: $___ (-___%)
   • Trailing Stop: কোথায় move করবো?
   • Break-even কখন move করবো?

💥 RISK CALCULATIONS:
   • Liquidation Price (5x): $___
   • Liquidation Price (10x): $___
   • Liquidation Price (20x): $___
   • Max recommended position size: capital-এর ___%
   • Risk per trade: capital-এর ___%
   • Risk/Reward Ratio: ___:1

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ SECTION 4: SHORT-TERM SCALPING PLAN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
১৫ মিনিট থেকে ৪ ঘন্টার জন্য:

⚡ SCALP DIRECTION: UP/DOWN
• Quick Entry: $___
• Scalp Target 1: $___ (+___%) — ৩০ মিনিটে
• Scalp Target 2: $___ (+___%) — ১ ঘন্টায়
• Scalp Target 3: $___ (+___%) — ৪ ঘন্টায়
• Scalp Stop Loss: $___ (-___%)
• Best timeframe for scalp: ___

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔮 SECTION 5: PRICE PREDICTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Data-based prediction:

⏰ Next 1 Hour:
• Expected Range: $___ — $___
• Most likely direction: UP/DOWN/SIDEWAYS
• Probability: UP ___% | DOWN ___% | SIDEWAYS ___%

⏰ Next 4 Hours:
• Expected Range: $___ — $___
• Key level to break: $___
• If breaks up → goes to: $___
• If breaks down → goes to: $___

⏰ Next 24 Hours:
• Expected Range: $___ — $___
• Major catalyst to watch: ___
• Bias: BULLISH/BEARISH/NEUTRAL

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🐂🐻 SECTION 6: BULL vs BEAR SCENARIO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🐂 BULL CASE (এই conditions হলে উপরে যাবে):
• Condition 1: ___
• Condition 2: ___
• Condition 3: ___
• Bull target: $___ (+___%)
• Probability: ___%

🐻 BEAR CASE (এই conditions হলে নিচে যাবে):
• Condition 1: ___
• Condition 2: ___
• Condition 3: ___
• Bear target: $___ (-___%)
• Probability: ___%

⚖️ BASE CASE (সবচেয়ে সম্ভাবনাময়):
• কী হবে বলে মনে হচ্ছে?
• Probability: ___%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ SECTION 7: RISK WARNINGS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• সবচেয়ে বড় risk কোনটা?
• কোন level break হলে সব plan বাতিল?
• Avoid করা উচিত কখন?
• Market condition কেমন? Volatile নাকি Stable?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 SECTION 8: FINAL VERDICT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
সব মিলিয়ে:
• Overall Signal: BUY/SELL/HOLD (1-10 score দাও)
• Best Trade Setup: Spot নাকি Futures?
• আজকের জন্য সেরা strategy কী?
• একজন beginner-এর জন্য advice কী?
• একজন experienced trader-এর জন্য advice কী?

Emoji ব্যবহার করো। প্রতিটা price সংখ্যায় দাও। বাংলায় লেখো।"""

    async def analyze_chart(self, chart_bytes: bytes, symbol: str,
                            interval: str, signal: TradingSignal, ticker: dict) -> str:
        if not self.available:
            return self._fallback_analysis(signal, ticker, symbol)

        try:
            prompt = self._build_chart_prompt(symbol, interval, signal, ticker)

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
        if not self.available:
            return self._fallback_analysis(signal, ticker, symbol)

        try:
            price = ticker['price']
            prompt = f"""তুমি একজন professional crypto trader।
{symbol} এর জন্য complete trading plan বাংলায় দাও।

Price: ${price:,.6f} | 24h: {ticker['change_24h']:+.2f}%
High: ${ticker['high_24h']:,.6f} | Low: ${ticker['low_24h']:,.6f}
RSI: {signal.rsi:.2f} | MACD: {signal.macd_signal} | BB: {signal.bb_signal}
Trend: {signal.trend} | Support: ${signal.support:,.6f} | Resistance: ${signal.resistance:,.6f}
Signal: {signal.action} ({signal.strength}) | {signal.confidence}% confident

নিচের সব section বিস্তারিক লেখো:

**🎯 SPOT PLAN**
Action + Entry + Stage1 + Stage2 + Stage3 + Stage4 + StopLoss (সব price দিয়ে)

**⚡ FUTURES PLAN**
Position + Leverage + Entry + TP1 + TP2 + TP3 + TP4 + StopLoss + Liquidation + R:R

**⏱️ SCALP PLAN**
Direction + Entry + 3 targets + StopLoss

**🔮 PREDICTION**
1h range + 4h range + 24h range + Bull target + Bear target

**🐂🐻 SCENARIOS**
Bull case + Bear case + Base case (probability দাও)

**⚠️ RISKS**
Top 3 risks + Warning levels

**🏆 FINAL VERDICT**
Best trade setup + Score/10 + Beginner advice + Pro advice

সব price সংখ্যায় দাও। Emoji দিয়ে বাংলায়।"""

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
        if not self.available:
            return self._futures_fallback(signal, ticker, symbol)

        try:
            price = ticker['price']
            prompt = f"""তুমি একজন expert crypto futures trader।
{symbol} এর জন্য ultra-detailed futures signal দাও। বাংলায়।

Price: ${price:,.6f} | RSI: {signal.rsi:.2f} | Trend: {signal.trend}
Support: ${signal.support:,.6f} | Resistance: ${signal.resistance:,.6f}
MACD: {signal.macd_signal} | BB: {signal.bb_signal}
Algorithm: {signal.action} ({signal.confidence}% confident)

Complete futures plan:

⚡ FUTURES SIGNAL — {symbol}
━━━━━━━━━━━━━━━━━━━━

📍 Position: LONG/SHORT (কেন — ৫ কারণ)
⚖️ Leverage: Conservative/Moderate/Aggressive (___x/___x/___x)
💰 Entry Zone: $___ — $___
✅ Entry Confirmation: কী দেখলে enter করবো?

🎯 PROFIT STAGES (Partial Close):
• TP1: $___ (+___%) → ২৫% close | কেন?
• TP2: $___ (+___%) → ২৫% close | কেন?
• TP3: $___ (+___%) → ২৫% close | কেন?
• TP4: $___ (+___%) → ২৫% close | কেন?

🛑 STOP LOSS PLAN:
• Initial SL: $___ (-___%)
• Move to Break-even: $___  হলে
• Trailing Stop: কীভাবে?

💥 RISK CALCULATIONS:
• Liq. Price (5x): $___
• Liq. Price (10x): $___
• Liq. Price (20x): $___
• Risk/Reward: ___:1
• Max position: capital-এর ___%

⏰ Trade Duration: ___
🔥 Signal Strength: ___/10
📊 Win Probability: ___%

⚠️ Main risks: (৩টা)
✅ Invalidation level: $___"""

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
            prompt = f"""Professional crypto market analysis:
{coins_text}

বাংলায় বিস্তারিত বলো:
🌍 Overall Market: Bullish/Bearish/Neutral? কেন?
🏆 Best opportunity: কোনটা এবং কেন?
⚠️ Avoid: কোনটা এবং কেন?
📊 Market correlation: একসাথে কোনদিকে যাচ্ছে?
⚡ Best futures opportunity: কোনটা?
📈 Today's strategy: কী করা উচিত?
🔮 Next 24h market outlook: কী হবে?

Emoji দিয়ে বিস্তারিত বাংলায়।"""

            response = self.client.models.generate_content(
                model=self.model, contents=[prompt]
            )
            return response.text
        except Exception as e:
            return "⚠️ Market sentiment unavailable।"

    def _futures_fallback(self, signal, ticker, symbol):
        price = ticker['price']
        is_long = signal.action == "BUY"
        m = 1 if is_long else -1

        tp1 = price * (1 + m*0.015)
        tp2 = price * (1 + m*0.030)
        tp3 = price * (1 + m*0.050)
        tp4 = price * (1 + m*0.080)
        sl  = price * (1 - m*0.020)
        liq5  = price * (1 - m*0.18)
        liq10 = price * (1 - m*0.09)
        pos = "LONG 📈" if is_long else "SHORT 📉"

        return f"""⚡ **FUTURES SIGNAL — {symbol}**
━━━━━━━━━━━━━━━━━━━━
📍 Position: **{pos}**
⚖️ Leverage: 5x (safe) / 10x (moderate)
💰 Entry: **${price:,.4f}**

🎯 **Profit Stages:**
• TP1: ${tp1:,.4f} (+1.5%) → ২৫% close
• TP2: ${tp2:,.4f} (+3.0%) → ২৫% close
• TP3: ${tp3:,.4f} (+5.0%) → ২৫% close
• TP4: ${tp4:,.4f} (+8.0%) → ২৫% close

🛑 **Stop Loss:** ${sl:,.4f} (-2%)
💥 **Liquidation (5x):** ${liq5:,.4f}
💥 **Liquidation (10x):** ${liq10:,.4f}
📊 **Risk/Reward:** 1:4
💪 **Signal:** {signal.strength} | {signal.confidence}%"""

    def _fallback_analysis(self, signal, ticker, symbol):
        price = ticker['price']
        is_buy = signal.action == "BUY"
        m = 1 if is_buy else -1

        s1 = price*(1+m*0.02); s2 = price*(1+m*0.04)
        s3 = price*(1+m*0.07); s4 = price*(1+m*0.12)
        ssl = price*(1-m*0.03)

        f1 = price*(1+m*0.015); f2 = price*(1+m*0.03)
        f3 = price*(1+m*0.05); f4 = price*(1+m*0.08)
        fsl = price*(1-m*0.02)
        liq5 = price*(1-m*0.18); liq10 = price*(1-m*0.09)

        sc1 = price*(1+m*0.008); sc2 = price*(1+m*0.015); sc3 = price*(1+m*0.025)
        scsl = price*(1-m*0.01)

        action = "🟢 BUY" if is_buy else "🔴 SELL" if signal.action=="SELL" else "🟡 HOLD"
        pos = "LONG 📈" if is_buy else "SHORT 📉"
        reasons = "\n".join(signal.reasons[:6])

        return f"""📊 **{symbol} — Complete Analysis**
━━━━━━━━━━━━━━━━━━━━
💰 ${price:,.6f} | 24h: {ticker['change_24h']:+.2f}%
**Signal:** {action} | {signal.strength} | {signal.confidence}%

**Indicators:**
{reasons}

━━━━━━━━━━━━━━━━━━━━
**🎯 SPOT TRADING**
Entry: ${price:,.4f}
🥉 Stage 1: ${s1:,.4f} (+2%) → ৩০% sell
🥈 Stage 2: ${s2:,.4f} (+4%) → ৪০% sell
🥇 Stage 3: ${s3:,.4f} (+7%) → ২০% sell
🏆 Stage 4: ${s4:,.4f} (+12%) → ১০% sell
🛑 Stop Loss: ${ssl:,.4f} (-3%)

━━━━━━━━━━━━━━━━━━━━
**⏱️ SCALP PLAN**
Direction: {"UP ⬆️" if is_buy else "DOWN ⬇️"}
• Scalp TP1: ${sc1:,.4f} (+0.8%)
• Scalp TP2: ${sc2:,.4f} (+1.5%)
• Scalp TP3: ${sc3:,.4f} (+2.5%)
• Scalp SL: ${scsl:,.4f} (-1%)

━━━━━━━━━━━━━━━━━━━━
**⚡ FUTURES TRADING**
Position: {pos} | Leverage: 5-10x
Entry: ${price:,.4f}
• TP1: ${f1:,.4f} (+1.5%) → ২৫% close
• TP2: ${f2:,.4f} (+3.0%) → ২৫% close
• TP3: ${f3:,.4f} (+5.0%) → ২৫% close
• TP4: ${f4:,.4f} (+8.0%) → ২৫% close
• Stop Loss: ${fsl:,.4f} (-2%)
• Liq (5x): ${liq5:,.4f}
• Liq (10x): ${liq10:,.4f}
• Risk/Reward: 1:4

━━━━━━━━━━━━━━━━━━━━
📉 Support: ${signal.support:,.4f}
📈 Resistance: ${signal.resistance:,.4f}"""


# Singleton
ai_analyzer = AIAnalyzer()
