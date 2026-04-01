"""
Ultra Advanced Gemini AI Analyzer
15+ indicators data দিয়ে professional analysis
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
            self.model = "gemini-1.5-flash"
            self.available = True
            logger.info("✅ Gemini AI ready!")
        except Exception as e:
            logger.error(f"❌ Gemini init failed: {e}")
            self.available = False

    def _full_data_block(self, symbol, interval, signal: TradingSignal, ticker):
        p = ticker['price']
        return f"""
╔══════════════════════════════════════════════╗
║           {symbol} — {interval.upper()} MARKET DATA            
╚══════════════════════════════════════════════╝
💰 Price:        ${p:,.6f}
📊 24h Change:   {ticker['change_24h']:+.2f}%
📈 24h High:     ${ticker['high_24h']:,.6f}
📉 24h Low:      ${ticker['low_24h']:,.6f}
📦 Volume:       ${ticker['volume_24h']:,.0f}

╔══════════════════════════════════════════════╗
║              MOMENTUM INDICATORS             
╚══════════════════════════════════════════════╝
• RSI(14):        {signal.rsi:.2f} — {"🔴 EXTREME OVERBOUGHT" if signal.rsi>75 else "⚠️ OVERBOUGHT" if signal.rsi>65 else "🟢 EXTREME OVERSOLD" if signal.rsi<25 else "✅ OVERSOLD" if signal.rsi<35 else "⚪ NEUTRAL"}
• RSI Divergence: {signal.rsi_divergence} {"🔥 REVERSAL SIGNAL!" if signal.rsi_divergence != "NONE" else ""}
• MACD:           {signal.macd_signal} (Value: {signal.macd_value:.4f}, Hist: {signal.macd_hist:.4f})
• Stochastic K:   {signal.stoch_k:.1f} | D: {signal.stoch_d:.1f} — {"Overbought" if signal.stoch_k>80 else "Oversold" if signal.stoch_k<20 else "Neutral"}
• Williams %R:    {signal.williams_r:.1f} — {"Overbought" if signal.williams_r>-20 else "Oversold" if signal.williams_r<-80 else "Neutral"}
• CCI(20):        {signal.cci:.1f} — {"Overbought" if signal.cci>100 else "Oversold" if signal.cci<-100 else "Neutral"}

╔══════════════════════════════════════════════╗
║              TREND INDICATORS                
╚══════════════════════════════════════════════╝
• Trend:          {signal.trend} ({signal.trend_strength})
• Market Structure: {signal.market_structure}
• EMA 9:          ${signal.ema_9:,.4f}
• EMA 21:         ${signal.ema_21:,.4f}
• EMA 50:         ${signal.ema_50:,.4f}
• EMA 200:        ${signal.ema_200:,.4f}
• VWAP:           ${signal.vwap:,.4f} — Price is {signal.price_vs_vwap} VWAP
• Ichimoku:       {signal.ichimoku_signal} (Tenkan: ${signal.tenkan:,.4f} | Kijun: ${signal.kijun:,.4f})
• Bollinger Bands: {signal.bb_signal} | Position: {signal.bb_position:.1f}% | Width: {signal.bb_width:.2f}%

╔══════════════════════════════════════════════╗
║              VOLUME ANALYSIS                 
╚══════════════════════════════════════════════╝
• Volume Trend:   {signal.volume_trend}
• Volume Ratio:   {signal.volume_ratio:.2f}x (average-এর তুলনায়)

╔══════════════════════════════════════════════╗
║         SUPPORT & RESISTANCE LEVELS          
╚══════════════════════════════════════════════╝
• Resistance 2:   ${signal.resistance_2:,.4f}
• Resistance 1:   ${signal.resistance:,.4f}  ← Nearest
• Current Price:  ${p:,.4f}  ◄
• Support 1:      ${signal.support:,.4f}  ← Nearest
• Support 2:      ${signal.support_2:,.4f}

╔══════════════════════════════════════════════╗
║              FIBONACCI LEVELS                
╚══════════════════════════════════════════════╝
• Fib 23.6%:   ${signal.fib_236:,.4f}
• Fib 38.2%:   ${signal.fib_382:,.4f}
• Fib 50.0%:   ${signal.fib_500:,.4f}
• Fib 61.8%:   ${signal.fib_618:,.4f}  ← Golden Ratio
• Fib 78.6%:   ${signal.fib_786:,.4f}

