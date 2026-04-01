"""
India Options & Futures Telegram Commands
/options /oi /vix /futures /greeks /strategy
"""
import logging
import asyncio
from io import BytesIO
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatAction

from india_options_client import india_options, INDEX_SYMBOLS
from options_analyzer import options_ai
from stock_client import stock_client
from technical_analysis import analyzer
from chart_generator import chart_gen

logger = logging.getLogger(__name__)


async def cmd_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Full options chain analysis"""
    if not context.args:
        help_text = """📊 **India Options Analysis**
━━━━━━━━━━━━━━━━━━━━

**Index Options:**
`/options NIFTY` — Nifty 50 Options
`/options BANKNIFTY` — Bank Nifty Options
`/options FINNIFTY` — Fin Nifty Options
`/options SENSEX` — Sensex Options

**Equity Options:**
`/options RELIANCE`
`/options TCS`
`/options HDFCBANK`

**Features:**
✅ Complete Options Chain
✅ PCR Analysis
✅ Max Pain calculation
✅ Support/Resistance from OI
✅ AI Strategy recommendations
✅ India VIX analysis"""
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
        return

    symbol = context.args[0].upper()
    await update.message.chat.send_action(ChatAction.TYPING)
    status = await update.message.reply_text(
        f"📊 **{symbol}** Options Chain লোড হচ্ছে...\n⏳ NSE থেকে data নিচ্ছি...",
        parse_mode=ParseMode.MARKDOWN
    )

    try:
        # Fetch all data concurrently
        chain_task = india_options.get_options_chain(symbol)
        vix_task = india_options.get_india_vix()

        chain_data, vix_data = await asyncio.gather(chain_task, vix_task)

        # Analyze
        analysis = india_options.analyze_options_chain(chain_data)

        # Get chart for underlying
        underlying = chain_data.get("underlying_value", 0)

        # Format quick summary first
        pcr = chain_data.get("pcr", 1.0)
        max_call = chain_data.get("max_call_oi_strike", 0)
        max_put = chain_data.get("max_put_oi_strike", 0)
        atm = chain_data.get("atm_strike", 0)
        expiries = chain_data.get("expiry_dates", [])
        vix = vix_data.get("vix", 0)
        pcr_signal = analysis.get("pcr_signal", "")
        pcr_bias = analysis.get("pcr_bias", "NEUTRAL")

        # Quick summary message
        pcr_emoji = "🟢" if "BULL" in pcr_bias else "🔴" if "BEAR" in pcr_bias else "🟡"

        summary = f"""
📊 **{symbol} Options Chain**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 **Underlying:** ₹{underlying:,.2f}
🎯 **ATM Strike:** ₹{atm:,}
📅 **Nearest Expiry:** {expiries[0] if expiries else 'N/A'}

**📈 OI Analysis:**
🔴 Max Call OI (Resistance): ₹{max_call:,}
🟢 Max Put OI (Support): ₹{max_put:,}
📊 Total Call OI: {chain_data.get('total_call_oi',0):,}
📊 Total Put OI: {chain_data.get('total_put_oi',0):,}

**PCR: {pcr:.3f}** {pcr_emoji}
{pcr_signal}

**😰 India VIX: {vix:.2f}**
{vix_data.get('sentiment', '')}

**Recommended Strategies:**
{chr(10).join(analysis.get('strategies', []))}

