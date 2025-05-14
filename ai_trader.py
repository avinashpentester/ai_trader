import requests
import pandas as pd
import yfinance as yf
import datetime
from tqdm import tqdm
import pandas_ta as ta
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

NIFTY_50_SYMBOLS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "KOTAKBANK.NS", "ITC.NS", "SBIN.NS", "LT.NS",
    "AXISBANK.NS", "BAJFINANCE.NS", "BHARTIARTL.NS", "ASIANPAINT.NS", "MARUTI.NS",
    "SUNPHARMA.NS", "WIPRO.NS", "ULTRACEMCO.NS", "HCLTECH.NS", "DIVISLAB.NS",
    "TITAN.NS", "GRASIM.NS", "ADANIENT.NS", "ADANIPORTS.NS", "COALINDIA.NS",
    "JSWSTEEL.NS", "NTPC.NS", "POWERGRID.NS", "TATASTEEL.NS", "TECHM.NS",
    "DRREDDY.NS", "NESTLEIND.NS", "HDFCLIFE.NS", "SBILIFE.NS", "BRITANNIA.NS",
    "BAJAJ-AUTO.NS", "HEROMOTOCO.NS", "EICHERMOT.NS", "CIPLA.NS", "BAJAJFINSV.NS",
    "HINDALCO.NS", "ONGC.NS", "BPCL.NS", "UPL.NS", "SHREECEM.NS",
    "TATAMOTORS.NS", "INDUSINDBK.NS", "M&M.NS", "IOC.NS", "LTIM.NS"
]

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print(f"📲 Alert sent: {message}")
        else:
            print(f"⚠️ Failed to send alert. Status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Telegram alert failed: {e}")

def get_history_data(symbol):
    try:
        data = yf.download(symbol, start="2022-01-01", end="2024-12-31", progress=False)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [' '.join(col).strip() for col in data.columns.values]
        data = data.rename(columns=lambda x: x.capitalize())
        return data
    except Exception as e:
        print(f"⚠️ Failed to get ticker '{symbol}': {e}")
        return pd.DataFrame()

def pattern_analysis(symbol):
    print(f"------------ Pattern analysis for symbol: {symbol} -----------------", end="\n")
    hist_data = get_history_data(symbol)
    print("Historical data size:", hist_data.shape)
    if hist_data.shape[0] < 90:
        print("Insufficient data for analysis: expected at least 90 days of data.")
        return None

    required_cols = ["Open", "High", "Low", "Close", "Volume"]
    if not all(col in hist_data.columns for col in required_cols):
        print(f"⚠️ {symbol} missing required columns. Skipping.")
        return None

    patterns_recognised = []
    rsi_trend = ""
    macd_trend = ""
    sma_value = 0.0
    wma_value = 0.0
    obv_value = 0.0

    hist_data.ta.rsi(length=14, append=True)
    hist_data.ta.macd(append=True)
    hist_data.ta.sma(length=14, append=True)
    hist_data.ta.wma(length=14, append=True)
    hist_data.ta.obv(append=True)

    rsi = hist_data['RSI_14']
    macd = hist_data['MACD_12_26_9']
    macd_signal = hist_data['MACDs_12_26_9']
    sma = hist_data['SMA_14']
    wma = hist_data['WMA_14']
    obv = hist_data['OBV']

    if not rsi.empty:
        if rsi.iloc[-1] > 70:
            rsi_trend = "UP"
        elif rsi.iloc[-1] < 30:
            rsi_trend = "DOWN"
        else:
            rsi_trend = "Sideways"

    if not macd.empty and not macd_signal.empty:
        if macd.iloc[-1] > macd_signal.iloc[-1]:
            macd_trend = "UP"
        elif macd.iloc[-1] < macd_signal.iloc[-1]:
            macd_trend = "DOWN"
        else:
            macd_trend = "Sideways"

    if not sma.empty:
        sma_value = sma.iloc[-1]
    if not wma.empty:
        wma_value = wma.iloc[-1]
    if not obv.empty:
        obv_value = obv.iloc[-1]

    alert_msg = f"📈 {symbol}\nRSI: {rsi_trend}, MACD: {macd_trend}\nSMA: {sma_value:.2f}, WMA: {wma_value:.2f}, OBV: {obv_value:.2f}"
    if rsi_trend != "Sideways" or macd_trend != "Sideways":
        send_telegram_alert(alert_msg)

    return [symbol, patterns_recognised, rsi_trend, macd_trend, sma_value, wma_value, obv_value]

def main():
    print("Nifty 50 selected stocks:", len(NIFTY_50_SYMBOLS))

    data_list = []
    for symbol in tqdm(NIFTY_50_SYMBOLS):
        analysis_result = pattern_analysis(symbol)
        if analysis_result:
            data_list.append(analysis_result)

    data_df = pd.DataFrame(data_list, columns=['Symbol', 'Recognised Pattern Names', 'RSI Trend', 'MACD Trend', 'SMA', 'WMA', 'OBV'])
    data_df.to_csv('analysis_data.csv', index=False)

if __name__ == "__main__":
    main()
