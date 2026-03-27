import requests
import time
import os
import json
import traceback
from datetime import datetime, timedelta, timezone 
from flask import Flask, request
from threading import Thread

# =========================================================
# BSC SNIPER BOT (FORENSICS V21 - ENTERPRISE DELTA-CACHE)
# All features: V14 Router Skip, V16 Smart Schedule, V17 UI, 
# V18 Retry 45s, V19 Silent, V20 AutoMenu, V21 Delta-Cache.
# =========================================================

# --- PHẦN 1: TẠO WEB SERVER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "BSC Sniper Bot (Forensics V21 - Enterprise Delta-Cache) đang hoạt động!"

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
    "MANUAL_MIN_BUYS": 1,    
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

TEXTS = {
    "vi": {"lang_prompt": "🌐 <b>Chọn ngôn ngữ:</b>", "lang_changed": "✅ Đã chuyển sang Tiếng Việt!"},
    "en": {"lang_prompt": "🌐 <b>Select Language:</b>", "lang_changed": "✅ Changed to English!"}
}

KNOWN_AGGREGATORS = [
    "0x8D0119F280C5562762a4928bE627a8d504505315".lower(), 
    "0x1111111254EEB25477B68fB85Ed929f73A960582".lower(), 
    "0x10ED43C718714eb63d5aA57B78B54704E256024E".lower(), 
    "0xDef1C0ded9bec7F1a1670819833240f027b25EfF".lower(), 
    "0x57A5B1812674e14D2A4d2b3F30C8fA26A281E1BF".lower()  
]

def t(key, *args):
    lang = CONFIG["LANGUAGE"]
    text = TEXTS.get(lang, TEXTS["vi"]).get(key, key)
    if args: return text.format(*args)
    return text

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

# --- AUTO MENU V20 ---
def setup_telegram_commands():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setMyCommands"
    commands = [{"command": "menu", "description": "🎛 Mở Bảng Điều Khiển Bot"}]
    try:
        response = requests.post(url, json={"commands": commands}, timeout=5)
        if response.status_code == 200:
            print("✅ Da cai dat nut /menu tren Telegram thanh cong!", flush=True)
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

# --- WEBHOOK V18 & V19 (45s Retry + Silent Mode) ---
def process_new_coin_async(new_token, lp_address):
    global AUTO_COINS, CONFIG, MANUAL_COINS
    coin_name = f"BSC_{new_token[:4]}"
    
    try:
        meta_url = f"https://deep-index.moralis.io/api/v2.2/erc20/metadata?chain=bsc&addresses={new_token}"
        res = requests.get(meta_url, headers=get_current_headers(), timeout=5)
        if res.status_code == 200:
            meta_data = res.json()
            if len(meta_data) > 0 and meta_data[0].get('symbol'):
                coin_name = meta_data[0].get('symbol')
    except: pass

    print(f"   => Dang kiem tra bao mat cho {coin_name}...", flush=True)
    sec_info = None
    for attempt in range(3):
        sec_info = check_bsc_security(new_token)
        if sec_info is not None:
            print(f"   => Da lay duoc du lieu bao mat tu GoPlus o lan thu {attempt+1}!", flush=True)
            break
        print(f"   => [GoPlus] Chua kip quet ma nguon. Cho 15s thu lai (Lan {attempt+1}/3)...", flush=True)
        time.sleep(15) 

    is_clean = False
    if sec_info and not sec_info['is_honeypot'] and sec_info['buy_tax'] < 10 and sec_info['sell_tax'] < 10:
        is_clean = True

    if CONFIG.get("NOTIFY_NEW_COIN", True):
        hp_str = "🔴 CÓ (Lừa đảo)" if sec_info and sec_info['is_honeypot'] else ("🟢 Không" if sec_info else "⚠️ Lỗi quét (Hết 45s Timeout)")
        bt = f"{sec_info['buy_tax']:.1f}" if sec_info else "?"
        st = f"{sec_info['sell_tax']:.1f}" if sec_info else "?"
        msg = f"🆕 <b>CÓ COIN MỚI VỪA TẠO THANH KHOẢN!</b>\n\n🪙 Tên Coin: <b>{coin_name}</b>\n📝 CA: <code>{new_token}</code>\n🛡 <b>Bảo mật:</b> Honeypot: {hp_str} | Thuế: {bt}% / {st}%\n\n"
        send_telegram_alert(msg)
    else:
        print(f"   => [Silent Mode] Da tat thong bao Telegram, chuyen sang theo doi ngam.", flush=True)

    if is_clean:
        if len(AUTO_COINS) >= CONFIG['MAX_AUTO_COINS']: AUTO_COINS.pop(0)
        # Khởi tạo kèm các trường Sổ tay (Cache V21)
        AUTO_COINS.append({"name": coin_name, "chain": "bsc", "ca": new_token, "lp": lp_address, "scan_interval": 5, "tx_limit": 100, "last_scan_time": 0, "last_alert_at": time.time(), "prompt_sent": False, "tx_cache": [], "last_fetch_timestamp": ""})
        print(f"   => Da them {coin_name} vao ro AUTO quet ca map.", flush=True)
    else:
        print(f"   => Bo qua {coin_name} do rui ro lanh it du nhieu.", flush=True)

