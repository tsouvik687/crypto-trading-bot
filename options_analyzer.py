"""
India Options AI Analyzer
Gemini দিয়ে Options & Futures analysis — বাংলায়
"""
import logging
from config import config

logger = logging.getLogger(__name__)


class OptionsAIAnalyzer:
    def __init__(self):
        try:
            from google import genai
            from google.genai import types
            self.client = genai.Client(api_key=config.GEMINI_API_KEY)
            self.types = types
            self.model = "gemini-2.0-flash"
            self.available = True
        except Exception as e:
            logger.error(f"Gemini init failed: {e}")
            self.available = False

    async def analyze_options_chain(self, symbol: str, chain_data: dict,
                                    analysis: dict, vix_data: dict,
                                    chart_bytes=None) -> str:
        """Complete options chain AI analysis"""
        if not self.available:
            return self._fallback_options(symbol, chain_data, analysis)

        try:
            underlying = chain_data.get("underlying_value", 0)
            pcr = chain_data.get("pcr", 1.0)
            expiries = chain_data.get("expiry_dates", [])
            max_call = chain_data.get("max_call_oi_strike", 0)
            max_put = chain_data.get("max_put_oi_strike", 0)
            atm = chain_data.get("atm_strike", 0)
            vix = vix_data.get("vix", 0)
            vix_sentiment = vix_data.get("sentiment", "")
            pcr_signal = analysis.get("pcr_signal", "")
            pcr_bias = analysis.get("pcr_bias", "NEUTRAL")
            strategies = analysis.get("strategies", [])

            # Get nearest expiry options data
            nearest_expiry = expiries[0] if expiries else "N/A"
            options_near = chain_data.get("options", {}).get(nearest_expiry, [])

            # ATM options data
            atm_data = None
            for opt in options_near:
                if opt.get("strike") == atm:
                    atm_data = opt
                    break

            # Top 5 strikes near ATM
            near_atm = []
            for opt in sorted(options_near, key=lambda x: abs(x.get("strike", 0) - underlying)):
                if len(near_atm) < 8:
                    near_atm.append(opt)

            # Build options data string
            options_table = ""
            for opt in near_atm:
                strike = opt.get("strike", 0)
                atm_marker = " ← ATM" if strike == atm else ""
                options_table += f"""
Strike {strike}{atm_marker}:
  CALL: LTP=₹{opt.get('ce_ltp',0):.2f} | OI={opt.get('ce_oi',0):,} | ΔOI={opt.get('ce_chg_oi',0):+,} | IV={opt.get('ce_iv',0):.1f}% | Vol={opt.get('ce_volume',0):,}
  PUT:  LTP=₹{opt.get('pe_ltp',0):.2f} | OI={opt.get('pe_oi',0):,} | ΔOI={opt.get('pe_chg_oi',0):+,} | IV={opt.get('pe_iv',0):.1f}% | Vol={opt.get('pe_volume',0):,}"""

            prompt = f"""তুমি একজন expert Indian stock market options trader এবং analyst।
নিচের সম্পূর্ণ options chain data দেখে professional analysis বাংলায় করো।

╔══════════════════════════════════════════════════╗
║        {symbol} OPTIONS CHAIN DATA               
╚══════════════════════════════════════════════════╝
🎯 Underlying: {symbol} @ ₹{underlying:,.2f}
📅 Nearest Expiry: {nearest_expiry}
📊 ATM Strike: ₹{atm:,}
🔴 Max Call OI Strike: ₹{max_call:,} ← KEY RESISTANCE
🟢 Max Put OI Strike: ₹{max_put:,} ← KEY SUPPORT

╔══════════════════════════════════════════════════╗
║              PCR & SENTIMENT                     
╚══════════════════════════════════════════════════╝
• PCR (Put-Call Ratio): {pcr:.3f}
• Signal: {pcr_signal}
• Bias: {pcr_bias}
• Total Call OI: {chain_data.get('total_call_oi',0):,}
• Total Put OI: {chain_data.get('total_put_oi',0):,}

╔══════════════════════════════════════════════════╗
║              INDIA VIX                           
╚══════════════════════════════════════════════════╝
• VIX Level: {vix:.2f} ({vix_data.get('change',0):+.2f}%)
• Market Fear: {vix_sentiment}
• Options Premium: {"EXPENSIVE — Premium Selling Better" if vix > 20 else "CHEAP — Premium Buying Better" if vix < 14 else "MODERATE"}

╔══════════════════════════════════════════════════╗
║           OPTIONS CHAIN (Near ATM)               
╚══════════════════════════════════════════════════╝
{options_table}

{"✅ ATM CE: ₹" + str(atm_data.get('ce_ltp',0)) + " | ATM PE: ₹" + str(atm_data.get('pe_ltp',0)) if atm_data else ""}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
সব data দেখে সম্পূর্ণ options analysis বাংলায় করো:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**━━━ 📊 OPTIONS CHAIN ANALYSIS ━━━**
• Options chain দেখে বাজার কোনদিকে যাবে?
• কোন strike-এ সবচেয়ে বেশি Call OI? এটা কী বলছে?
• কোন strike-এ সবচেয়ে বেশি Put OI? এটা কী বলছে?
• Call OI বাড়ছে নাকি কমছে? মানে কী?
• Put OI বাড়ছে নাকি কমছে? মানে কী?
• Open Interest based support কোথায়? ₹___
• Open Interest based resistance কোথায়? ₹___

**━━━ 📈 PCR ANALYSIS ━━━**
• PCR {pcr:.3f} মানে কী বিস্তারিত বলো
• এই PCR-এ market কোনদিকে যাওয়ার সম্ভাবনা বেশি?
• Historical average PCR-এর তুলনায় কেমন?

**━━━ 😰 VIX ANALYSIS ━━━**
• VIX {vix:.2f} মানে কী?
• Option buy করা ভালো নাকি sell করা?
• আজকের trading-এ VIX কী বলছে?

**━━━ 🎯 DIRECTIONAL VIEW ━━━**
• আজকের বাজার BULLISH নাকি BEARISH?
• Probability: UP ___% | DOWN ___% | RANGE ___%
• Intraday range: ₹___ থেকে ₹___
• Weekly range: ₹___ থেকে ₹___
• Maximum Pain Level: ₹___

**━━━ 💰 OPTIONS TRADING STRATEGIES ━━━**

🎯 STRATEGY 1 — সবচেয়ে Simple (Beginner):
• Strategy Name: ___
• Buy/Sell: ___
• Strike: ₹___ | Expiry: ___
• Premium cost: ₹___ per lot
• Target: ₹___ profit
• Stop Loss: ₹___
• Risk/Reward: ___:1
• কেন এই strategy?

🎯 STRATEGY 2 — Moderate:
• Strategy Name: ___
• Legs: ___
• Net Premium: ₹___
• Max Profit: ₹___ | Max Loss: ₹___
• Breakeven: ₹___
• কখন এই strategy নেবো?

🎯 STRATEGY 3 — Advanced:
• Strategy Name: ___
• Complete setup: ___
• Profit zone: ₹___ থেকে ₹___
• Loss zone: ___
• Greeks consideration: ___

**━━━ ⚡ INDEX FUTURES PLAN ━━━**
• Position: LONG / SHORT
• Entry: ₹___
• TP1: ₹___ | TP2: ₹___ | TP3: ₹___
• Stop Loss: ₹___
• Lot size: 1 lot = ___ units
• Capital required: ₹___ approx
• R:R = ___:1

**━━━ 🔢 GREEKS ANALYSIS ━━━**
ATM options-এর Greeks explain করো:
• Delta: ___ মানে কী?
• Theta: ___ (Time decay প্রতিদিন কত?)
• IV: ___% — High নাকি Low?
• Premium fairly priced আছে?

**━━━ ⚠️ KEY LEVELS ━━━**
• Major Resistance: ₹___ (Max Call OI)
• Minor Resistance: ₹___
• Current Price: ₹{underlying:,.2f}
• Minor Support: ₹___
• Major Support: ₹___ (Max Put OI)
• If ₹{max_call:,} break UP → goes to: ₹___
• If ₹{max_put:,} break DOWN → goes to: ₹___

**━━━ 📅 EXPIRY STRATEGY ━━━**
• This week expiry-তে কী করবো?
• Monthly expiry strategy কী?
• Expiry day-এ কোন strategy best?

**━━━ 🏆 TODAY'S ACTION PLAN ━━━**
সময় অনুযায়ী plan:
• Market Open (9:15-9:30): কী করবো?
• Morning (9:30-11:30): কী করবো?
• Afternoon (11:30-2:00): কী করবো?
• Pre-Close (2:00-3:30): কী করবো?

• Beginner-এর জন্য: ___
• Experienced-এর জন্য: ___
• Risk-averse-এর জন্য: ___

সব price ₹ দিয়ে। Emoji দিয়ে বাংলায়। বিস্তারিত লেখো।"""

            contents = [prompt]
            if chart_bytes:
                contents = [
                    self.types.Part.from_bytes(data=chart_bytes, mime_type="image/png"),
                    prompt
                ]

            response = self.client.models.generate_content(
                model=self.model,
                contents=contents
            )
            return response.text

        except Exception as e:
            logger.error(f"Options AI error: {e}")
            return self._fallback_options(symbol, chain_data, analysis)

    async def analyze_specific_option(self, symbol: str, strike: float,
                                      option_type: str, expiry: str,
                                      greeks: dict, market_data: dict) -> str:
        """Specific option analysis with Greeks"""
        if not self.available:
            return "⚠️ AI analysis unavailable"

        try:
            prompt = f"""তুমি একজন expert options trader।
এই specific option-এর complete analysis বাংলায় দাও।

Option Details:
• Symbol: {symbol}
• Strike: ₹{strike:,}
• Type: {option_type} ({"Call" if option_type=="CE" else "Put"})
• Expiry: {expiry}
• Current LTP: ₹{market_data.get('ltp', 0):.2f}
• OI: {market_data.get('oi', 0):,}
• Volume: {market_data.get('volume', 0):,}
• IV: {market_data.get('iv', 0):.2f}%

Greeks:
• Delta: {greeks.get('delta', 0):.4f}
• Gamma: {greeks.get('gamma', 0):.6f}
• Theta: ₹{greeks.get('theta', 0):.2f}/day
• Vega: ₹{greeks.get('vega', 0):.2f}/1% IV change
• Theoretical Price: ₹{greeks.get('theoretical_price', 0):.2f}

Market: {market_data.get('underlying', 0):.2f} | VIX: {market_data.get('vix', 0):.2f}

বলো:
1. এই option BUY করা উচিত নাকি SELL?
2. Fair value কত? Overpriced নাকি Underpriced?
3. Theta decay কতটা dangerous?
4. Profit হতে হলে market কতটা move করতে হবে?
5. Exit strategy কী হবে?
6. Max profit ও max loss কত?

₹ দিয়ে price। Emoji দিয়ে বাংলায়।"""

            response = self.client.models.generate_content(
                model=self.model, contents=[prompt]
            )
            return response.text

        except Exception as e:
            return f"❌ Analysis error: {e}"

    def _fallback_options(self, symbol, chain_data, analysis):
        underlying = chain_data.get("underlying_value", 0)
        pcr = chain_data.get("pcr", 1.0)
        max_call = chain_data.get("max_call_oi_strike", 0)
        max_put = chain_data.get("max_put_oi_strike", 0)
        atm = chain_data.get("atm_strike", underlying)
        pcr_signal = analysis.get("pcr_signal", "")
        strategies = analysis.get("strategies", [])

        return f"""📊 **{symbol} Options Analysis**
━━━━━━━━━━━━━━━━━━━━
💰 Underlying: ₹{underlying:,.2f}
🎯 ATM Strike: ₹{atm:,}

**PCR Analysis:**
• PCR: {pcr:.3f}
• {pcr_signal}

**Key Levels:**
🔴 Resistance (Max Call OI): ₹{max_call:,}
🟢 Support (Max Put OI): ₹{max_put:,}

**Recommended Strategies:**
{chr(10).join(strategies)}

**Futures Plan:**
• LONG above ₹{max_put:,}
• SHORT below ₹{max_call:,}
• TP: ₹{max_call*1.01:,.0f} | SL: ₹{max_put*0.99:,.0f}"""


# Singleton
options_ai = OptionsAIAnalyzer()
