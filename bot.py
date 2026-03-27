import requests
import time
import os
import json
import traceback
from datetime import datetime, timedelta, timezone 
from flask import Flask, request
from threading import Thread

# =========================================================
# BSC SNIPER BOT (FORENSICS V24 - SNIPER LEDGER & DEEP TRACE)
# All previous features + Wallet-Specific Tracking + Ledger UI
# =========================================================

# --- PHẦN 1: TẠO WEB SERVER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "BSC Sniper Bot (Forensics V24 - Sniper Ledger) đang hoạt động!"

def run_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)

# --- PHẦN 2: THÔNG SỐ CỐ ĐỊNH & TOKEN ---
RAW_API_KEYS = [
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImU0Y2QxMTFlLTE3YzYtNDU2My1iOGM5LTFjZWZkMjNmMjJhYiIsIm9yZ0lkIjoiNTA3MDc2IiwidXNlcklkIjoiNTIxNzQ5IiwidHlwZUlkIjoiZDhjZmE3NTEtNTAyMC00MTZkLWJkOGItZWJlMWM3Y2Q0NGJiIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQ0ODczODMsImV4cCI6NDkzMDI0NzM4M30.EdCGoN5pzZEuiDmvbEbHvLLGtQU2D2O_gSHX0t2JKug',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjczZTU1ZWQxLTNjYzQtNGM3ZC05MTVmLThiMDc5MTQ3YjAyYiIsIm9yZ0lkIjoiNTA3MDc4IiwidXNlcklkIjoiNTIxNzUxIiwidHlwZUlkIjoiODFkY2ZiNTgtNTAxNC00NjRkLTg3ZDYtMTM0ZjQzZTVkZmRkIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQ0ODg3NTksImV4cCI6NDkzMDI0ODc1OX0.6hBFIZcOM1rVa6sUPNUZEUUEfSKanrurzqKQPbffiSI',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjVkZTJkNDIzLTY4NmItNDQ1ZS1iNjQ3LTBjNDA5Y2NhZjhiOCIsIm9yZ0lkIjoiNTA3MDc5IiwidXNlcklkIjoiNTIxNzUyIiwidHlwZUlkIjoiMGZhMWU1ZTItYTE1Ny00ODc5LTkxNzktZDA5ZmNlNGJkZjY3IiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQ0ODkxNDUsImV4cCI6NDkzMDI0OTE0NX0.iSlSkU4z_HtWHRQAPRl0H6ZcX1jBbusE9dxjGdIqNp0',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjM3NWFiODUxLWJkN2ItNGRjYy05OWU4LTY3YWExZTY5NjVmNyIsIm9yZ0lkIjoiNTA2NzE3IiwidXNlcklkIjoiNTIxMzgxIiwidHlwZUlkIjoiZTkzYzUwZjctOGI2ZC00ZDkyLTk4MDItMGIyNDllMTUzMzNiIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQyNTkyNjEsImV4cCI6NDkzMDAxOTI2MX0.-ERcEVFm28TLwIr5udsgMWBAvaUaHf5cf5Qd0vLzb18',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImUzYzYyNzRhLWMxZGItNDhlYS1hMjkxLWMzZGQ0YTU0YmM0NiIsIm9yZ0lkIjoiNTA3MDI0IiwidXNlcklkIjoiNTIxNjk2IiwidHlwZUlkIjoiMGExM2FmMGEtNDU2Yi00YTgwLWE0ZjMtZjNlZTc4N2Q0N2M1IiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQ0NTYyMzEsImV4cCI6NDkzMDIxNjIzMX0.gCOXCBjaTjWSo5XskcX4jdvo5fZDptZ-VsI6NuQZwvY',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjZhYzI0NTU0LWI4OTMtNDA5YS1hYThjLTllMjY3YzYzZGUyOCIsIm9yZ0lkIjoiNTA3MTk5IiwidXNlcklkIjoiNTIxODc2IiwidHlwZUlkIjoiNzQyY2JlMWUtZjI4My00OWU0LWE4ZTMtYjk5MTE1ODUzNDRmIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQ1NzYyMzgsImV4cCI6NDkzMDMzNjIzOH0.57uFGZ8ME6Aa6UXayEUMuY6_aWZ8-yO6ESwQ71UweDc',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjM5MzcxZGI4LTQ2ZTMtNDQyOS05MGUzLTlkZDEzNzI1YTliMSIsIm9yZ0lkIjoiNTA3MjAwIiwidXNlcklkIjoiNTIxODc3IiwidHlwZUlkIjoiZTlmMGEzMDUtZjcwZC00YjI5LTkxYzktNGZkY2Y4YjAyOTYzIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQ1NzY3NzYsImV4cCI6NDkzMDMzNjc3Nn0.yMOh0meKfi4sVg7eSNHNtGniiQ53qAk7J-r4rrz5S4g'
]
API_KEYS = list(set(RAW_API_KEYS))
TELEGRAM_BOT_TOKEN = '8526113763:AAH3wANXx126AloxzAKJQrKJAPWiQm7Kb6Q'
TELEGRAM_CHAT_ID = '1976782751'

