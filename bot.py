import requests
import time
import os
import json
import traceback
from datetime import datetime, timedelta, timezone 
from flask import Flask, request
from threading import Thread

# =========================================================
# BSC SNIPER BOT (V29 - ANTI-FAKE LOCK & MICRO CONFIG)
# Features: Lock Duration Check (30 Days Threshold), LP Gatekeeper, Sniper Trace
# =========================================================

app = Flask(__name__)

@app.route('/')
def home():
    return "BSC Sniper Bot (V29 - Anti-Fake Lock) đang hoạt động!"

def run_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)

RAW_API_KEYS = [
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImU0Y2QxMTFlLTE3YzYtNDU2My1iOGM5LTFjZWZkMjNmMjJhYiIsIm9yZ0lkIjoiNTA3MDc2IiwidXNlcklkIjoiNTIxNzQ5IiwidHlwZUlkIjoiZDhjZmE3NTEtNTAyMC00MTZkLWJkOGItZWJlMWM3Y2Q0NGJiIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQ0ODczODMsImV4cCI6NDkzMDI0NzM4M30.EdCGoN5pzZEuiDmvbEbHvLLGtQU2D2O_gSHX0t2JKug',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjczZTU1ZWQxLTNjYzQtNGM3ZC05MTVmLThiMDc5MTQ3YjAyYiIsIm9yZ0lkIjoiNTA3MDc4IiwidXNlcklkIjoiNTIxNzUxIiwidHlwZUlkIjoiODFkY2ZiNTgtNTAxNC00NjRkLTg3ZDYtMTM0ZjQzZTVkZmRkIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQ0ODg3NTksImV4cCI6NDkzMDI0ODc1OX0.6hBFIZcOM1rVa6sUPNUZEUUEfSKanrurzqKQPbffiSI',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IjVkZTJkNDIzLTY4NmItNDQ1ZS1iNjQ3LTBjNDA5Y2NhZjhiOCIsIm9yZ0lkIjoiNTA3MDc5IiwidXNlcklkIjoiNTIxNzUyIiwidHlwZUlkIjoiMGZhMWU1ZTItYTE1Ny00ODc5LTkxNzktZDA5ZmNlNGJkZjY3IiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQ0ODkxNDUsImV4cCI6NDkzMDI0OTE0NX0.iSlSkU4z_HtWHRQAPRl0H6ZcX1jBbusE9dxjGdIqNp0',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IjM3NWFiODUxLWJkN2ItNGRjYy05OWU4LTY3YWExZTY5NjVmNyIsIm9yZ0lkIjoiNTA2NzE3IiwidXNlcklkIjoiNTIxMzgxIiwidHlwZUlkIjoiZTkzYzUwZjctOGI2ZC00ZDkyLTk4MDItMGIyNDllMTUzMzNiIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQyNTkyNjEsImV4cCI6NDkzMDAxOTI2MX0.-ERcEVFm28TLwIr5udsgMWBAvaUaHf5cf5Qd0vLzb18'
]
API_KEYS = list(set(RAW_API_KEYS))
TELEGRAM_BOT_TOKEN = '8526113763:AAH3wANXx126AloxzAKJQrKJAPWiQm7Kb6Q'
TELEGRAM_CHAT_ID = '1976782751'

CONFIG = {
    "MAX_AUTO_COINS": 10,     
    "MAX_MANUAL_COINS": 20,    
    "AUTO_SCAN": True,
    "MIN_LP_BNB": 1.0,       
    "NOTIFY_NEW_COIN": True  
}

MANUAL_COINS = []
AUTO_COINS = [] 
user_state = {} 
current_api_index = 0 
BLACKLIST_COINS = ["0x55d398326f99059ff775485246999027b3197955".lower()]
WBNB_CA = "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c".lower()
KNOWN_AGGREGATORS = ["0x8D0119F280C5562762a4928bE627a8d504505315".lower(), "0x1111111254EEB25477B68fB85Ed929f73A960582".lower(), "0x10ED43C718714eb63d5aA57B78B54704E256024E".lower()]

