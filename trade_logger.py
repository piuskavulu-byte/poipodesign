import sqlite3, datetime, os

DB_PATH = "/tmp/trades.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id TEXT,
            symbol TEXT,
            direction TEXT,
            stake REAL,
            sl REAL,
            tp REAL,
            entry_time TEXT,
            exit_time TEXT,
            pnl REAL,
            result TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_trade(contract_id, symbol, direction, stake, sl, tp):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO trades (contract_id, symbol, direction, stake, sl, tp, entry_time) VALUES (?,?,?,?,?,?,?)",
        (contract_id, symbol, direction, stake, sl, tp, datetime.datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

def update_trade(contract_id, pnl, result):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE trades SET pnl=?, result=?, exit_time=? WHERE contract_id=?",
        (pnl, result, datetime.datetime.utcnow().isoformat(), contract_id)
    )
    conn.commit()
    conn.close()

def get_win_rate(symbol=None, limit=100):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    q = "SELECT result FROM trades WHERE result IS NOT NULL"
    params = []
    if symbol:
        q += " AND symbol=?"
        params.append(symbol)
    q += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(q, params).fetchall()
    conn.close()
    if not rows: return 0,0,0
    wins = sum(1 for r in rows if r[0]=='win')
    total = len(rows)
    return wins, total, round(wins/total*100,1)

def get_stats():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    today = datetime.datetime.utcnow().date().isoformat()
    rows = conn.execute("SELECT COUNT(*), SUM(pnl), SUM(CASE WHEN result='win' THEN 1 ELSE 0 END) FROM trades WHERE date(entry_time)=?", (today,)).fetchone()
    conn.close()
    trades, pnl, wins = rows
    return {"trades": trades or 0, "pnl": pnl or 0, "wins": wins or 0}

def get_win_rate_by_hour():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    sql = "SELECT strftime('%H', entry_time) as hr, COUNT(*), SUM(CASE WHEN result='win' THEN 1 ELSE 0 END), ROUND(100.0 * SUM(CASE WHEN result='win' THEN 1 ELSE 0 END) / COUNT(*),1) FROM trades WHERE result IS NOT NULL GROUP BY hr ORDER BY hr"
    rows = conn.execute(sql).fetchall()
    conn.close()
    return [{"hour": r[0], "trades": r[1], "wins": r[2], "winrate": r[3]} for r in rows]

def get_index_ranking(limit=19):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    sql = "SELECT symbol, COUNT(*) as trades, SUM(pnl) as total_pnl, ROUND(100.0 * SUM(CASE WHEN result='win' THEN 1 ELSE 0 END) / COUNT(*),1) as winrate FROM trades WHERE result IS NOT NULL GROUP BY symbol ORDER BY total_pnl DESC LIMIT ?"
    rows = conn.execute(sql, (limit,)).fetchall()
    conn.close()
    return [{"symbol": r[0], "trades": r[1], "pnl": round(r[2] or 0,2), "winrate": r[3]} for r in rows]

def get_equity_curve():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT exit_time, pnl FROM trades WHERE result IS NOT NULL ORDER BY exit_time").fetchall()
    conn.close()
    equity = []
    cum = 0
    for t, pnl in rows:
        if pnl is None: continue
        cum += pnl
        equity.append({"time": t, "equity": round(cum,2)})
    return equity