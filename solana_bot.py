import requests
import time
import os
import json
from datetime import datetime, timedelta, timezone 
from collections import defaultdict
from flask import Flask
from threading import Thread

# --- PHẦN 1: TẠO WEB SERVER (Giữ cho Render sống) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Solana Sniper Bot (Tích hợp DexScreener) đang hoạt động!"

def run_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

# --- PHẦN 2: THÔNG SỐ CỐ ĐỊNH ---
API_KEYS = [
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImU0Y2QxMTFlLTE3YzYtNDU2My1iOGM5LTFjZWZkMjNmMjJhYiIsIm9yZ0lkIjoiNTA3MDc2IiwidXNlcklkIjoiNTIxNzQ5IiwidHlwZUlkIjoiZDhjZmE3NTEtNTAyMC00MTZkLWJkOGItZWJlMWM3Y2Q0NGJiIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQ0ODczODMsImV4cCI6NDkzMDI0NzM4M30.EdCGoN5pzZEuiDmvbEbHvLLGtQU2D2O_gSHX0t2JKug',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjczZTU1ZWQxLTNjYzQtNGM3ZC05MTVmLThiMDc5MTQ3YjAyYiIsIm9yZ0lkIjoiNTA3MDc4IiwidXNlcklkIjoiNTIxNzUxIiwidHlwZUlkIjoiODFkY2ZiNTgtNTAxNC00NjRkLTg3ZDYtMTM0ZjQzZTVkZmRkIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQ0ODg3NTksImV4cCI6NDkzMDI0ODc1OX0.6hBFIZcOM1rVa6sUPNUZEUUEfSKanrurzqKQPbffiSI',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImUzYzYyNzRhLWMxZGItNDhlYS1hMjkxLWMzZGQ0YTU0YmM0NiIsIm9yZ0lkIjoiNTA3MDI0IiwidXNlcklkIjoiNTIxNjk2IiwidHlwZUlkIjoiMGExM2FmMGEtNDU2Yi00YTgwLWE0ZjMtZjNlZTc4N2Q0N2M1IiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQ0NTYyMzEsImV4cCI6NDkzMDIxNjIzMX0.gCOXCBjaTjWSo5XskcX4jdvo5fZDptZ-VsI6NuQZwvY'
]

TELEGRAM_BOT_TOKEN = '8202619989:AAExXHIbOHIA1VNszdv9j5mUlT6VfhqxfrA'
TELEGRAM_CHAT_ID = '1976782751'

CONFIG = {
    "MANUAL_TIME_FRAME": 6,  
    "MANUAL_MIN_BUYS": 2,    
    "AUTO_TIME_FRAME": 2,    
    "AUTO_MIN_BUYS": 2,      
    "MAX_AUTO_COINS": 5,     
    "AUTO_SCAN": True,
    "LANGUAGE": "vi"
}

MANUAL_COINS = []
AUTO_COINS = [] 
SMART_WALLETS = [] 
user_state = {} 
current_api_index = 0 

def get_current_headers():
    global current_api_index
    if not API_KEYS: return {"accept": "application/json"}
    if current_api_index >= len(API_KEYS): current_api_index = 0
    return {"accept": "application/json", "X-API-Key": API_KEYS[current_api_index]}

def send_telegram_alert(message, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True}
    if reply_markup: data["reply_markup"] = json.dumps(reply_markup)
    try: requests.post(url, data=data, timeout=10)
    except Exception: pass

TEXTS = {
    "vi": {
        "lang_prompt": "🌐 <b>Chọn ngôn ngữ / Select Language:</b>",
        "lang_changed": "✅ Đã chuyển ngôn ngữ sang Tiếng Việt!"
    },
    "en": {
        "lang_prompt": "🌐 <b>Select Language / Chọn ngôn ngữ:</b>",
        "lang_changed": "✅ Language successfully changed to English!"
    }
}

def t(key, *args):
    lang = CONFIG["LANGUAGE"]
    text = TEXTS[lang].get(key, key)
    if args: return text.format(*args)
    return text