@app.route('/webhook', methods=['POST'])
def moralis_webhook():
    print("\n📥 [WEBHOOK] Co nguoi go cua!", flush=True)
    global AUTO_COINS, CONFIG
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
                    if any(c['ca'].lower() == new_token.lower() for c in AUTO_COINS + MANUAL_COINS): continue
                    Thread(target=process_new_coin_async, args=(new_token, lp_address), daemon=True).start()
    except Exception as e: print(f"❌ [WEBHOOK LOI]: {e}", flush=True)
    return "OK", 200

# --- GIAO DIỆN & TƯƠNG TÁC V17 ---
def send_main_menu():
    notify_text = "🔔 Báo Coin Mới: BẬT" if CONFIG.get("NOTIFY_NEW_COIN", True) else "🔕 Báo Coin Mới: TẮT (Ngầm)"
    keyboard = {"inline_keyboard": [
        [{"text": "📊 Xem Cấu Hình", "callback_data": "menu_status"}, {"text": "📋 List Đang Quét", "callback_data": "menu_list"}],
        [{"text": "⚙️ Tần suất quét Coin", "callback_data": "menu_freq_coin"}, {"text": "🗑 Xóa Coin", "callback_data": "menu_del"}],
        [{"text": "⏱ Lịch sử soi (h)", "callback_data": "menu_set_time"}, {"text": "🛒 Đổi Lệnh Mua", "callback_data": "menu_set_buy"}],
        [{"text": "➕ Thêm Coin BSC", "callback_data": "menu_add"}, {"text": "📦 Giới Hạn Auto", "callback_data": "menu_set_max_auto"}],
        [{"text": "🐋 Cài Tay To (BNB)", "callback_data": "menu_set_bnb"}, {"text": "🔑 Kho API Keys", "callback_data": "menu_keys"}],
        [{"text": notify_text, "callback_data": "menu_toggle_new"}, {"text": "🌐 Đổi Ngôn Ngữ", "callback_data": "menu_language"}],
        [{"text": "🚫 Hủy Lệnh", "callback_data": "menu_cancel"}]
    ]}
    send_telegram_alert("🎛 <b>BẢNG ĐIỀU KHIỂN BSC SNIPER (V21 - Enterprise)</b>\n👉 Chọn chức năng bên dưới:", reply_markup=keyboard)

