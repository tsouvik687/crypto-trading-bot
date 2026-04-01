"""
Stock Market AI Analyzer
Gemini দিয়ে stock analysis — বাংলায়
"""
import logging
from config import config
from technical_analysis import TradingSignal

logger = logging.getLogger(__name__)


class StockAIAnalyzer:
    def __init__(self):
        try:
            from google import genai
            from google.genai import types
            self.client = genai.Client(api_key=config.GEMINI_API_KEY)
            self.types = types
            self.model = "gemini-1.5-flash"
            self.available = True
        except Exception as e:
            logger.error(f"Gemini init failed: {e}")
            self.available = False

    async def analyze_chart(self, chart_bytes, symbol, interval,
                            signal: TradingSignal, ticker: dict) -> str:
        if not self.available:
            return self._fallback(signal, ticker, symbol)

        try:
            p = ticker['price']
            currency = ticker.get('currency', 'USD')
            market = ticker.get('market', '🌍')
            exchange = ticker.get('exchange', '')
            curr_sym = "₹" if "India" in market else "$" if "US" in market else "£" if "London" in market else "¥" if "Japan" in market else "€" if "Germany" in market else "$"

            prompt = f"""তুমি একজন institutional-grade stock market analyst এবং trader।
নিচের chart এবং সব data দেখে সম্পূর্ণ professional stock analysis বাংলায় করো।

╔══════════════════════════════════════════════╗
║         STOCK MARKET DATA                    
╚══════════════════════════════════════════════╝
📊 Stock: {symbol} — {ticker.get('name', symbol)}
🌍 Market: {market} | Exchange: {exchange}
💱 Currency: {currency}
⏰ Timeframe: {interval}
💰 Price: {curr_sym}{p:,.2f}
📊 Change: {ticker['change_24h']:+.2f}%
📈 High: {curr_sym}{ticker['high_24h']:,.2f}
📉 Low:  {curr_sym}{ticker['low_24h']:,.2f}
📦 Volume: {ticker['volume_24h']:,.0f}
📅 Prev Close: {curr_sym}{ticker.get('prev_close', p):,.2f}

╔══════════════════════════════════════════════╗
║         TECHNICAL INDICATORS                 
╚══════════════════════════════════════════════╝
• RSI(14):      {signal.rsi:.2f} — {"Overbought" if signal.rsi>70 else "Oversold" if signal.rsi<30 else "Neutral"}
• RSI Divergence: {signal.rsi_divergence}
• MACD:         {signal.macd_signal} ({signal.macd_value:.4f})
• Bollinger:    {signal.bb_signal} | Position: {signal.bb_position:.1f}%
• EMA Trend:    {signal.trend} ({signal.trend_strength})
• EMA 9/21/50:  {curr_sym}{signal.ema_9:,.2f} / {curr_sym}{signal.ema_21:,.2f} / {curr_sym}{signal.ema_50:,.2f}
• VWAP:         {curr_sym}{signal.vwap:,.2f} ({signal.price_vs_vwap})
• Stochastic:   K={signal.stoch_k:.1f} D={signal.stoch_d:.1f}
• Williams %R:  {signal.williams_r:.1f}
• CCI:          {signal.cci:.1f}
• ATR:          {curr_sym}{signal.atr:,.2f} ({signal.atr_pct:.2f}%)
• Volume:       {signal.volume_trend} ({signal.volume_ratio:.1f}x avg)

╔══════════════════════════════════════════════╗
║         KEY LEVELS                           
╚══════════════════════════════════════════════╝
• Resistance 2: {curr_sym}{signal.resistance_2:,.2f}
• Resistance 1: {curr_sym}{signal.resistance:,.2f}
• Price:        {curr_sym}{p:,.2f} ◄
• Support 1:    {curr_sym}{signal.support:,.2f}
• Support 2:    {curr_sym}{signal.support_2:,.2f}
• Fib 61.8%:    {curr_sym}{signal.fib_618:,.2f}
• Fib 38.2%:    {curr_sym}{signal.fib_382:,.2f}
• Pivot:        {curr_sym}{signal.pivot:,.2f}
• Pivot R1:     {curr_sym}{signal.pivot_r1:,.2f}
• Pivot S1:     {curr_sym}{signal.pivot_s1:,.2f}

╔══════════════════════════════════════════════╗
║         PATTERNS & SIGNAL                    
╚══════════════════════════════════════════════╝
• Patterns: {', '.join(signal.patterns) if signal.patterns else 'None'}
• Market Structure: {signal.market_structure}
• Algorithm: {signal.action} | {signal.strength} | {signal.confidence}%
• Buy Score: {signal.buy_score} | Sell Score: {signal.sell_score}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Chart দেখে সম্পূর্ণ stock analysis বাংলায় করো:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**━━━ 📸 CHART ANALYSIS ━━━**
• Chart-এ কী দেখছো? Candlestick pattern কী?
• Trend কোনদিকে? Strong নাকি weak?
• Volume কেমন? Institutional buying/selling আছে?
• Key breakout বা breakdown zone কোথায়?
• Indicator দেখে কী মনে হচ্ছে?

**━━━ 📰 FUNDAMENTAL CONTEXT ━━━**
• এই stock/index এখন কেমন অবস্থায় আছে?
• কোনো major sector trend আছে?
• {market} market এর overall condition কী?

**━━━ 🎯 TRADING PLAN ━━━**
• BUY 🟢 / SELL 🔴 / HOLD 🟡 — কেন? (৫ কারণ)
• Entry Price: {curr_sym}___
• Entry Confirmation: কী দেখলে ঢুকবো?

📊 PROFIT TARGETS:
• Target 1 (Short-term ১-৭ দিন): {curr_sym}___ (+___%)
• Target 2 (Medium ১-৪ সপ্তাহ): {curr_sym}___ (+___%)
• Target 3 (Long ১-৩ মাস):       {curr_sym}___ (+___%)
• Target 4 (Investment target):    {curr_sym}___ (+___%)

🛑 STOP LOSS:
• Hard Stop: {curr_sym}___ (-___%)
• Trailing Stop strategy: ___

**━━━ 📈 INDEX FUTURES PLAN ━━━**
(যদি Index হয় তাহলে Futures plan দাও)
• Position: LONG/SHORT
• Lot size consideration: ___
• Entry: {curr_sym}___ | TP1-TP3 | SL: {curr_sym}___
• Leverage recommendation: ___

**━━━ 🔮 PRICE PREDICTION ━━━**
• Next week range: {curr_sym}___ — {curr_sym}___
• Next month range: {curr_sym}___ — {curr_sym}___
• 3 month target: {curr_sym}___
• Bull case: {curr_sym}___ | Bear case: {curr_sym}___

**━━━ 🐂🐻 SCENARIOS ━━━**
🐂 Bull: Condition + Target {curr_sym}___ (___%)
🐻 Bear: Condition + Target {curr_sym}___ (-___%)
⚖️ Base case: {curr_sym}___ (___%)

**━━━ ⚠️ RISKS ━━━**
• Market risk: ___
• Stock-specific risk: ___
• Global factor: ___
• Invalidation level: {curr_sym}___

**━━━ 📊 SCORECARD ━━━**
RSI/MACD/BB/EMA/Volume/Pattern প্রতিটা ___/10
Overall: ___/10

**━━━ 🏆 VERDICT ━━━**
• Signal: BUY/SELL/HOLD | Score: ___/10
• Best for: Day trade / Swing / Investment
• Beginner advice: ___
• Pro advice: ___

{curr_sym} দিয়ে সব price লেখো। Emoji দিয়ে বাংলায়।"""

            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    self.types.Part.from_bytes(data=chart_bytes, mime_type="image/png"),
                    prompt
                ]
            )
            return response.text

        except Exception as e:
            logger.error(f"Stock AI error: {e}")
            return await self.get_quick_advice(symbol, signal, ticker)

    async def get_quick_advice(self, symbol, signal: TradingSignal, ticker) -> str:
        if not self.available:
            return self._fallback(signal, ticker, symbol)

        try:
            p = ticker['price']
            market = ticker.get('market', '🌍')
            curr_sym = "₹" if "India" in market else "$"

            prompt = f"""তুমি একজন professional stock trader।
{symbol} ({ticker.get('name','')}) — {market} এর জন্য complete analysis বাংলায়।

Price: {curr_sym}{p:,.2f} | Change: {ticker['change_24h']:+.2f}%
RSI: {signal.rsi:.1f} | MACD: {signal.macd_signal} | Trend: {signal.trend}
Support: {curr_sym}{signal.support:,.2f} | Resistance: {curr_sym}{signal.resistance:,.2f}
Signal: {signal.action} ({signal.strength}) | {signal.confidence}%

দাও:
**🎯 TRADING PLAN**: BUY/SELL/HOLD + Entry + TP1-4 + SL
**📈 INDEX FUTURES**: LONG/SHORT + Entry + TP1-3 + SL (যদি index হয়)
**🔮 PREDICTION**: Week/Month/3Month range
**🐂🐻 SCENARIOS**: Bull + Bear + Base (probability)
**⚠️ RISKS**: Top 3 + Invalidation
**🏆 VERDICT**: Score/10 + Best setup

{curr_sym} দিয়ে price। Emoji দিয়ে বাংলায়।"""

            response = self.client.models.generate_content(
                model=self.model, contents=[prompt]
            )
            return response.text

        except Exception as e:
            logger.error(f"Stock quick error: {e}")
            return self._fallback(signal, ticker, symbol)

    def _fallback(self, signal, ticker, symbol):
        p = ticker['price']
        market = ticker.get('market', '🌍')
        curr_sym = "₹" if "India" in market else "$"
        m = 1 if signal.action == "BUY" else -1

        return f"""📊 **{symbol} — {ticker.get('name', '')}**
━━━━━━━━━━━━━━━━━━━━
{market} | {curr_sym}{p:,.2f} | {ticker['change_24h']:+.2f}%
**Signal:** {"🟢 BUY" if signal.action=="BUY" else "🔴 SELL" if signal.action=="SELL" else "🟡 HOLD"}
**Strength:** {signal.strength} | **Confidence:** {signal.confidence}%

**📊 Targets:**
• TP1: {curr_sym}{p*(1+m*.03):,.2f} (+3%)
• TP2: {curr_sym}{p*(1+m*.06):,.2f} (+6%)
• TP3: {curr_sym}{p*(1+m*.10):,.2f} (+10%)
• TP4: {curr_sym}{p*(1+m*.15):,.2f} (+15%)
• SL:  {curr_sym}{p*(1-m*.04):,.2f} (-4%)

**Levels:**
📈 Resistance: {curr_sym}{signal.resistance:,.2f}
📉 Support: {curr_sym}{signal.support:,.2f}
🔄 VWAP: {curr_sym}{signal.vwap:,.2f}"""


# Singleton
stock_ai = StockAIAnalyzer()
