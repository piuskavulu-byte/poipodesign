import asyncio, json, websockets
import pandas as pd
from risk_manager import add_risk
from trade_logger import log_trade, update_trade

class DerivClient:
    def __init__(self, app_id, token):
        self.url = f"wss://ws.derivws.com/websockets/v3?app_id={app_id}"
        self.token = token

    async def _call(self, payload):
        async with websockets.connect(self.url) as ws:
            await ws.send(json.dumps({"authorize": self.token}))
            await ws.recv()
            await ws.send(json.dumps(payload))
            return json.loads(await ws.recv())

    async def get_candles(self, symbol, granularity=60, count=300):
        resp = await self._call({
            "ticks_history": symbol,
            "style": "candles",
            "granularity": granularity,
            "count": count,
            "end": "latest"
        })
        candles = resp.get("candles", [])
        if not candles:
            return pd.DataFrame()
        df = pd.DataFrame(candles)
        df['epoch'] = pd.to_datetime(df['epoch'], unit='s')
        df.set_index('epoch', inplace=True)
        df.rename(columns={'open':'open','high':'high','low':'low','close':'close'}, inplace=True)
        df['volume'] = 1
        return df

    async def get_balance(self):
        resp = await self._call({"balance":1})
        return float(resp.get("balance",{}).get("balance",0))

    def calculate_position_size(self, balance, risk_percent, sl_pips, symbol):
        risk_amount = balance * (risk_percent / 100)
        pip_size = 0.01 if ("R_" in symbol or "HZ" in symbol) else 1
        sl_distance = sl_pips * pip_size
        stake = max(1.0, round(risk_amount,2))
        return {"stake": stake, "stop_loss": stake, "sl_distance": sl_distance, "risk_amount": risk_amount}

    async def buy_multiplier(self, symbol, stake, stop_loss, take_profit, multiplier=500, direction="MULTUP"):
        resp = await self._call({
            "buy": 1,
            "price": stake,
            "parameters": {
                "contract_type": direction,
                "symbol": symbol,
                "multiplier": multiplier,
                "stop_loss": stop_loss,
                "take_profit": take_profit
            }
        })
        contract_id = str(resp.get("buy",{}).get("contract_id",""))
        if contract_id:
            log_trade(contract_id, symbol, direction, stake, stop_loss, take_profit)
            add_risk(stake)
        return resp

    async def get_open_contracts(self):
        resp = await self._call({"proposal_open_contract":1})
        return resp