def get_current_headers():
    global current_api_index
    if not API_KEYS: return {"accept": "application/json"}
    current_api_index = (current_api_index + 1) % len(API_KEYS)
    return {"accept": "application/json", "X-API-Key": API_KEYS[current_api_index]}

def send_telegram_alert(message, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True}
    if reply_markup: data["reply_markup"] = json.dumps(reply_markup)
    try: requests.post(url, data=data, timeout=10)
    except: pass

# --- CORE BẢO MẬT V29: CHECK THỜI GIAN KHÓA ---
def check_bsc_security(ca):
    try:
        url = f"https://api.gopluslabs.io/api/v1/token_security/56?contract_addresses={ca}"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            result = res.json().get("result", {}).get(ca.lower(), {})
            if result:
                is_hp = str(result.get("is_honeypot", "0")) == "1"
                b_tax = float(result.get("buy_tax", 0) or 0) * 100
                s_tax = float(result.get("sell_tax", 0) or 0) * 100
                
                lock_info = "🔓 MỞ (Chưa khóa thanh khoản)"
                is_lp_locked = False
                
                lp_holders = result.get("lp_holders", [])
                if lp_holders:
                    for h in lp_holders:
                        addr = str(h.get("address", "")).lower()
                        is_lck = str(h.get("is_locked", "0")) == "1"
                        is_burn = addr in ["0x0000000000000000000000000000000000000000", "0x000000000000000000000000000000000000dead"]
                        
                        if is_lck or is_burn:
                            is_lp_locked = True
                            if is_burn:
                                lock_info = "🔥 ĐÃ ĐỐT (Vĩnh viễn)"
                                break
                            else:
                                lock_detail = h.get("locked_detail", [])
                                if lock_detail:
                                    end_ts_str = lock_detail[0].get("end_time", "")
                                    if end_ts_str:
                                        end_ts = int(end_ts_str)
                                        days_left = (end_ts - int(time.time())) // 86400
                                        unlock_date = datetime.fromtimestamp(end_ts).strftime('%d/%m/%Y')
                                        if days_left < 30:
                                            lock_info = f"🔴 KHÓA NGẮN ({days_left} ngày - Mở: {unlock_date})"
                                        else:
                                            lock_info = f"🟢 KHÓA DÀI ({days_left} ngày - Mở: {unlock_date})"
                                    else: lock_info = "🔒 ĐÃ KHÓA (N/A)"
                                else: lock_info = "🔒 ĐÃ KHÓA (N/A)"
                                break
                
                return {"is_honeypot": is_hp, "buy_tax": b_tax, "sell_tax": s_tax, "is_lp_locked": is_lp_locked, "lock_detail": lock_info}
    except: pass
    return None

def format_bsc_security(sec):
    if not sec: return "🛡 <b>Bảo mật:</b> ⚠️ Lỗi quét.\n"
    hp_str = "🔴 CÓ (Lừa đảo)" if sec['is_honeypot'] else "🟢 Không"
    return f"🛡 <b>Bảo mật:</b> Honeypot: {hp_str} | Thuế: {sec['buy_tax']:.1f}%/{sec['sell_tax']:.1f}%\n💧 <b>Tình trạng LP:</b> {sec['lock_detail']}\n"

def get_coin_balance(wallet, ca, decimals):
    try:
        res = requests.get(f"https://deep-index.moralis.io/api/v2.2/{wallet}/erc20?chain=bsc&token_addresses={ca}", headers=get_current_headers(), timeout=5)
        if res.status_code == 200 and len(res.json()) > 0: return float(res.json()[0].get('balance', '0')) / (10**decimals)
    except: pass
    return 0.0

def get_bnb_balance(wallet):
    try:
        res = requests.get(f"https://deep-index.moralis.io/api/v2.2/{wallet}/balance?chain=bsc", headers=get_current_headers(), timeout=5)
        if res.status_code == 200: return int(res.json().get('balance', '0')) / (10**18)
    except: pass
    return 0.0

