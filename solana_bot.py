import requests
import time
import os
import json 
from datetime import datetime, timedelta, timezone 
from collections import defaultdict
from flask import Flask, request
from threading import Thread

# --- PHẦN 1: TẠO WEB SERVER & NHẬN STREAMS API ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Solana Sniper Bot (Giao Diện Nút Bấm) đang hoạt động!"

@app.route('/webhook', methods=['POST'])
def moralis_webhook():
    global AUTO_COINS, MANUAL_COINS, CONFIG
    if not CONFIG.get('AUTO_SCAN', True):
        return "Auto scan is disabled", 200

    try:
        data = request.json
        # Dữ liệu Streams của Solana trả về dưới dạng một danh sách (List) các giao dịch
        if data and isinstance(data, list):
            for tx in data:
                mints = set()
                
                # Quét tìm các token xuất hiện trong giao dịch trả phí tạo Pool này
                for transfer in tx.get('tokenTransfers', []):
                    if transfer.get('mint'):
                        mints.add(transfer['mint'])
                        
                # Bỏ qua đồng WSOL mặc định của hệ Solana
                wsol = "So11111111111111111111111111111111111111112"
                if wsol in mints:
                    mints.remove(wsol)
                    
                for new_token in mints:
                    # Chống trùng lặp
                    if any(c['ca'].lower() == new_token.lower() for c in AUTO_COINS + MANUAL_COINS): 
                        continue
                        
                    # Đưa qua máy X-Quang Solana
                    sec_info = check_solana_security(new_token)
                    
                    # CỰC KỲ QUAN TRỌNG: Chỉ lấy coin ĐÃ KHÓA Mint và Freeze
                    if sec_info and not sec_info['mintable'] and not sec_info['freezable']:
                        
                        # Băng chuyền Auto
                        if len(AUTO_COINS) >= CONFIG['MAX_AUTO_COINS']:
                            dropped = AUTO_COINS.pop(0) 
                            send_telegram_alert(f"🗑 Đã xóa <b>{dropped['name']}</b> để nhường chỗ cho Gem Solana mới.")
                        
                        new_coin_obj = {
                            "name": f"SolAuto_{new_token[:4]}", 
                            "chain": "solana", 
                            "ca": new_token, 
                            "lp": "raydium_pool",
                            "last_alert_at": time.time(), 
                            "prompt_sent": False,
                            "prompt_time": 0
                        }
                        AUTO_COINS.append(new_coin_obj)
                        
                        alert_msg = (
                            f"🚨 <b>STREAMS BẮT ĐƯỢC GEM SOLANA MỚI!</b> 🚨\n\n"
                            f"🌐 <b>Mạng:</b> SOLANA\n"
                            f"📝 <b>CA:</b> <code>{new_token}</code>\n"
                            f"✅ <b>Bảo mật (Tuyệt đối an toàn):</b>\n"
                            f" ├ Quyền in coin (Mint): Đã khóa 🟢\n"
                            f" └ Quyền đóng băng (Freeze): Đã khóa 🟢\n\n"
                            f"<i>👉 Đã tự động đưa vào Radar quét cá mập.</i>\n"
                            f"🔍 <a href='https://solscan.io/token/{new_token}'>Soi trên Solscan</a>"
                        )
                        send_telegram_alert(alert_msg)
    except Exception as e:
        print(f"Lỗi Webhook Solana: {e}", flush=True)
    return "OK", 200

def run_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

# --- PHẦN 2: THÔNG SỐ CỐ ĐỊNH CHO SOLANA ---
API_KEYS = [
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImU0Y2QxMTFlLTE3YzYtNDU2My1iOGM5LTFjZWZkMjNmMjJhYiIsIm9yZ0lkIjoiNTA3MDc2IiwidXNlcklkIjoiNTIxNzQ5IiwidHlwZUlkIjoiZDhjZmE3NTEtNTAyMC00MTZkLWJkOGItZWJlMWM3Y2Q0NGJiIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQ0ODczODMsImV4cCI6NDkzMDI0NzM4M30.EdCGoN5pzZEuiDmvbEbHvLLGtQU2D2O_gSHX0t2JKug',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjczZTU1ZWQxLTNjYzQtNGM3ZC05MTVmLThiMDc5MTQ3YjAyYiIsIm9yZ0lkIjoiNTA3MDc4IiwidXNlcklkIjoiNTIxNzUxIiwidHlwZUlkIjoiODFkY2ZiNTgtNTAxNC00NjRkLTg3ZDYtMTM0ZjQzZTVkZmRkIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQ0ODg3NTksImV4cCI6NDkzMDI0ODc1OX0.6hBFIZcOM1rVa6sUPNUZEUUEfSKanrurzqKQPbffiSI',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImUzYzYyNzRhLWMxZGItNDhlYS1hMjkxLWMzZGQ0YTU0YmM0NiIsIm9yZ0lkIjoiNTA3MDI0IiwidXNlcklkIjoiNTIxNjk2IiwidHlwZUlkIjoiMGExM2FmMGEtNDU2Yi00YTgwLWE0ZjMtZjNlZTc4N2Q0N2M1IiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQ0NTYyMzEsImV4cCI6NDkzMDIxNjIzMX0.gCOXCBjaTjWSo5XskcX4jdvo5fZDptZ-VsI6NuQZwvY'
]

