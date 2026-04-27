import asyncio, os, datetime
from dotenv import load_dotenv
from telegram_bot import build_app, config, scanner, client
from trade_logger import init_db, update_trade, get_equity_curve, get_win_rate, get_stats
from charting import generate_equity_chart

load_dotenv()
init_db()

async def auto_loop():
    while True:
        if config['auto']:
            picks = await scanner.scan_once()
            print("AUTO picks:", picks[:2])
        await asyncio.sleep(30)

async def trade_updater():
    while True:
        try:
            resp = await client.get_open_contracts()
        except Exception as e:
            print("updater error", e)
        await asyncio.sleep(60)

async def daily_report_task(app):
    # 21:00 Nairobi = 18:00 UTC
    while True:
        now = datetime.datetime.utcnow()
        target = now.replace(hour=18, minute=0, second=0, microsecond=0)
        if now >= target:
            target += datetime.timedelta(days=1)
        wait = (target - now).total_seconds()
        await asyncio.sleep(wait)
        chat_id = os.getenv("TELEGRAM_REPORT_CHAT_ID")
        if not chat_id:
            continue
        equity = get_equity_curve()
        if not equity:
            continue
        path = generate_equity_chart(equity)
        stats = get_stats()
        wins, total, pct = get_win_rate(None, 100)
        caption = f"Daily 21:00 Nairobi Report\nTotal trades: {total} | Win rate: {pct}% | Today PnL: ${stats['pnl']:.2f}"
        try:
            await app.bot.send_photo(chat_id=int(chat_id), photo=open(path,'rb'), caption=caption)
        except Exception as e:
            print("report send error", e)

async def main():
    app = build_app()
    await asyncio.gather(
        app.run_polling(),
        auto_loop(),
        trade_updater(),
        daily_report_task(app)
    )

if __name__ == "__main__":
    asyncio.run(main())