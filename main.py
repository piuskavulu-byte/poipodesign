# main.py — poipodesign v4.1 (Conflict fix + startup ping)
import asyncio
import os
import datetime
import traceback
from aiohttp import web
from dotenv import load_dotenv
from telegram import Update

from telegram_bot import build_app, config, scanner
from trade_logger import init_db, get_equity_curve, get_win_rate, get_stats
from charting import generate_equity_chart

load_dotenv()
init_db()

# ---- Render web server ----
async def health(request):
    return web.Response(text="poipodesign alive")

async def start_web():
    app = web.Application()
    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"WEB OK on {port}", flush=True)

# ---- auto scanner ----
async def auto_loop():
    while True:
        try:
            if config.get('auto'):
                await scanner.scan_once()
        except Exception as e:
            print("auto_loop error:", e, flush=True)
        await asyncio.sleep(30)

# ---- daily 21:00 report ----
async def daily_report(tg_app, chat_id):
    while True:
        now = datetime.datetime.utcnow()
        target = now.replace(hour=18, minute=0, second=0, microsecond=0)  # 21:00 Nairobi = 18:00 UTC
        if now >= target:
            target += datetime.timedelta(days=1)
        await asyncio.sleep((target - now).total_seconds())
        try:
            equity = get_equity_curve()
            if equity:
                path = generate_equity_chart(equity)
                stats = get_stats()
                w, t, p = get_win_rate(None, 100)
                cap = f"📊 Daily 21:00\nTrades: {t} | Win: {p}%\nPnL: ${stats['pnl']:.2f}"
                await tg_app.bot.send_photo(chat_id=int(chat_id), photo=open(path, 'rb'), caption=cap)
        except Exception as e:
            print("daily_report error:", e, flush=True)

# ---- main ----
async def main():
    await start_web()

    tg = build_app()

    # STEP 1 FIX: kill any old webhook or polling session FIRST
    try:
        await tg.bot.delete_webhook(drop_pending_updates=True)
        print("Webhook deleted, old sessions cleared", flush=True)
    except Exception as e:
        print("delete_webhook error:", e, flush=True)

    await tg.initialize()
    await tg.start()
    await tg.updater.start_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )
    print("TELEGRAM POLLING STARTED", flush=True)

    # startup ping on every deploy
    chat_id = os.getenv("TELEGRAM_REPORT_CHAT_ID")
    if chat_id:
        try:
            await tg.bot.send_message(
                chat_id=int(chat_id),
                text=f"✅ poipodesign DEPLOYED\nBot is online.\nTime: {datetime.datetime.now().strftime('%H:%M:%S')}\nhttps://poipodesign.onrender.com"
            )
            print("Startup message sent to", chat_id, flush=True)
        except Exception as e:
            print("Startup message FAILED:", e, flush=True)
    else:
        print("WARNING: TELEGRAM_REPORT_CHAT_ID not set", flush=True)

    tasks = [auto_loop()]
    if chat_id:
        tasks.append(daily_report(tg, chat_id))
    
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        traceback.print_exc()
