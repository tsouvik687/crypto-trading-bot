"""
Stock Market Telegram Commands
/stock /stockprice /stockalert /indices /stockmarket
"""
import logging
from io import BytesIO
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatAction

from stock_client import stock_client, POPULAR_STOCKS
from stock_analyzer import stock_ai
from technical_analysis import analyzer
from chart_generator import chart_gen
from alert_manager import alert_manager

logger = logging.getLogger(__name__)


def format_price(price: float, currency: str = "USD") -> str:
    sym = "₹" if currency == "INR" else "$" if currency == "USD" else "£" if currency == "GBP" else "¥" if currency == "JPY" else "€" if currency == "EUR" else "$"
    if price >= 1000:
        return f"{sym}{price:,.2f}"
    elif price >= 1:
        return f"{sym}{price:,.4f}"
    else:
        return f"{sym}{price:,.6f}"


async def cmd_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stock signal + chart + AI analysis"""
    if not context.args:
        help_text = """❌ Usage: `/stock SYMBOL` বা `/stock SYMBOL INTERVAL`

**🇺🇸 US Stocks:**
`/stock AAPL` `/stock TSLA` `/stock NVDA`

**🇮🇳 India NSE:**
`/stock RELIANCE.NS` `/stock TCS.NS` `/stock INFY.NS`

**📈 Indices:**
`/stock ^NSEI` — Nifty 50
`/stock ^GSPC` — S&P 500
`/stock ^FTSE` — FTSE 100

**⏰ Timeframes:** 1h, 4h, 1d, 1w"""
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
        return

    symbol = context.args[0].upper()
    interval = context.args[1].lower() if len(context.args) > 1 else "1d"

    await update.message.chat.send_action(ChatAction.UPLOAD_PHOTO)
    status_msg = await update.message.reply_text(
        f"📊 **{symbol}** analysis করছি...",
        parse_mode=ParseMode.MARKDOWN
    )

    try:
        df = await stock_client.get_klines(symbol, interval, 100)
        ticker = await stock_client.get_ticker(symbol)
        signal = analyzer.analyze(df)
        chart_bytes = chart_gen.generate_chart(df, symbol, interval, signal)

        currency = ticker.get('currency', 'USD')
        p = ticker['price']
        market = ticker.get('market', '🌍')
        curr_sym = "₹" if currency == "INR" else "$" if currency == "USD" else "£" if currency == "GBP" else "¥" if currency == "JPY" else "€"

        change_emoji = "📈" if ticker['change_24h'] >= 0 else "📉"
        action_emoji = "🟢" if signal.action == "BUY" else "🔴" if signal.action == "SELL" else "🟡"

        caption = f"""
{action_emoji} **{symbol}** — {ticker.get('name', '')}
{market} | {ticker.get('exchange', '')} | {interval.upper()}
━━━━━━━━━━━━━━━━━━━━

{change_emoji} **Price:** {curr_sym}{p:,.2f}
📊 **Change:** {ticker['change_24h']:+.2f}%
📈 **High:** {curr_sym}{ticker['high_24h']:,.2f}
📉 **Low:** {curr_sym}{ticker['low_24h']:,.2f}

**Signal:** {action_emoji} {signal.action} | {signal.strength} | {signal.confidence}%
**Trend:** {signal.trend} ({signal.trend_strength})
**Structure:** {signal.market_structure}

**Indicators:**
• RSI: {signal.rsi:.1f} {"🔴" if signal.rsi>70 else "🟢" if signal.rsi<30 else "⚪"}
• MACD: {signal.macd_signal}
• VWAP: {curr_sym}{signal.vwap:,.2f} ({signal.price_vs_vwap})
• Ichimoku: {signal.ichimoku_signal}

