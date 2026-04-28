import asyncio, os, datetime
from aiohttp import web
from dotenv import load_dotenv
from telegram_bot import build_app, config, scanner
from trade_logger import init_db, get_equity_curve, get_win_rate, get_stats
from charting import generate_equity_chart

load_dotenv()
init_db()

# --- Render needs a web server ---
async def health(request):
    return web.Response(text="poipodesign alive")

async def start_web():
    app = web.Application()
    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    await web.TCPSite(runner, "0.0.0.0", port).start()
    print(f"Web server on {port}")

async def auto_loop():
    while True:
        if config['auto']:
            picks = await scanner.scan_once()
            print("AUTO:", picks[:1])
        await asyncio.sleep(30)

async def daily_report(tg_app):
    while True:
        now = datetime.datetime.utcnow()
        target = now.replace(hour=18, minute=0, second=0)
        if now >= target: target += datetime.timedelta(days=1)
        await asyncio.sleep((target-now).total_seconds())
        chat_id = os.getenv("TELEGRAM_REPORT_CHAT_ID")
        if not chat_id: continue
        equity = get_equity_curve()
        if equity:
            path = generate_equity_chart(equity)
            stats = get_stats()
            w,t,p = get_win_rate(None,100)
            cap = f"Daily 21:00 Nairobi\nTrades:{t} Win:{p}% PnL:${stats['pnl']:.2f}"
            try: await tg_app.bot.send_photo(int(chat_id), open(path,'rb'), caption=cap)
            except: pass

async def main():
    await start_web()  # satisfies Render port check
    tg = build_app()
    await tg.initialize()
    await tg.start()
    await tg.updater.start_polling()
    await asyncio.gather(auto_loop(), daily_report(tg))

if __name__ == "__main__":
    asyncio.run(main())
