import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from scanner import Scanner
from deriv_client import DerivClient
from charting import generate_chart, generate_equity_chart
from risk_manager import remaining
from trade_logger import get_win_rate, get_stats, get_win_rate_by_hour, get_index_ranking, get_equity_curve

config = {
    "sl_pips": 100,
    "tp_pips": 300,
    "rr": 3,
    "risk": 0.5,
    "adx_min": 18,
    "rsi_min": 30,
    "rsi_max": 70,
    "auto": False,
    "use_atr_sl": True,
    "atr_period": 14,
    "atr_mult": 1.5,
    "daily_max_loss_pct": 3.0
}

client = DerivClient(os.getenv("APP_ID","1089"), os.getenv("DERIV_TOKEN_DEMO"))
scanner = Scanner(client, config)

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Deriv bot ready. Use /report for equity curve.")

async def scan_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    picks = await scanner.scan_once()
    if not picks:
        bal = await client.get_balance()
        rem = remaining(bal, config['daily_max_loss_pct'])
        await update.message.reply_text(f"No picks. Remaining: ${rem:.2f}")
        return
    lines = [f"{p['symbol']} | ADX {p['adx']} | SL {p['sl_pips']:.1f}pip | Stake ${p['stake']}" for p in picks]
    await update.message.reply_text("\n".join(lines))

async def stats_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    symbol = ctx.args[0] if ctx.args else None
    wins, total, pct = get_win_rate(symbol, 100)
    today = get_stats()
    msg = f"Win rate{' '+symbol if symbol else ''} (last {total}): {pct}% ({wins}/{total})\nToday: {today['trades']} trades, PnL ${today['pnl']:.2f}"
    await update.message.reply_text(msg)

async def hourly_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = get_win_rate_by_hour()
    if not data:
        await update.message.reply_text("No trades yet")
        return
    lines = ["Hour | Trades | Win%"]
    for d in data:
        lines.append(f"{d['hour']}h | {d['trades']} | {d['winrate']}%")
    await update.message.reply_text("\n".join(lines[:15]))

async def ranking_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = get_index_ranking()
    if not data:
        await update.message.reply_text("No trades yet")
        return
    lines = ["Best/Worst by PnL:"]
    for i, d in enumerate(data[:5],1):
        lines.append(f"{i}. {d['symbol']} ${d['pnl']} ({d['winrate']}% WR)")
    await update.message.reply_text("\n".join(lines))

async def report_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    equity = get_equity_curve()
    if not equity:
        await update.message.reply_text("No closed trades yet")
        return
    path = generate_equity_chart(equity)
    stats = get_stats()
    wins, total, pct = get_win_rate(None, 100)
    caption = f"Equity Curve\nTotal trades: {total} | Win rate: {pct}% | Today PnL: ${stats['pnl']:.2f}"
    await update.message.reply_photo(open(path,'rb'), caption=caption)

async def chart_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    sym = ctx.args[0] if ctx.args else "R_75"
    df = await client.get_candles(sym, 60, 300)
    path = generate_chart(df, sym)
    await update.message.reply_photo(open(path,'rb'))

def build_app():
    app = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("hourly", hourly_cmd))
    app.add_handler(CommandHandler("ranking", ranking_cmd))
    app.add_handler(CommandHandler("report", report_cmd))
    app.add_handler(CommandHandler("chart", chart_cmd))
    return app