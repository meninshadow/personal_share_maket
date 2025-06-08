import time
import requests
from datetime import datetime
import upstox_client
from upstox_client.rest import ApiException
import os

# === CONFIGURATION ===
BOT_TOKEN = os.getenv("telgram_bot_token")

CHAT_ID = os.getenv('telgram_bot_chat_id')

API_KEY = os.getenv("UP_API_KEY")
ACCESS_TOKEN = os.getenv("UPS_ACCESS_TOKEN")

strike_prices = [50000, 53000, 63000]
option_types = ['CE', 'PE']
EXPIRY = '12JUN25'  # Update to current expiry, e.g., '27JUN25'
last_data = {}

# Initialize Upstox SDK
configuration = upstox_client.Configuration()
configuration.access_token = ACCESS_TOKEN
configuration.api_key['apiKey'] = API_KEY
market_api = upstox_client.MarketQuoteApi(upstox_client.ApiClient(configuration))

def send_message(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {'chat_id': CHAT_ID, 'text': msg}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram Error:", e)

def track_option_trends():
    header = ["🕒 Option Trend Update: " + datetime.now().strftime('%H:%M:%S'), ""]
    result_lines = header.copy()

    # Build comma-separated instrument_key list
    instrument_keys = []
    for strike in strike_prices:
        for typ in option_types:
            key = f"NSE_FO|BANKNIFTY{EXPIRY}{strike}{typ}"
            instrument_keys.append(key)
    symbols = ",".join(instrument_keys)

    try:
        resp = market_api.get_full_market_quote(symbols, api_version='2.0')
        quotes = resp.data  # dict of instrument_key → QuoteData
    except ApiException as e:
        send_message(f"❌ API error fetching quotes:\n{e}")
        return

    for inst_key, data in quotes.items():
        try:
            parts = inst_key.split('|')[-1]  # e.g. BANKNIFTY27JUN2550000CE
            # Extract strike and type
            strike = ''.join(filter(str.isdigit, parts[len(EXPIRY):]))
            opt_type = parts[-2:]  # 'CE' or 'PE'
            ltp = data.last_price
            oi = data.oi

            k_price = f"{strike}_{opt_type}_PRICE"
            k_oi = f"{strike}_{opt_type}_OI"

            prev_price = last_data.get(k_price, ltp)
            trend_price = "up" if ltp > prev_price else "down" if ltp < prev_price else "same"
            last_data[k_price] = ltp

            prev_oi = last_data.get(k_oi, oi)
            trend_oi = "up" if oi > prev_oi else "down" if oi < prev_oi else "same"
            last_data[k_oi] = oi

            result_lines.append(f"{strike} | {opt_type} | ₹{ltp} ({trend_price}) | OI: {oi} ({trend_oi})")
        except Exception as e:
            result_lines.append(f"Error parsing {inst_key}: {e}")

    send_message("\n".join(result_lines))

# Run once (schedule this every 15 min)
if __name__ == "__main__":
    track_option_trends()