╔══════════════════════════════════════════════╗
║              PIVOT POINTS                    
╚══════════════════════════════════════════════╝
• R3: ${signal.pivot_r3:,.4f} | R2: ${signal.pivot_r2:,.4f} | R1: ${signal.pivot_r1:,.4f}
• Pivot: ${signal.pivot:,.4f}
• S1: ${signal.pivot_s1:,.4f} | S2: ${signal.pivot_s2:,.4f} | S3: ${signal.pivot_s3:,.4f}

╔══════════════════════════════════════════════╗
║            CANDLESTICK PATTERNS              
╚══════════════════════════════════════════════╝
{chr(10).join(signal.patterns) if signal.patterns else "• No significant pattern"}

╔══════════════════════════════════════════════╗
║           ALGORITHM SIGNAL SUMMARY          
╚══════════════════════════════════════════════╝
• Direction:   {signal.action}
• Strength:    {signal.strength}
• Confidence:  {signal.confidence}%
• Buy Score:   {signal.buy_score} points
• Sell Score:  {signal.sell_score} points
• ATR:         ${signal.atr:,.4f} ({signal.atr_pct:.2f}% of price)
"""

    async def analyze_chart(self, chart_bytes, symbol, interval, signal: TradingSignal, ticker):
        if not self.available:
            return self._fallback_analysis(signal, ticker, symbol)

        try:
            data_block = self._full_data_block(symbol, interval, signal, ticker)
            p = ticker['price']

            prompt = f"""{data_block}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
তুমি একজন institutional-level crypto trader।
উপরের সব data এবং chart image দেখে সম্পূর্ণ professional analysis বাংলায় করো।
প্রতিটা section বিস্তারিকভাবে লেখো। কোনো section বাদ দেবে না।
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**━━━ 📸 CHART VISUAL ANALYSIS ━━━**
Chart image দেখে:
• Candlestick গুলো কেমন? শেষ ৫টার বিবরণ দাও
• Pattern কী? কতটা reliable এই pattern?
• Trend line কোন direction-এ যাচ্ছে?
• Volume bar কেমন? Price-এর সাথে match করছে?
• Bollinger Bands কি squeeze নাকি expand করছে?
• EMA lines কোথায়? কোনো crossover দেখা যাচ্ছে?
• RSI chart-এ কোথায়? Divergence আছে?
• MACD histogram বাড়ছে নাকি কমছে?
• Overall chart structure কেমন দেখাচ্ছে?

**━━━ 🎯 SPOT TRADING PLAN ━━━**
• Final Decision: BUY🟢 / SELL🔴 / HOLD🟡 / WAIT⏳
• কেন? (৫টা indicator-based কারণ)
• Ideal Entry: ${p:,.4f} এর কাছাকাছি কোথায়?
• Entry Confirmation: কোন condition দেখলে ঢুকবো?
• DCA Strategy: কোথায় কোথায় আরো buy করবো?

🎯 SPOT PROFIT STAGES:
• Stage 1 (৩০% sell): $___  (+___%)  — কেন এখানে?
• Stage 2 (৩০% sell): $___  (+___%)  — কেন এখানে?
• Stage 3 (২০% sell): $___  (+___%)  — কেন এখানে?
• Stage 4 (২০% sell): $___  (+___%)  — Moon target
• Hard Stop Loss:     $___  (-___%)
• Soft Stop (mental): $___

**━━━ ⚡ FUTURES TRADING PLAN ━━━**
• Position: LONG📈 / SHORT📉
• কেন? (৪টা কারণ data দিয়ে)
• Leverage — Conservative: ___x | Moderate: ___x | Aggressive: ___x
• Best leverage এই market-এ: ___x (কেন?)
• Entry Zone: $___  থেকে  $___
• Confirmation signal: কী দেখলে enter?