CONFIG = {
    "MANUAL_TIME_FRAME": 6,  
    "MANUAL_MIN_BUYS": 2,    
    "AUTO_TIME_FRAME": 2,    
    "AUTO_MIN_BUYS": 2,      
    "MAX_AUTO_COINS": 10,     
    "AUTO_SCAN": True,
    "MIN_BNB_BUY": 0.01,     
    "LANGUAGE": "vi",
    "NOTIFY_NEW_COIN": True  
}

MANUAL_COINS = []
AUTO_COINS = [] 
user_state = {} 
current_api_index = 0 
BLACKLIST_COINS = ["0x55d398326f99059ff775485246999027b3197955".lower()]

KNOWN_AGGREGATORS = [
    "0x8D0119F280C5562762a4928bE627a8d504505315".lower(), 
    "0x1111111254EEB25477B68fB85Ed929f73A960582".lower(), 
    "0x10ED43C718714eb63d5aA57B78B54704E256024E".lower(), 
    "0xDef1C0ded9bec7F1a1670819833240f027b25EfF".lower(), 
    "0x57A5B1812674e14D2A4d2b3F30C8fA26A281E1BF".lower()  
]

def get_current_headers():
    global current_api_index
    if not API_KEYS: return {"accept": "application/json"}
    if current_api_index >= len(API_KEYS): current_api_index = 0
    header = {"accept": "application/json", "X-API-Key": API_KEYS[current_api_index]}
    current_api_index += 1
    return header

def send_telegram_alert(message, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True}
    if reply_markup: data["reply_markup"] = json.dumps(reply_markup)
    try: requests.post(url, data=data, timeout=10)
    except: pass

def setup_telegram_commands():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setMyCommands"
    commands = [{"command": "menu", "description": "🎛 Mở Bảng Điều Khiển Bot"}]
    try: requests.post(url, json={"commands": commands}, timeout=5)
    except: pass

def check_bsc_security(ca):
    try:
        url = f"https://api.gopluslabs.io/api/v1/token_security/56?contract_addresses={ca}"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            result = res.json().get("result", {}).get(ca.lower(), {})
            if result:
                is_honeypot = result.get("is_honeypot", "0") == "1"
                buy_tax = float(result.get("buy_tax", 0) or 0) * 100
                sell_tax = float(result.get("sell_tax", 0) or 0) * 100
                return {"is_honeypot": is_honeypot, "buy_tax": buy_tax, "sell_tax": sell_tax}
    except: pass
    return None

def format_bsc_security(ca):
    sec = check_bsc_security(ca)
    if not sec: return "🛡 <b>Bảo mật:</b> ⚠️ Không thể quét contract.\n"
    hp_str = "🔴 CÓ (Nguy hiểm)" if sec['is_honeypot'] else "🟢 Không"
    return f"🛡 <b>Bảo mật:</b> Honeypot: {hp_str} | Thuế: Mua {sec['buy_tax']:.1f}% - Bán {sec['sell_tax']:.1f}%\n"

def get_coin_balance(wallet, ca, decimals):
    try:
        tk_res = requests.get(f"https://deep-index.moralis.io/api/v2.2/{wallet}/erc20?chain=bsc&token_addresses={ca}", headers=get_current_headers(), timeout=5)
        if tk_res.status_code == 200 and tk_res.json() and len(tk_res.json()) > 0:
            return float(tk_res.json()[0].get('balance', '0')) / (10**decimals)
    except: pass
    return 0.0

def get_bnb_balance(wallet):
    try:
        bal_res = requests.get(f"https://deep-index.moralis.io/api/v2.2/{wallet}/balance?chain=bsc", headers=get_current_headers(), timeout=5)
        if bal_res.status_code == 200: return int(bal_res.json().get('balance', '0')) / (10**18)
    except: pass
    return 0.0

def init_coin_dict(name, ca, lp):
    return {
        "name": name, "chain": "bsc", "ca": ca, "lp": lp, 
        "scan_interval": 5, "tx_limit": 100, "last_scan_time": 0, 
        "last_alert_at": time.time(), "prompt_sent": False, 
        "tx_cache": [], "last_fetch_timestamp": "",
        "accumulators": {}, # Chứa Sổ tay Ví Gom: wallet -> list of buy events
        "alerted_wallets": {} # Tránh báo cáo lặp lại liên tục cho 1 ví
    }