def execute_command(cmd):
    global CONFIG, user_state
    if cmd == 'status':
        msg = (f"⚙️ <b>CẤU HÌNH HIỆN TẠI</b>\n"
               f"🤖 Lịch sử soi (Auto): <b>{CONFIG['AUTO_TIME_FRAME']}h</b> | Gom >= <b>{CONFIG['AUTO_MIN_BUYS']}</b>\n"
               f"👤 Lịch sử soi (Thủ công): <b>{CONFIG['MANUAL_TIME_FRAME']}h</b> | Gom >= <b>{CONFIG['MANUAL_MIN_BUYS']}</b>\n"
               f"🐋 Mức Tay To: <b>>= {CONFIG['MIN_BNB_BUY']} BNB</b>\n"
               f"🔑 Kho API: <b>{len(API_KEYS)} Key</b>\n"
               f"🕵️‍♂️ Router Translucency & Delta-Cache: <b>ON</b>\n"
               f"🔔 Báo Telegram khi có Coin mới: <b>{'BẬT (Báo cáo)' if CONFIG.get('NOTIFY_NEW_COIN', True) else 'TẮT (Theo dõi ngầm)'}</b>\n\n"
               f"⏱ <b>TẦN SUẤT & BỘ NHỚ TỪNG COIN:</b>\n")
        all_listed = AUTO_COINS + MANUAL_COINS
        if not all_listed: msg += "<i>(Chưa có coin nào)</i>"
        for c in all_listed:
            cache_size = len(c.get('tx_cache', []))
            msg += f"🔹 <b>{c['name']}</b>: {c.get('scan_interval', 5)}p / {c.get('tx_limit', 100)}tx (Sổ tay: {cache_size} lệnh)\n"
        send_telegram_alert(msg)
    elif cmd == 'list':
        msg = f"📋 <b>DANH SÁCH BSC</b>\n\n🤖 <b>AUTO ({len(AUTO_COINS)}/{CONFIG['MAX_AUTO_COINS']})</b>\n"
        for c in AUTO_COINS: msg += f" ├ <b>{c['name']}</b>\n └ CA: <code>{c['ca']}</code>\n"
        msg += f"\n👤 <b>THỦ CÔNG ({len(MANUAL_COINS)})</b>\n"
        for c in MANUAL_COINS: msg += f" ├ <b>{c['name']}</b>\n └ CA: <code>{c['ca']}</code>\n"
        send_telegram_alert(msg)
    elif cmd == 'freq_coin':
        all_coins = AUTO_COINS + MANUAL_COINS
        if not all_coins:
            send_telegram_alert("⚠️ Danh sách hiện tại đang trống!")
            return
        kb = {"inline_keyboard": []}
        for c in all_coins: kb["inline_keyboard"].append([{"text": f"⚙️ {c['name']} ({c['ca'][:6]}...)", "callback_data": f"setfreq_{c['ca']}"}])
        user_state = {'step': 'WAITING_FREQ_CHOICE', 'last_time': time.time()}
        send_telegram_alert("👇 Chọn coin bạn muốn thay đổi Tần suất quét:", reply_markup=kb)
    elif cmd == 'del':
        all_coins = AUTO_COINS + MANUAL_COINS
        if not all_coins:
            send_telegram_alert("⚠️ Danh sách trống, không có gì để xóa!")
            return
        kb = {"inline_keyboard": []}
        for c in all_coins: kb["inline_keyboard"].append([{"text": f"🗑 {c['name']} ({c['ca'][:6]}...)", "callback_data": f"delcoin_{c['ca']}"}])
        user_state = {'step': 'WAITING_DEL_CHOICE', 'last_time': time.time()}
        send_telegram_alert("👇 Chọn coin bạn muốn <b>XÓA</b> khỏi hệ thống:", reply_markup=kb)
    elif cmd == 'toggle_new':
        CONFIG["NOTIFY_NEW_COIN"] = not CONFIG.get("NOTIFY_NEW_COIN", True)
        if CONFIG["NOTIFY_NEW_COIN"]: send_telegram_alert("🔔 <b>ĐÃ BẬT:</b> Bot sẽ gửi thông báo lên Telegram mỗi khi có Coin mới.\n👉 Bấm /menu để tải lại bảng điều khiển.")
        else: send_telegram_alert("🔕 <b>ĐÃ TẮT (Silent Mode):</b> Bot âm thầm quét và đưa Coin mới vào Rổ AUTO.\n👉 Bấm /menu để tải lại bảng điều khiển.")
    elif cmd == 'set_time':
        kb = {"inline_keyboard": [[{"text": "🤖 Cho rổ Auto", "callback_data": "set_time_auto"}, {"text": "👤 Cho Thủ Công", "callback_data": "set_time_manual"}]]}
        send_telegram_alert("🕒 Cài Khung giờ Lịch sử cho rổ nào?", reply_markup=kb)
    elif cmd == 'set_buy':
        kb = {"inline_keyboard": [[{"text": "🤖 Cho rổ Auto", "callback_data": "set_buy_auto"}, {"text": "👤 Cho Thủ Công", "callback_data": "set_buy_manual"}]]}
        send_telegram_alert("🛒 Cài Số lệnh mua cho rổ nào?", reply_markup=kb)
    elif cmd == 'add':
        user_state = {'step': 'WAITING_CA', 'last_time': time.time()}
        send_telegram_alert("📝 Nhập CA BSC muốn thêm:")
    elif cmd == 'set_max_auto':
        user_state = {'step': 'WAITING_MAX_AUTO', 'last_time': time.time()}
        send_telegram_alert("📦 Rổ Auto tối đa chứa bao nhiêu coin? (VD: 10)")
    elif cmd == 'set_bnb':
        user_state = {'step': 'WAITING_BNB_VAL', 'last_time': time.time()}
        send_telegram_alert(f"🐋 <b>TAY TO (Mức: {CONFIG['MIN_BNB_BUY']} BNB)</b>\n👉 Nhập số BNB tối thiểu để tính 1 lệnh gom:")
    elif cmd == 'keys':
        send_telegram_alert(f"🔑 <b>KHO API KEYS ({len(API_KEYS)})</b>\n")
    elif cmd == 'cancel':
        user_state.clear()
        send_telegram_alert("🚫 Đã hủy thao tác.")