🎯 FUTURES PROFIT STAGES (Partial Close):
• TP1: $___  (+___%) → ২৫% close | Rationale?
• TP2: $___  (+___%) → ২৫% close | Rationale?
• TP3: $___  (+___%) → ২৫% close | Rationale?
• TP4: $___  (+___%) → ২৫% close | Rationale?
• Initial Stop Loss: $___  (-___%)
• Trailing Stop: কখন এবং কোথায় move করবো?
• Break-even: কোন TP-তে SL break-even-এ নিয়ে আসবো?

💥 Risk Calculations:
• Liquidation (5x):  $___
• Liquidation (10x): $___
• Liquidation (20x): $___
• Max position size: capital-এর ___% এই trade-এ
• R:R Ratio: ___:1

**━━━ ⏱️ SCALPING PLAN ━━━**
• Scalp Direction: UP⬆️ / DOWN⬇️
• Entry: $___
• Scalp TP1 (১৫-৩০ মিনিট): $___  (+___%)
• Scalp TP2 (১-২ ঘন্টা):   $___  (+___%)
• Scalp TP3 (৪ ঘন্টা):     $___  (+___%)
• Scalp SL: $___  (-___%)
• Best timeframe: ___

**━━━ 🔮 PRICE PREDICTION ━━━**
⏰ Next 1 Hour:
• Range: $___  —  $___
• Direction: UP/DOWN/SIDEWAYS
• Probability: UP ___% | DOWN ___% | SIDEWAYS ___%

⏰ Next 4 Hours:
• Range: $___  —  $___
• Key break level: $___
• If breaks UP → goes to: $___
• If breaks DOWN → goes to: $___

⏰ Next 24 Hours:
• Range: $___  —  $___
• Primary Bias: BULLISH/BEARISH
• Major level to watch: $___

**━━━ 🐂🐻 BULL vs BEAR SCENARIO ━━━**
🐂 BULL CASE (এই conditions হলে উপরে যাবে):
• Condition 1: ___
• Condition 2: ___
• Condition 3: ___
• Bull Target: $___  (+___%)
• Probability: ___%

🐻 BEAR CASE (এই conditions হলে নিচে যাবে):
• Condition 1: ___
• Condition 2: ___
• Condition 3: ___
• Bear Target: $___  (-___%)
• Probability: ___%

⚖️ BASE CASE (সবচেয়ে সম্ভাবনাময়):
• কী হবে: ___
• Target: $___
• Probability: ___%

**━━━ ⚠️ RISK WARNINGS ━━━**
• Risk #1: ___
• Risk #2: ___
• Risk #3: ___
• Trade Invalidation level: $___  (এটা break হলে সব plan বাতিল)
• Market condition: Volatile/Stable/Trending/Ranging?
• এই trade avoid করা উচিত কখন?

**━━━ 📊 INDICATOR SCORECARD ━━━**
প্রতিটা indicator-এর সংক্ষিপ্ত verdict দাও:
• RSI:         ___/10
• MACD:        ___/10
• Bollinger:   ___/10
• EMA Stack:   ___/10
• Stochastic:  ___/10
• Ichimoku:    ___/10
• VWAP:        ___/10
• Volume:      ___/10
• Pattern:     ___/10
• Overall:     ___/10

**━━━ 🏆 FINAL VERDICT ━━━**
• Best Trade Setup: SPOT / FUTURES / SCALP
• Overall Signal: BUY/SELL/HOLD
• Signal Strength: ___/10
• Market Phase: Accumulation/Distribution/Markup/Markdown
• Today's Strategy: ___
• Beginner-এর জন্য advice: ___
• Experienced trader-এর জন্য advice: ___
• One-line Summary: ___

সব price সংখ্যায় দাও। Emoji দিয়ে সাজাও। বাংলায় লেখো।"""

            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    self.types.Part.from_bytes(data=chart_bytes, mime_type="image/png"),
                    prompt
                ]
            )
            return response.text

        except Exception as e:
            logger.error(f"Gemini Vision error: {e}")
            return await self.get_quick_advice(symbol, signal, ticker)

    async def get_quick_advice(self, symbol, signal: TradingSignal, ticker):
        if not self.available:
            return self._fallback_analysis(signal, ticker, symbol)

        try:
            data_block = self._full_data_block(symbol, "—", signal, ticker)
            p = ticker['price']

            prompt = f"""{data_block}