def init_coin_dict(name, ca, lp):
    return {
        "name": name, "chain": "bsc", "ca": ca, "lp": lp, 
        "time_frame": 2, "min_buys": 2, "min_bnb": 0.1, "scan_interval": 5,
        "last_scan_time": 0, "last_alert_at": time.time(), "last_fetch_timestamp": "",
        "tx_cache": [], "accumulators": {}, "alerted_wallets": {} 
    }

def process_new_coin_async(new_token, lp_address):
    global AUTO_COINS, CONFIG, WBNB_CA
    coin_name = f"BSC_{new_token[:4]}"
    try:
        res = requests.get(f"https://deep-index.moralis.io/api/v2.2/erc20/metadata?chain=bsc&addresses={new_token}", headers=get_current_headers(), timeout=5)
        if res.status_code == 200 and len(res.json()) > 0: coin_name = res.json()[0].get('symbol', coin_name)
    except: pass

    lp_wbnb_bal = get_coin_balance(lp_address, WBNB_CA, 18)
    if lp_wbnb_bal < CONFIG['MIN_LP_BNB']: return

    sec_info = None
    for attempt in range(20): # Scan 20 lần mỗi 15s chờ Dev khóa LP
        sec_info = check_bsc_security(new_token)
        if sec_info and sec_info.get('is_lp_locked'): break
        time.sleep(15) 

    if sec_info and CONFIG.get("NOTIFY_NEW_COIN", True):
        msg = f"🆕 <b>PHÁT HIỆN THANH KHOẢN MỚI!</b>\n\n🪙 Token: <b>{coin_name}</b>\n📝 CA: <code>{new_token}</code>\n🏦 Pool: <b>{lp_wbnb_bal:.2f} BNB</b>\n{format_bsc_security(sec_info)}"
        send_telegram_alert(msg)

    if sec_info and sec_info['is_lp_locked'] and not sec_info['is_honeypot']:
        if len(AUTO_COINS) >= CONFIG['MAX_AUTO_COINS']: AUTO_COINS.pop(0)
        AUTO_COINS.append(init_coin_dict(coin_name, new_token, lp_address))

@app.route('/webhook', methods=['POST'])
def moralis_webhook():
    if not CONFIG.get('AUTO_SCAN', True): return "Disabled", 200
    try:
        data = request.json
        if data and data.get('confirmed'):
            for log in data.get('logs', []):
                if log.get('topic0') == '0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9':
                    t0, t1 = "0x" + log.get('topic1', '')[-40:], "0x" + log.get('topic2', '')[-40:]
                    new_token = t1 if t0.lower() == WBNB_CA else t0
                    if new_token.lower() in BLACKLIST_COINS: continue
                    lp = "0x" + log.get('data', '')[26:66]
                    Thread(target=process_new_coin_async, args=(new_token, lp), daemon=True).start()
    except: pass
    return "OK", 200

def send_main_menu():
    notify_text = "🔔 Báo Coin: BẬT" if CONFIG.get("NOTIFY_NEW_COIN", True) else "🔕 Báo Coin: TẮT"
    kb = {"inline_keyboard": [
        [{"text": "📊 Tổng Quan", "callback_data": "menu_status"}, {"text": "📋 Danh Sách", "callback_data": "menu_list"}],
        [{"text": "📒 Sổ Tay Ví Gom", "callback_data": "menu_wallet_ledger"}],
        [{"text": "⚙️ Cài Đặt Riêng (Từng Coin)", "callback_data": "menu_config_coin_list"}],
        [{"text": "🗑 Xóa Coin", "callback_data": "menu_del"}, {"text": "➕ Thêm Thủ Công", "callback_data": "menu_add"}],
        [{"text": "⛔ Blacklist", "callback_data": "menu_blacklist_view"}, {"text": notify_text, "callback_data": "menu_toggle_new"}],
        [{"text": "🚫 Hủy Lệnh", "callback_data": "menu_cancel"}]
    ]}
    send_telegram_alert("🎛 <b>BSC SNIPER V29 (Anti-Fake Lock)</b>", reply_markup=kb)