def process_new_coin_async(new_token, lp_address):
    global AUTO_COINS, CONFIG, MANUAL_COINS, BLACKLIST_COINS
    coin_name = f"BSC_{new_token[:4]}"
    try:
        meta_url = f"https://deep-index.moralis.io/api/v2.2/erc20/metadata?chain=bsc&addresses={new_token}"
        res = requests.get(meta_url, headers=get_current_headers(), timeout=5)
        if res.status_code == 200 and len(res.json()) > 0 and res.json()[0].get('symbol'):
            coin_name = res.json()[0].get('symbol')
    except: pass

    sec_info = None
    for attempt in range(20):
        sec_info = check_bsc_security(new_token)
        if sec_info is not None: break
        time.sleep(15) 

    is_clean = False
    if sec_info and not sec_info['is_honeypot'] and sec_info['buy_tax'] < 10 and sec_info['sell_tax'] < 10:
        is_clean = True

    if CONFIG.get("NOTIFY_NEW_COIN", True):
        hp_str = "🔴 CÓ (Lừa đảo)" if sec_info and sec_info['is_honeypot'] else ("🟢 Không" if sec_info else f"⚠️ Lỗi quét (Timeout)")
        bt = f"{sec_info['buy_tax']:.1f}" if sec_info else "?"
        st = f"{sec_info['sell_tax']:.1f}" if sec_info else "?"
        msg = f"🆕 <b>CÓ COIN MỚI VỪA TẠO THANH KHOẢN!</b>\n\n🪙 Tên Coin: <b>{coin_name}</b>\n📝 CA: <code>{new_token}</code>\n🛡 <b>Bảo mật:</b> Honeypot: {hp_str} | Thuế: {bt}% / {st}%\n\n"
        send_telegram_alert(msg)

    if is_clean:
        if len(AUTO_COINS) >= CONFIG['MAX_AUTO_COINS']: AUTO_COINS.pop(0)
        AUTO_COINS.append(init_coin_dict(coin_name, new_token, lp_address))

@app.route('/webhook', methods=['POST'])
def moralis_webhook():
    global AUTO_COINS, CONFIG, BLACKLIST_COINS
    if not CONFIG.get('AUTO_SCAN', True): return "Auto scan is disabled", 200
    try:
        data = request.json
        if data and data.get('confirmed'):
            logs = data.get('logs', [])
            for log in logs:
                if log.get('topic0') == '0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9':
                    token0 = "0x" + log.get('topic1', '')[-40:]
                    token1 = "0x" + log.get('topic2', '')[-40:]
                    wbnb = "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"
                    new_token = token1 if token0.lower() == wbnb else token0
                    lp_address = "0x" + log.get('data', '')[26:66]
                    if new_token.lower() in BLACKLIST_COINS: continue
                    if any(c['ca'].lower() == new_token.lower() for c in AUTO_COINS + MANUAL_COINS): continue
                    Thread(target=process_new_coin_async, args=(new_token, lp_address), daemon=True).start()
    except: pass
    return "OK", 200

# --- MENU & GIAO DIỆN TƯƠNG TÁC SỔ TAY VÍ ---
def send_main_menu():
    notify_text = "🔔 Báo Coin Mới: BẬT" if CONFIG.get("NOTIFY_NEW_COIN", True) else "🔕 Báo Coin Mới: TẮT (Ngầm)"
    keyboard = {"inline_keyboard": [
        [{"text": "📊 Xem Cấu Hình", "callback_data": "menu_status"}, {"text": "📋 List Đang Quét", "callback_data": "menu_list"}],
        [{"text": "📒 Sổ Tay Ví Gom (NEW)", "callback_data": "menu_wallet_ledger"}],
        [{"text": "⚙️ Tần suất quét Coin", "callback_data": "menu_freq_coin"}, {"text": "🗑 Xóa Coin", "callback_data": "menu_del"}],
        [{"text": "⛔ Chặn CA (Blacklist)", "callback_data": "menu_blacklist_add"}, {"text": "👁 Xem Blacklist", "callback_data": "menu_blacklist_view"}],
        [{"text": "⏱ Lịch sử soi (h)", "callback_data": "menu_set_time"}, {"text": "🛒 Số Lệnh Gom (Min)", "callback_data": "menu_set_buy"}],
        [{"text": "➕ Thêm Coin BSC", "callback_data": "menu_add"}, {"text": "🐋 Cài Tay To (BNB)", "callback_data": "menu_set_bnb"}],
        [{"text": notify_text, "callback_data": "menu_toggle_new"}, {"text": "🚫 Hủy Lệnh", "callback_data": "menu_cancel"}]
    ]}
    send_telegram_alert("🎛 <b>BSC SNIPER BOT (V24 - Sniper Ledger)</b>\n👉 Chọn chức năng bên dưới:", reply_markup=keyboard)