def process_update(item):
    global AUTO_COINS, MANUAL_COINS, CONFIG, user_state, API_KEYS, RAW_API_KEYS
    try:
        if user_state and time.time() - user_state.get('last_time', time.time()) > 300:
            user_state.clear()
            send_telegram_alert("⏳ Quá 5 phút không phản hồi. Lệnh tự động hủy.")

        if "callback_query" in item:
            data = item["callback_query"]["data"]
            if data.startswith("menu_"): execute_command(data.replace("menu_", "")); return
            
            if data.startswith("delcoin_"):
                if not user_state or user_state.get('step') not in ['WAITING_DEL_CHOICE', 'WAITING_DEL_CONFIRM']: return
                ca_target = data.split("_")[1]
                coin_name = next((c['name'] for c in AUTO_COINS + MANUAL_COINS if c['ca'] == ca_target), "Unknown")
                user_state = {'step': 'WAITING_DEL_CONFIRM', 'last_time': time.time(), 'target_ca': ca_target}
                kb = {"inline_keyboard": [[{"text": "✅ Xóa", "callback_data": f"confirmdel_{ca_target}"}, {"text": "❌ Tôi nhầm", "callback_data": "menu_del"}]]}
                send_telegram_alert(f"❓ Xóa coin <b>{coin_name}</b> (<code>{ca_target}</code>)?", reply_markup=kb)
                return

            if data.startswith("confirmdel_"):
                if not user_state or user_state.get('step') != 'WAITING_DEL_CONFIRM': return
                ca_target = data.split("_")[1]
                MANUAL_COINS[:] = [c for c in MANUAL_COINS if c['ca'] != ca_target]
                AUTO_COINS[:] = [c for c in AUTO_COINS if c['ca'] != ca_target]
                send_telegram_alert("🗑 Đã xóa coin thành công!"); user_state.clear(); return

            if data.startswith("setfreq_"):
                if not user_state or user_state.get('step') != 'WAITING_FREQ_CHOICE': return
                ca_target = data.split("_")[1]
                user_state = {'step': 'WAITING_FREQ_MIN', 'target_ca': ca_target, 'last_time': time.time()}
                send_telegram_alert(f"⏱ Cấu hình: <code>{ca_target}</code>\n👉 <b>BAO NHIÊU PHÚT</b> bot quét 1 lần?")
                return

            if data.startswith("dead_yes_"):
                ca_to_del = data.split("_")[2]
                AUTO_COINS[:] = [c for c in AUTO_COINS if c['ca'].lower() != ca_to_del.lower()]
                send_telegram_alert(f"✅ Đã xóa coin khỏi hệ thống."); return
            if data.startswith("dead_no_"):
                ca_to_keep = data.split("_")[2]
                for c in AUTO_COINS:
                    if c['ca'].lower() == ca_to_keep.lower():
                        c['last_alert_at'] = time.time(); c['prompt_sent'] = False
                        send_telegram_alert(f"✅ Đã gia hạn theo dõi <b>{c['name']}</b> 24h."); break
                return
            if data in ["set_time_auto", "set_time_manual"]:
                lst = "AUTO_SCAN" if data == "set_time_auto" else "THỦ CÔNG"
                user_state = {'step': 'WAITING_TIME_VAL_' + data.split('_')[2].upper(), 'last_time': time.time()}
                send_telegram_alert(f"🕒 Cài Khung giờ cho <b>{lst}</b>\nNhập số giờ (VD: 2):"); return
            if data in ["set_buy_auto", "set_buy_manual"]:
                lst = "AUTO_SCAN" if data == "set_buy_auto" else "THỦ CÔNG"
                user_state = {'step': 'WAITING_BUY_VAL_' + data.split('_')[2].upper(), 'last_time': time.time()}
                send_telegram_alert(f"🛒 Cài Số lệnh gom cho <b>{lst}</b>\nNhập số lệnh (VD: 2):"); return

        if "message" in item:
            text = item["message"].get("text", "").strip()
            if not text: return
            if text in ['/menu', '/start']: send_main_menu()
            elif user_state:
                if text == '/cancel': execute_command('cancel'); return
                step = user_state.get('step')
                
                if step == 'WAITING_FREQ_MIN':
                    try:
                        user_state['minutes'] = float(text)
                        user_state['step'] = 'WAITING_FREQ_TX'
                        user_state['last_time'] = time.time()
                        send_telegram_alert(f"👉 Đã nhận <b>{text} phút/lần</b>.\nTiếp theo, mỗi lần quét lấy tối đa <b>BAO NHIÊU GIAO DỊCH</b> (Khởi tạo)?")
                    except: send_telegram_alert("❌ Vui lòng nhập số (VD: 5).")
                
                elif step == 'WAITING_FREQ_TX':
                    try:
                        tx_limit = int(text)
                        target_ca = user_state['target_ca']
                        mins = user_state['minutes']
                        for lst in [AUTO_COINS, MANUAL_COINS]:
                            for c in lst:
                                if c['ca'] == target_ca:
                                    c['scan_interval'] = mins; c['tx_limit'] = tx_limit
                                    send_telegram_alert(f"✅ Đã lưu cấu hình cho <b>{c['name']}</b>: {mins} phút / {tx_limit} tx!")
                        user_state.clear()
                    except: send_telegram_alert("❌ Vui lòng nhập số nguyên (VD: 500).")

                elif step == 'WAITING_CA':
                    user_state['ca'] = text
                    user_state['step'] = 'WAITING_LP'
                    user_state['last_time'] = time.time()
                    send_telegram_alert("✅ Nhập tiếp địa chỉ LP:")
                
                elif step == 'WAITING_LP':
                    ca = user_state['ca']
                    lp = text
                    coin_name = f"BSC_{ca[:4]}" 
                    try:
                        res = requests.get(f"https://deep-index.moralis.io/api/v2.2/erc20/metadata?chain=bsc&addresses={ca}", headers=get_current_headers(), timeout=5)
                        if res.status_code == 200 and len(res.json()) > 0 and res.json()[0].get('symbol'):
                            coin_name = res.json()[0].get('symbol')
                    except: pass
                    # V21: Cấp Sổ tay (Cache) ngay khi add
                    MANUAL_COINS.append({"name": coin_name, "ca": ca, "lp": lp, "scan_interval": 5, "tx_limit": 100, "last_scan_time": 0, "tx_cache": [], "last_fetch_timestamp": ""})
                    send_telegram_alert(f"🎉 Đã thêm <b>{coin_name}</b>!\n(Mặc định: 5 phút / 100 tx).")
                    user_state.clear()
                
                elif step == 'WAITING_BNB_VAL':
                    try: CONFIG['MIN_BNB_BUY'] = float(text); send_telegram_alert(f"✅ Đã cài Tay to: <b>{text} BNB</b>."); user_state.clear()
                    except: send_telegram_alert("❌ Nhập số hợp lệ.")
                elif step == 'WAITING_MAX_AUTO':
                    try: CONFIG['MAX_AUTO_COINS'] = int(text); send_telegram_alert(f"✅ Rổ Auto tối đa: <b>{text} coin</b>."); user_state.clear()
                    except: send_telegram_alert("❌ Nhập số nguyên.")
                elif step == 'WAITING_ADD_KEY':
                    if text not in RAW_API_KEYS: RAW_API_KEYS.append(text); API_KEYS.append(text)
                    send_telegram_alert(f"✅ Thêm Key thành công. Tổng: {len(API_KEYS)}"); user_state.clear()
                elif step.startswith('WAITING_TIME_VAL_'):
                    try: CONFIG[f"{step.split('_')[3]}_TIME_FRAME"] = int(text); send_telegram_alert(f"✅ Đã lưu khung giờ: {text}h."); user_state.clear()
                    except: send_telegram_alert("❌ Nhập số hợp lệ.")
                elif step.startswith('WAITING_BUY_VAL_'):
                    try: CONFIG[f"{step.split('_')[3]}_MIN_BUYS"] = int(text); send_telegram_alert(f"✅ Đã lưu số lệnh gom: {text}."); user_state.clear()
                    except: send_telegram_alert("❌ Nhập số hợp lệ.")
    except: pass

