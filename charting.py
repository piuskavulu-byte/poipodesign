import plotly.graph_objects as go
from plotly.subplots import make_subplots
from indicators import ichimoku, atr_bands, swing_hl, rsi
import pandas as pd

def generate_chart(df: pd.DataFrame, symbol: str, out_path="/tmp/chart.png"):
    df = df.copy().tail(200)
    tenkan, kijun, senkou_a, senkou_b, chikou = ichimoku(df)
    atr_up, atr_low, atr = atr_bands(df['close'], df['high'], df['low'])
    sh, sl = swing_hl(df['close'])
    df['rsi'] = rsi(df['close'])

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.7,0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Price"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=tenkan, line=dict(width=1), name="Tenkan"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=kijun, line=dict(width=1), name="Kijun"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=senkou_a, line=dict(width=1), name="Senkou A"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=senkou_b, line=dict(width=1), name="Senkou B"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=atr_up, line=dict(dash='dot'), name="ATR Up"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=atr_low, line=dict(dash='dot'), name="ATR Low"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=sh, mode='markers', marker_symbol='triangle-down', name="Swing H"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=sl, mode='markers', marker_symbol='triangle-up', name="Swing L"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['rsi'], name="RSI"), row=2, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['volume'], name="Volume", opacity=0.3), row=2, col=1)
    fig.update_layout(title=f"{symbol} - Clean 2-Panel", xaxis_rangeslider_visible=False, height=800, showlegend=False, template="plotly_dark")
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="RSI", range=[0,100], row=2, col=1)
    fig.write_image(out_path, scale=2)
    return out_path

def generate_equity_chart(equity_data, out_path="/tmp/equity.png"):
    if not equity_data:
        return None
    df = pd.DataFrame(equity_data)
    df['time'] = pd.to_datetime(df['time'])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['time'], y=df['equity'], mode='lines+markers', name='Equity', line=dict(width=3)))
    fig.add_hline(y=0, line_dash="dash")
    fig.update_layout(title="Equity Curve", template="plotly_dark", height=500, xaxis_title="Time", yaxis_title="Cumulative PnL ($)")
    fig.write_image(out_path, scale=2)
    return out_path