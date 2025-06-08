import time
import requests
from datetime import datetime
import upstox_client
from upstox_client.rest import ApiException
import os

# === CONFIGURATION ===
BOT_TOKEN = os.getenv("telgram_bot_token")
CHAT_ID = os.getenv('telgram_bot_chat_id')
API_KEY = os.getenv("UPS_API_KEY")
ACCESS_TOKEN = os.getenv("UPS_ACCESS_TOKEN")


configuration = upstox_client.Configuration()
configuration.api_key['apiKey'] = API_KEY
configuration.access_token = ACCESS_TOKEN
api_client = upstox_client.ApiClient(configuration)
option_api = upstox_client.OptionChainApi(api_client)

index_keys = {
    "NIFTY 50": "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank",
    "SENSEX": "BSE_INDEX|Sensex"
}

def get_latest_expiry(key):
    try:
        resp = option_api.get_option_expiry(key)
        weekly = [d for d in resp.data if "T00:00:00+05:30" in d]
        return weekly[0] if weekly else resp.data[0]
    except ApiException as e:
        print(f"Error: {e}")
        return None

def fetch_chain(key, expiry):
    all_data = []
    offset = 0
    limit = 50
    while True:
        try:
            res = option_api.get_option_chain(key, expiry, offset=offset, limit=limit)
            data = res.data or []
            all_data += data
            if len(data) < limit:
                break
            offset += limit
        except ApiException as e:
            print(f"Chain fetch error: {e}")
            break
    return all_data

result = {}
for name, key in index_keys.items():
    expiry = get_latest_expiry(key)
    if expiry:
        data = fetch_chain(key, expiry)
        result[name] = {"expiry": expiry, "data": data}

filename = f"nifty_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(filename, "w") as f:
    json.dump(result, f, indent=2)

print(f"✅ Saved to {filename}")
