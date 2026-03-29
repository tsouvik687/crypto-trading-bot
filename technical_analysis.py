"""
Technical Analysis Engine
RSI, MACD, Bollinger Bands, EMA, Support/Resistance
"""
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class TradingSignal:
    action: str          # BUY / SELL / HOLD
    strength: str        # STRONG / MODERATE / WEAK
    confidence: int      # 0-100%
    reasons: list        # কেন এই signal
    rsi: float
    macd_signal: str     # BULLISH / BEARISH / NEUTRAL
    bb_signal: str       # OVERSOLD / OVERBOUGHT / NEUTRAL
    trend: str           # UPTREND / DOWNTREND / SIDEWAYS
    support: float
    resistance: float
    stop_loss: float
    take_profit: float

class TechnicalAnalyzer:
    
    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """RSI calculation"""
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period, min_periods=1).mean()
        avg_loss = loss.rolling(window=period, min_periods=1).mean()
        
        rs = avg_gain / avg_loss.replace(0, np.finfo(float).eps)
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_macd(self, df: pd.DataFrame, fast=12, slow=26, signal=9):
        """MACD calculation"""
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram

    def calculate_bollinger_bands(self, df: pd.DataFrame, period=20, std=2):
        """Bollinger Bands"""
        sma = df['close'].rolling(window=period).mean()
        std_dev = df['close'].rolling(window=period).std()
        
        upper = sma + (std_dev * std)
        lower = sma - (std_dev * std)
        
        return upper, sma, lower

    def calculate_ema(self, df: pd.DataFrame, period: int) -> pd.Series:
        """EMA calculation"""
        return df['close'].ewm(span=period, adjust=False).mean()

    def calculate_stochastic(self, df: pd.DataFrame, k_period=14, d_period=3):
        """Stochastic Oscillator"""
        low_min = df['low'].rolling(window=k_period).min()
        high_max = df['high'].rolling(window=k_period).max()
        
        k = 100 * (df['close'] - low_min) / (high_max - low_min + 1e-10)
        d = k.rolling(window=d_period).mean()
        
        return k, d

    def calculate_atr(self, df: pd.DataFrame, period=14) -> pd.Series:
        """Average True Range (volatility)"""
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr

    def find_support_resistance(self, df: pd.DataFrame, window=10) -> tuple:
        """Support & Resistance levels"""
        highs = df['high'].rolling(window=window, center=True).max()
        lows = df['low'].rolling(window=window, center=True).min()
        
        # Recent price levels
        recent_highs = df['high'].tail(50)
        recent_lows = df['low'].tail(50)
        
        resistance = recent_highs.max()
        support = recent_lows.min()
        
        # Better: find local pivots
        pivot_high = []
        pivot_low = []
        
        for i in range(window, len(df) - window):
            if df['high'].iloc[i] == df['high'].iloc[i-window:i+window].max():
                pivot_high.append(df['high'].iloc[i])
            if df['low'].iloc[i] == df['low'].iloc[i-window:i+window].min():
                pivot_low.append(df['low'].iloc[i])
        
        current_price = df['close'].iloc[-1]
        
        # Find nearest support/resistance
        resistances = [h for h in pivot_high if h > current_price]
        supports = [l for l in pivot_low if l < current_price]
        
        resistance = min(resistances) if resistances else current_price * 1.05
        support = max(supports) if supports else current_price * 0.95
        
        return support, resistance

    def detect_candlestick_pattern(self, df: pd.DataFrame) -> list:
        """Candlestick Pattern Recognition"""
        patterns = []
        
        if len(df) < 3:
            return patterns
        
        last = df.iloc[-1]
        prev = df.iloc[-2]
        prev2 = df.iloc[-3]
        
        body = abs(last['close'] - last['open'])
        upper_wick = last['high'] - max(last['close'], last['open'])
        lower_wick = min(last['close'], last['open']) - last['low']
        total_range = last['high'] - last['low']
        
        if total_range == 0:
            return patterns
        
        # Doji
        if body / total_range < 0.1:
            patterns.append("🕯️ Doji (অনিশ্চয়তা)")
        
        # Hammer (Bullish)
        if (lower_wick > 2 * body and upper_wick < body * 0.5 
                and last['close'] > last['open']):
            patterns.append("🔨 Hammer (Bullish)")
        
        # Shooting Star (Bearish)
        if (upper_wick > 2 * body and lower_wick < body * 0.5 
                and last['close'] < last['open']):
            patterns.append("⭐ Shooting Star (Bearish)")
        
        # Bullish Engulfing
        if (prev['close'] < prev['open'] and  # prev red
                last['close'] > last['open'] and  # current green
                last['open'] < prev['close'] and
                last['close'] > prev['open']):
            patterns.append("🟢 Bullish Engulfing")
        
        # Bearish Engulfing
        if (prev['close'] > prev['open'] and  # prev green
                last['close'] < last['open'] and  # current red
                last['open'] > prev['close'] and
                last['close'] < prev['open']):
            patterns.append("🔴 Bearish Engulfing")
        
        # Morning Star (3-candle bullish)
        if (prev2['close'] < prev2['open'] and  # red
                abs(prev['close'] - prev['open']) < abs(prev2['close'] - prev2['open']) * 0.3 and  # small body
                last['close'] > last['open'] and  # green
                last['close'] > (prev2['open'] + prev2['close']) / 2):
            patterns.append("🌟 Morning Star (Bullish)")
        
        # Three White Soldiers
        if (all(df.iloc[-i]['close'] > df.iloc[-i]['open'] for i in range(1, 4)) and
                df.iloc[-1]['close'] > df.iloc[-2]['close'] > df.iloc[-3]['close']):
            patterns.append("⚔️ Three White Soldiers (Strong Bullish)")
        
        # Three Black Crows
        if (all(df.iloc[-i]['close'] < df.iloc[-i]['open'] for i in range(1, 4)) and
                df.iloc[-1]['close'] < df.iloc[-2]['close'] < df.iloc[-3]['close']):
            patterns.append("🦅 Three Black Crows (Strong Bearish)")
        
        return patterns

    def analyze(self, df: pd.DataFrame) -> TradingSignal:
        """Complete technical analysis & signal generation"""
        
        # Calculate all indicators
        rsi = self.calculate_rsi(df)
        macd_line, signal_line, histogram = self.calculate_macd(df)
        bb_upper, bb_mid, bb_lower = self.calculate_bollinger_bands(df)
        ema_9 = self.calculate_ema(df, 9)
        ema_21 = self.calculate_ema(df, 21)
        ema_50 = self.calculate_ema(df, 50)
        ema_200 = self.calculate_ema(df, 200)
        stoch_k, stoch_d = self.calculate_stochastic(df)
        atr = self.calculate_atr(df)
        support, resistance = self.find_support_resistance(df)
        patterns = self.detect_candlestick_pattern(df)
        
        # Current values
        current_price = df['close'].iloc[-1]
        current_rsi = rsi.iloc[-1]
        current_macd = macd_line.iloc[-1]
        current_signal = signal_line.iloc[-1]
        current_hist = histogram.iloc[-1]
        prev_hist = histogram.iloc[-2]
        current_bb_upper = bb_upper.iloc[-1]
        current_bb_lower = bb_lower.iloc[-1]
        current_ema9 = ema_9.iloc[-1]
        current_ema21 = ema_21.iloc[-1]
        current_ema50 = ema_50.iloc[-1] if len(df) >= 50 else current_price
        current_atr = atr.iloc[-1]
        current_stoch = stoch_k.iloc[-1]
        
        # ═══ Signal Scoring System ═══
        buy_score = 0
        sell_score = 0
        reasons = []
        
        # RSI Analysis
        if current_rsi < 30:
            buy_score += 3
            reasons.append(f"✅ RSI: {current_rsi:.1f} (Oversold - BUY zone)")
        elif current_rsi < 40:
            buy_score += 1
            reasons.append(f"✅ RSI: {current_rsi:.1f} (নিচে - Bullish bias)")
        elif current_rsi > 70:
            sell_score += 3
            reasons.append(f"❌ RSI: {current_rsi:.1f} (Overbought - SELL zone)")
        elif current_rsi > 60:
            sell_score += 1
            reasons.append(f"⚠️ RSI: {current_rsi:.1f} (উপরে - Bearish bias)")
        else:
            reasons.append(f"➡️ RSI: {current_rsi:.1f} (Neutral)")
        
        # MACD Analysis
        if current_macd > current_signal and current_hist > 0 and current_hist > prev_hist:
            buy_score += 2
            macd_sig = "BULLISH"
            reasons.append("✅ MACD: Bullish crossover + Momentum বাড়ছে")
        elif current_macd > current_signal:
            buy_score += 1
            macd_sig = "BULLISH"
            reasons.append("✅ MACD: Bullish (MACD > Signal)")
        elif current_macd < current_signal and current_hist < 0 and current_hist < prev_hist:
            sell_score += 2
            macd_sig = "BEARISH"
            reasons.append("❌ MACD: Bearish crossover + Momentum কমছে")
        elif current_macd < current_signal:
            sell_score += 1
            macd_sig = "BEARISH"
            reasons.append("❌ MACD: Bearish (MACD < Signal)")
        else:
            macd_sig = "NEUTRAL"
            reasons.append("➡️ MACD: Neutral")
        
        # Bollinger Bands
        if current_price <= current_bb_lower:
            buy_score += 2
            bb_sig = "OVERSOLD"
            reasons.append("✅ BB: Price নিচের band-এ (Oversold)")
        elif current_price >= current_bb_upper:
            sell_score += 2
            bb_sig = "OVERBOUGHT"
            reasons.append("❌ BB: Price উপরের band-এ (Overbought)")
        else:
            bb_sig = "NEUTRAL"
            bb_pct = (current_price - current_bb_lower) / (current_bb_upper - current_bb_lower) * 100
            reasons.append(f"➡️ BB: Band-এর {bb_pct:.0f}% position-এ")
        
        # EMA Trend
        if current_ema9 > current_ema21 > current_ema50:
            buy_score += 2
            trend = "UPTREND"
            reasons.append("✅ EMA: 9 > 21 > 50 (Strong Uptrend)")
        elif current_ema9 < current_ema21 < current_ema50:
            sell_score += 2
            trend = "DOWNTREND"
            reasons.append("❌ EMA: 9 < 21 < 50 (Strong Downtrend)")
        elif current_ema9 > current_ema21:
            buy_score += 1
            trend = "UPTREND"
            reasons.append("✅ EMA 9 > 21 (Short-term Bullish)")
        elif current_ema9 < current_ema21:
            sell_score += 1
            trend = "DOWNTREND"
            reasons.append("❌ EMA 9 < 21 (Short-term Bearish)")
        else:
            trend = "SIDEWAYS"
        
        # Stochastic
        if current_stoch < 20:
            buy_score += 1
            reasons.append(f"✅ Stochastic: {current_stoch:.1f} (Oversold)")
        elif current_stoch > 80:
            sell_score += 1
            reasons.append(f"❌ Stochastic: {current_stoch:.1f} (Overbought)")
        
        # Support/Resistance proximity
        if abs(current_price - support) / current_price < 0.02:
            buy_score += 1
            reasons.append(f"✅ Price Support-এর কাছে (${support:,.2f})")
        if abs(current_price - resistance) / current_price < 0.02:
            sell_score += 1
            reasons.append(f"❌ Price Resistance-এর কাছে (${resistance:,.2f})")
        
        # Pattern signals
        bullish_patterns = ["Hammer", "Bullish Engulfing", "Morning Star", "Three White Soldiers"]
        bearish_patterns = ["Shooting Star", "Bearish Engulfing", "Three Black Crows"]
        
        for pattern in patterns:
            if any(bp in pattern for bp in bullish_patterns):
                buy_score += 1
                reasons.append(f"✅ Pattern: {pattern}")
            elif any(bp in pattern for bp in bearish_patterns):
                sell_score += 1
                reasons.append(f"❌ Pattern: {pattern}")
            else:
                reasons.append(f"ℹ️ Pattern: {pattern}")
        
        # ═══ Final Decision ═══
        total_score = buy_score + sell_score
        
        if buy_score > sell_score:
            action = "BUY"
            confidence = min(95, int((buy_score / max(total_score, 1)) * 100))
            if buy_score >= 8:
                strength = "STRONG"
            elif buy_score >= 5:
                strength = "MODERATE"
            else:
                strength = "WEAK"
        elif sell_score > buy_score:
            action = "SELL"
            confidence = min(95, int((sell_score / max(total_score, 1)) * 100))
            if sell_score >= 8:
                strength = "STRONG"
            elif sell_score >= 5:
                strength = "MODERATE"
            else:
                strength = "WEAK"
        else:
            action = "HOLD"
            strength = "NEUTRAL"
            confidence = 50
        
        # ═══ Risk Management ═══
        atr_val = current_atr if not pd.isna(current_atr) else current_price * 0.02
        
        if action == "BUY":
            stop_loss = current_price - (atr_val * 2)
            take_profit = current_price + (atr_val * 3)
        elif action == "SELL":
            stop_loss = current_price + (atr_val * 2)
            take_profit = current_price - (atr_val * 3)
        else:
            stop_loss = current_price - (atr_val * 2)
            take_profit = current_price + (atr_val * 2)
        
        return TradingSignal(
            action=action,
            strength=strength,
            confidence=confidence,
            reasons=reasons,
            rsi=current_rsi,
            macd_signal=macd_sig,
            bb_signal=bb_sig,
            trend=trend,
            support=support,
            resistance=resistance,
            stop_loss=stop_loss,
            take_profit=take_profit
        )

# Singleton
analyzer = TechnicalAnalyzer()
