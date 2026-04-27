# Deriv Synthetic Indices Auto-Rotator Bot

Scans 19 Deriv synthetic indices every 30s, applies ADX, RSI, H1 alignment, Ichimoku, ATR bands, swing filters, and trades 1:3 RR with 500x multipliers (demo only).

## Features
- Auto-rotate scanner (19 indices)
- 1:3 RR: 100 pip SL, 300 pip TP, 500x multiplier
- Clean 2-panel charts: candles + Ichimoku + ATR bands + swing H/L, RSI + volume
- Filters: ADX>18, H1 alignment, RSI 30-70, volume, spread, swing distance
- Telegram controls: /auto /scan /chart /sl /rr /risk /close_all

## Deploy to Render.com
1. Push to GitHub
2. Create New > Background Worker on Render
3. Add Environment Variables from .env.example
4. Build Command: pip install -r requirements.txt
5. Start Command: python main.py

WARNING: Deriv is not licensed by Kenya CMA. Use demo only. 500x is extremely risky.
