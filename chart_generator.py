"""
Advanced Candlestick Chart Generator
মনোমুগ্ধকর charts তৈরি করে Claude AI-র জন্য
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import matplotlib.gridspec as gridspec
from io import BytesIO
import base64
import logging
from technical_analysis import TechnicalAnalyzer

logger = logging.getLogger(__name__)

# Dark theme colors
COLORS = {
    'bg': '#0d1117',
    'panel': '#161b22',
    'grid': '#21262d',
    'text': '#e6edf3',
    'subtext': '#8b949e',
    'green': '#3fb950',
    'red': '#f85149',
    'blue': '#58a6ff',
    'yellow': '#e3b341',
    'purple': '#bc8cff',
    'orange': '#db6d28',
    'teal': '#39d353',
}

class ChartGenerator:
    def __init__(self):
        self.ta = TechnicalAnalyzer()
        plt.rcParams.update({
            'figure.facecolor': COLORS['bg'],
            'axes.facecolor': COLORS['panel'],
            'axes.edgecolor': COLORS['grid'],
            'axes.labelcolor': COLORS['text'],
            'xtick.color': COLORS['subtext'],
            'ytick.color': COLORS['subtext'],
            'text.color': COLORS['text'],
            'grid.color': COLORS['grid'],
            'grid.alpha': 0.5,
            'font.family': 'monospace',
        })

    def generate_chart(self, df: pd.DataFrame, symbol: str, interval: str, signal) -> bytes:
        """Full trading chart with indicators"""
        
        # Calculate indicators
        rsi = self.ta.calculate_rsi(df)
        macd_line, signal_line, histogram = self.ta.calculate_macd(df)
        bb_upper, bb_mid, bb_lower = self.ta.calculate_bollinger_bands(df)
        ema_9 = self.ta.calculate_ema(df, 9)
        ema_21 = self.ta.calculate_ema(df, 21)
        ema_50 = self.ta.calculate_ema(df, 50)
        volume = df['volume']
        
        # Use last 60 candles for clean display
        n = min(60, len(df))
        df_plot = df.tail(n).copy()
        rsi_plot = rsi.tail(n)
        macd_plot = macd_line.tail(n)
        signal_plot = signal_line.tail(n)
        hist_plot = histogram.tail(n)
        bb_u = bb_upper.tail(n)
        bb_m = bb_mid.tail(n)
        bb_l = bb_lower.tail(n)
        ema9_plot = ema_9.tail(n)
        ema21_plot = ema_21.tail(n)
        ema50_plot = ema_50.tail(n)
        vol_plot = volume.tail(n)
        
        x = np.arange(len(df_plot))
        current_price = df_plot['close'].iloc[-1]
        
        # Create figure with subplots
        fig = plt.figure(figsize=(16, 12), dpi=100)
        fig.patch.set_facecolor(COLORS['bg'])
        
        gs = gridspec.GridSpec(4, 1, figure=fig, 
                               height_ratios=[5, 1.5, 1.5, 1.5],
                               hspace=0.08)
        
        ax1 = fig.add_subplot(gs[0])  # Candlestick + BB + EMA
        ax2 = fig.add_subplot(gs[1], sharex=ax1)  # Volume
        ax3 = fig.add_subplot(gs[2], sharex=ax1)  # RSI
        ax4 = fig.add_subplot(gs[3], sharex=ax1)  # MACD
        
        for ax in [ax1, ax2, ax3, ax4]:
            ax.set_facecolor(COLORS['panel'])
            ax.grid(True, alpha=0.3, color=COLORS['grid'], linewidth=0.5)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_color(COLORS['grid'])
            ax.spines['left'].set_color(COLORS['grid'])
        
        # ═══ Panel 1: Candlestick Chart ═══
        # Bollinger Bands fill
        ax1.fill_between(x, bb_u.values, bb_l.values, alpha=0.08, color=COLORS['blue'])
        ax1.plot(x, bb_u.values, color=COLORS['blue'], linewidth=0.7, alpha=0.6, label='BB Upper')
        ax1.plot(x, bb_m.values, color=COLORS['yellow'], linewidth=0.7, alpha=0.6, linestyle='--', label='BB Mid')
        ax1.plot(x, bb_l.values, color=COLORS['blue'], linewidth=0.7, alpha=0.6, label='BB Lower')
        
        # EMAs
        ax1.plot(x, ema9_plot.values, color=COLORS['orange'], linewidth=1.2, alpha=0.9, label='EMA 9')
        ax1.plot(x, ema21_plot.values, color=COLORS['purple'], linewidth=1.2, alpha=0.9, label='EMA 21')
        ax1.plot(x, ema50_plot.values, color=COLORS['teal'], linewidth=1.2, alpha=0.9, label='EMA 50')
        
        # Candlesticks
        for i in range(len(df_plot)):
            o = df_plot['open'].iloc[i]
            h = df_plot['high'].iloc[i]
            l = df_plot['low'].iloc[i]
            c = df_plot['close'].iloc[i]
            
            color = COLORS['green'] if c >= o else COLORS['red']
            
            # Wick
            ax1.plot([x[i], x[i]], [l, h], color=color, linewidth=0.8, alpha=0.9)
            
            # Body
            body_h = abs(c - o)
            body_bottom = min(o, c)
            rect = plt.Rectangle((x[i] - 0.35, body_bottom), 0.7, max(body_h, (h-l)*0.01),
                                   color=color, alpha=0.85)
            ax1.add_patch(rect)
        
        # Current price line
        ax1.axhline(y=current_price, color=COLORS['yellow'], 
                    linewidth=1, linestyle='--', alpha=0.8)
        ax1.text(len(df_plot)-1, current_price, 
                 f' ${current_price:,.2f}', 
                 color=COLORS['yellow'], fontsize=8, va='center')
        
        # Signal indicator on chart
        if signal.action == "BUY":
            action_color = COLORS['green']
            action_marker = '▲'
        elif signal.action == "SELL":
            action_color = COLORS['red']
            action_marker = '▼'
        else:
            action_color = COLORS['yellow']
            action_marker = '●'
        
        ax1.scatter(x[-1], df_plot['low'].iloc[-1] * 0.998 if signal.action == "BUY" 
                   else df_plot['high'].iloc[-1] * 1.002,
                   color=action_color, s=200, zorder=10, marker='^' if signal.action=='BUY' else 'v')
        
        # Support & Resistance
        ax1.axhline(y=signal.support, color=COLORS['green'], 
                    linewidth=1, linestyle=':', alpha=0.6)
        ax1.axhline(y=signal.resistance, color=COLORS['red'], 
                    linewidth=1, linestyle=':', alpha=0.6)
        ax1.text(0, signal.support, f'S: ${signal.support:,.2f}', 
                color=COLORS['green'], fontsize=7, alpha=0.8)
        ax1.text(0, signal.resistance, f'R: ${signal.resistance:,.2f}', 
                color=COLORS['red'], fontsize=7, alpha=0.8)
        
        ax1.legend(loc='upper left', fontsize=7, 
                  facecolor=COLORS['panel'], edgecolor=COLORS['grid'],
                  labelcolor=COLORS['text'], ncol=3)
        ax1.set_ylabel('Price (USDT)', color=COLORS['subtext'], fontsize=9)
        plt.setp(ax1.get_xticklabels(), visible=False)
        
        # ═══ Panel 2: Volume ═══
        vol_colors = [COLORS['green'] if df_plot['close'].iloc[i] >= df_plot['open'].iloc[i] 
                      else COLORS['red'] for i in range(len(df_plot))]
        ax2.bar(x, vol_plot.values, color=vol_colors, alpha=0.6, width=0.8)
        ax2.set_ylabel('Volume', color=COLORS['subtext'], fontsize=8)
        plt.setp(ax2.get_xticklabels(), visible=False)
        
        # ═══ Panel 3: RSI ═══
        ax3.plot(x, rsi_plot.values, color=COLORS['purple'], linewidth=1.2, label='RSI(14)')
        ax3.axhline(y=70, color=COLORS['red'], linewidth=0.8, linestyle='--', alpha=0.7)
        ax3.axhline(y=30, color=COLORS['green'], linewidth=0.8, linestyle='--', alpha=0.7)
        ax3.axhline(y=50, color=COLORS['subtext'], linewidth=0.5, alpha=0.5)
        
        ax3.fill_between(x, rsi_plot.values, 70, 
                         where=(rsi_plot.values >= 70), alpha=0.15, color=COLORS['red'])
        ax3.fill_between(x, rsi_plot.values, 30, 
                         where=(rsi_plot.values <= 30), alpha=0.15, color=COLORS['green'])
        
        ax3.text(0, 72, 'OB', color=COLORS['red'], fontsize=7)
        ax3.text(0, 24, 'OS', color=COLORS['green'], fontsize=7)
        ax3.set_ylim(0, 100)
        ax3.set_ylabel('RSI', color=COLORS['subtext'], fontsize=8)
        
        current_rsi = rsi_plot.iloc[-1]
        rsi_color = COLORS['red'] if current_rsi > 70 else COLORS['green'] if current_rsi < 30 else COLORS['purple']
        ax3.text(len(df_plot)-1, current_rsi, f' {current_rsi:.1f}', 
                color=rsi_color, fontsize=8, va='center')
        plt.setp(ax3.get_xticklabels(), visible=False)
        
        # ═══ Panel 4: MACD ═══
        hist_colors = [COLORS['green'] if h >= 0 else COLORS['red'] for h in hist_plot.values]
        ax4.bar(x, hist_plot.values, color=hist_colors, alpha=0.6, width=0.8, label='Histogram')
        ax4.plot(x, macd_plot.values, color=COLORS['blue'], linewidth=1.2, label='MACD')
        ax4.plot(x, signal_plot.values, color=COLORS['orange'], linewidth=1.2, label='Signal')
        ax4.axhline(y=0, color=COLORS['subtext'], linewidth=0.5, alpha=0.5)
        ax4.set_ylabel('MACD', color=COLORS['subtext'], fontsize=8)
        ax4.legend(loc='upper left', fontsize=7, 
                  facecolor=COLORS['panel'], edgecolor=COLORS['grid'],
                  labelcolor=COLORS['text'])
        
        # X-axis labels (timestamps)
        tick_positions = x[::max(1, len(x)//8)]
        tick_labels = [df_plot.index[i].strftime('%m/%d\n%H:%M') 
                      for i in tick_positions]
        ax4.set_xticks(tick_positions)
        ax4.set_xticklabels(tick_labels, fontsize=7, color=COLORS['subtext'])
        
        # ═══ Title Bar ═══
        signal_emoji = "🟢" if signal.action == "BUY" else "🔴" if signal.action == "SELL" else "🟡"
        title = (f"{symbol} | {interval.upper()} | "
                 f"{signal_emoji} {signal.action} ({signal.strength}) | "
                 f"Confidence: {signal.confidence}%")
        
        fig.suptitle(title, fontsize=13, color=action_color, 
                    fontweight='bold', y=0.98)
        
        plt.tight_layout(rect=[0, 0, 1, 0.97])
        
        # Save to bytes
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight',
                   facecolor=COLORS['bg'])
        plt.close(fig)
        buf.seek(0)
        
        return buf.getvalue()

    def get_base64_chart(self, df: pd.DataFrame, symbol: str, interval: str, signal) -> str:
        """Base64 encoded chart for Claude AI vision"""
        chart_bytes = self.generate_chart(df, symbol, interval, signal)
        return base64.b64encode(chart_bytes).decode('utf-8')


# Singleton
chart_gen = ChartGenerator()