# --- MENU NÚT BẤM CHÍNH ---
def send_main_menu():
    keyboard = {
        "inline_keyboard": [
            [{"text": "📊 Xem Cấu Hình", "callback_data": "menu_status"}, {"text": "📋 List Đang Quét", "callback_data": "menu_list"}],
            [{"text": "⏱ Đổi Khung Giờ", "callback_data": "menu_set_time"}, {"text": "🛒 Đổi Lệnh Mua", "callback_data": "menu_set_buy"}],
            [{"text": "➕ Thêm Coin SOL", "callback_data": "menu_add"}, {"text": "🗑 Xóa Coin", "callback_data": "menu_del"}],
            [{"text": "🐋 Ví Smart Money", "callback_data": "menu_add_wallet"}, {"text": "📦 Giới Hạn Auto", "callback_data": "menu_set_max_auto"}],
            [{"text": "🤖 Bật/Tắt Quét DexScreener", "callback_data": "menu_auto_scan"}],
            [{"text": "🔑 Kho API Keys", "callback_data": "menu_keys"}, {"text": "➕ Nạp API Key", "callback_data": "menu_add_key"}],
            [{"text": "🌐 Đổi Ngôn Ngữ", "callback_data": "menu_language"}, {"text": "🚫 Hủy Lệnh", "callback_data": "menu_cancel"}]
        ]
    }
    send_telegram_alert("🎛 <b>BẢNG ĐIỀU KHIỂN SOLANA SNIPER</b>\n\n👉 Vui lòng chọn chức năng bên dưới:", reply_markup=keyboard)

# --- CÁC HÀM CÔNG CỤ CHO SOLANA ---
def get_solana_token_price(ca):
    try:
        url = f"https://solana-gateway.moralis.io/token/mainnet/{ca}/price"
        res = requests.get(url, headers=get_current_headers(), timeout=10)
        if res.status_code == 200:
            price = res.json().get("usdPrice", 0)
            return f"${price:.6f}" if price < 1 else f"${price:.2f}"
    except Exception: pass
    return "N/A"

def check_solana_security(ca):
    try:
        url = f"https://api.gopluslabs.io/api/v1/solana/token_security?contract_addresses={ca}"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            result = res.json().get("result", {}).get(ca.lower(), {})
            if result:
                mintable = result.get("mintable", "0") == "1"
                freezable = result.get("freezable", "0") == "1"
                return {"mintable": mintable, "freezable": freezable}
    except Exception: pass
    return None

def format_solana_security(ca):
    sec = check_solana_security(ca)
    if not sec: return "🛡 <b>Bảo mật:</b> ⚠️ Không thể quét contract.\n"
    mint_str = "🔴 CHƯA KHÓA (Nguy hiểm)" if sec['mintable'] else "🟢 Đã khóa (An toàn)"
    freeze_str = "🔴 CHƯA KHÓA (Nguy hiểm)" if sec['freezable'] else "🟢 Đã khóa (An toàn)"
    text = "🛡 <b>Bảo mật Contract (Solana):</b>\n"
    text += f" ├ Quyền in coin (Mint): {mint_str}\n"
    text += f" └ Quyền đóng băng (Freeze): {freeze_str}\n"
    return text

