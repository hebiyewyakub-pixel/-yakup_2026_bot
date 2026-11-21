import os
import time
import requests
import pandas as pd

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
SYMBOL = os.environ.get("SYMBOL", "BTCUSDT")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def get_rsi(symbol, interval="15m", period=14):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=100"
    data = requests.get(url).json()
    
    closes = [float(candle[4]) for candle in data]
    series = pd.Series(closes)
    
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1], closes[-1]

send_telegram(f"🚀 *{SYMBOL}* üçin signal boty işe başlady!")

last_signal = None

while True:
    try:
        rsi_value, current_price = get_rsi(SYMBOL)
        print(f"{SYMBOL} Baha: {current_price} | RSI: {rsi_value:.2f}")

        if rsi_value < 30 and last_signal != "BUY":
            send_telegram(f"🟢 *SATYN AL (BUY) SIGNALI!*\n\n💰 Baha: `{current_price}`\n📊 RSI: `{rsi_value:.2f}`")
            last_signal = "BUY"
            
        elif rsi_value > 70 and last_signal != "SELL":
            send_telegram(f"🔴 *SAT (SELL) SIGNALI!*\n\n💰 Baha: `{current_price}`\n📊 RSI: `{rsi_value:.2f}`")
            last_signal = "SELL"
            
        elif 35 <= rsi_value <= 65:
            last_signal = None

    except Exception as e:
        print("Ýalňyşlyk:", e)

    time.sleep(60)
  
