"""
Alert Manager - Live price alerts & monitoring
"""
import asyncio
import logging
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from config import config

logger = logging.getLogger(__name__)

@dataclass
class PriceAlert:
    user_id: int
    symbol: str
    target_price: float
    condition: str  # 'above' or 'below'
    created_at: datetime = field(default_factory=datetime.now)
    triggered: bool = False

@dataclass  
class LiveMonitor:
    user_id: int
    symbol: str
    interval: str
    last_signal: str = ""
    last_price: float = 0.0
    active: bool = True

class AlertManager:
    def __init__(self):
        self.price_alerts: List[PriceAlert] = []
        self.live_monitors: Dict[str, LiveMonitor] = {}  # key: f"{user_id}_{symbol}"
        self.running = False
        self.app = None  # Telegram app reference
        
    def set_app(self, app):
        self.app = app
    
    def add_price_alert(self, user_id: int, symbol: str, 
                        target_price: float, condition: str) -> bool:
        """নতুন price alert যোগ করো"""
        # Check duplicate
        for alert in self.price_alerts:
            if (alert.user_id == user_id and alert.symbol == symbol 
                    and alert.target_price == target_price and not alert.triggered):
                return False
        
        alert = PriceAlert(
            user_id=user_id,
            symbol=symbol,
            target_price=target_price,
            condition=condition
        )
        self.price_alerts.append(alert)
        logger.info(f"Alert added: {symbol} {condition} ${target_price} for user {user_id}")
        return True
    
    def get_user_alerts(self, user_id: int) -> List[PriceAlert]:
        """User-এর সব active alerts"""
        return [a for a in self.price_alerts 
                if a.user_id == user_id and not a.triggered]
    
    def remove_alert(self, user_id: int, index: int) -> bool:
        """Alert মুছে ফেলো"""
        user_alerts = self.get_user_alerts(user_id)
        if 0 <= index < len(user_alerts):
            self.price_alerts.remove(user_alerts[index])
            return True
        return False
    
    def add_live_monitor(self, user_id: int, symbol: str, interval: str):
        """Live monitoring চালু করো"""
        key = f"{user_id}_{symbol}"
        self.live_monitors[key] = LiveMonitor(
            user_id=user_id,
            symbol=symbol,
            interval=interval,
            active=True
        )
        logger.info(f"Live monitor started: {symbol} for user {user_id}")
    
    def stop_live_monitor(self, user_id: int, symbol: str):
        """Live monitoring বন্ধ করো"""
        key = f"{user_id}_{symbol}"
        if key in self.live_monitors:
            self.live_monitors[key].active = False
            del self.live_monitors[key]
    
    def get_active_monitors(self, user_id: int) -> List[LiveMonitor]:
        """User-এর active monitors"""
        return [m for m in self.live_monitors.values() 
                if m.user_id == user_id and m.active]
    
    async def check_price_alerts(self, binance_client):
        """Price alerts check করো"""
        if not self.price_alerts:
            return
        
        # Get unique symbols
        symbols = list(set(a.symbol for a in self.price_alerts if not a.triggered))
        
        for symbol in symbols:
            try:
                ticker = await binance_client.get_ticker(symbol)
                current_price = ticker['price']
                
                for alert in self.price_alerts:
                    if alert.symbol != symbol or alert.triggered:
                        continue
                    
                    triggered = False
                    if alert.condition == 'above' and current_price >= alert.target_price:
                        triggered = True
                    elif alert.condition == 'below' and current_price <= alert.target_price:
                        triggered = True
                    
                    if triggered:
                        alert.triggered = True
                        await self._send_alert_notification(alert, current_price)
                        
            except Exception as e:
                logger.error(f"Alert check error for {symbol}: {e}")
    
    async def check_live_monitors(self, binance_client, analyzer):
        """Live monitors check করো - signal পরিবর্তন হলে alert দাও"""
        for key, monitor in list(self.live_monitors.items()):
            if not monitor.active:
                continue
            
            try:
                from binance_client import binance
                df = await binance.get_klines(monitor.symbol, monitor.interval, 100)
                signal = analyzer.analyze(df)
                ticker = await binance.get_ticker(monitor.symbol)
                current_price = ticker['price']
                
                # Signal পরিবর্তন হয়েছে কিনা
                if (monitor.last_signal != signal.action and 
                        signal.action in ["BUY", "SELL"] and
                        signal.strength in ["STRONG", "MODERATE"]):
                    
                    monitor.last_signal = signal.action
                    monitor.last_price = current_price
                    await self._send_signal_alert(monitor, signal, ticker)
                
                # Price change > 3%
                if monitor.last_price > 0:
                    price_change = abs(current_price - monitor.last_price) / monitor.last_price * 100
                    if price_change >= 3:
                        monitor.last_price = current_price
                        await self._send_price_change_alert(monitor, ticker, price_change)
                        
            except Exception as e:
                logger.error(f"Live monitor error for {key}: {e}")
    
    async def _send_alert_notification(self, alert: PriceAlert, current_price: float):
        """Price alert notification পাঠাও"""
        if not self.app:
            return
        
        emoji = "📈" if alert.condition == 'above' else "📉"
        condition_text = "উপরে উঠেছে" if alert.condition == 'above' else "নিচে নেমেছে"
        
        message = f"""
🔔 **Price Alert Triggered!**

{emoji} **{alert.symbol}** Target Hit!
💰 Current Price: ${current_price:,.4f}
🎯 Target Was: ${alert.target_price:,.4f}
✅ Price {condition_text} target-এর!

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        try:
            await self.app.bot.send_message(
                chat_id=alert.user_id,
                text=message,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
    
    async def _send_signal_alert(self, monitor: LiveMonitor, signal, ticker: dict):
        """Signal change alert পাঠাও"""
        if not self.app:
            return
        
        emoji = "🚀" if signal.action == "BUY" else "⚠️"
        action_emoji = "🟢 BUY" if signal.action == "BUY" else "🔴 SELL"
        
        message = f"""
{emoji} **Live Alert - {monitor.symbol}**