def execute_command(cmd):
    global CONFIG, user_state
    if cmd == 'status':
        auto_state = "🟢 BẬT" if CONFIG['AUTO_SCAN'] else "🔴 TẮT"
        msg = (
            f"⚙️ <b>CẤU HÌNH HIỆN TẠI (HỆ SOL)</b>\n"
            f"🤖 AUTO: Quét <b>{CONFIG['AUTO_TIME_FRAME']}h</b> | Gom >= <b>{CONFIG['AUTO_MIN_BUYS']}</b>\n"
            f"👤 THỦ CÔNG: Quét <b>{CONFIG['MANUAL_TIME_FRAME']}h</b> | Gom >= <b>{CONFIG['MANUAL_MIN_BUYS']}</b>\n"
            f"🔑 API: <b>{current_api_index + 1}/{len(API_KEYS)}</b>\n"
            f"🔄 Radar DexScreener: <b>{auto_state}</b>\n"
            f"👉 Bấm List Đang Quét để xem chi tiết."
        )
        send_telegram_alert(msg)
    elif cmd == 'list':
        msg = f"📋 <b>DANH SÁCH SOLANA ĐANG THEO DÕI</b>\n\n"
        msg += f"🤖 <b>TỰ ĐỘNG (AUTO) - {len(AUTO_COINS)}/{CONFIG['MAX_AUTO_COINS']}</b>\n"
        if not AUTO_COINS: msg += " └ (Trống)\n"
        for c in AUTO_COINS: msg += f" ├ {c['name']} - <code>{c['ca'][:6]}..{c['ca'][-4:]}</code>\n"
        msg += f"\n👤 <b>THỦ CÔNG (MANUAL) - {len(MANUAL_COINS)}</b>\n"
        if not MANUAL_COINS: msg += " └ (Trống)\n"
        for c in MANUAL_COINS: msg += f" ├ {c['name']} - <code>{c['ca'][:6]}..{c['ca'][-4:]}</code>\n"
        if SMART_WALLETS:
            msg += f"\n🐋 <b>VÍ SMART MONEY - {len(SMART_WALLETS)}</b>\n"
            for w in SMART_WALLETS: msg += f" ├ {w['name']} - <code>{w['address'][:6]}..{w['address'][-4:]}</code>\n"
        send_telegram_alert(msg)
    elif cmd == 'auto_scan':
        CONFIG['AUTO_SCAN'] = not CONFIG.get('AUTO_SCAN', True)
        if CONFIG['AUTO_SCAN']: send_telegram_alert("🟢 <b>Quét DexScreener Tự Động: ĐÃ BẬT</b>")
        else: send_telegram_alert("🔴 <b>Quét DexScreener Tự Động: ĐÃ TẮT</b>")
    elif cmd == 'set_time':
        keyboard = {"inline_keyboard": [[{"text": "🤖 Đổi cho Auto", "callback_data": "set_time_auto"}, {"text": "👤 Đổi cho Thủ Công", "callback_data": "set_time_manual"}]]}
        send_telegram_alert("🕒 Bạn muốn cài Khung giờ cho rổ nào?", reply_markup=keyboard)
    elif cmd == 'set_buy':
        keyboard = {"inline_keyboard": [[{"text": "🤖 Đổi cho Auto", "callback_data": "set_buy_auto"}, {"text": "👤 Đổi cho Thủ Công", "callback_data": "set_buy_manual"}]]}
        send_telegram_alert("🛒 Bạn muốn cài Số lệnh mua cho rổ nào?", reply_markup=keyboard)
    elif cmd == 'set_max_auto':
        user_state = {'step': 'WAITING_MAX_AUTO', 'last_time': time.time()}
        send_telegram_alert("🤖 Bạn muốn rổ Auto chứa được TỐI ĐA bao nhiêu coin? (Mặc định: 5)")
    elif cmd == 'add':
        user_state = {'step': 'WAITING_CA', 'last_time': time.time()}
        user_state['chain'] = 'solana'
        send_telegram_alert("📝 <b>THÊM COIN HỆ SOLANA</b>\n\n👉 Hãy dán Contract Address (CA) của đồng coin vào đây:")
    elif cmd == 'del':
        user_state = {'step': 'WAITING_DEL_COIN', 'last_time': time.time()}
        send_telegram_alert("🗑 Nhập CA hoặc Tên coin muốn xóa:")
    elif cmd == 'add_wallet':
        user_state = {'step': 'WAITING_SMART_ADDRESS', 'last_time': time.time()}
        user_state['chain'] = 'solana'
        send_telegram_alert("🐋 <b>THEO DÕI CÁ MẬP SOLANA</b>\n\n👉 Dán địa chỉ Ví Cá Mập hệ Sol vào đây:")
    elif cmd == 'add_key':
        user_state = {'step': 'WAITING_ADD_KEY', 'last_time': time.time()}
        send_telegram_alert("🔑 Nhập API Key mới để nạp vào hệ thống:")
    elif cmd == 'keys':
        msg = f"🔑 <b>KHO CHỨA API KEYS ({len(API_KEYS)} Keys)</b>\n\n"
        for i, k in enumerate(API_KEYS):
            is_active = "(Đang dùng 🟢)" if i == current_api_index else ""
            msg += f"🔹 Key {i+1}: <code>{k[:10]}...{k[-10:]}</code> {is_active}\n"
        send_telegram_alert(msg)
    elif cmd == 'language':
        keyboard = {"inline_keyboard": [[{"text": "🇻🇳 Tiếng Việt", "callback_data": "lang_vi"}, {"text": "🇬🇧 English", "callback_data": "lang_en"}]]}
        send_telegram_alert(t("lang_prompt"), reply_markup=keyboard)
    elif cmd == 'cancel':
        user_state.clear()
        send_telegram_alert("🚫 Đã hủy tác vụ đang làm dở.")

