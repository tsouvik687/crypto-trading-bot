"""
Ultra Advanced Technical Analysis Engine
RSI, MACD, BB, EMA, Ichimoku, Fibonacci, VWAP, OBV,
Williams %R, CCI, Pivot Points, Multi S/R levels
"""
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class TradingSignal:
    # Core signal
    action: str            # BUY / SELL / HOLD
    strength: str          # STRONG / MODERATE / WEAK
    confidence: int        # 0-100%
    reasons: list

    # Basic indicators
    rsi: float
    rsi_divergence: str    # BULLISH / BEARISH / NONE
    macd_signal: str
    macd_value: float
    macd_hist: float
    bb_signal: str
    bb_width: float        # Band width %
    bb_position: float     # 0-100% position in band

    # Trend
    trend: str
    trend_strength: str    # STRONG / MODERATE / WEAK

    # EMA stack
    ema_9: float
    ema_21: float
    ema_50: float
    ema_200: float

    # Oscillators
    stoch_k: float
    stoch_d: float
    williams_r: float
    cci: float

    # Volatility
    atr: float
    atr_pct: float         # ATR as % of price

    # Volume
    volume_trend: str      # INCREASING / DECREASING / NEUTRAL
    volume_ratio: float    # Current vs avg volume

    # Levels
    support: float
    resistance: float
    support_2: float       # Second support
    resistance_2: float    # Second resistance
    stop_loss: float
    take_profit: float

    # Fibonacci
    fib_236: float
    fib_382: float
    fib_500: float
    fib_618: float
    fib_786: float

    # Pivot Points
    pivot: float
    pivot_r1: float
    pivot_r2: float
    pivot_r3: float
    pivot_s1: float
    pivot_s2: float
    pivot_s3: float

    # VWAP
    vwap: float
    price_vs_vwap: str     # ABOVE / BELOW

    # Ichimoku
    ichimoku_signal: str   # BULLISH / BEARISH / NEUTRAL
    tenkan: float
    kijun: float

    # Candlestick patterns
    patterns: List[str]

    # Multi-timeframe score
    buy_score: int
    sell_score: int

    # Market structure
    market_structure: str  # UPTREND / DOWNTREND / RANGE / BREAKOUT / BREAKDOWN