# ĐÃ CẬP NHẬT BOT TOKEN MỚI CỦA BẠN
TELEGRAM_BOT_TOKEN = '8202619989:AAExXHIbOHIA1VNszdv9j5mUlT6VfhqxfrA'
TELEGRAM_CHAT_ID = '1976782751'

EXPLORERS = {
    "solana": "solscan.io"
}

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

# --- BỘ TỪ ĐIỂN ĐÃ ĐƯỢC TÙY BIẾN CHO SOLANA ---
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
            [{"text": "🤖 Bật/Tắt Quét Streams", "callback_data": "menu_auto_scan"}],
            [{"text": "🔑 Kho API Keys", "callback_data": "menu_keys"}, {"text": "➕ Nạp API Key", "callback_data": "menu_add_key"}],
            [{"text": "🌐 Đổi Ngôn Ngữ", "callback_data": "menu_language"}, {"text": "🚫 Hủy Lệnh", "callback_data": "menu_cancel"}]
        ]
    }
    send_telegram_alert("🎛 <b>BẢNG ĐIỀU KHIỂN SOLANA SNIPER</b>\n\n👉 Vui lòng chọn chức năng bên dưới:", reply_markup=keyboard)

# --- CÁC HÀM CÔNG CỤ CHO SOLANA ---
def get_solana_token_price(ca):
    try:
        # Sử dụng Endpoint của Solana Gateway
        url = f"https://solana-gateway.moralis.io/token/mainnet/{ca}/price"
        res = requests.get(url, headers=get_current_headers(), timeout=10)
        if res.status_code == 200:
            price = res.json().get("usdPrice", 0)
            return f"${price:.6f}" if price < 1 else f"${price:.2f}"
    except Exception: pass
    return "N/A"

def check_solana_security(ca):
    try:
        # Sử dụng API GoPlus chuyên dụng cho mạng Solana (chain_id = solana)
        url = f"https://api.gopluslabs.io/api/v1/solana/token_security?contract_addresses={ca}"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            result = res.json().get("result", {}).get(ca.lower(), {})
            if result:
                # Top lừa đảo Solana: Quyền in thêm coin và Quyền đóng băng ví
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
            f"🔄 Auto Scan Streams: <b>{auto_state}</b>\n"
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
        if CONFIG['AUTO_SCAN']: send_telegram_alert("🟢 <b>Quét Tự Động: ĐÃ BẬT</b>")
        else: send_telegram_alert("🔴 <b>Quét Tự Động: ĐÃ TẮT</b>")
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
        # Mặc định luôn là SOLANA, không cần chọn Chain nữa
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
                
                # Logic cho Solana
                if user_state['step'] == 'WAITING_CA':
                    user_state['ca'] = text
                    user_state['step'] = 'WAITING_LP'
                    # Bỏ qua bước xác thực bắt đầu bằng 0x vì CA của Solana là chuỗi Base58
                    send_telegram_alert("✅ Đã nhận CA Solana.\n📝 Tiếp theo, hãy nhập <b>địa chỉ LP (Raydium/Pumpfun Pool)</b> của nó:")
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
                    MANUAL_COINS[:] = [c for c in MANUAL_COINS if c['ca'].lower() != target and c['name'].lower() != target]
                    AUTO_COINS[:] = [c for c in AUTO_COINS if c['ca'].lower() != target and c['name'].lower() != target]
                    if len(MANUAL_COINS) < m_len or len(AUTO_COINS) < a_len: send_telegram_alert("🗑 <b>Đã xóa coin khỏi radar!</b>")
                    else: send_telegram_alert("❌ Không tìm thấy coin. Mời nhập lại (/cancel để hủy):")
                    return
                elif user_state['step'].startswith('WAITING_TIME_VAL_'):
                    try:
                        val = int(text)
                        target_list = user_state['step'].split('_')[3] 
                        CONFIG[f'{target_list}_TIME_FRAME'] = val
                        send_telegram_alert(f"✅ Đã đổi thời gian cho {target_list} thành {val} giờ.")
                        user_state.clear()
                    except ValueError: send_telegram_alert("❌ Vui lòng nhập số:")
                    return
                elif user_state['step'].startswith('WAITING_BUY_VAL_'):
                    try:
                        val = int(text)
                        target_list = user_state['step'].split('_')[3]
                        CONFIG[f'{target_list}_MIN_BUYS'] = val
                        send_telegram_alert(f"✅ Đã đổi số lệnh mua cho {target_list} thành {val} lệnh.")
                        user_state.clear()
                    except ValueError: send_telegram_alert("❌ Vui lòng nhập số:")
                    return
                elif user_state['step'] == 'WAITING_MAX_AUTO':
                    try:
                        val = int(text)
                        CONFIG['MAX_AUTO_COINS'] = val
                        send_telegram_alert(f"✅ Giới hạn rổ Auto Scan đã đổi thành: <b>{val} Coin</b>.")
                        user_state.clear()
                    except ValueError: send_telegram_alert("❌ Vui lòng nhập số:")
                    return
                elif user_state['step'] == 'WAITING_ADD_KEY':
                    if text not in API_KEYS: API_KEYS.append(text)
                    send_telegram_alert(f"✅ Đã thêm Key. Tổng băng đạn: {len(API_KEYS)}")
                    user_state.clear()
                    return
                elif user_state['step'] == 'WAITING_SMART_ADDRESS':
                    user_state['address'] = text
                    user_state['step'] = 'WAITING_SMART_NAME'
                    send_telegram_alert("✅ Đã nhận địa chỉ ví SOL. Đặt tên cho ví Cá Mập này:")
                    return
                elif user_state['step'] == 'WAITING_SMART_NAME':
                    SMART_WALLETS.append({"name": text, "chain": "solana", "address": user_state['address']})
                    send_telegram_alert("🎉 <b>ĐÃ ĐƯA VÍ CÁ MẬP SOLANA VÀO TẦM NGẮM!</b>")
                    user_state.clear()
                    return
                
            if text.startswith('/'):
                cmd = text.replace("/", "")
                execute_command(cmd)

    except Exception: pass