**Key Levels:**
• 📈 R1: {curr_sym}{signal.resistance:,.2f} | R2: {curr_sym}{signal.resistance_2:,.2f}
• 📉 S1: {curr_sym}{signal.support:,.2f} | S2: {curr_sym}{signal.support_2:,.2f}
• 🛑 SL: {curr_sym}{signal.stop_loss:,.2f}
• 🎯 TP: {curr_sym}{signal.take_profit:,.2f}
"""

        keyboard = [
            [InlineKeyboardButton("🤖 AI Analysis", callback_data=f"stockai_{symbol}_{interval}"),
             InlineKeyboardButton("🔄 Refresh", callback_data=f"stock_{symbol}_{interval}")],
            [InlineKeyboardButton("🔔 Set Alert", callback_data=f"stockalert_{symbol}"),
             InlineKeyboardButton("📡 Monitor", callback_data=f"stocklive_{symbol}")]
        ]

        await status_msg.delete()
        await update.message.reply_photo(
            photo=BytesIO(chart_bytes),
            caption=caption,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}\n\nSymbol ঠিক আছে? যেমন: AAPL, RELIANCE.NS, ^NSEI")
        logger.error(f"Stock error: {e}", exc_info=True)


async def cmd_stock_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Full AI stock analysis"""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/stockai AAPL` বা `/stockai TCS.NS 1d`",
                                        parse_mode=ParseMode.MARKDOWN)
        return

    symbol = context.args[0].upper()
    interval = context.args[1].lower() if len(context.args) > 1 else "1d"

    await update.message.chat.send_action(ChatAction.UPLOAD_PHOTO)
    status_msg = await update.message.reply_text(
        f"🤖 **{symbol}** AI analysis চলছে...",
        parse_mode=ParseMode.MARKDOWN
    )

    try:
        df = await stock_client.get_klines(symbol, interval, 100)
        ticker = await stock_client.get_ticker(symbol)
        signal = analyzer.analyze(df)
        chart_bytes = chart_gen.generate_chart(df, symbol, interval, signal)

        ai_text = await stock_ai.analyze_chart(chart_bytes, symbol, interval, signal, ticker)

        await status_msg.delete()

        await update.message.reply_photo(
            photo=BytesIO(chart_bytes),
            caption=f"📊 **{symbol}** — {ticker.get('name', '')} | {interval.upper()}",
            parse_mode=ParseMode.MARKDOWN
        )

        # Split if too long
        if len(ai_text) > 4000:
            parts = [ai_text[i:i+4000] for i in range(0, len(ai_text), 4000)]
            for part in parts:
                await update.message.reply_text(part, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(ai_text, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")
        logger.error(f"Stock AI error: {e}", exc_info=True)


async def cmd_stockprice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick stock price"""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/sp AAPL`", parse_mode=ParseMode.MARKDOWN)
        return

    symbol = context.args[0].upper()
    await update.message.chat.send_action(ChatAction.TYPING)

    try:
        ticker = await stock_client.get_ticker(symbol)
        p = ticker['price']
        currency = ticker.get('currency', 'USD')
        market = ticker.get('market', '🌍')
        curr_sym = "₹" if currency == "INR" else "$" if currency == "USD" else "£" if currency == "GBP" else "¥" if currency == "JPY" else "€"

        change_emoji = "📈" if ticker['change_24h'] >= 0 else "📉"

        msg = f"""
{change_emoji} **{symbol}** — {ticker.get('name', '')}
{market} | {ticker.get('exchange', '')}
━━━━━━━━━━━━━━━━━━━━
💰 Price: **{curr_sym}{p:,.2f}**
📊 Change: **{ticker['change_24h']:+.2f}%**
📈 High: {curr_sym}{ticker['high_24h']:,.2f}
📉 Low: {curr_sym}{ticker['low_24h']:,.2f}
📦 Volume: {ticker['volume_24h']:,.0f}
📅 Prev Close: {curr_sym}{ticker.get('prev_close', p):,.2f}
⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        keyboard = [[
            InlineKeyboardButton("📊 Signal", callback_data=f"stock_{symbol}_1d"),
            InlineKeyboardButton("🤖 AI", callback_data=f"stockai_{symbol}_1d")
        ]]
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN,
                                        reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def cmd_indices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """World indices overview"""
    await update.message.chat.send_action(ChatAction.TYPING)
    status = await update.message.reply_text("🌍 World indices লোড হচ্ছে...")

    try:
        overview = await stock_client.get_market_overview()

        msg = "🌍 **World Market Indices**\n━━━━━━━━━━━━━━━━━━━━\n\n"

        for name, ticker in overview.items():
            if not ticker:
                continue
            p = ticker['price']
            chg = ticker['change_24h']
            emoji = "📈" if chg >= 0 else "📉"
            curr = "₹" if "India" in name else "$" if "S&P" in name or "NASDAQ" in name or "Dow" in name else "£" if "FTSE" in name else "¥" if "Nikkei" in name else "€" if "DAX" in name else "$"
            msg += f"{emoji} **{name}:** {curr}{p:,.2f} ({chg:+.2f}%)\n"

        msg += f"\n⏰ {datetime.now().strftime('%H:%M:%S')}"

        await status.edit_text(msg, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        await status.edit_text(f"❌ Error: {str(e)}")


async def cmd_stock_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set stock price alert"""
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Usage:\n`/salert AAPL 200` — price hit হলে\n"
            "`/salert TCS.NS 4000 above` — উপরে গেলে\n"
            "`/salert TSLA 150 below` — নিচে নামলে",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    symbol = context.args[0].upper()
    try:
        target = float(context.args[1])
    except:
        await update.message.reply_text("❌ Price সংখ্যায় দিন")
        return

    valid = await stock_client.validate_symbol(symbol)
    if not valid:
        await update.message.reply_text(f"❌ Symbol '{symbol}' পাওয়া যায়নি!")
        return

    ticker = await stock_client.get_ticker(symbol)
    current = ticker['price']
    condition = context.args[2].lower() if len(context.args) > 2 else ('above' if target > current else 'below')

    user_id = update.effective_user.id
    success = alert_manager.add_price_alert(user_id, symbol, target, condition)

    if success:
        cond_text = "উপরে উঠলে" if condition == 'above' else "নিচে নামলে"
        curr_sym = "₹" if ticker.get('currency') == "INR" else "$"
        diff = abs(target - current) / current * 100

        await update.message.reply_text(
            f"✅ **Stock Alert Set!**\n\n"
            f"📌 {symbol} — {ticker.get('name', '')}\n"
            f"🎯 Target: {curr_sym}{target:,.2f}\n"
            f"📋 {cond_text} alert\n"
            f"💰 Current: {curr_sym}{current:,.2f}\n"
            f"📏 Distance: {diff:.2f}%",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text("⚠️ এই alert আগে থেকেই আছে!")


async def cmd_stockmarket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Popular stocks overview by market"""
    await update.message.chat.send_action(ChatAction.TYPING)
    status = await update.message.reply_text("📊 Stock market data লোড হচ্ছে...")

    popular = [
        ("AAPL", "🇺🇸"), ("TSLA", "🇺🇸"), ("NVDA", "🇺🇸"),
        ("RELIANCE.NS", "🇮🇳"), ("TCS.NS", "🇮🇳"), ("INFY.NS", "🇮🇳"),
    ]

    msg = "📊 **Popular Stocks**\n━━━━━━━━━━━━━━━━━━━━\n\n"

    for sym, flag in popular:
        try:
            ticker = await stock_client.get_ticker(sym)
            p = ticker['price']
            chg = ticker['change_24h']
            emoji = "📈" if chg >= 0 else "📉"
            curr = "₹" if ticker.get('currency') == "INR" else "$"
            name = ticker.get('name', sym)[:20]
            msg += f"{flag}{emoji} **{sym}**: {curr}{p:,.2f} ({chg:+.2f}%)\n"
            import asyncio
            await asyncio.sleep(0.3)
        except:
            pass

    msg += f"\n⏰ {datetime.now().strftime('%H:%M:%S')}"
    await status.edit_text(msg, parse_mode=ParseMode.MARKDOWN)


async def handle_stock_callback(query, context):
    """Handle stock button callbacks"""
    data = query.data

    if data.startswith("stock_"):
        parts = data.split("_")
        symbol = parts[1]
        interval = parts[2] if len(parts) > 2 else "1d"
        from telegram import Update
        fake_update = type('obj', (object,), {'message': query.message, 'effective_user': query.from_user})()
        context.args = [symbol, interval]
        await cmd_stock(fake_update, context)

    elif data.startswith("stockai_"):
        parts = data.split("_")
        symbol = parts[1]
        interval = parts[2] if len(parts) > 2 else "1d"
        fake_update = type('obj', (object,), {'message': query.message, 'effective_user': query.from_user})()
        context.args = [symbol, interval]
        await cmd_stock_analyze(fake_update, context)

    elif data.startswith("stockalert_"):
        symbol = data.split("_")[1]
        await query.message.reply_text(
            f"🔔 **{symbol}** alert:\n`/salert {symbol} <price>`",
            parse_mode=ParseMode.MARKDOWN
        )