⏰ {datetime.now().strftime('%H:%M:%S')}
"""

        keyboard = [
            [InlineKeyboardButton("🤖 Full AI Analysis", callback_data=f"optionsai_{symbol}"),
             InlineKeyboardButton("🔄 Refresh", callback_data=f"options_{symbol}")],
            [InlineKeyboardButton("⚡ Futures Signal", callback_data=f"indexfutures_{symbol}"),
             InlineKeyboardButton("📈 VIX Details", callback_data="vix")]
        ]

        await status.delete()
        await update.message.reply_text(
            summary,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        await status.edit_text(f"❌ Error: {str(e)}\n\nSymbol ঠিক আছে তো? যেমন: NIFTY, BANKNIFTY")
        logger.error(f"Options error: {e}", exc_info=True)


async def cmd_options_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Full AI options analysis"""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/optionsai NIFTY`",
                                        parse_mode=ParseMode.MARKDOWN)
        return

    symbol = context.args[0].upper()
    await update.message.chat.send_action(ChatAction.TYPING)
    status = await update.message.reply_text(
        f"🤖 **{symbol}** AI Options Analysis চলছে...\n⏳ সম্পূর্ণ analysis হচ্ছে...",
        parse_mode=ParseMode.MARKDOWN
    )

    try:
        # Fetch data
        chain_data, vix_data = await asyncio.gather(
            india_options.get_options_chain(symbol),
            india_options.get_india_vix()
        )
        analysis = india_options.analyze_options_chain(chain_data)

        # Try to get chart
        chart_bytes = None
        try:
            yf_map = {"NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK", "SENSEX": "^BSESN",
                      "FINNIFTY": "^NSEFIN"}
            yf_sym = yf_map.get(symbol, f"{symbol}.NS")
            df = await stock_client.get_klines(yf_sym, "1d", 100)
            sig = analyzer.analyze(df)
            chart_bytes = chart_gen.generate_chart(df, symbol, "1d", sig)

            # Send chart first
            await update.message.reply_photo(
                photo=BytesIO(chart_bytes),
                caption=f"📊 **{symbol}** Price Chart"
            )
        except Exception as ce:
            logger.warning(f"Chart not available for {symbol}: {ce}")

        # AI Analysis
        ai_text = await options_ai.analyze_options_chain(
            symbol, chain_data, analysis, vix_data, chart_bytes
        )

        await status.delete()

        # Split long message
        if len(ai_text) > 4000:
            parts = [ai_text[i:i+4000] for i in range(0, len(ai_text), 4000)]
            for i, part in enumerate(parts):
                if i == 0:
                    await update.message.reply_text(part, parse_mode=ParseMode.MARKDOWN)
                else:
                    await asyncio.sleep(0.5)
                    await update.message.reply_text(part, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(ai_text, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        await status.edit_text(f"❌ Error: {str(e)}")
        logger.error(f"Options AI error: {e}", exc_info=True)


async def cmd_vix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """India VIX analysis"""
    await update.message.chat.send_action(ChatAction.TYPING)

    try:
        vix_data = await india_options.get_india_vix()
        vix = vix_data.get("vix", 0)
        change = vix_data.get("change", 0)
        sentiment = vix_data.get("sentiment", "")
        outlook = vix_data.get("market_outlook", "NEUTRAL")

        vix_level = ""
        strategy = ""

        if vix < 12:
            vix_level = "😴 অত্যন্ত কম"
            strategy = """• Options SELL strategy ভালো (premium কম)
• Straddle/Strangle buy করার সময় না
• Trend follow করো
• Complacency থেকে সাবধান"""
        elif vix < 16:
            vix_level = "😊 কম"
            strategy = """• Option Selling better (Iron Condor, Credit Spread)
• ATM options buy করা যায়
• Covered Call লেখা যায়
• Market stable, trend trade করো"""
        elif vix < 20:
            vix_level = "😐 Normal"
            strategy = """• Buy এবং Sell দুটোই চলবে
• Spread strategies best
• ATM Straddle consider করো
• Market দেখে সিদ্ধান্ত নাও"""
        elif vix < 25:
            vix_level = "😟 বেশি"
            strategy = """• Option BUY better (premium বেশি হলেও চলবে)
• Stop loss tight রাখো
• Position size কমাও
• Hedge করো portfolio"""
        else:
            vix_level = "😱 অত্যন্ত বেশি (PANIC)"
            strategy = """• Contrarian BUY opportunity!
• Put Sell করা যায় (high premium)
• Straddle Sell করো (caution সহ)
• Market bottom কাছে হতে পারে"""

        msg = f"""
😰 **India VIX Analysis**
━━━━━━━━━━━━━━━━━━━━

📊 **VIX Level: {vix:.2f}** ({change:+.2f}%)
🎭 **Fear Level:** {vix_level}
🌍 **Market Outlook:** {outlook}

**VIX মানে কী?**
• VIX = বাজারের "ভয়ের মাপকাঠি"
• কম VIX = শান্ত বাজার, কম volatility
• বেশি VIX = ভয়, বেশি volatility, বড় move আসতে পারে

**{sentiment}**

**এই VIX-এ Options Strategy:**
{strategy}

**VIX Ranges:**
• < 12: 😴 Extremely Low
• 12-16: 😊 Low (Stable)
• 16-20: 😐 Normal
• 20-25: 😟 High (Caution)
• 25-35: 😨 Very High (Fear)
• > 35: 😱 Extreme Fear (Panic)

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        await update.message.reply_text(f"❌ VIX data error: {str(e)}")


async def cmd_greeks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Calculate option Greeks"""
    if len(context.args) < 4:
        await update.message.reply_text(
            "❌ Usage: `/greeks NIFTY 22000 CE 7`\n"
            "Format: `/greeks SYMBOL STRIKE CE/PE DAYS_TO_EXPIRY`\n\n"
            "Example:\n"
            "`/greeks NIFTY 22000 CE 7` — Nifty 22000 Call, 7 days left\n"
            "`/greeks BANKNIFTY 48000 PE 3` — BankNifty 48000 Put, 3 days left",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    symbol = context.args[0].upper()
    try:
        strike = float(context.args[1])
        option_type = context.args[2].upper()
        days = int(context.args[3])
    except:
        await update.message.reply_text("❌ Correct format: `/greeks NIFTY 22000 CE 7`",
                                        parse_mode=ParseMode.MARKDOWN)
        return

    await update.message.chat.send_action(ChatAction.TYPING)

    try:
        # Get current price
        yf_map = {"NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK", "SENSEX": "^BSESN"}
        yf_sym = yf_map.get(symbol, f"{symbol}.NS")

        ticker = await stock_client.get_ticker(yf_sym)
        spot = ticker['price']

        # Try to get IV from options chain
        iv = 15.0  # Default IV
        try:
            chain = await india_options.get_options_chain(symbol)
            options = chain.get("options", {})
            nearest_expiry = chain.get("expiry_dates", [""])[0]
            for opt in options.get(nearest_expiry, []):
                if opt.get("strike") == strike:
                    if option_type == "CE":
                        iv = opt.get("ce_iv", 15.0) or 15.0
                    else:
                        iv = opt.get("pe_iv", 15.0) or 15.0
                    break
        except:
            pass

        # Calculate Greeks
        greeks = india_options.calculate_options_greeks(
            spot=spot, strike=strike,
            expiry_days=days, iv=iv,
            option_type=option_type
        )

        market_data = {
            "underlying": spot,
            "vix": 0,
            "iv": iv
        }

        # AI Analysis
        ai_text = await options_ai.analyze_specific_option(
            symbol, strike, option_type,
            f"{days} days to expiry",
            greeks, market_data
        )

        msg = f"""
🔢 **{symbol} {strike} {option_type} Greeks**
━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 **Spot Price:** ₹{spot:,.2f}
🎯 **Strike:** ₹{strike:,}
📊 **Type:** {"📈 CALL" if option_type=="CE" else "📉 PUT"}
📅 **Days to Expiry:** {days} days
📊 **IV Used:** {iv:.2f}%

**Theoretical Price:** ₹{greeks.get('theoretical_price', 0):.2f}

**Greeks:**
• 📐 Delta: **{greeks.get('delta', 0):.4f}**
  (₹1 move → ₹{abs(greeks.get('delta',0)):.4f} option change)
• 📊 Gamma: **{greeks.get('gamma', 0):.6f}**
  (Delta change per ₹1 move)
• ⏰ Theta: **₹{greeks.get('theta', 0):.2f}/day**
  (Time decay প্রতিদিন)
• 📈 Vega: **₹{greeks.get('vega', 0):.2f}**
  (IV 1% change-এ option change)

━━━━━━━━━━━━━━━━━━━━━━━━━━
**🤖 AI Analysis:**
{ai_text}
"""

        await update.message.reply_text(msg[:4000], parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
        logger.error(f"Greeks error: {e}", exc_info=True)


async def cmd_index_futures(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Index Futures trading signal"""
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: `/ifutures NIFTY` বা `/ifutures BANKNIFTY`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    symbol = context.args[0].upper()
    interval = context.args[1] if len(context.args) > 1 else "1h"

    await update.message.chat.send_action(ChatAction.UPLOAD_PHOTO)
    status = await update.message.reply_text(
        f"⚡ **{symbol} Futures** signal তৈরি হচ্ছে...",
        parse_mode=ParseMode.MARKDOWN
    )

    try:
        yf_map = {"NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK",
                  "SENSEX": "^BSESN", "FINNIFTY": "^CNXFIN"}
        yf_sym = yf_map.get(symbol, f"^NSEI")

        df = await stock_client.get_klines(yf_sym, interval, 100)
        ticker = await stock_client.get_ticker(yf_sym)
        signal = analyzer.analyze(df)
        chart_bytes = chart_gen.generate_chart(df, symbol, interval, signal)

        p = ticker['price']

        # Lot sizes
        lot_sizes = {"NIFTY": 50, "BANKNIFTY": 15, "FINNIFTY": 40,
                     "MIDCPNIFTY": 75, "SENSEX": 10}
        lot = lot_sizes.get(symbol, 50)
        margin = p * lot * 0.12  # Approx 12% margin

        action = signal.action
        is_long = action == "BUY"
        m = 1 if is_long else -1
        pos = "LONG 📈" if is_long else "SHORT 📉"

        tp1 = p * (1 + m * 0.003)
        tp2 = p * (1 + m * 0.006)
        tp3 = p * (1 + m * 0.012)
        sl  = p * (1 - m * 0.004)

        caption = f"""
⚡ **{symbol} Futures Signal** | {interval.upper()}
━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 **Position: {pos}**
💰 **Spot: ₹{p:,.2f}**
📊 **Signal: {action}** ({signal.strength}) {signal.confidence}%

**🎯 Profit Targets:**
• TP1: ₹{tp1:,.2f} (+{abs(tp1-p)/p*100:.2f}%) — ৩৩%
• TP2: ₹{tp2:,.2f} (+{abs(tp2-p)/p*100:.2f}%) — ৩৩%
• TP3: ₹{tp3:,.2f} (+{abs(tp3-p)/p*100:.2f}%) — ৩৩%
🛑 **Stop Loss: ₹{sl:,.2f}** (-{abs(sl-p)/p*100:.2f}%)

**📊 Lot Info:**
• Lot Size: {lot} units
• Approx Margin: ₹{margin:,.0f}
• P&L per lot (TP1): ₹{abs(tp1-p)*lot:,.0f}
• Max Loss (SL): ₹{abs(sl-p)*lot:,.0f}

**Key Indicators:**
• RSI: {signal.rsi:.1f}
• MACD: {signal.macd_signal}
• Trend: {signal.trend} ({signal.trend_strength})
• Structure: {signal.market_structure}
"""

        keyboard = [
            [InlineKeyboardButton("📊 Options Chain", callback_data=f"options_{symbol}"),
             InlineKeyboardButton("🔄 Refresh", callback_data=f"indexfutures_{symbol}_{interval}")],
            [InlineKeyboardButton("😰 VIX Check", callback_data="vix"),
             InlineKeyboardButton("🤖 AI Analysis", callback_data=f"optionsai_{symbol}")]
        ]

        await status.delete()
        await update.message.reply_photo(
            photo=BytesIO(chart_bytes),
            caption=caption,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        await status.edit_text(f"❌ Error: {str(e)}")
        logger.error(f"Index futures error: {e}", exc_info=True)


async def cmd_strategy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Options strategy recommendations"""
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: `/strategy NIFTY BULLISH` বা `/strategy NIFTY BEARISH` বা `/strategy NIFTY NEUTRAL`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    symbol = context.args[0].upper()
    bias = context.args[1].upper() if len(context.args) > 1 else "NEUTRAL"

    await update.message.chat.send_action(ChatAction.TYPING)

    try:
        # Get VIX and current price
        vix_data = await india_options.get_india_vix()
        vix = vix_data.get("vix", 15)

        yf_map = {"NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK", "SENSEX": "^BSESN"}
        yf_sym = yf_map.get(symbol, f"{symbol}.NS")
        ticker = await stock_client.get_ticker(yf_sym)
        spot = ticker['price']
        atm = round(spot / 50) * 50

        # Strategy based on bias and VIX
        if bias == "BULLISH":
            if vix < 16:
                strategies_text = f"""
**VIX কম ({vix:.1f}) + Bullish = Premium Selling Better**

🎯 **Strategy 1: Bull Put Spread (Best)**
• SELL ₹{atm-100:,} PE
• BUY ₹{atm-200:,} PE
• Net Credit: ₹___ collect করো
• Max Profit: Premium received
• Max Loss: ₹100 difference - premium
• Margin: ~₹{spot*50*0.05:,.0f}

🎯 **Strategy 2: CE Buy (Simple)**
• BUY ₹{atm:,} CE (ATM)
• Target: ₹{atm+150:,}
• SL: যদি Nifty ₹{atm-100:,} নিচে যায়

🎯 **Strategy 3: Ratio Call Spread**
• BUY 1x ₹{atm:,} CE
• SELL 2x ₹{atm+200:,} CE
• Cheap entry, limited profit"""
            else:
                strategies_text = f"""
**VIX বেশি ({vix:.1f}) + Bullish = Premium Buying**

🎯 **Strategy 1: CE Buy**
• BUY ₹{atm:,} CE (ATM)
• High IV = expensive, but worth it
• Target: ₹{atm+200:,}
• SL: ₹{atm-150:,}

🎯 **Strategy 2: Bull Call Spread**
• BUY ₹{atm:,} CE
• SELL ₹{atm+200:,} CE
• Max profit capped কিন্তু সস্তা
• Breakeven: ₹{atm:,} + net debit"""

        elif bias == "BEARISH":
            if vix < 16:
                strategies_text = f"""
**VIX কম ({vix:.1f}) + Bearish = Bear Call Spread**

🎯 **Strategy 1: Bear Call Spread**
• SELL ₹{atm+100:,} CE
• BUY ₹{atm+200:,} CE
• Net Credit collect করো
• Max Profit: Premium received

🎯 **Strategy 2: PE Buy**
• BUY ₹{atm:,} PE (ATM)
• Target: ₹{atm-150:,}
• SL: যদি Nifty ₹{atm+100:,} উপরে যায়"""
            else:
                strategies_text = f"""
**VIX বেশি ({vix:.1f}) + Bearish = Put Buy**

🎯 **Strategy 1: PE Buy (Best)**
• BUY ₹{atm:,} PE
• High IV premium মানবে
• Target: ₹{atm-200:,}

🎯 **Strategy 2: Bear Put Spread**
• BUY ₹{atm:,} PE
• SELL ₹{atm-200:,} PE
• Cost কমাও"""
        else:
            strategies_text = f"""
**Neutral Market = Range Bound Strategies**

🎯 **Strategy 1: Short Straddle (High Risk)**
• SELL ₹{atm:,} CE + SELL ₹{atm:,} PE
• Profit if stays between ₹{atm-150:,} — ₹{atm+150:,}
• Max Profit: Both premiums
• Risk: Unlimited if big move

🎯 **Strategy 2: Iron Condor (Best)**
• SELL ₹{atm+100:,} CE + BUY ₹{atm+200:,} CE
• SELL ₹{atm-100:,} PE + BUY ₹{atm-200:,} PE
• Profit zone: ₹{atm-100:,} — ₹{atm+100:,}
• Limited risk, limited reward

🎯 **Strategy 3: Short Strangle**
• SELL ₹{atm+150:,} CE + SELL ₹{atm-150:,} PE
• Wider range, less premium"""

        msg = f"""
📊 **{symbol} Options Strategy**
━━━━━━━━━━━━━━━━━━━━

💰 **Spot: ₹{spot:,.2f}**
🎯 **ATM: ₹{atm:,}**
😰 **VIX: {vix:.2f}** — {vix_data.get('sentiment','')}
📊 **Bias: {bias}**

{strategies_text}

━━━━━━━━━━━━━━━━━━━━
⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def handle_options_callback(query, context):
    """Handle options button callbacks"""
    data = query.data

    class FakeUpdate:
        def __init__(self, msg, user):
            self.message = msg
            self.effective_user = user

    fake_update = FakeUpdate(query.message, query.from_user)

    if data.startswith("options_"):
        symbol = data.split("_")[1]
        context.args = [symbol]
        await cmd_options(fake_update, context)

    elif data.startswith("optionsai_"):
        symbol = data.split("_")[1]
        context.args = [symbol]
        await cmd_options_ai(fake_update, context)

    elif data == "vix":
        context.args = []
        await cmd_vix(fake_update, context)

    elif data.startswith("indexfutures_"):
        parts = data.split("_")
        symbol = parts[1]
        interval = parts[2] if len(parts) > 2 else "1h"
        context.args = [symbol, interval]
        await cmd_index_futures(fake_update, context)