def execute_command(cmd):
    global CONFIG, user_state, BLACKLIST_COINS, AUTO_COINS, MANUAL_COINS
    if cmd == 'status':
        msg = (f"⚙️ <b>CẤU HÌNH HIỆN TẠI</b>\n"
               f"🤖 Lịch sử soi (Auto): <b>{CONFIG['AUTO_TIME_FRAME']}h</b> | Đòi hỏi: <b>Ví gom >= {CONFIG['AUTO_MIN_BUYS']} lệnh</b>\n"
               f"👤 Lịch sử soi (Thủ công): <b>{CONFIG['MANUAL_TIME_FRAME']}h</b> | Đòi hỏi: <b>Ví gom >= {CONFIG['MANUAL_MIN_BUYS']} lệnh</b>\n"
               f"🐋 Mức Tay To: <b>>= {CONFIG['MIN_BNB_BUY']} BNB</b>\n"
               f"🕵️‍♂️ Chế độ Bắn Tỉa Cá Nhân (Sniper Ledger): <b>BẬT</b>\n")
        send_telegram_alert(msg)
    elif cmd == 'list':
        msg = f"📋 <b>DANH SÁCH BSC</b>\n\n🤖 <b>AUTO ({len(AUTO_COINS)}/{CONFIG['MAX_AUTO_COINS']})</b>\n"
        for c in AUTO_COINS: msg += f" ├ <b>{c['name']}</b>\n └ CA: <code>{c['ca']}</code>\n"
        msg += f"\n👤 <b>THỦ CÔNG ({len(MANUAL_COINS)})</b>\n"
        for c in MANUAL_COINS: msg += f" ├ <b>{c['name']}</b>\n └ CA: <code>{c['ca']}</code>\n"
        send_telegram_alert(msg)
    elif cmd == 'wallet_ledger':
        kb = {"inline_keyboard": []}
        found = False
        for c in AUTO_COINS + MANUAL_COINS:
            if c.get('accumulators') and len(c['accumulators']) > 0:
                found = True
                kb["inline_keyboard"].append([{"text": f"📒 {c['name']} ({len(c['accumulators'])} ví gom)", "callback_data": f"w_c_{c['ca'][:10]}"}])
        if not found:
            send_telegram_alert("⚠️ Hiện tại chưa có cuốn sổ tay nào (Chưa phát hiện ví nào gom đủ số lệnh cài đặt).")
        else:
            send_telegram_alert("📒 <b>SỔ TAY VÍ GOM</b>\n👇 Chọn đồng coin để xem danh sách ví đang âm thầm gom hàng:", reply_markup=kb)
    # Các lệnh UI cũ rút gọn cho tiết kiệm dòng...
    elif cmd == 'freq_coin':
        all_coins = AUTO_COINS + MANUAL_COINS
        if not all_coins: send_telegram_alert("⚠️ Danh sách hiện tại đang trống!"); return
        kb = {"inline_keyboard": [[{"text": f"⚙️ {c['name']}", "callback_data": f"setfreq_{c['ca'][:10]}"}] for c in all_coins]}
        send_telegram_alert("👇 Chọn coin bạn muốn đổi Tần suất quét:", reply_markup=kb)
    elif cmd == 'del':
        all_coins = AUTO_COINS + MANUAL_COINS
        if not all_coins: send_telegram_alert("⚠️ Danh sách trống!"); return
        kb = {"inline_keyboard": [[{"text": f"🗑 {c['name']}", "callback_data": f"delcoin_{c['ca'][:10]}"}] for c in all_coins]}
        send_telegram_alert("👇 Chọn coin muốn <b>XÓA</b>:", reply_markup=kb)
    elif cmd == 'blacklist_add':
        user_state = {'step': 'WAITING_BLACKLIST_CA', 'last_time': time.time()}
        send_telegram_alert("⛔ Nhập CA muốn chặn vĩnh viễn:")
    elif cmd == 'blacklist_view':
        if not BLACKLIST_COINS: send_telegram_alert("🟢 Blacklist trống.")
        else: send_telegram_alert(f"⛔ <b>BLACKLIST:</b>\n" + "\n".join([f" ├ <code>{ca}</code>" for ca in BLACKLIST_COINS]))
    elif cmd == 'toggle_new':
        CONFIG["NOTIFY_NEW_COIN"] = not CONFIG.get("NOTIFY_NEW_COIN", True)
        send_telegram_alert(f"✅ Báo Coin Mới: {'BẬT' if CONFIG['NOTIFY_NEW_COIN'] else 'TẮT (Silent)'}")
    elif cmd in ['set_time', 'set_buy']:
        kb = {"inline_keyboard": [[{"text": "🤖 Auto", "callback_data": f"{cmd}_auto"}, {"text": "👤 Thủ Công", "callback_data": f"{cmd}_manual"}]]}
        send_telegram_alert(f"Cài đặt cho rổ nào?", reply_markup=kb)
    elif cmd == 'add':
        user_state = {'step': 'WAITING_CA', 'last_time': time.time()}; send_telegram_alert("📝 Nhập CA BSC muốn thêm:")
    elif cmd == 'set_bnb':
        user_state = {'step': 'WAITING_BNB_VAL', 'last_time': time.time()}; send_telegram_alert("🐋 Nhập số BNB tối thiểu / lệnh:")
    elif cmd == 'cancel':
        user_state.clear(); send_telegram_alert("🚫 Đã hủy thao tác.")