# --- WALLET API CHO SOLANA ---
def run_smart_money_bot():
    global current_api_index
    alerted_txs = set()
    while True:
        if not SMART_WALLETS or not API_KEYS:
            time.sleep(60)
            continue
        for w in list(SMART_WALLETS):
            try:
                address = w['address']
                explorer = "solscan.io"
                
                # API lấy giao dịch SPL Token của ví trên mạng Solana
                url = f"https://solana-gateway.moralis.io/account/mainnet/{address}/transfers"
                res = requests.get(url, headers=get_current_headers(), timeout=10)
                
                if res.status_code == 200:
                    for tx in res.json():
                        tx_hash = tx.get('signature')
                        
                        # Ví cá mập là người NHẬN token
                        if tx.get('toUserAccount', '').lower() == address.lower() and tx_hash not in alerted_txs:
                            alerted_txs.add(tx_hash)
                            
                            tx_time = datetime.strptime(tx['timestamp'][:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
                            if tx_time > datetime.now(timezone.utc) - timedelta(hours=1):
                                ca = tx.get('mint', '')
                                amount = float(tx.get('amount', 0))
                                
                                msg = f"🚨 <b>CÁ MẬP SOLANA MUA HÀNG!</b>\n\n👤 <b>{w['name']}</b>\n💰 Đã nhận: {amount:,.2f} token\n📝 CA: <code>{ca}</code>\n🔗 <a href='https://{explorer}/tx/{tx_hash}'>Xem TX trên Solscan</a>"
                                send_telegram_alert(msg)
                                
                elif res.status_code in [401, 429, 403]:
                    current_api_index = (current_api_index + 1) % len(API_KEYS)
            except Exception: pass
            time.sleep(2)
        time.sleep(120) 

# --- LOGIC BOT CHÍNH (QUÉT CÁ MẬP SOLANA + AUTO CLEANUP) ---
def run_bot():
    global current_api_index, AUTO_COINS
    alerted_wallets = set()
    if not API_KEYS: return
    send_telegram_alert("🚀 <b>SOLANA SNIPER BOT ĐÃ KHỞI ĐỘNG MÁY!</b>\n👉 Hãy gõ <b>/menu</b> để mở Bảng Điều Khiển.")

    while True:
        if not API_KEYS:
            time.sleep(60)
            continue
            
        now = time.time()
        
        for coin in list(AUTO_COINS):
            if coin.get('prompt_sent'):
                if now - coin.get('prompt_time', 0) > 300:
                    coin['prompt_sent'] = False
                    coin['last_alert_at'] = now
                    send_telegram_alert(f"⏳ Lệnh hỏi xóa <b>{coin['name']}</b> đã tự hủy.\nHệ thống tự động gia hạn theo dõi thêm 24h.")
            elif now - coin.get('last_alert_at', now) > 86400:
                coin['prompt_sent'] = True
                coin['prompt_time'] = now
                keyboard = {"inline_keyboard": [
                    [{"text": "✅ Xóa Coin Này", "callback_data": f"dead_yes_{coin['ca']}"}],
                    [{"text": "❌ Giữ lại theo dõi 24h", "callback_data": f"dead_no_{coin['ca']}"}]
                ]}
                send_telegram_alert(f"🗑 <b>DỌN RÁC AUTO SCAN:</b>\n\nĐồng coin SOL <b>{coin['name']}</b> đã héo sau 24h. Bạn có muốn xóa nó khỏi rổ theo dõi không?", reply_markup=keyboard)

        all_configs = [("AUTO", AUTO_COINS), ("MANUAL", MANUAL_COINS)]
        
        for list_type, coin_list in all_configs:
            time_frame = CONFIG[f"{list_type}_TIME_FRAME"]
            min_buys = CONFIG[f"{list_type}_MIN_BUYS"]
            
            for coin in list(coin_list): 
                try:
                    coin_name = coin["name"]
                    ca = coin["ca"]
                    lp = coin["lp"]
                    explorer = "solscan.io"
                    
                    # Lấy dữ liệu Token Transfers trên Solana
                    url = f"https://solana-gateway.moralis.io/token/mainnet/{ca}/transfers"
                    time_ago = datetime.now(timezone.utc) - timedelta(hours=time_frame)
                    
                    buy_counts = defaultdict(int)
                    cursor = None
                    reached_time_limit = False
                    page_count = 0 

                    while not reached_time_limit and page_count < 50:
                        page_count += 1
                        params = {"limit": 100}
                        if cursor: params["cursor"] = cursor
                        
                        response = requests.get(url, params=params, headers=get_current_headers(), timeout=10)
                        
                        if response.status_code != 200:
                            if response.status_code in [429, 401, 402, 403]:
                                current_api_index += 1
                                if current_api_index >= len(API_KEYS):
                                    current_api_index = 0 
                                    send_telegram_alert(f"💀 <b>BÁO ĐỘNG ĐỎ</b>: Hết {len(API_KEYS)} Key! Nghỉ 30 phút.")
                                    time.sleep(1800) 
                                    break 
                                else:
                                    send_telegram_alert(f"🔄 <b>ĐỔI KEY TỰ ĐỘNG</b>: Sang <b>Key số {current_api_index + 1}</b>!")
                                    time.sleep(2)
                                    page_count -= 1 
                                    continue 
                            else: break
                            
                        data = response.json()
                        if not data: break
                        
                        # Phân tích dữ liệu JSON trả về (Morlaisa Sol API trả mảng trực tiếp hoặc có cursor)
                        transactions = data.get('result', []) if isinstance(data, dict) else data

                        for tx in transactions:
                            # Parse timestamp
                            tx_time_str = tx.get('timestamp', '')[:19] 
                            if not tx_time_str: continue
                            tx_time = datetime.strptime(tx_time_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
                            
                            if tx_time < time_ago:
                                reached_time_limit = True
                                break 

                            sender = tx.get('fromUserAccount', '').lower()
                            receiver = tx.get('toUserAccount', '').lower()
                            
                            # Nếu nguồn xuất phát là LP (Raydium Pool) thì tính là MUA
                            if sender == lp.lower(): 
                                buy_counts[receiver] += 1
                                
                        cursor = data.get("cursor") if isinstance(data, dict) else None
                        if not cursor: break
                        time.sleep(0.5) 

                    # Cảnh báo Cá Mập
                    for buyer, count in buy_counts.items():
                        if count >= min_buys and buyer not in alerted_wallets:
                            sec_info = format_solana_security(ca)
                            defi_info = f"📊 Giá: {get_solana_token_price(ca)}"

                            msg = f"💎 <b>CÁ MẬP GOM SOLANA ({time_frame}H) - {list_type}</b>\n\n🪙 <b>Coin:</b> {coin_name}\n💳 <code>{buyer}</code>\n🟢 Rút từ Pool {count} lệnh.\n{sec_info}{defi_info}\n🔍 <a href='https://{explorer}/account/{buyer}'>Soi ví trên Solscan</a>"
                            send_telegram_alert(msg)
                            alerted_wallets.add(buyer)
                            
                            if list_type == "AUTO": coin['last_alert_at'] = time.time()

                except Exception: pass
                time.sleep(3) 
                
        time.sleep(300) 

if __name__ == "__main__":
    t1 = Thread(target=run_bot)
    t1.daemon = True
    t1.start()
    
    t2 = Thread(target=listen_telegram_commands)
    t2.daemon = True
    t2.start()
    
    t3 = Thread(target=run_smart_money_bot)
    t3.daemon = True
    t3.start()
    
    run_server()