{action_emoji} Signal! ({signal.strength})
💰 Price: ${ticker['price']:,.4f}
📊 Confidence: {signal.confidence}%
📈 24h: {ticker['change_24h']:+.2f}%

**Indicators:**
• RSI: {signal.rsi:.1f}
• Trend: {signal.trend}
• MACD: {signal.macd_signal}

🛡️ Stop Loss: ${signal.stop_loss:,.4f}
🎯 Take Profit: ${signal.take_profit:,.4f}

⏰ {datetime.now().strftime('%H:%M:%S')}
⚠️ _নিজে verify করুন আগে trade করুন_
"""
        
        try:
            await self.app.bot.send_message(
                chat_id=monitor.user_id,
                text=message,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to send signal alert: {e}")
    
    async def _send_price_change_alert(self, monitor: LiveMonitor, ticker: dict, change_pct: float):
        """Price spike/drop alert"""
        if not self.app:
            return
        
        emoji = "🚀" if change_pct > 0 else "📉"
        
        message = f"""
{emoji} **Price Alert - {monitor.symbol}**

💥 Price {change_pct:.1f}% পরিবর্তন হয়েছে!
💰 Current: ${ticker['price']:,.4f}
📊 24h Change: {ticker['change_24h']:+.2f}%

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        
        try:
            await self.app.bot.send_message(
                chat_id=monitor.user_id,
                text=message,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to send price alert: {e}")
    
    async def start_background_tasks(self, binance_client, analyzer):
        """Background tasks শুরু করো"""
        self.running = True
        
        async def alert_loop():
            while self.running:
                try:
                    await self.check_price_alerts(binance_client)
                    await asyncio.sleep(config.ALERT_CHECK_INTERVAL)
                except Exception as e:
                    logger.error(f"Alert loop error: {e}")
                    await asyncio.sleep(10)
        
        async def monitor_loop():
            while self.running:
                try:
                    await self.check_live_monitors(binance_client, analyzer)
                    await asyncio.sleep(config.LIVE_MONITOR_INTERVAL)
                except Exception as e:
                    logger.error(f"Monitor loop error: {e}")
                    await asyncio.sleep(30)
        
        asyncio.create_task(alert_loop())
        asyncio.create_task(monitor_loop())
        logger.info("Background tasks started!")
    
    def stop(self):
        self.running = False


# Singleton
alert_manager = AlertManager()