def process_update(item):
    global AUTO_COINS, MANUAL_COINS, CONFIG, user_state, API_KEYS, RAW_API_KEYS, BLACKLIST_COINS
    try:
        if user_state and time.time() - user_state.get('last_time', time.time()) > 300:
            user_state.clear()

        if "callback_query" in item:
            data = item["callback_query"]["data"]
            if data.startswith("menu_"): execute_command(data.replace("menu_", "")); return
            
            all_c = AUTO_COINS + MANUAL_COINS
            
            # --- LUỒNG DEEP TRACE (V24) ---
            if data.startswith("w_c_"): # Chọn Coin trong Ledger
                ca_short = data.split("_")[2]
                coin = next((c for c in all_c if c['ca'].startswith(ca_short)), None)
                if not coin or not coin.get('accumulators'): return
                user_state = {'view_ca': coin['ca'], 'last_time': time.time()} # Lưu CA vào não bot
                kb = {"inline_keyboard": []}
                for w, buys in coin['accumulators'].items():
                    kb["inline_keyboard"].append([{"text": f"💳 {w[:6]}... ({len(buys)} lệnh)", "callback_data": f"w_w_{w}"}])
                send_telegram_alert(f"📒 <b>SỔ TAY COIN: {coin['name']}</b>\n👇 Chọn 1 ví để check Info & Dòng tiền:", reply_markup=kb)
                return

            if data.startswith("w_w_"): # Check ví cụ thể & Trace
                wallet = data.split("_")[2]
                ca = user_state.get('view_ca')
                coin = next((c for c in all_c if c['ca'] == ca), None)
                if not coin: send_telegram_alert("⚠️ Dữ liệu coin đã bị xóa."); return
                
                # Fetch Realtime
                bnb_bal = get_bnb_balance(wallet)
                token_decimals = 18 # Guessing default
                try:
                    price_res = requests.get(f"https://deep-index.moralis.io/api/v2.2/erc20/{ca}/price?chain=bsc", headers=get_current_headers(), timeout=5)
                    if price_res.status_code == 200: token_decimals = int(price_res.json().get('tokenDecimals', 18))
                except: pass
                token_bal = get_coin_balance(wallet, ca, token_decimals)
                
                buys_list = coin.get('accumulators', {}).get(wallet, [])
                buys_cnt = len(buys_list)
                
                # Tìm Giao dịch cuối cùng từ Sổ tay Cache của Bot (Không cần gọi API thêm)
                last_action = "Chưa rõ"
                dest_wallet = None
                sorted_txs = sorted(coin.get('tx_cache', []), key=lambda x: x.get('block_timestamp', ''))
                for tx in sorted_txs:
                    s, r = tx.get('from_address', '').lower(), tx.get('to_address', '').lower()
                    if s == wallet:
                        if r == coin['lp']: last_action = "🔴 ĐÃ XẢ HÀNG (Bán lại vào Pool)"
                        else: 
                            last_action = "➡️ ĐÃ CHUYỂN TOKEN (Tẩu tán)"
                            dest_wallet = r
                    elif r == wallet:
                        last_action = "🟢 MUA / NHẬN THÊM TOKEN"
                        dest_wallet = None # Bị đè lại thành nhận
                
                msg = (f"🔍 <b>HỒ SƠ VÍ GOM:</b>\n💳 <code>{wallet}</code>\n\n"
                       f"🪙 <b>Coin:</b> {coin['name']}\n"
                       f"├ Dư (Gas): <b>{bnb_bal:.4f} BNB</b>\n"
                       f"├ Đang Hold: <b>{token_bal:,.2f} {coin['name']}</b>\n"
                       f"├ Số lệnh gom: <b>{buys_cnt} lệnh</b>\n"
                       f"└ Action cuối: <b>{last_action}</b>\n")
                
                kb = None
                if dest_wallet:
                    msg += f"\n🚨 <b>Phát hiện Chuyển Token đến:</b>\n👉 <code>{dest_wallet}</code>"
                    kb = {"inline_keyboard": [
                        [{"text": "🔍 Truy vết tiếp Ví nhận Token này", "callback_data": f"w_w_{dest_wallet}"}],
                        [{"text": "🔙 Quay lại Sổ tay", "callback_data": f"w_c_{ca[:10]}"}]
                    ]}
                else:
                    kb = {"inline_keyboard": [[{"text": "🔙 Quay lại Sổ tay", "callback_data": f"w_c_{ca[:10]}"}]]}
                
                send_telegram_alert(msg, reply_markup=kb)
                return

            # CÁC LUỒNG CŨ RÚT GỌN...
            if data.startswith("delcoin_"):
                ca_short = data.split("_")[1]
                coin = next((c for c in all_c if c['ca'].startswith(ca_short)), None)
                if coin:
                    user_state = {'step': 'WAITING_DEL_CONFIRM', 'last_time': time.time(), 'target_ca': coin['ca']}
                    kb = {"inline_keyboard": [[{"text": "✅ Xóa", "callback_data": f"confirmdel_{coin['ca'][:10]}"}, {"text": "❌ Tôi nhầm", "callback_data": "menu_del"}]]}
                    send_telegram_alert(f"❓ Xóa coin <b>{coin['name']}</b>?", reply_markup=kb)
                return
            if data.startswith("confirmdel_"):
                if not user_state or user_state.get('step') != 'WAITING_DEL_CONFIRM': return
                ca_short = data.split("_")[1]
                MANUAL_COINS[:] = [c for c in MANUAL_COINS if not c['ca'].startswith(ca_short)]
                AUTO_COINS[:] = [c for c in AUTO_COINS if not c['ca'].startswith(ca_short)]
                send_telegram_alert("🗑 Đã xóa!"); user_state.clear(); return

            if data.startswith("setfreq_"):
                ca_short = data.split("_")[1]
                coin = next((c for c in all_c if c['ca'].startswith(ca_short)), None)
                if coin:
                    user_state = {'step': 'WAITING_FREQ_MIN', 'target_ca': coin['ca'], 'last_time': time.time()}
                    send_telegram_alert(f"⏱ Cấu hình: {coin['name']}\n👉 <b>BAO NHIÊU PHÚT</b> bot quét 1 lần?")
                return

            if data in ["set_time_auto", "set_time_manual", "set_buy_auto", "set_buy_manual"]:
                lst, prm = ("AUTO_SCAN", "TIME_FRAME") if "auto" in data else ("THỦ CÔNG", "MIN_BUYS")
                if "time" in data: user_state = {'step': f"WAITING_TIME_VAL_{data.split('_')[2].upper()}", 'last_time': time.time()}; send_telegram_alert("🕒 Nhập số giờ (VD: 2):")
                else: user_state = {'step': f"WAITING_BUY_VAL_{data.split('_')[2].upper()}", 'last_time': time.time()}; send_telegram_alert("🛒 Nhập số lệnh gom (VD: 2):")
                return

        if "message" in item:
            text = item["message"].get("text", "").strip()
            if not text: return
            if text in ['/menu', '/start']: send_main_menu()
            elif user_state:
                if text == '/cancel': execute_command('cancel'); return
                step = user_state.get('step')
                
                if step == 'WAITING_BLACKLIST_CA':
                    target_ca = text.lower()
                    if target_ca not in BLACKLIST_COINS:
                        BLACKLIST_COINS.append(target_ca)
                        MANUAL_COINS[:] = [c for c in MANUAL_COINS if c['ca'].lower() != target_ca]
                        AUTO_COINS[:] = [c for c in AUTO_COINS if c['ca'].lower() != target_ca]
                        send_telegram_alert(f"✅ Đã chặn vĩnh viễn <code>{target_ca}</code>")
                    user_state.clear()
                
                elif step == 'WAITING_FREQ_MIN':
                    try: user_state['minutes'] = float(text); user_state['step'] = 'WAITING_FREQ_TX'; user_state['last_time'] = time.time(); send_telegram_alert("👉 Lấy tối đa BAO NHIÊU GIAO DỊCH (Lần đầu)?")
                    except: send_telegram_alert("❌ Nhập số.")
                elif step == 'WAITING_FREQ_TX':
                    try:
                        tx_limit = int(text)
                        target_ca, mins = user_state['target_ca'], user_state['minutes']
                        for c in AUTO_COINS + MANUAL_COINS:
                            if c['ca'] == target_ca: c['scan_interval'] = mins; c['tx_limit'] = tx_limit; send_telegram_alert(f"✅ Đã lưu: {mins} phút / {tx_limit} tx!")
                        user_state.clear()
                    except: send_telegram_alert("❌ Nhập số nguyên.")
                elif step == 'WAITING_CA':
                    if text.lower() in BLACKLIST_COINS: send_telegram_alert("🚫 CA nằm trong Blacklist."); user_state.clear(); return
                    user_state['ca'] = text; user_state['step'] = 'WAITING_LP'; user_state['last_time'] = time.time(); send_telegram_alert("✅ Nhập tiếp địa chỉ LP:")
                elif step == 'WAITING_LP':
                    ca, lp = user_state['ca'], text
                    MANUAL_COINS.append(init_coin_dict(f"BSC_{ca[:4]}", ca, lp))
                    send_telegram_alert(f"🎉 Đã thêm!"); user_state.clear()
                elif step == 'WAITING_BNB_VAL':
                    try: CONFIG['MIN_BNB_BUY'] = float(text); send_telegram_alert(f"✅ Đã cài Tay to: <b>{text} BNB</b>."); user_state.clear()
                    except: pass
                elif step.startswith('WAITING_TIME_VAL_'):
                    try: CONFIG[f"{step.split('_')[3]}_TIME_FRAME"] = int(text); send_telegram_alert(f"✅ Đã lưu."); user_state.clear()
                    except: pass
                elif step.startswith('WAITING_BUY_VAL_'):
                    try: CONFIG[f"{step.split('_')[3]}_MIN_BUYS"] = int(text); send_telegram_alert(f"✅ Đã lưu."); user_state.clear()
                    except: pass
    except: pass