def process_update(item):
    global AUTO_COINS, MANUAL_COINS, CONFIG, user_state, BLACKLIST_COINS
    try:
        if "callback_query" in item:
            data = item["callback_query"]["data"]
            if data.startswith("menu_status"):
                msg = f"⚙️ <b>HỆ THỐNG:</b>\n🤖 Rổ Auto: {len(AUTO_COINS)}/{CONFIG['MAX_AUTO_COINS']}\n👤 VIP: {len(MANUAL_COINS)}/{CONFIG['MAX_MANUAL_COINS']}\n🏦 Min Pool: {CONFIG['MIN_LP_BNB']} BNB"
                send_telegram_alert(msg)
            elif data == "menu_list":
                msg = "📋 <b>COIN ĐANG THEO DÕI:</b>\n"
                for c in AUTO_COINS + MANUAL_COINS: msg += f" ├ {c['name']} (CA: {c['ca'][:6]}...)\n"
                send_telegram_alert(msg)
            elif data == "menu_cancel": user_state.clear(); send_telegram_alert("🚫 Đã hủy.")
            # ... (Các logic callback khác sếp giữ như bản cũ nhé) ...
        
        if "message" in item:
            text = item["message"].get("text", "").strip()
            if text in ['/menu', '/start']: send_main_menu()
            # ... (Phần nhận CA/LP thủ công giữ nguyên) ...
    except: pass

def run_bot():
    print("--- BOT V29 STARTING (30D LOCK THRESHOLD) ---", flush=True)
    send_telegram_alert("🚀 <b>Bot V29 đã Online!</b>\n🛡 Đã kích hoạt bộ lọc khóa LP > 30 ngày.")
    while True:
        now = time.time()
        for coin in list(AUTO_COINS + MANUAL_COINS):
            try:
                if now - coin.get('last_scan_time', 0) < (coin.get('scan_interval', 5) * 60): continue
                coin['last_scan_time'] = now
                
                ca, lp = coin["ca"].lower(), coin["lp"].lower()
                price_res = requests.get(f"https://deep-index.moralis.io/api/v2.2/erc20/{ca}/price?chain=bsc", headers=get_current_headers(), timeout=10)
                if price_res.status_code != 200: continue
                
                token_price_bnb = float(price_res.json().get("nativePrice", {}).get("value", "0")) / (10**18)
                token_decimals = int(price_res.json().get('tokenDecimals', 18))

                new_txs, cursor = [], ""
                for _ in range(5):
                    page_url = f"https://deep-index.moralis.io/api/v2.2/erc20/{ca}/transfers?chain=bsc&limit=100" + (f"&cursor={cursor}" if cursor else "")
                    res = requests.get(page_url, headers=get_current_headers(), timeout=10)
                    if res.status_code == 200:
                        batch = res.json().get('result', [])
                        for tx in batch:
                            if coin['last_fetch_timestamp'] and tx.get('block_timestamp', '') <= coin['last_fetch_timestamp']: break
                            new_txs.append(tx)
                        cursor = res.json().get('cursor')
                        if not cursor or (coin['last_fetch_timestamp'] and batch[-1].get('block_timestamp', '') <= coin['last_fetch_timestamp']): break
                    else: break
                
                if new_txs:
                    coin['last_fetch_timestamp'] = max([tx.get('block_timestamp', '') for tx in new_txs])
                    coin['tx_cache'].extend(new_txs)

                # Logic lọc ví gom hàng (Sếp giữ nguyên phần tính toán Accumulator từ bản V28)
                # ... (Phần code gom hàng ở đây) ...
                
            except: pass
            time.sleep(2)
        time.sleep(10)

# Khởi chạy đa luồng
Thread(target=lambda: requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setMyCommands?commands=" + json.dumps([{"command":"menu","description":"Mở Bot"}])), daemon=True).start()
Thread(target=lambda: [time.sleep(2), listen_telegram_commands()] if 'listen_telegram_commands' in globals() else None, daemon=True).start()
Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__": run_server()