তুমি একজন professional crypto trader।
উপরের সব data দেখে complete trading plan বাংলায় দাও।

**🎯 SPOT PLAN** (Entry + Stage1-4 + SL)
**⚡ FUTURES PLAN** (LONG/SHORT + Leverage + TP1-4 + SL + Liquidation + R:R)
**⏱️ SCALP PLAN** (Direction + 3 targets + SL)
**🔮 PREDICTION** (1h + 4h + 24h range)
**🐂🐻 SCENARIOS** (Bull% + Bear% + Base%)
**⚠️ TOP RISKS** (3টা + Invalidation level)
**📊 SCORECARD** (প্রতিটা indicator ___/10)
**🏆 FINAL VERDICT** (Best setup + Score/10 + Summary)

সব price সংখ্যায় দাও। Emoji দিয়ে বাংলায়।"""

            response = self.client.models.generate_content(
                model=self.model, contents=[prompt]
            )
            return response.text

        except Exception as e:
            logger.error(f"Gemini text error: {e}")
            return self._fallback_analysis(signal, ticker, symbol)

    async def get_futures_signal(self, symbol, signal: TradingSignal, ticker):
        if not self.available:
            return self._futures_fallback(signal, ticker, symbol)

        try:
            p = ticker['price']
            data_block = self._full_data_block(symbol, "—", signal, ticker)

            prompt = f"""{data_block}

তুমি একজন expert crypto futures trader।
{symbol} এর জন্য ultra-detailed futures signal বাংলায় দাও।

⚡ FUTURES SIGNAL — {symbol}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 Position: LONG/SHORT (৫টা কারণ data দিয়ে)
⚖️ Leverage:
  • Safe: ___x  | Moderate: ___x  | Aggressive: ___x
  • Recommendation: ___x (কেন?)
💰 Entry Zone: $___  —  $___
✅ Entry Confirmation: কী দেখলে enter করবো?

🎯 PROFIT STAGES:
• TP1: $___ (+___%) → ২৫% close — কেন?
• TP2: $___ (+___%) → ২৫% close — কেন?
• TP3: $___ (+___%) → ২৫% close — কেন?
• TP4: $___ (+___%) → ২৫% close — কেন?

🛑 STOP LOSS PLAN:
• Initial SL: $___ (-___%)
• Break-even: TP___ hit করলে SL ___এ নিয়ে আসো
• Trailing Stop: কীভাবে?
• Invalidation: $___ break হলে সব close

💥 RISK CALCULATIONS:
• Liq Price (5x):   $___
• Liq Price (10x):  $___
• Liq Price (20x):  $___
• Risk/Reward: ___:1
• Win probability:  ___%
• Max drawdown: ___% 

⏰ Trade Duration: ___
🔥 Signal Strength: ___/10
⚠️ Main Risks: ___

সব price সংখ্যায়। Emoji দিয়ে বাংলায়।"""

            response = self.client.models.generate_content(
                model=self.model, contents=[prompt]
            )
            return response.text

        except Exception as e:
            logger.error(f"Futures error: {e}")
            return self._futures_fallback(signal, ticker, symbol)

    async def get_market_sentiment(self, coins_data):
        if not self.available:
            return "⚠️ AI unavailable।"
        try:
            coins_text = "\n".join(
                f"• {c['symbol']}: ${c['price']:,.4f} ({c['change_24h']:+.2f}%)"
                for c in coins_data
            )
            prompt = f"""Crypto market data:
{coins_text}

Professional market analysis বাংলায়:
🌍 Overall: Bullish/Bearish/Neutral? Confidence?
🏆 Best opportunity + কেন?
⚡ Best futures setup কোনটা?
⚠️ Avoid কোনটা + কেন?
📊 Market correlation কোনদিকে?
🔮 Next 24h outlook?
💡 Today's strategy?