# --- LẮNG NGHE LỆNH TỪ TELEGRAM ---
def listen_telegram_commands():
    global user_state
    last_update_id = 0
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    
    while True:
        try:
            if user_state and (time.time() - user_state.get('last_time', 0) > 300):
                send_telegram_alert("⏳ <b>Quá 5 phút không phản hồi!</b> Hủy tác vụ.")
                user_state.clear()

            res = requests.get(url, params={"offset": last_update_id + 1, "timeout": 10}, timeout=15).json()
            for item in res.get("result", []):
                last_update_id = item["update_id"]
                process_update(item) 
        except Exception: pass
        time.sleep(2)

def process_update(item):
    global AUTO_COINS, MANUAL_COINS, CONFIG, user_state, API_KEYS, SMART_WALLETS
    try:
        if "callback_query" in item:
            callback = item["callback_query"]
            chat_id = str(callback["message"]["chat"]["id"])
            data = callback["data"]
            if chat_id != TELEGRAM_CHAT_ID: return

            if data in ["lang_vi", "lang_en"]:
                CONFIG["LANGUAGE"] = data.split("_")[1]
                send_telegram_alert(t("lang_changed"))
                return

            if data.startswith("menu_"):
                cmd = data.replace("menu_", "")
                execute_command(cmd)
                return

            if data.startswith("dead_yes_"):
                ca_to_del = data.split("_")[2]
                AUTO_COINS[:] = [c for c in AUTO_COINS if c['ca'].lower() != ca_to_del.lower()]
                send_telegram_alert(f"✅ Đã xóa coin Solana <code>{ca_to_del[:6]}...</code> khỏi hệ thống Auto.")
                return
            if data.startswith("dead_no_"):
                ca_to_keep = data.split("_")[2]
                for c in AUTO_COINS:
                    if c['ca'].lower() == ca_to_keep.lower():
                        c['last_alert_at'] = time.time()
                        c['prompt_sent'] = False
                        send_telegram_alert(f"✅ Đã gia hạn theo dõi <b>{c['name']}</b> thêm 24h nữa.")
                        break
                return

            if data in ["set_time_auto", "set_time_manual"]:
                list_type = "AUTO_SCAN" if data == "set_time_auto" else "THỦ CÔNG"
                user_state['step'] = 'WAITING_TIME_VAL_' + data.split('_')[2].upper() 
                user_state['last_time'] = time.time()
                send_telegram_alert(f"👉 Cấu hình Khung giờ cho <b>{list_type}</b>\nNhập số giờ (VD: 2, 6):")
                return
            if data in ["set_buy_auto", "set_buy_manual"]:
                list_type = "AUTO_SCAN" if data == "set_buy_auto" else "THỦ CÔNG"
                user_state['step'] = 'WAITING_BUY_VAL_' + data.split('_')[2].upper()
                user_state['last_time'] = time.time()
                send_telegram_alert(f"👉 Cấu hình Số lệnh mua cho <b>{list_type}</b>\nNhập số lệnh (VD: 2, 5):")
                return
            return

        if "message" in item:
            chat_id = str(item["message"]["chat"]["id"])
            text = item["message"].get("text", "").strip()
            if chat_id != TELEGRAM_CHAT_ID or not text: return

            if text in ['/menu', '/start', '/help']:
                send_main_menu()
                return

            if user_state:
                if text == '/cancel':
                    execute_command('cancel')
                    return
                user_state['last_time'] = time.time()
                
                if user_state['step'] == 'WAITING_CA':
                    user_state['ca'] = text
                    user_state['step'] = 'WAITING_LP'
                    send_telegram_alert("✅ Đã nhận CA Solana.\n📝 Tiếp theo, hãy nhập <b>địa chỉ LP (Raydium/Pumpfun Pool)</b> của nó (Nhập bừa ký tự nếu không biết):")
                    return
                elif user_state['step'] == 'WAITING_LP':
                    user_state['lp'] = text
                    user_state['step'] = 'WAITING_NAME'
                    send_telegram_alert("✅ Hợp lệ. Cuối cùng, hãy đặt một cái tên gợi nhớ cho đồng coin này:")
                    return
                elif user_state['step'] == 'WAITING_NAME':
                    MANUAL_COINS.append({"name": text, "chain": "solana", "ca": user_state['ca'], "lp": user_state['lp']})
                    send_telegram_alert("🎉 <b>ĐÃ ĐƯA COIN SOLANA VÀO RADAR THỦ CÔNG!</b>")
                    user_state.clear()
                    return
                elif user_state['step'] == 'WAITING_DEL_COIN':
                    target = text.lower()
                    m_len = len(MANUAL_COINS)
                    a_len = len(AUTO_COINS)
                    MANUAL_COINS[:]
