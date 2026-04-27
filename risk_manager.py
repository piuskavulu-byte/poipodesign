import json, os, datetime

STATE_FILE = "/tmp/daily_risk.json"

def get_state():
    today = datetime.date.today().isoformat()
    if os.path.exists(STATE_FILE):
        data = json.load(open(STATE_FILE))
        if data.get("date") == today:
            return data
    return {"date": today, "risk_used": 0.0}

def can_trade(balance, daily_max_pct):
    state = get_state()
    max_loss = balance * daily_max_pct / 100
    return state["risk_used"] < max_loss

def add_risk(amount):
    state = get_state()
    state["risk_used"] += amount
    json.dump(state, open(STATE_FILE, "w"))

def remaining(balance, daily_max_pct):
    state = get_state()
    max_loss = balance * daily_max_pct / 100
    return max(0, max_loss - state["risk_used"])