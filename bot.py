import asyncio
import os
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

# ===== Sazlamalar =====
BOT_TOKEN = os.environ["BOT_TOKEN"]   # Railway Variables-dan alynýar
INTERVAL = "1m"                       # 1 minutlyk şemler

MARKETS = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CAD": "USDCAD=X",
    "🥇 Gold (XAU)": "GC=F",
    "₿ Bitcoin": "BTC-USD",
}
NAMES = {symbol: name for name, symbol in MARKETS.items()}


def rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    return 100 - 100 / (1 + gain / loss)


def analyze(symbol):
    df = yf.download(symbol, period="5d", interval=INTERVAL,
                     progress=False, auto_adjust=True)
    closes = df["Close"].squeeze().dropna()
    if len(closes) < 30:
        raise ValueError("Maglumat ýeterlik däl")

    price = float(closes.iloc[-1])
    value = float(rsi(closes).iloc[-1])
    ema5 = closes.ewm(span=5, adjust=False).mean().iloc[-1]
    ema20 = closes.ewm(span=20, adjust=False).mean().iloc[-1]

    trend = 1 if ema5 > ema20 else -1                      # tendensiýa
    rsi_s = 1 if value < 35 else (-1 if value > 65 else 0) # aşa satylan/alnan
    mom = 1 if closes.iloc[-1] > closes.iloc[-3] else -1   # soňky hereket

    score = trend + rsi_s + mom
    if score == 0:
        score = trend   # deň bolsa tendensiýa boýunça

    signal = "🟢 BUY (satyn al)" if score > 0 else "🔴 SELL (sat)"
    strength = {3: "ýokary", 2: "orta"}.get(abs(score), "pes")

    decimals = 5 if price < 50 else 2
    last_candle = closes.index[-1].strftime("%Y-%m-%d %H:%M")
    now = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
    return (
        f"{NAMES.get(symbol, symbol)} (1 min)\n\n"
        f"Signal: {signal}\n"
        f"Güýji: {strength}\n"
        f"Baha: {price:,.{decimals}f}\n"
        f"RSI: {value:.1f}\n\n"
        f"Soňky şem: {last_candle}\n"
        f"🕒 {now}\n"
        f"⚠️ Bu çaklama, kepil däl. Pocket Option OTC bahalary başgaça bolup biler."
    )


def menu_keyboard():
    buttons = [
        InlineKeyboardButton(name, callback_data=f"m:{symbol}")
        for name, symbol in MARKETS.items()
    ]
    rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    return InlineKeyboardMarkup(rows)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bazar saýla:", reply_markup=menu_keyboard())


async def on_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "menu":
        await query.edit_message_text("Bazar saýla:", reply_markup=menu_keyboard())
        return

    symbol = query.data.split(":", 1)[1]
    try:
        text = await asyncio.to_thread(analyze, symbol)
    except Exception:
        text = "Maglumat alyp bolmady (bazar ýapyk bolup biler), soň synap gör."

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔄 Täzele", callback_data=f"m:{symbol}"),
        InlineKeyboardButton("⬅️ Yza", callback_data="menu"),
    ]])
    await query.edit_message_text(text, reply_markup=keyboard)


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_click))
    app.run_polling()


if __name__ == "__main__":
    main()