class TechnicalAnalyzer:

    # ═══ BASIC INDICATORS ═══

    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.ewm(com=period-1, min_periods=period).mean()
        avg_loss = loss.ewm(com=period-1, min_periods=period).mean()
        rs = avg_gain / avg_loss.replace(0, 1e-10)
        return 100 - (100 / (1 + rs))

    def calculate_macd(self, df, fast=12, slow=26, signal=9):
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    def calculate_bollinger_bands(self, df, period=20, std=2):
        sma = df['close'].rolling(window=period).mean()
        std_dev = df['close'].rolling(window=period).std()
        upper = sma + (std_dev * std)
        lower = sma - (std_dev * std)
        return upper, sma, lower

    def calculate_ema(self, df: pd.DataFrame, period: int) -> pd.Series:
        return df['close'].ewm(span=period, adjust=False).mean()

    def calculate_stochastic(self, df, k_period=14, d_period=3):
        low_min = df['low'].rolling(window=k_period).min()
        high_max = df['high'].rolling(window=k_period).max()
        k = 100 * (df['close'] - low_min) / (high_max - low_min + 1e-10)
        d = k.rolling(window=d_period).mean()
        return k, d

    def calculate_atr(self, df, period=14) -> pd.Series:
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()

    # ═══ ADVANCED INDICATORS ═══

    def calculate_williams_r(self, df, period=14) -> pd.Series:
        """Williams %R — Overbought/Oversold"""
        high_max = df['high'].rolling(window=period).max()
        low_min = df['low'].rolling(window=period).min()
        wr = -100 * (high_max - df['close']) / (high_max - low_min + 1e-10)
        return wr

    def calculate_cci(self, df, period=20) -> pd.Series:
        """Commodity Channel Index"""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        sma = typical_price.rolling(window=period).mean()
        mean_dev = typical_price.rolling(window=period).apply(
            lambda x: np.mean(np.abs(x - x.mean()))
        )
        cci = (typical_price - sma) / (0.015 * mean_dev + 1e-10)
        return cci

    def calculate_vwap(self, df) -> pd.Series:
        """Volume Weighted Average Price"""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
        return vwap

    def calculate_obv(self, df) -> pd.Series:
        """On Balance Volume"""
        obv = pd.Series(index=df.index, dtype=float)
        obv.iloc[0] = df['volume'].iloc[0]
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + df['volume'].iloc[i]
            elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - df['volume'].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        return obv

    def calculate_ichimoku(self, df):
        """Ichimoku Cloud"""
        tenkan = (df['high'].rolling(9).max() + df['low'].rolling(9).min()) / 2
        kijun = (df['high'].rolling(26).max() + df['low'].rolling(26).min()) / 2
        senkou_a = ((tenkan + kijun) / 2).shift(26)
        senkou_b = ((df['high'].rolling(52).max() + df['low'].rolling(52).min()) / 2).shift(26)
        chikou = df['close'].shift(-26)
        return tenkan, kijun, senkou_a, senkou_b, chikou

    def calculate_fibonacci(self, df, lookback=50):
        """Fibonacci Retracement Levels"""
        recent = df.tail(lookback)
        high = recent['high'].max()
        low = recent['low'].min()
        diff = high - low

        return {
            'high': high,
            'low': low,
            '786': high - diff * 0.786,
            '618': high - diff * 0.618,
            '500': high - diff * 0.500,
            '382': high - diff * 0.382,
            '236': high - diff * 0.236,
        }

    def calculate_pivot_points(self, df):
        """Classic Pivot Points"""
        prev = df.iloc[-2]
        high = prev['high']
        low = prev['low']
        close = prev['close']

        pivot = (high + low + close) / 3
        r1 = 2 * pivot - low
        r2 = pivot + (high - low)
        r3 = high + 2 * (pivot - low)
        s1 = 2 * pivot - high
        s2 = pivot - (high - low)
        s3 = low - 2 * (high - pivot)

        return pivot, r1, r2, r3, s1, s2, s3

    def find_multi_support_resistance(self, df, window=10):
        """Multiple Support & Resistance levels"""
        current_price = df['close'].iloc[-1]
        pivot_high = []
        pivot_low = []

        for i in range(window, len(df) - window):
            if df['high'].iloc[i] == df['high'].iloc[i-window:i+window].max():
                pivot_high.append(df['high'].iloc[i])
            if df['low'].iloc[i] == df['low'].iloc[i-window:i+window].min():
                pivot_low.append(df['low'].iloc[i])

        resistances = sorted([h for h in pivot_high if h > current_price])
        supports = sorted([l for l in pivot_low if l < current_price], reverse=True)

        r1 = resistances[0] if resistances else current_price * 1.03
        r2 = resistances[1] if len(resistances) > 1 else current_price * 1.06
        s1 = supports[0] if supports else current_price * 0.97
        s2 = supports[1] if len(supports) > 1 else current_price * 0.94

        return s1, s2, r1, r2

    def detect_rsi_divergence(self, df, rsi):
        """RSI Divergence Detection"""
        if len(df) < 20:
            return "NONE"

        price_last = df['close'].iloc[-1]
        price_prev = df['close'].iloc[-10]
        rsi_last = rsi.iloc[-1]
        rsi_prev = rsi.iloc[-10]

        # Bullish divergence: price lower low, RSI higher low
        if price_last < price_prev and rsi_last > rsi_prev and rsi_last < 50:
            return "BULLISH"
        # Bearish divergence: price higher high, RSI lower high
        elif price_last > price_prev and rsi_last < rsi_prev and rsi_last > 50:
            return "BEARISH"
        return "NONE"

    def detect_market_structure(self, df):
        """Market Structure Analysis"""
        if len(df) < 20:
            return "UNKNOWN"

        closes = df['close'].tail(20)
        highs = df['high'].tail(20)
        lows = df['low'].tail(20)

        # Check for breakout/breakdown
        prev_high = highs.iloc[:-3].max()
        prev_low = lows.iloc[:-3].min()
        current_price = closes.iloc[-1]

        if current_price > prev_high:
            return "BREAKOUT"
        elif current_price < prev_low:
            return "BREAKDOWN"

        # Trend structure
        first_half = closes.iloc[:10].mean()
        second_half = closes.iloc[10:].mean()

        if second_half > first_half * 1.02:
            return "UPTREND"
        elif second_half < first_half * 0.98:
            return "DOWNTREND"
        else:
            return "RANGE"

    def detect_candlestick_pattern(self, df):
        """Enhanced Candlestick Pattern Recognition"""
        patterns = []
        if len(df) < 5:
            return patterns

        c = df.iloc[-1]
        p1 = df.iloc[-2]
        p2 = df.iloc[-3]
        p3 = df.iloc[-4]
        p4 = df.iloc[-5]

        body = abs(c['close'] - c['open'])
        upper_wick = c['high'] - max(c['close'], c['open'])
        lower_wick = min(c['close'], c['open']) - c['low']
        total_range = c['high'] - c['low']
        if total_range == 0:
            return patterns

        body_pct = body / total_range

        # Single candle patterns
        if body_pct < 0.1:
            patterns.append("🕯️ Doji — বাজার অনিশ্চিত")

        if lower_wick > 2.5 * body and upper_wick < 0.3 * body and c['close'] > c['open']:
            patterns.append("🔨 Hammer — Bullish Reversal সম্ভব")

        if lower_wick > 2.5 * body and upper_wick < 0.3 * body and c['close'] < c['open']:
            patterns.append("🔨 Inverted Hammer — Bullish Reversal")

        if upper_wick > 2.5 * body and lower_wick < 0.3 * body and c['close'] < c['open']:
            patterns.append("⭐ Shooting Star — Bearish Reversal সম্ভব")

        if upper_wick > 2.5 * body and lower_wick < 0.3 * body and c['close'] > c['open']:
            patterns.append("⭐ Inverted Shooting Star — Bearish")

        if body_pct > 0.8 and c['close'] > c['open']:
            patterns.append("🟩 Marubozu Bull — Strong Buying Pressure")

        if body_pct > 0.8 and c['close'] < c['open']:
            patterns.append("🟥 Marubozu Bear — Strong Selling Pressure")

        # Two candle patterns
        if (p1['close'] < p1['open'] and c['close'] > c['open'] and
                c['open'] < p1['close'] and c['close'] > p1['open']):
            patterns.append("🟢 Bullish Engulfing — Strong BUY signal")

        if (p1['close'] > p1['open'] and c['close'] < c['open'] and
                c['open'] > p1['close'] and c['close'] < p1['open']):
            patterns.append("🔴 Bearish Engulfing — Strong SELL signal")

        if (p1['close'] > p1['open'] and c['close'] > c['open'] and
                c['open'] > p1['close'] and c['close'] > p1['high']):
            patterns.append("🚀 Bullish Gap Up — Strong Momentum")

        # Three candle patterns
        if (p2['close'] < p2['open'] and
                abs(p1['close']-p1['open']) < abs(p2['close']-p2['open'])*0.3 and
                c['close'] > c['open'] and
                c['close'] > (p2['open']+p2['close'])/2):
            patterns.append("🌟 Morning Star — Powerful Bullish Reversal")

        if (p2['close'] > p2['open'] and
                abs(p1['close']-p1['open']) < abs(p2['close']-p2['open'])*0.3 and
                c['close'] < c['open'] and
                c['close'] < (p2['open']+p2['close'])/2):
            patterns.append("🌙 Evening Star — Powerful Bearish Reversal")

        if (all(df.iloc[-i]['close'] > df.iloc[-i]['open'] for i in range(1, 4)) and
                df.iloc[-1]['close'] > df.iloc[-2]['close'] > df.iloc[-3]['close']):
            patterns.append("⚔️ Three White Soldiers — Very Strong Bullish")

        if (all(df.iloc[-i]['close'] < df.iloc[-i]['open'] for i in range(1, 4)) and
                df.iloc[-1]['close'] < df.iloc[-2]['close'] < df.iloc[-3]['close']):
            patterns.append("🦅 Three Black Crows — Very Strong Bearish")

        # Four/Five candle patterns
        bodies = [abs(df.iloc[-i]['close']-df.iloc[-i]['open']) for i in range(1, 5)]
        if (max(bodies[1:]) < bodies[0] * 0.3):
            if c['close'] > c['open']:
                patterns.append("💥 Bullish Harami — Reversal Forming")
            else:
                patterns.append("💥 Bearish Harami — Reversal Forming")

        return patterns

    def analyze(self, df: pd.DataFrame) -> TradingSignal:
        """Complete Ultra Advanced Analysis"""

        # ═══ Calculate All Indicators ═══
        rsi = self.calculate_rsi(df)
        macd_line, signal_line, histogram = self.calculate_macd(df)
        bb_upper, bb_mid, bb_lower = self.calculate_bollinger_bands(df)
        ema_9   = self.calculate_ema(df, 9)
        ema_21  = self.calculate_ema(df, 21)
        ema_50  = self.calculate_ema(df, 50)
        ema_200 = self.calculate_ema(df, 200)
        stoch_k, stoch_d = self.calculate_stochastic(df)
        atr = self.calculate_atr(df)
        williams_r = self.calculate_williams_r(df)
        cci = self.calculate_cci(df)
        vwap = self.calculate_vwap(df)
        obv = self.calculate_obv(df)
        tenkan, kijun, senkou_a, senkou_b, chikou = self.calculate_ichimoku(df)
        fib = self.calculate_fibonacci(df)
        pivot, pr1, pr2, pr3, ps1, ps2, ps3 = self.calculate_pivot_points(df)
        s1, s2, r1, r2 = self.find_multi_support_resistance(df)
        patterns = self.detect_candlestick_pattern(df)
        market_structure = self.detect_market_structure(df)
        rsi_div = self.detect_rsi_divergence(df, rsi)

        # ═══ Current Values ═══
        price = df['close'].iloc[-1]
        curr_rsi      = float(rsi.iloc[-1])
        curr_macd     = float(macd_line.iloc[-1])
        curr_signal   = float(signal_line.iloc[-1])
        curr_hist     = float(histogram.iloc[-1])
        prev_hist     = float(histogram.iloc[-2])
        curr_bb_up    = float(bb_upper.iloc[-1])
        curr_bb_low   = float(bb_lower.iloc[-1])
        curr_bb_mid   = float(bb_mid.iloc[-1])
        curr_ema9     = float(ema_9.iloc[-1])
        curr_ema21    = float(ema_21.iloc[-1])
        curr_ema50    = float(ema_50.iloc[-1]) if len(df)>=50 else price
        curr_ema200   = float(ema_200.iloc[-1]) if len(df)>=200 else price
        curr_stoch_k  = float(stoch_k.iloc[-1])
        curr_stoch_d  = float(stoch_d.iloc[-1])
        curr_wr       = float(williams_r.iloc[-1])
        curr_cci      = float(cci.iloc[-1])
        curr_vwap     = float(vwap.iloc[-1])
        curr_atr      = float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else price*0.02
        curr_tenkan   = float(tenkan.iloc[-1]) if not pd.isna(tenkan.iloc[-1]) else price
        curr_kijun    = float(kijun.iloc[-1]) if not pd.isna(kijun.iloc[-1]) else price

        # BB position & width
        bb_range = curr_bb_up - curr_bb_low
        bb_pos = ((price - curr_bb_low) / bb_range * 100) if bb_range > 0 else 50
        bb_width = (bb_range / curr_bb_mid * 100) if curr_bb_mid > 0 else 0

        # ATR %
        atr_pct = (curr_atr / price * 100)

        # Volume trend
        avg_vol = df['volume'].rolling(20).mean().iloc[-1]
        curr_vol = df['volume'].iloc[-1]
        vol_ratio = curr_vol / avg_vol if avg_vol > 0 else 1.0
        if vol_ratio > 1.3:
            volume_trend = "INCREASING"
        elif vol_ratio < 0.7:
            volume_trend = "DECREASING"
        else:
            volume_trend = "NEUTRAL"

        # OBV trend
        obv_trend_up = obv.iloc[-1] > obv.rolling(5).mean().iloc[-1]

        # Ichimoku signal
        cloud_top = max(float(senkou_a.iloc[-1]) if not pd.isna(senkou_a.iloc[-1]) else price,
                       float(senkou_b.iloc[-1]) if not pd.isna(senkou_b.iloc[-1]) else price)
        cloud_bot = min(float(senkou_a.iloc[-1]) if not pd.isna(senkou_a.iloc[-1]) else price,
                       float(senkou_b.iloc[-1]) if not pd.isna(senkou_b.iloc[-1]) else price)

        if price > cloud_top and curr_tenkan > curr_kijun:
            ichimoku_sig = "BULLISH"
        elif price < cloud_bot and curr_tenkan < curr_kijun:
            ichimoku_sig = "BEARISH"
        else:
            ichimoku_sig = "NEUTRAL"

        # ═══ Scoring System ═══
        buy_score = 0
        sell_score = 0
        reasons = []

        # RSI (max 4 points)
        if curr_rsi < 25:
            buy_score += 4
            reasons.append(f"🟢 RSI {curr_rsi:.1f} — Extreme Oversold (Strong BUY)")
        elif curr_rsi < 35:
            buy_score += 3
            reasons.append(f"✅ RSI {curr_rsi:.1f} — Oversold (BUY zone)")
        elif curr_rsi < 45:
            buy_score += 1
            reasons.append(f"✅ RSI {curr_rsi:.1f} — Mildly Bullish")
        elif curr_rsi > 75:
            sell_score += 4
            reasons.append(f"🔴 RSI {curr_rsi:.1f} — Extreme Overbought (Strong SELL)")
        elif curr_rsi > 65:
            sell_score += 3
            reasons.append(f"❌ RSI {curr_rsi:.1f} — Overbought (SELL zone)")
        elif curr_rsi > 55:
            sell_score += 1
            reasons.append(f"⚠️ RSI {curr_rsi:.1f} — Mildly Bearish")
        else:
            reasons.append(f"➡️ RSI {curr_rsi:.1f} — Neutral Zone")

        # RSI Divergence
        if rsi_div == "BULLISH":
            buy_score += 3
            reasons.append("🔥 RSI Bullish Divergence — Reversal আসছে!")
        elif rsi_div == "BEARISH":
            sell_score += 3
            reasons.append("💀 RSI Bearish Divergence — Drop আসছে!")

        # MACD (max 3 points)
        if curr_macd > curr_signal and curr_hist > 0 and curr_hist > prev_hist:
            buy_score += 3
            reasons.append("✅ MACD Bullish Crossover + Histogram বাড়ছে")
            macd_sig = "BULLISH"
        elif curr_macd > curr_signal and curr_hist > prev_hist:
            buy_score += 2
            reasons.append("✅ MACD Bullish + Momentum improving")
            macd_sig = "BULLISH"
        elif curr_macd > curr_signal:
            buy_score += 1
            reasons.append("✅ MACD Bullish (MACD > Signal)")
            macd_sig = "BULLISH"
        elif curr_macd < curr_signal and curr_hist < 0 and curr_hist < prev_hist:
            sell_score += 3
            reasons.append("❌ MACD Bearish Crossover + Histogram কমছে")
            macd_sig = "BEARISH"
        elif curr_macd < curr_signal and curr_hist < prev_hist:
            sell_score += 2
            reasons.append("❌ MACD Bearish + Momentum deteriorating")
            macd_sig = "BEARISH"
        elif curr_macd < curr_signal:
            sell_score += 1
            reasons.append("❌ MACD Bearish (MACD < Signal)")
            macd_sig = "BEARISH"
        else:
            macd_sig = "NEUTRAL"
            reasons.append("➡️ MACD Neutral")

        # Bollinger Bands (max 3 points)
        if price <= curr_bb_low:
            buy_score += 3
            bb_sig = "OVERSOLD"
            reasons.append(f"✅ BB Oversold — নিচের band touch করেছে")
        elif bb_pos < 20:
            buy_score += 2
            bb_sig = "OVERSOLD"
            reasons.append(f"✅ BB নিচের দিকে ({bb_pos:.0f}% position)")
        elif price >= curr_bb_up:
            sell_score += 3
            bb_sig = "OVERBOUGHT"
            reasons.append(f"❌ BB Overbought — উপরের band touch করেছে")
        elif bb_pos > 80:
            sell_score += 2
            bb_sig = "OVERBOUGHT"
            reasons.append(f"❌ BB উপরের দিকে ({bb_pos:.0f}% position)")
        else:
            bb_sig = "NEUTRAL"
            reasons.append(f"➡️ BB Neutral ({bb_pos:.0f}% position, Width: {bb_width:.1f}%)")

        # EMA Stack (max 4 points)
        if curr_ema9 > curr_ema21 > curr_ema50 > curr_ema200:
            buy_score += 4
            trend = "UPTREND"
            trend_strength = "STRONG"
            reasons.append("✅ EMA 9>21>50>200 — Perfect Bull Stack")
        elif curr_ema9 > curr_ema21 > curr_ema50:
            buy_score += 3
            trend = "UPTREND"
            trend_strength = "STRONG"
            reasons.append("✅ EMA 9>21>50 — Strong Uptrend")
        elif curr_ema9 > curr_ema21:
            buy_score += 1
            trend = "UPTREND"
            trend_strength = "MODERATE"
            reasons.append("✅ EMA 9>21 — Short-term Bullish")
        elif curr_ema9 < curr_ema21 < curr_ema50 < curr_ema200:
            sell_score += 4
            trend = "DOWNTREND"
            trend_strength = "STRONG"
            reasons.append("❌ EMA 9<21<50<200 — Perfect Bear Stack")
        elif curr_ema9 < curr_ema21 < curr_ema50:
            sell_score += 3
            trend = "DOWNTREND"
            trend_strength = "STRONG"
            reasons.append("❌ EMA 9<21<50 — Strong Downtrend")
        elif curr_ema9 < curr_ema21:
            sell_score += 1
            trend = "DOWNTREND"
            trend_strength = "MODERATE"
            reasons.append("❌ EMA 9<21 — Short-term Bearish")
        else:
            trend = "SIDEWAYS"
            trend_strength = "WEAK"

        # Stochastic (max 2 points)
        if curr_stoch_k < 20 and curr_stoch_k > curr_stoch_d:
            buy_score += 2
            reasons.append(f"✅ Stoch {curr_stoch_k:.1f} Oversold + Bullish Cross")
        elif curr_stoch_k < 20:
            buy_score += 1
            reasons.append(f"✅ Stoch {curr_stoch_k:.1f} Oversold")
        elif curr_stoch_k > 80 and curr_stoch_k < curr_stoch_d:
            sell_score += 2
            reasons.append(f"❌ Stoch {curr_stoch_k:.1f} Overbought + Bearish Cross")
        elif curr_stoch_k > 80:
            sell_score += 1
            reasons.append(f"❌ Stoch {curr_stoch_k:.1f} Overbought")

        # Williams %R (max 2 points)
        if curr_wr < -80:
            buy_score += 2
            reasons.append(f"✅ Williams %R {curr_wr:.1f} — Oversold")
        elif curr_wr > -20:
            sell_score += 2
            reasons.append(f"❌ Williams %R {curr_wr:.1f} — Overbought")

        # CCI (max 2 points)
        if curr_cci < -100:
            buy_score += 2
            reasons.append(f"✅ CCI {curr_cci:.0f} — Oversold zone")
        elif curr_cci > 100:
            sell_score += 2
            reasons.append(f"❌ CCI {curr_cci:.0f} — Overbought zone")

        # VWAP (max 2 points)
        vwap_signal = "ABOVE" if price > curr_vwap else "BELOW"
        if price > curr_vwap:
            buy_score += 2
            reasons.append(f"✅ Price VWAP-এর উপরে (${curr_vwap:,.4f}) — Bullish")
        else:
            sell_score += 2
            reasons.append(f"❌ Price VWAP-এর নিচে (${curr_vwap:,.4f}) — Bearish")

        # Ichimoku (max 2 points)
        if ichimoku_sig == "BULLISH":
            buy_score += 2
            reasons.append("✅ Ichimoku Bullish — Cloud-এর উপরে")
        elif ichimoku_sig == "BEARISH":
            sell_score += 2
            reasons.append("❌ Ichimoku Bearish — Cloud-এর নিচে")

        # OBV (max 1 point)
        if obv_trend_up:
            buy_score += 1
            reasons.append("✅ OBV Bullish — Accumulation চলছে")
        else:
            sell_score += 1
            reasons.append("❌ OBV Bearish — Distribution চলছে")

        # Volume (max 2 points)
        if volume_trend == "INCREASING" and trend == "UPTREND":
            buy_score += 2
            reasons.append(f"✅ Volume বাড়ছে ({vol_ratio:.1f}x avg) + Uptrend = Confirmed")
        elif volume_trend == "INCREASING" and trend == "DOWNTREND":
            sell_score += 2
            reasons.append(f"❌ Volume বাড়ছে ({vol_ratio:.1f}x avg) + Downtrend = Confirmed")
        elif volume_trend == "DECREASING":
            reasons.append(f"⚠️ Volume কম ({vol_ratio:.1f}x avg) — Trend weak")

        # Market Structure (max 2 points)
        if market_structure == "BREAKOUT":
            buy_score += 2
            reasons.append("🚀 BREAKOUT — Previous high break করেছে!")
        elif market_structure == "BREAKDOWN":
            sell_score += 2
            reasons.append("💥 BREAKDOWN — Previous low break করেছে!")

        # Support/Resistance proximity
        if abs(price - s1) / price < 0.015:
            buy_score += 2
            reasons.append(f"✅ Strong Support-এর কাছে (${s1:,.4f})")
        if abs(price - r1) / price < 0.015:
            sell_score += 2
            reasons.append(f"❌ Strong Resistance-এর কাছে (${r1:,.4f})")

        # Candlestick patterns
        bullish_words = ["Bullish", "Hammer", "Morning Star", "White Soldiers", "Gap Up"]
        bearish_words = ["Bearish", "Shooting Star", "Evening Star", "Black Crows"]

        for pat in patterns:
            if any(w in pat for w in bullish_words):
                buy_score += 2
                reasons.append(f"✅ {pat}")
            elif any(w in pat for w in bearish_words):
                sell_score += 2
                reasons.append(f"❌ {pat}")
            else:
                reasons.append(f"ℹ️ {pat}")

        # Fibonacci levels proximity
        for level_name, level_price in [('61.8%', fib['618']), ('50%', fib['500']), ('38.2%', fib['382'])]:
            if abs(price - level_price) / price < 0.01:
                reasons.append(f"📐 Fibonacci {level_name} level-এ (${level_price:,.4f}) — Key level!")

        # ═══ Final Signal ═══
        total = buy_score + sell_score

        if buy_score > sell_score:
            action = "BUY"
            conf = min(95, int((buy_score / max(total, 1)) * 100))
            strength = "STRONG" if buy_score >= 15 else "MODERATE" if buy_score >= 8 else "WEAK"
        elif sell_score > buy_score:
            action = "SELL"
            conf = min(95, int((sell_score / max(total, 1)) * 100))
            strength = "STRONG" if sell_score >= 15 else "MODERATE" if sell_score >= 8 else "WEAK"
        else:
            action = "HOLD"
            strength = "NEUTRAL"
            conf = 50

        # ═══ ATR-based Risk Levels ═══
        if action == "BUY":
            sl = price - (curr_atr * 2.5)
            tp = price + (curr_atr * 4)
        elif action == "SELL":
            sl = price + (curr_atr * 2.5)
            tp = price - (curr_atr * 4)
        else:
            sl = price - (curr_atr * 2)
            tp = price + (curr_atr * 2)

        return TradingSignal(
            action=action, strength=strength, confidence=conf, reasons=reasons,
            rsi=curr_rsi, rsi_divergence=rsi_div,
            macd_signal=macd_sig, macd_value=curr_macd, macd_hist=curr_hist,
            bb_signal=bb_sig, bb_width=bb_width, bb_position=bb_pos,
            trend=trend, trend_strength=trend_strength,
            ema_9=curr_ema9, ema_21=curr_ema21, ema_50=curr_ema50, ema_200=curr_ema200,
            stoch_k=curr_stoch_k, stoch_d=curr_stoch_d,
            williams_r=curr_wr, cci=curr_cci,
            atr=curr_atr, atr_pct=atr_pct,
            volume_trend=volume_trend, volume_ratio=vol_ratio,
            support=s1, resistance=r1, support_2=s2, resistance_2=r2,
            stop_loss=sl, take_profit=tp,
            fib_236=fib['236'], fib_382=fib['382'], fib_500=fib['500'],
            fib_618=fib['618'], fib_786=fib['786'],
            pivot=pivot, pivot_r1=pr1, pivot_r2=pr2, pivot_r3=pr3,
            pivot_s1=ps1, pivot_s2=ps2, pivot_s3=ps3,
            vwap=curr_vwap, price_vs_vwap=vwap_signal,
            ichimoku_signal=ichimoku_sig, tenkan=curr_tenkan, kijun=curr_kijun,
            patterns=patterns, buy_score=buy_score, sell_score=sell_score,
            market_structure=market_structure
        )


# Singleton
analyzer = TechnicalAnalyzer()