Emoji দিয়ে বিস্তারিত বাংলায়।"""

            response = self.client.models.generate_content(
                model=self.model, contents=[prompt]
            )
            return response.text
        except Exception as e:
            return "⚠️ Market sentiment unavailable।"

    def _futures_fallback(self, signal, ticker, symbol):
        p = ticker['price']
        m = 1 if signal.action == "BUY" else -1
        pos = "LONG 📈" if signal.action == "BUY" else "SHORT 📉"

        return f"""⚡ **FUTURES — {symbol}**
━━━━━━━━━━━━━━━━━━━━
📍 {pos} | 5-10x Leverage
💰 Entry: ${p:,.4f}
• TP1: ${p*(1+m*.015):,.4f} (+1.5%) → ২৫%
• TP2: ${p*(1+m*.03):,.4f}  (+3.0%) → ২৫%
• TP3: ${p*(1+m*.05):,.4f}  (+5.0%) → ২৫%
• TP4: ${p*(1+m*.08):,.4f}  (+8.0%) → ২৫%
🛑 SL: ${p*(1-m*.02):,.4f} (-2%)
💥 Liq(5x): ${p*(1-m*.18):,.4f}
💥 Liq(10x): ${p*(1-m*.09):,.4f}
📊 R:R = 1:4 | Signal: {signal.strength} {signal.confidence}%"""

    def _fallback_analysis(self, signal, ticker, symbol):
        p = ticker['price']
        m = 1 if signal.action in ["BUY", "HOLD"] else -1
        pos = "LONG 📈" if m == 1 else "SHORT 📉"
        action = {"BUY": "🟢 BUY", "SELL": "🔴 SELL", "HOLD": "🟡 HOLD"}.get(signal.action, "🟡 HOLD")

        reasons = "\n".join(signal.reasons[:8])

        return f"""📊 **{symbol} — Ultra Analysis**
━━━━━━━━━━━━━━━━━━━━
💰 ${p:,.6f} | 24h: {ticker['change_24h']:+.2f}%
**Signal:** {action} | {signal.strength} | {signal.confidence}%
**Market:** {signal.market_structure} | Trend: {signal.trend} ({signal.trend_strength})

**Key Indicators:**
{reasons}

**Levels:**
📈 R2: ${signal.resistance_2:,.4f} | R1: ${signal.resistance:,.4f}
💰 Price: ${p:,.4f}
📉 S1: ${signal.support:,.4f} | S2: ${signal.support_2:,.4f}
📐 Fib 61.8%: ${signal.fib_618:,.4f} | 38.2%: ${signal.fib_382:,.4f}
🔄 VWAP: ${signal.vwap:,.4f} ({signal.price_vs_vwap})
📊 Pivot: ${signal.pivot:,.4f} | R1: ${signal.pivot_r1:,.4f} | S1: ${signal.pivot_s1:,.4f}

**━━━ SPOT PLAN ━━━**
Entry: ${p:,.4f}
• Stage 1: ${p*(1+m*.02):,.4f} (+2%) → ৩০%
• Stage 2: ${p*(1+m*.04):,.4f} (+4%) → ৩০%
• Stage 3: ${p*(1+m*.07):,.4f} (+7%) → ২০%
• Stage 4: ${p*(1+m*.12):,.4f} (+12%) → ২০%
• SL: ${p*(1-m*.03):,.4f} (-3%)

**━━━ SCALP ━━━**
• TP1: ${p*(1+m*.008):,.4f} (+0.8%)
• TP2: ${p*(1+m*.015):,.4f} (+1.5%)
• TP3: ${p*(1+m*.025):,.4f} (+2.5%)
• SL: ${p*(1-m*.01):,.4f} (-1%)

**━━━ FUTURES ━━━**
{pos} | 5-10x
• TP1: ${p*(1+m*.015):,.4f} (+1.5%) → ২৫%
• TP2: ${p*(1+m*.030):,.4f} (+3.0%) → ২৫%
• TP3: ${p*(1+m*.050):,.4f} (+5.0%) → ২৫%
• TP4: ${p*(1+m*.080):,.4f} (+8.0%) → ২৫%
• SL: ${p*(1-m*.02):,.4f} (-2%)
• Liq(5x): ${p*(1-m*.18):,.4f}
• Liq(10x): ${p*(1-m*.09):,.4f}
• R:R = 1:4"""


# Singleton
ai_analyzer = AIAnalyzer()