def listen_telegram_commands():
    setup_telegram_commands()
    last_update_id = 0
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    while True:
        try:
            res = requests.get(url, params={"offset": last_update_id + 1, "timeout": 10}).json()
            for item in res.get("result", []):
                last_update_id = item["update_id"]
                process_update(item) 
        except: pass
        time.sleep(2)

# --- LÕI ĐIỀU TRA ON-CHAIN V21 (DELTA-CACHE) ---
def run_bot():
    try:
        print("--- LUONG QUET V21 DA KHOI DONG (Enterprise Delta-Cache) ---", flush=True)
        send_telegram_alert("🚀 <b>Bot Săn Meme V21 đã sẵn sàng, gõ /menu để bắt đầu</b>")
        alerted_coins_state = {} 
        
        while True:
            now = time.time()
            for coin in list(AUTO_COINS):
                if coin.get('prompt_sent'):
                    if now - coin.get('prompt_time', 0) > 300:
                        coin['prompt_sent'] = False; coin['last_alert_at'] = now
                elif now - coin.get('last_alert_at', now) > 86400:
                    coin['prompt_sent'] = True; coin['prompt_time'] = now
                    kb = {"inline_keyboard": [[{"text": "✅ Xóa", "callback_data": f"dead_yes_{coin['ca']}"}, {"text": "❌ Giữ 24h", "callback_data": f"dead_no_{coin['ca']}"}]]}
                    send_telegram_alert(f"🗑 <b>DỌN RÁC:</b> Đồng <b>{coin['name']}</b> héo sau 24h, xóa không?", reply_markup=kb)

            for list_type, coin_list in [("AUTO", AUTO_COINS), ("MANUAL", MANUAL_COINS)]:
                time_frame = CONFIG[f"{list_type}_TIME_FRAME"]
                min_buys = CONFIG[f"{list_type}_MIN_BUYS"]
                min_bnb = CONFIG['MIN_BNB_BUY']
                
                for coin in list(coin_list):
                    try:
                        scan_interval_sec = coin.get('scan_interval', 5) * 60
                        last_scan = coin.get('last_scan_time', 0)
                        if now - last_scan < scan_interval_sec: continue 
                        coin['last_scan_time'] = time.time()
                        
                        ca, lp = coin["ca"].lower(), coin["lp"].lower()
                        alert_key = f"{ca}_{time_frame}_{list_type}"

                        # Đảm bảo có Sổ tay (Cache)
                        if 'tx_cache' not in coin: coin['tx_cache'] = []
                        if 'last_fetch_timestamp' not in coin: coin['last_fetch_timestamp'] = ""

                        print(f"\n--- Dang soi coin: {coin['name']} (CA: {ca[:6]}...) ---", flush=True)

                        token_price_bnb, token_decimals = 0, 18
                        price_res = requests.get(f"https://deep-index.moralis.io/api/v2.2/erc20/{ca}/price?chain=bsc", headers=get_current_headers(), timeout=10)
                        if price_res.status_code == 200:
                            p_data = price_res.json()
                            token_decimals = int(p_data.get('tokenDecimals', 18))
                            token_price_bnb = float(p_data.get("nativePrice", {}).get("value", "0")) / (10**18)
                            print(f"   => Gia quy doi: {token_price_bnb:.8f} BNB", flush=True)

                        # 🔥 VŨ KHÍ 1: TẢI CHÊNH LỆCH VÀ PHÂN TRANG (DELTA FETCH) 🔥
                        new_txs = []
                        cursor = ""
                        max_pages = max(1, (coin.get('tx_limit', 100) + 99) // 100) if not coin['last_fetch_timestamp'] else 20
                        hit_old_data = False

                        for scan_page in range(max_pages): 
                            page_url = f"https://deep-index.moralis.io/api/v2.2/erc20/{ca}/transfers?chain=bsc&limit=100" + (f"&cursor={cursor}" if cursor else "")
                            response = requests.get(page_url, headers=get_current_headers(), timeout=10)
                            if response.status_code == 200:
                                page_data = response.json()
                                results = page_data.get('result', [])
                                
                                for tx in results:
                                    tx_time = tx.get('block_timestamp', '')
                                    # Nếu đụng mốc thời gian cũ -> Ngừng tải, tiết kiệm API
                                    if coin['last_fetch_timestamp'] and tx_time <= coin['last_fetch_timestamp']:
                                        hit_old_data = True
                                        break
                                    new_txs.append(tx)
                                
                                cursor = page_data.get('cursor')
                                if not cursor or hit_old_data: break 
                            else:
                                print(f"   ⚠️ LOI QUET P{scan_page+1}: HTTP {response.status_code}", flush=True)
                                break
                                
                        if new_txs:
                            max_ts = max([tx.get('block_timestamp', '') for tx in new_txs])
                            if max_ts > coin['last_fetch_timestamp']:
                                coin['last_fetch_timestamp'] = max_ts
                            coin['tx_cache'].extend(new_txs)
                            print(f"   => Keo Delta: {len(new_txs)} lenh moi.", flush=True)
                        else:
                            print(f"   => Khong co lenh moi. Phat hien qua Local Cache.", flush=True)

                        # 🔥 VŨ KHÍ 2: CÁI KÉO THỜI GIAN (TIME-BASED PRUNING) 🔥
                        time_ago = datetime.now(timezone.utc) - timedelta(hours=time_frame)
                        valid_cache = []
                        for tx in coin['tx_cache']:
                            tx_ts_str = tx.get('block_timestamp', '')[:19]
                            try:
                                tx_dt = datetime.strptime(tx_ts_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
                                if tx_dt >= time_ago:
                                    valid_cache.append(tx)
                            except: pass
                        
                        coin['tx_cache'] = valid_cache
                        print(f"   => So tay phinh len: {len(valid_cache)} lenh.", flush=True)
                        
                        # Soi Cũ -> Mới
                        sorted_txs = sorted(valid_cache, key=lambda x: x.get('block_timestamp', ''))
                        
                        suspect_wallets, terminal_holders, valid_buy_chains = {}, set(), 0
                        router_temporary_sources = {} 

                        for tx in sorted_txs:
                            sender, receiver, value_raw = tx.get('from_address', '').lower(), tx.get('to_address', '').lower(), int(tx.get('value', '0'))
                            tx_hash, tx_timestamp_str = tx.get('transaction_hash', ''), tx.get('block_timestamp', '')
                            if value_raw == 0 or not tx_timestamp_str: continue
                            
                            tx_timestamp = datetime.strptime(tx_timestamp_str[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).timestamp()
                            tx_bnb_value = (value_raw / (10**token_decimals)) * token_price_bnb

                            # Mắt Thần V14
                            if sender == lp:
                                if token_price_bnb > 0 and tx_bnb_value >= min_bnb:
                                    if receiver in KNOWN_AGGREGATORS:
                                        router_temporary_sources[receiver] = {"amount_raw": value_raw, "timestamp": tx_timestamp, "hash": tx_hash}
                                    else:
                                        suspect_wallets[receiver] = 0; terminal_holders.add(receiver); valid_buy_chains += 1
                            elif sender in KNOWN_AGGREGATORS and sender in router_temporary_sources:
                                source_info = router_temporary_sources[sender]
                                if tx_timestamp == source_info["timestamp"] and value_raw <= source_info["amount_raw"]:
                                    if receiver not in suspect_wallets: 
                                        suspect_wallets[receiver] = 0; terminal_holders.add(receiver); valid_buy_chains += 1
                                        del router_temporary_sources[sender]
                            elif sender in suspect_wallets:
                                current_depth = suspect_wallets[sender]
                                if receiver == lp:
                                    if sender in terminal_holders: valid_buy_chains -= 1; terminal_holders.remove(sender)
                                    del suspect_wallets[sender] 
                                else:
                                    if current_depth < 10:
                                        suspect_wallets[receiver] = current_depth + 1; terminal_holders.add(receiver)
                                        if sender in terminal_holders: terminal_holders.remove(sender)
                        
                        router_temporary_sources.clear()
                        last_reported_chains = alerted_coins_state.get(alert_key, 0)

                        if valid_buy_chains >= min_buys and valid_buy_chains > last_reported_chains:
                            alerted_coins_state[alert_key] = valid_buy_chains

                            holders_details = []
                            for w in list(terminal_holders)[:3]:
                                if w not in suspect_wallets: continue
                                depth = suspect_wallets[w]
                                lifetime_buys_count = 0
                                buy_amounts_bnb = []
                                for t in sorted_txs:
                                    s_addr, r_addr = t.get('from_address', '').lower(), t.get('to_address', '').lower()
                                    v_raw = int(t.get('value', '0'))
                                    if v_raw == 0: continue
                                    if r_addr == w and (s_addr == lp or s_addr in KNOWN_AGGREGATORS):
                                        v_bnb = (v_raw / (10**token_decimals)) * token_price_bnb
                                        if v_bnb > 0:
                                            lifetime_buys_count += 1; buy_amounts_bnb.append(f"{v_bnb:.2f}")
                                buys_str = ", ".join(buy_amounts_bnb) if buy_amounts_bnb else "0"
                                
                                bnb_balance, token_hold_balance = 0, 0
                                try:
                                    bal_res = requests.get(f"https://deep-index.moralis.io/api/v2.2/{w}/balance?chain=bsc", headers=get_current_headers(), timeout=5)
                                    if bal_res.status_code == 200: bnb_balance = int(bal_res.json().get('balance', '0')) / (10**18)
                                    tk_res = requests.get(f"https://deep-index.moralis.io/api/v2.2/{w}/erc20?chain=bsc&token_addresses={ca}", headers=get_current_headers(), timeout=5)
                                    if tk_res.status_code == 200 and tk_res.json() and len(tk_res.json()) > 0:
                                        token_hold_balance = float(tk_res.json()[0].get('balance', '0')) / (10**token_decimals)
                                except: pass
                                
                                holders_details.append(
                                    f"💳 <code>{w}</code> (Đời F{depth})\n   ├ Dư (Gas): <b>{bnb_balance:.4f} BNB</b>\n   ├ Đang Hold: <b>{token_hold_balance:,.2f} {coin['name']}</b>\n   └ Đã gom: <b>{lifetime_buys_count} lệnh</b> [{buys_str} BNB]"
                                )
                            
                            holders_str = "\n".join(holders_details)
                            sec_info = format_bsc_security(ca)
                            
                            msg = (f"💎 <b>CÁ MẬP V21 GOM HÀNG ({list_type})</b>\n\n"
                                   f"🪙 <b>Coin:</b> {coin['name']} | CA: <code>{ca}</code>\n"
                                   f"🎯 <b>Cập nhật:</b> Lên tới {valid_buy_chains} chuỗi gom >= {min_bnb} BNB!\n"
                                   f"🧠 <i>(Phân tích từ {len(sorted_txs)} lệnh trong Sổ tay Cache)</i>\n"
                                   f"🕵️‍♂️ <b>Hồ sơ Ví cuối (Skipped Routers):</b>\n{holders_str}\n\n"
                                   f"✅ Bot xác nhận: Tuyệt đối chưa dump hàng!\n{sec_info}")
                            send_telegram_alert(msg)

                        elif valid_buy_chains < last_reported_chains:
                            alerted_coins_state[alert_key] = valid_buy_chains
                            
                    except Exception as e:
                        print(f"   ⚠️ LOI QUET COIN: {e}", flush=True)
                    time.sleep(2) 
            time.sleep(15) 

    except Exception as e:
        print(f"CRITICAL THREAD CRASH: {e}")
        traceback.print_exc()

Thread(target=listen_telegram_commands, daemon=True).start()
Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    run_server()
