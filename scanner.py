import asyncio
from deriv_client import DerivClient
from indicators import rsi, adx, atr_bands
from risk_manager import can_trade, remaining
import pandas as pd

INDICES = [
    "R_10","R_25","R_50","R_75","R_100",
    "1HZ10V","1HZ25V","1HZ50V","1HZ75V","1HZ100V",
    "BOOM300N","BOOM500","BOOM1000",
    "CRASH300N","CRASH500","CRASH1000",
    "STPRNG","JD10","JD25"
]

class Scanner:
    def __init__(self, client, config):
        self.client = client
        self.cfg = config

    async def scan_once(self):
        balance = await self.client.get_balance()
        if not can_trade(balance, self.cfg['daily_max_loss_pct']):
            return []

        picks = []
        for sym in INDICES:
            m1 = await self.client.get_candles(sym, 60, 300)
            h1 = await self.client.get_candles(sym, 3600, 100)
            if m1.empty or h1.empty: continue
            m1['rsi'] = rsi(m1['close'])
            m1['adx'] = adx(m1['high'], m1['low'], m1['close'])
            upper, lower, atr = atr_bands(m1['close'], m1['high'], m1['low'], self.cfg['atr_period'], self.cfg['atr_mult'])
            last = m1.iloc[-1]
            h1_up = h1['close'].iloc[-1] > h1['close'].rolling(20).mean().iloc[-1]
            if not (self.cfg['adx_min'] < last['adx'] < 60): continue
            if not (self.cfg['rsi_min'] < last['rsi'] < self.cfg['rsi_max']): continue
            if not h1_up: continue

            pip_size = 0.01 if ("R_" in sym or "HZ" in sym) else 1
            if self.cfg['use_atr_sl']:
                sl_dist_price = atr.iloc[-1] * self.cfg['atr_mult']
                sl_pips = sl_dist_price / pip_size
            else:
                sl_pips = self.cfg['sl_pips']

            pos = self.client.calculate_position_size(balance, self.cfg['risk'], sl_pips, sym)
            tp_amount = pos['stake'] * self.cfg['rr']

            picks.append({
                "symbol": sym,
                "rsi": round(last['rsi'],1),
                "adx": round(last['adx'],1),
                "sl_pips": round(sl_pips,1),
                "stake": pos['stake'],
                "tp_money": round(tp_amount,2),
                "atr": round(atr.iloc[-1],2)
            })
        return sorted(picks, key=lambda x: x['adx'], reverse=True)[:5]