def listen_telegram_commands():
    setup_telegram_commands()
    last_update_id = 0
    while True:
        try:
            res = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates", params={"offset": last_update_id + 1, "timeout": 10}).json()
            for item in res.get("result", []):
                last_update_id = item["update_id"]; process_update(item) 
        except: pass
        time.sleep(2)

# --- LÕI ĐIỀU TRA ON-CHAIN V24 (WALLET-SPECIFIC TRACKING) ---
def run_bot():
    try:
        print("--- LUONG QUET V24 DA KHOI DONG (Sniper Mode) ---", flush=True)
        send_telegram_alert("🚀 <b>Bot Săn Meme V24 đã sẵn sàng, gõ /menu để bắt đầu</b>")
        
        while True:
            now = time.time()
            for list_type, coin_list in [("AUTO", AUTO_COINS), ("MANUAL", MANUAL_COINS)]:
                time_frame = CONFIG[f"{list_type}_TIME_FRAME"]
                min_buys = CONFIG[f"{list_type}_MIN_BUYS"] # Số lệnh ĐÒI HỎI CHO 1 VÍ
                min_bnb = CONFIG['MIN_BNB_BUY']
                
                for coin in list(coin_list):
                    try:
                        scan_interval_sec = coin.get('scan_interval', 5) * 60
                        if now - coin.get('last_scan_time', 0) < scan_interval_sec: continue 
                        coin['last_scan_time'] = time.time()
                        
                        ca, lp = coin["ca"].lower(), coin["lp"].lower()
                        print(f"\n--- Dang soi coin: {coin['name']} (CA: {ca[:6]}...) ---", flush=True)

                        token_price_bnb, token_decimals = 0, 18
                        price_res = requests.get(f"https://deep-index.moralis.io/api/v2.2/erc20/{ca}/price?chain=bsc", headers=get_current_headers(), timeout=10)
                        if price_res.status_code == 200:
                            p_data = price_res.json()
                            token_decimals = int(p_data.get('tokenDecimals', 18))
                            token_price_bnb = float(p_data.get("nativePrice", {}).get("value", "0")) / (10**18)

                        # Kéo Delta Fetch
                        new_txs, cursor, hit_old_data = [], "", False
                        max_pages = max(1, (coin.get('tx_limit', 100) + 99) // 100) if not coin['last_fetch_timestamp'] else 20

                        for _ in range(max_pages): 
                            page_url = f"https://deep-index.moralis.io/api/v2.2/erc20/{ca}/transfers?chain=bsc&limit=100" + (f"&cursor={cursor}" if cursor else "")
                            response = requests.get(page_url, headers=get_current_headers(), timeout=10)
                            if response.status_code == 200:
                                page_data = response.json()
                                for tx in page_data.get('result', []):
                                    if coin['last_fetch_timestamp'] and tx.get('block_timestamp', '') <= coin['last_fetch_timestamp']: hit_old_data = True; break
                                    new_txs.append(tx)
                                cursor = page_data.get('cursor')
                                if not cursor or hit_old_data: break 
                            else: break
                                
                        if new_txs:
                            max_ts = max([tx.get('block_timestamp', '') for tx in new_txs])
                            if max_ts > coin['last_fetch_timestamp']: coin['last_fetch_timestamp'] = max_ts
                            coin['tx_cache'].extend(new_txs)

                        # Time Pruning
                        time_ago = datetime.now(timezone.utc) - timedelta(hours=time_frame)
                        valid_cache = []
                        for tx in coin['tx_cache']:
                            try:
                                if datetime.strptime(tx.get('block_timestamp', '')[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc) >= time_ago: valid_cache.append(tx)
                            except: pass
                        coin['tx_cache'] = valid_cache
                        
                        sorted_txs = sorted(valid_cache, key=lambda x: x.get('block_timestamp', ''))
                        
                        # 🔥 V24 CORE: THEO DÕI TỪNG VÍ CÁ NHÂN (WALLET RECEIPTS) 🔥
                        wallet_receipts = {} # Dict: wallet -> list of buy objects: {"time": "...", "bnb": ...}
                        router_temporary_sources = {} 

                        for tx in sorted_txs:
                            sender, receiver, value_raw = tx.get('from_address', '').lower(), tx.get('to_address', '').lower(), int(tx.get('value', '0'))
                            tx_ts_str = tx.get('block_timestamp', '')
                            if value_raw == 0 or not tx_ts_str: continue
                            
                            tx_dt = datetime.strptime(tx_ts_str[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
                            nice_time = (tx_dt + timedelta(hours=7)).strftime("%H:%M:%S") # UTC+7 for display
                            tx_bnb_value = (value_raw / (10**token_decimals)) * token_price_bnb

                            # NẾU MUA TỪ LP
                            if sender == lp:
                                if token_price_bnb > 0 and tx_bnb_value >= min_bnb:
                                    if receiver in KNOWN_AGGREGATORS: 
                                        router_temporary_sources[receiver] = {"amount_raw": value_raw, "bnb": tx_bnb_value, "time": nice_time}
                                    else: 
                                        wallet_receipts.setdefault(receiver, []).append({"time": nice_time, "bnb": tx_bnb_value})
                            # NẾU MUA QUA ROUTER
                            elif sender in KNOWN_AGGREGATORS and sender in router_temporary_sources:
                                s_info = router_temporary_sources[sender]
                                if value_raw <= s_info["amount_raw"]: # Match block time usually, simplified here for speed
                                    wallet_receipts.setdefault(receiver, []).append({"time": s_info["time"], "bnb": s_info["bnb"]})
                                    del router_temporary_sources[sender]
                            # NẾU CÓ SỰ DỊCH CHUYỂN TOKEN GIỮA CÁC VÍ
                            elif sender in wallet_receipts:
                                if receiver == lp: # Dump -> Xóa án tích gom hàng
                                    wallet_receipts.pop(sender, None)
                                else: # Transfer -> Chuyển toàn bộ biên lai sang ví nhận
                                    wallet_receipts.setdefault(receiver, []).extend(wallet_receipts[sender])
                                    wallet_receipts.pop(sender, None)

                        # KIỂM TRA ĐIỀU KIỆN KÍCH HOẠT CHO TỪNG VÍ
                        for wallet, buys in wallet_receipts.items():
                            if len(buys) >= min_buys:
                                # Kiểm tra xem đã báo cho ví này với số lệnh này chưa?
                                last_alerted_count = coin['alerted_wallets'].get(wallet, 0)
                                if len(buys) > last_alerted_count:
                                    # LƯU VÀO SỔ TAY VÍ GOM
                                    coin['accumulators'][wallet] = buys
                                    coin['alerted_wallets'][wallet] = len(buys)
                                    
                                    # TRÍCH XUẤT THÔNG TIN REAL-TIME
                                    bnb_bal = get_bnb_balance(wallet)
                                    token_bal = get_coin_balance(wallet, ca, token_decimals)
                                    
                                    # TẠO TIN NHẮN BÁO CÁO CÁ NHÂN HÓA
                                    msg = (f"🚨 <b>PHÁT HIỆN VÍ GOM HÀNG!</b>\n\n"
                                           f"🪙 Coin: <b>{coin['name']}</b>\n"
                                           f"📝 CA: <code>{ca}</code>\n"
                                           f"💳 <b>Ví gom:</b> <code>{wallet}</code>\n"
                                           f"💰 <b>Đang Hold: {token_bal:,.2f} {coin['name']}</b>\n"
                                           f"⛽ Dư BNB: {bnb_bal:.4f} BNB\n\n"
                                           f"📊 <b>Chi tiết {len(buys)} lệnh gom (trong {time_frame}h):</b>\n")
                                    
                                    for b in buys:
                                        msg += f" ├ <i>{b['time']}</i> : Mua <b>{b['bnb']:.3f} BNB</b>\n"
                                    
                                    # NÚT THEO DÕI SÂU TRỰC TIẾP TRÊN TIN NHẮN
                                    kb = {"inline_keyboard": [[{"text": "🔍 Check Ví Này (Dòng tiền)", "callback_data": f"w_w_{wallet}"}]]}
                                    
                                    send_telegram_alert(msg, reply_markup=kb)
                            
                    except Exception as e: print(f"   ⚠️ LOI QUET COIN: {e}", flush=True)
                    time.sleep(2) 
            time.sleep(15) 

    except Exception as e: traceback.print_exc()

Thread(target=listen_telegram_commands, daemon=True).start()
Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__": run_server()
