"""
Telegram Bot - All command handlers
🤖 AI Crypto Trading Bot
"""
import asyncio
import logging
from io import BytesIO
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from telegram.constants import ParseMode, ChatAction

from config import config
from options_commands import (cmd_options, cmd_options_ai, cmd_vix,
                              cmd_greeks, cmd_index_futures, cmd_strategy,
                              handle_options_callback)
from stock_commands import (cmd_stock, cmd_stock_analyze, cmd_stockprice,
                             cmd_indices, cmd_stock_alert, cmd_stockmarket,
                             handle_stock_callback)
from binance_client import binance
from technical_analysis import analyzer
from chart_generator import chart_gen
from ai_analyzer import ai_analyzer
from alert_manager import alert_manager

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════

def format_number(num: float) -> str:
    if num >= 1:
        return f"{num:,.4f}"
    else:
        return f"{num:.8f}"

def signal_emoji(action: str) -> str:
    return {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(action, "⚪")

def trend_emoji(trend: str) -> str:
    return {"UPTREND": "📈", "DOWNTREND": "📉", "SIDEWAYS": "➡️"}.get(trend, "❓")


# ═══════════════════════════════════════════
# Command Handlers
# ═══════════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message"""
    user = update.effective_user
    
    keyboard = [
        [InlineKeyboardButton("📊 BTC Signal", callback_data="signal_BTCUSDT"),
         InlineKeyboardButton("📈 ETH Signal", callback_data="signal_ETHUSDT")],
        [InlineKeyboardButton("💰 BTC Price", callback_data="price_BTCUSDT"),
         InlineKeyboardButton("🔥 Top Movers", callback_data="top_movers")],
        [InlineKeyboardButton("📖 Help", callback_data="help"),
         InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome = f"""
🤖 **AI Crypto Trading Bot**
━━━━━━━━━━━━━━━━━━━━
👋 স্বাগতম, {user.first_name}!

আমি একটি Advanced AI-powered crypto trading bot।
Binance-এর real-time data ব্যবহার করে আমি:

✅ Candlestick Chart বিশ্লেষণ করি
✅ BUY/SELL/HOLD signal দিই
✅ RSI, MACD, Bollinger Bands দেখি
✅ Claude AI দিয়ে chart explain করি
✅ Live price alerts পাঠাই
✅ Support & Resistance বলি

**Commands:
`/options NIFTY` — Options Chain
`/optionsai NIFTY` — AI Options Analysis
`/ifutures NIFTY` — Index Futures Signal
`/vix` — India VIX
`/greeks NIFTY 22000 CE 7` — Greeks
`/strategy NIFTY BULLISH` — Strategy**
`/signal BTCUSDT` — Trading signal + Chart
`/price BTCUSDT` — Live price
`/analyze BTCUSDT 1h` — Full AI analysis  
`/alert BTCUSDT 50000` — Price alert set
`/live BTCUSDT` — Live monitoring
`/movers` — Top gainers & losers
`/help` — সব commands


"""
    
    await update.message.reply_text(
        welcome, 
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help message"""
    help_text = """
📚 **সব Commands:**
━━━━━━━━━━━━━━━━━━━━

**📊 Analysis:**
`/signal BTC` — BUY/SELL signal + Chart
`/signal ETH 4h` — Specific timeframe
`/analyze BTC 1h` — AI full analysis
`/price BTC` — Current price + stats

**🔔 Alerts:**
`/alert BTC 50000 above` — BUY alert
`/alert BTC 45000 below` — SELL alert
`/alerts` — সব active alerts দেখো
`/delalert 1` — Alert নম্বর মুছো

**📡 Live Monitor:**
`/live BTC on` — Monitoring চালু
`/live BTC off` — Monitoring বন্ধ
`/monitors` — Active monitors

**📈 Market:**
`/movers` — Top gainers & losers
`/market` — Market overview

**⏰ Timeframes:**
1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w

**উদাহরণ:**
`/signal BTCUSDT 4h`
`/analyze ETHUSDT 1d`
`/alert SOLUSDT 100 above`

⚠️ USDT pair ব্যবহার করুন (BTCUSDT, ETHUSDT)
"""
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def cmd_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Live price with stats"""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/price BTCUSDT`", parse_mode=ParseMode.MARKDOWN)
        return
    
    symbol = context.args[0].upper()
    if not symbol.endswith("USDT"):
        symbol += "USDT"
    
    await update.message.chat.send_action(ChatAction.TYPING)
    
    try:
        ticker = await binance.get_ticker(symbol)
        orderbook = await binance.get_orderbook(symbol)
        
        change_emoji = "📈" if ticker['change_24h'] >= 0 else "📉"
        change_color = "🟢" if ticker['change_24h'] >= 0 else "🔴"
        
        # Best bid/ask
        best_bid = orderbook['bids'][0][0] if orderbook['bids'] else 0
        best_ask = orderbook['asks'][0][0] if orderbook['asks'] else 0
        spread = ((best_ask - best_bid) / best_bid * 100) if best_bid > 0 else 0
        
        message = f"""
{change_emoji} **{ticker['symbol']} Live Price**
━━━━━━━━━━━━━━━━━━━━

💰 **Price:** ${format_number(ticker['price'])}
{change_color} **24h Change:** {ticker['change_24h']:+.2f}%

📊 **24h Stats:**
• High: ${format_number(ticker['high_24h'])}
• Low: ${format_number(ticker['low_24h'])}
• Volume: {ticker['volume_24h']:,.0f} {symbol.replace('USDT','')}
• Quote Vol: ${ticker['quote_volume']:,.0f}

📖 **Order Book:**
• Best Bid: ${format_number(best_bid)}
• Best Ask: ${format_number(best_ask)}
• Spread: {spread:.4f}%

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        
        keyboard = [
            [InlineKeyboardButton("📊 Get Signal", callback_data=f"signal_{symbol}"),
             InlineKeyboardButton("🤖 AI Analysis", callback_data=f"analyze_{symbol}")]
        ]
        
        await update.message.reply_text(
            message, 
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def cmd_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Trading signal with candlestick chart"""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/signal BTCUSDT` বা `/signal BTCUSDT 4h`", 
                                        parse_mode=ParseMode.MARKDOWN)
        return
    
    symbol = context.args[0].upper()
    if not symbol.endswith("USDT"):
        symbol += "USDT"
    
    interval = context.args[1].lower() if len(context.args) > 1 else config.DEFAULT_INTERVAL
    if interval not in config.INTERVALS:
        interval = "1h"
    
    # Send typing indicator
    await update.message.chat.send_action(ChatAction.UPLOAD_PHOTO)
    
    status_msg = await update.message.reply_text(
        f"📊 **{symbol}** {interval} analysis করছি...\n⏳ Chart তৈরি হচ্ছে...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    try:
        # Fetch data
        df = await binance.get_klines(symbol, interval, 100)
        ticker = await binance.get_ticker(symbol)
        
        # Technical analysis
        signal = analyzer.analyze(df)
        
        # Generate chart
        chart_bytes = chart_gen.generate_chart(df, symbol, interval, signal)
        
        # Build signal message
        action = signal.action
        action_text = {
            "BUY": "🟢 **BUY করুন!**",
            "SELL": "🔴 **SELL করুন!**",
            "HOLD": "🟡 **HOLD করুন**"
        }.get(action, "⚪ অপেক্ষা করুন")
        
        caption = f"""
{signal_emoji(action)} **{symbol}** | {config.INTERVALS.get(interval, interval)}
━━━━━━━━━━━━━━━━━━━━

{action_text}
💪 Strength: **{signal.strength}**
🎯 Confidence: **{signal.confidence}%**

💰 Price: **${format_number(ticker['price'])}**
📊 24h: {ticker['change_24h']:+.2f}%

**Indicators:**
• RSI: {signal.rsi:.1f} {"🔴 Overbought" if signal.rsi > 70 else "🟢 Oversold" if signal.rsi < 30 else "⚪ Normal"}
• MACD: {signal.macd_signal}
• BB: {signal.bb_signal}
• Trend: {trend_emoji(signal.trend)} {signal.trend}

**Levels:**
• 🛡️ Stop Loss: ${format_number(signal.stop_loss)}
• 🎯 Take Profit: ${format_number(signal.take_profit)}
• 📉 Support: ${format_number(signal.support)}
• 📈 Resistance: ${format_number(signal.resistance)}


"""
        
        keyboard = [
            [InlineKeyboardButton("🤖 AI Deep Analysis", callback_data=f"ai_{symbol}_{interval}"),
             InlineKeyboardButton("🔄 Refresh", callback_data=f"signal_{symbol}_{interval}")],
            [InlineKeyboardButton("🔔 Set Alert", callback_data=f"setalert_{symbol}"),
             InlineKeyboardButton("📡 Live Monitor", callback_data=f"live_{symbol}")]
        ]
        
        # Delete status message
        await status_msg.delete()
        
        # Send chart
        await update.message.reply_photo(
            photo=BytesIO(chart_bytes),
            caption=caption,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}\n\nSymbol ঠিক আছে তো? (BTCUSDT, ETHUSDT)")
        logger.error(f"Signal error: {e}", exc_info=True)

async def cmd_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Full AI analysis with chart"""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/analyze BTCUSDT 1h`", 
                                        parse_mode=ParseMode.MARKDOWN)
        return
    
    symbol = context.args[0].upper()
    if not symbol.endswith("USDT"):
        symbol += "USDT"
    
    interval = context.args[1].lower() if len(context.args) > 1 else "1h"
    
    await update.message.chat.send_action(ChatAction.UPLOAD_PHOTO)
    
    status_msg = await update.message.reply_text(
        f"🤖 **Claude AI** {symbol} analyze করছে...\n⏳ এটু সময় লাগবে...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    try:
        df = await binance.get_klines(symbol, interval, 100)
        ticker = await binance.get_ticker(symbol)
        signal = analyzer.analyze(df)
        chart_bytes = chart_gen.generate_chart(df, symbol, interval, signal)
        
        # AI analysis
        ai_analysis = await ai_analyzer.analyze_chart(
            chart_bytes, symbol, interval, signal, ticker
        )
        
        await status_msg.delete()
        
        # Send chart first
        await update.message.reply_photo(
            photo=BytesIO(chart_bytes),
            caption=f"📊 **{symbol}** {interval.upper()} Chart",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Send AI analysis
        header = f"🤖 **AI Analysis — {symbol}**\n━━━━━━━━━━━━━━━━━━━━\n\n"
        footer = f"\n\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        await update.message.reply_text(
            header + ai_analysis + footer,
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")
        logger.error(f"Analyze error: {e}", exc_info=True)

async def cmd_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set price alert"""
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Usage:\n`/alert BTCUSDT 50000` — price hit করলে alert\n"
            "`/alert BTCUSDT 50000 above` — উপরে গেলে\n"
            "`/alert BTCUSDT 45000 below` — নিচে গেলে",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    symbol = context.args[0].upper()
    if not symbol.endswith("USDT"):
        symbol += "USDT"
    
    try:
        target_price = float(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Price সঠিকভাবে দিন। যেমন: `50000`")
        return
    
    # Validate symbol
    valid = await binance.validate_symbol(symbol)
    if not valid:
        await update.message.reply_text(f"❌ Symbol '{symbol}' পাওয়া যায়নি!")
        return
    
    # Get current price to determine condition
    ticker = await binance.get_ticker(symbol)
    current_price = ticker['price']
    
    if len(context.args) >= 3:
        condition = context.args[2].lower()
        if condition not in ['above', 'below']:
            condition = 'above' if target_price > current_price else 'below'
    else:
        condition = 'above' if target_price > current_price else 'below'
    
    user_id = update.effective_user.id
    success = alert_manager.add_price_alert(user_id, symbol, target_price, condition)
    
    if success:
        cond_text = "উপরে উঠলে" if condition == 'above' else "নিচে নামলে"
        diff_pct = abs(target_price - current_price) / current_price * 100
        
        message = f"""
✅ **Alert Set Successfully!**

📌 Symbol: **{symbol}**
🎯 Target: **${format_number(target_price)}**
📋 Condition: {cond_text} alert পাবেন
💰 Current: ${format_number(current_price)}
📏 Distance: {diff_pct:.2f}%

যখন price ${format_number(target_price)} {cond_text} আপনাকে notify করব! 🔔
"""
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text("⚠️ এই alert আগে থেকেই আছে!")

async def cmd_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all alerts"""
    user_id = update.effective_user.id
    alerts = alert_manager.get_user_alerts(user_id)
    
    if not alerts:
        await update.message.reply_text("📭 কোনো active alert নেই।\n`/alert BTCUSDT 50000` দিয়ে set করুন!")
        return
    
    message = "🔔 **Your Active Alerts:**\n━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for i, alert in enumerate(alerts, 1):
        cond = "📈 উপরে" if alert.condition == 'above' else "📉 নিচে"
        message += f"{i}. **{alert.symbol}** → ${format_number(alert.target_price)} {cond}\n"
        message += f"   ⏰ Set: {alert.created_at.strftime('%m/%d %H:%M')}\n\n"
    
    message += f"\n`/delalert <number>` দিয়ে মুছুন"
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

async def cmd_delete_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete an alert"""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/delalert 1`", parse_mode=ParseMode.MARKDOWN)
        return
    
    try:
        index = int(context.args[0]) - 1
    except ValueError:
        await update.message.reply_text("❌ সঠিক নম্বর দিন")
        return
    
    user_id = update.effective_user.id
    success = alert_manager.remove_alert(user_id, index)
    
    if success:
        await update.message.reply_text("✅ Alert মুছে ফেলা হয়েছে!")
    else:
        await update.message.reply_text("❌ Alert পাওয়া যায়নি!")

async def cmd_live(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Live monitoring toggle"""
    if not context.args:
        await update.message.reply_text(
            "❌ Usage:\n`/live BTCUSDT on` — monitoring চালু\n`/live BTCUSDT off` — বন্ধ",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    symbol = context.args[0].upper()
    if not symbol.endswith("USDT"):
        symbol += "USDT"
    
    action = context.args[1].lower() if len(context.args) > 1 else "on"
    interval = context.args[2].lower() if len(context.args) > 2 else "1h"
    
    user_id = update.effective_user.id
    
    if action == "on":
        valid = await binance.validate_symbol(symbol)
        if not valid:
            await update.message.reply_text(f"❌ Symbol '{symbol}' পাওয়া যায়নি!")
            return
        
        alert_manager.add_live_monitor(user_id, symbol, interval)
        await update.message.reply_text(
            f"📡 **Live Monitoring Started!**\n\n"
            f"📌 Symbol: **{symbol}**\n"
            f"⏰ Interval: **{interval}**\n\n"
            f"Signal পরিবর্তন হলে auto-alert পাবেন! 🔔\n"
            f"বন্ধ করতে: `/live {symbol} off`",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        alert_manager.stop_live_monitor(user_id, symbol)
        await update.message.reply_text(f"⏹️ **{symbol}** monitoring বন্ধ করা হয়েছে।")

async def cmd_monitors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show active monitors"""
    user_id = update.effective_user.id
    monitors = alert_manager.get_active_monitors(user_id)
    
    if not monitors:
        await update.message.reply_text("📭 কোনো active monitor নেই।\n`/live BTCUSDT on` দিয়ে শুরু করুন!")
        return
    
    message = "📡 **Active Live Monitors:**\n━━━━━━━━━━━━━━━━━━━━\n\n"
    for m in monitors:
        message += f"• **{m.symbol}** [{m.interval}] — Last: {m.last_signal or 'N/A'}\n"
    
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

async def cmd_movers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Top gainers and losers"""
    await update.message.chat.send_action(ChatAction.TYPING)
    
    try:
        gainers, losers = await binance.get_top_movers()
        
        message = "🔥 **Market Top Movers**\n━━━━━━━━━━━━━━━━━━━━\n\n"
        
        message += "📈 **Top Gainers:**\n"
        for coin in gainers:
            change = float(coin['priceChangePercent'])
            price = float(coin['lastPrice'])
            message += f"🟢 {coin['symbol']}: ${format_number(price)} (+{change:.2f}%)\n"
        
        message += "\n📉 **Top Losers:**\n"
        for coin in losers:
            change = float(coin['priceChangePercent'])
            price = float(coin['lastPrice'])
            message += f"🔴 {coin['symbol']}: ${format_number(price)} ({change:.2f}%)\n"
        
        message += f"\n⏰ {datetime.now().strftime('%H:%M:%S')}"
        
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def cmd_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Market overview for popular pairs"""
    await update.message.chat.send_action(ChatAction.TYPING)
    
    message = "🌍 **Market Overview**\n━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for pair in config.POPULAR_PAIRS:
        try:
            ticker = await binance.get_ticker(pair)
            change = ticker['change_24h']
            emoji = "🟢" if change >= 0 else "🔴"
            symbol_short = pair.replace("USDT", "")
            message += f"{emoji} **{symbol_short}**: ${format_number(ticker['price'])} ({change:+.2f}%)\n"
        except:
            pass
    
    message += f"\n⏰ {datetime.now().strftime('%H:%M:%S')}"
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)


# ═══════════════════════════════════════════
# Callback Query Handlers (Button clicks)
# ═══════════════════════════════════════════

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button clicks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("signal_"):
        parts = data.split("_")
        symbol = parts[1]
        interval = parts[2] if len(parts) > 2 else "1h"
        
        context.args = [symbol, interval]
        # Create fake update with message
        update.message = query.message
        await cmd_signal(update, context)
    
    elif data.startswith("price_"):
        symbol = data.split("_")[1]
        context.args = [symbol]
        update.message = query.message
        await cmd_price(update, context)
    
    elif data.startswith("analyze_"):
        parts = data.split("_")
        symbol = parts[1]
        interval = parts[2] if len(parts) > 2 else "1h"
        context.args = [symbol, interval]
        update.message = query.message
        await cmd_analyze(update, context)
    
    elif data == "top_movers":
        update.message = query.message
        await cmd_movers(update, context)
    
    elif data == "help":
        update.message = query.message
        await cmd_help(update, context)
    
    elif data.startswith("live_"):
        symbol = data.split("_")[1]
        context.args = [symbol, "on"]
        update.message = query.message
        await cmd_live(update, context)
    
    elif (data.startswith("options") or data.startswith("optionsai") or 
          data == "vix" or data.startswith("indexfutures")):
        await handle_options_callback(query, context)

    elif data.startswith("stock") or data.startswith("stockai") or data.startswith("stockalert"):
        await handle_stock_callback(query, context)

    elif data.startswith("setalert_"):
        symbol = data.split("_")[1]
        await query.message.reply_text(
            f"🔔 **{symbol}** এর জন্য alert set করুন:\n\n"
            f"`/alert {symbol} <price> above` — উপরে গেলে\n"
            f"`/alert {symbol} <price> below` — নিচে গেলে\n\n"
            f"উদাহরণ: `/alert {symbol} 50000 above`",
            parse_mode=ParseMode.MARKDOWN
        )



async def cmd_futures(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Futures trading signal"""
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: `/futures BTCUSDT` বা `/futures BTCUSDT 4h`",
            parse_mode=ParseMode.MARKDOWN)
        return

    symbol = context.args[0].upper()
    if not symbol.endswith("USDT"):
        symbol += "USDT"
    interval = context.args[1].lower() if len(context.args) > 1 else "1h"

    await update.message.chat.send_action(ChatAction.UPLOAD_PHOTO)
    status_msg = await update.message.reply_text(
        f"⚡ **{symbol}** Futures signal তৈরি হচ্ছে...",
        parse_mode=ParseMode.MARKDOWN)

    try:
        df = await binance.get_klines(symbol, interval, 100)
        ticker = await binance.get_ticker(symbol)
        signal = analyzer.analyze(df)
        chart_bytes = chart_gen.generate_chart(df, symbol, interval, signal)
        futures_analysis = await ai_analyzer.get_futures_signal(symbol, signal, ticker)

        await status_msg.delete()

        keyboard = [
            [InlineKeyboardButton("📊 Full Analysis", callback_data=f"ai_{symbol}_{interval}"),
             InlineKeyboardButton("🔄 Refresh", callback_data=f"futures_{symbol}_{interval}")],
            [InlineKeyboardButton("🔔 Set Alert", callback_data=f"setalert_{symbol}"),
             InlineKeyboardButton("📡 Live Monitor", callback_data=f"live_{symbol}")]
        ]

        await update.message.reply_photo(
            photo=BytesIO(chart_bytes),
            caption=f"⚡ **{symbol}** Futures Signal | {interval.upper()}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        await update.message.reply_text(
            futures_analysis,
            parse_mode=ParseMode.MARKDOWN
        )

    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")
        logger.error(f"Futures error: {e}", exc_info=True)


# ═══════════════════════════════════════════
# Main Bot Class
# ═══════════════════════════════════════════

class CryptoTradingBot:
    def __init__(self):
        self.app = None
    
    async def post_init(self, app):
        """Bot started হলে background tasks শুরু করো"""
        alert_manager.set_app(app)
        await alert_manager.start_background_tasks(binance, analyzer)
        logger.info("✅ Background tasks started!")
    
    def run(self):
        """Bot চালু করো"""
        if not config.TELEGRAM_BOT_TOKEN:
            print("❌ TELEGRAM_BOT_TOKEN .env file-এ set করুন!")
            return
        
        
            print("⚠️ ANTHROPIC_API_KEY নেই। AI analysis disabled থাকবে।")
        
        app = (Application.builder()
               .token(config.TELEGRAM_BOT_TOKEN)
               .post_init(self.post_init)
               .build())
        
        # Register commands
        app.add_handler(CommandHandler("start", cmd_start))
        app.add_handler(CommandHandler("help", cmd_help))
        app.add_handler(CommandHandler("price", cmd_price))
        app.add_handler(CommandHandler("signal", cmd_signal))
        app.add_handler(CommandHandler("analyze", cmd_analyze))
        app.add_handler(CommandHandler("alert", cmd_alert))
        app.add_handler(CommandHandler("alerts", cmd_alerts))
        app.add_handler(CommandHandler("delalert", cmd_delete_alert))
        app.add_handler(CommandHandler("live", cmd_live))
        app.add_handler(CommandHandler("monitors", cmd_monitors))
        app.add_handler(CommandHandler("movers", cmd_movers))
        app.add_handler(CommandHandler("market", cmd_market))
        app.add_handler(CommandHandler("futures", cmd_futures))
        
        # ═══ Stock Market Commands ═══
        app.add_handler(CommandHandler("stock", cmd_stock))
        app.add_handler(CommandHandler("stockai", cmd_stock_analyze))
        app.add_handler(CommandHandler("sp", cmd_stockprice))
        app.add_handler(CommandHandler("indices", cmd_indices))
        app.add_handler(CommandHandler("salert", cmd_stock_alert))
        app.add_handler(CommandHandler("stockmarket", cmd_stockmarket))
        
        # ═══ India Options & Futures ═══
        app.add_handler(CommandHandler("options", cmd_options))
        app.add_handler(CommandHandler("optionsai", cmd_options_ai))
        app.add_handler(CommandHandler("vix", cmd_vix))
        app.add_handler(CommandHandler("greeks", cmd_greeks))
        app.add_handler(CommandHandler("ifutures", cmd_index_futures))
        app.add_handler(CommandHandler("strategy", cmd_strategy))
        
        # Callback query handler (button clicks)
        app.add_handler(CallbackQueryHandler(handle_callback))
        
        print("✅ Bot is running! Telegram-এ start করুন।")
        print("📊 Press Ctrl+C to stop.\n")
        
        app.run_polling(drop_pending_updates=True)
