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
    return "Solana Sniper Bot (V12 - Fixed) đang hoạt động!"

def run_server():
    port = int(os.environ.get('PORT', 10000))
    # Sử dụng các tham số tối ưu cho Render
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)

# --- PHẦN 2: THÔNG SỐ CỐ ĐỊNH ---
API_KEYS = [
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImU0Y2QxMTFlLTE3YzYtNDU2My1iOGM5LTFjZWZkMjNmMjJhYiIsIm9yZ0lkIjoiNTA3MDc2IiwidXNlcklkIjoiNTIxNzQ5IiwidHlwZUlkIjoiZDhjZmE3NTEtNTAyMC00MTZkLWJkOGItZWJlMWM3Y2Q0NGJiIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQ0ODczODMsImV4cCI6NDkzMDI0NzM4M30.EdCGoN5pzZEuiDmvbEbHvLLGtQU2D2O_gSHX0t2JKug',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IjczZTU1ZWQxLTNjYzQtNGM3ZC05MTVmLThiMDc5MTQ3YjAyYiIsIm9yZ0lkIjoiNTA3MDc4IiwidXNlcklkIjoiNTIxNzUxIiwidHlwZUlkIjoiODFkY2ZiNTgtNTAxNC00NjRkLTg3ZDYtMTM0ZjQzZTVkZmRkIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQ0ODg3NTksImV4cCI6NDkzMDI0ODc1OX0.6hBFIZcOM1rVa6sUPNUZEUUEfSKanrurzqKQPbffiSI',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6ImUzYzYyNzRhLWMxZGItNDhlYS1hMjkxLWMzZGQ0YTU0YmM0NiIsIm9yZ0lkIjoiNTA3MDI0IiwidXNlcklkIjoiNTIxNjk2IiwidHlwZUlkIjoiMGExM2FmMGEtNDU2Yi00YTgwLWE0ZjMtZjNlZTc4N2Q0N2M1IiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQ0NTYyMzEsImV4cCI6NDkzMDIxNjIzMX0.gCOXCBjaTjWSo5XskcX4jdvo5fZDptZ-VsI6NuQZwvY'
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
            result = res.json().get("result", {}).get(ca, {})
            if result:
                mintable = result.get("mintable", "0") == "1"
                freezable = result.get("freezable", "0") == "1"
                return {"mintable": mintable, "freezable": freezable}
    except Exception: pass
    return None

def format_solana_security(ca):
    sec = check_solana_security(ca)
    if not sec: return "🛡 <b>Bảo mật:</b> ⚠️ Không thể quét contract.\n"
    mint_str = "🔴 CHƯA KHÓA" if sec['mintable'] else "🟢 Đã khóa"
    freeze_str = "🔴 CHƯA KHÓA" if sec['freezable'] else "🟢 Đã khóa"
    return f"🛡 <b>Bảo mật:</b>\n ├ Quyền in coin (Mint): {mint_str}\n └ Quyền đóng băng (Freeze): {freeze_str}\n"

# --- XỬ LÝ LỆNH TELEGRAM ---
def send_main_menu():
    keyboard = {"inline_keyboard": [
        [{"text": "📊 Xem Cấu Hình", "callback_data": "menu_status"}, {"text": "📋 List Đang Quét", "callback_data": "menu_list"}],
        [{"text": "⏱ Đổi Khung Giờ", "callback_data": "menu_set_time"}, {"text": "🛒 Đổi Lệnh Mua", "callback_data": "menu_set_buy"}],
        [{"text": "➕ Thêm Coin SOL", "callback_data": "menu_add"}, {"text": "🗑 Xóa Coin", "callback_data": "menu_del"}],
        [{"text": "🤖 Bật/Tắt Radar", "callback_data": "menu_auto_scan"}],
        [{"text": "🚫 Hủy Lệnh", "callback_data": "menu_cancel"}]
    ]}
    send_telegram_alert("🎛 <b>BẢNG ĐIỀU KHIỂN SOLANA SNIPER</b>", reply_markup=keyboard)

def execute_command(cmd):
    global CONFIG, user_state
    if cmd == 'status':
        msg = f"⚙️ <b>TRẠNG THÁI:</b> Radar {'🟢 BẬT' if CONFIG['AUTO_SCAN'] else '🔴 TẮT'}"
        send_telegram_alert(msg)
    elif cmd == 'list':
        msg = f"📋 <b>DANH SÁCH:</b>\n🤖 Auto: {len(AUTO_COINS)}\n👤 Thủ công: {len(MANUAL_COINS)}"
        send_telegram_alert(msg)
    elif cmd == 'auto_scan':
        CONFIG['AUTO_SCAN'] = not CONFIG['AUTO_SCAN']
        send_telegram_alert(f"🤖 Radar DexScreener: {'BẬT 🟢' if CONFIG['AUTO_SCAN'] else 'TẮT 🔴'}")
    elif cmd == 'add':
        user_state = {'step': 'WAITING_CA', 'last_time': time.time()}
        send_telegram_alert("📝 Nhập CA Solana muốn theo dõi:")
    elif cmd == 'cancel':
        user_state.clear()
        send_telegram_alert("🚫 Đã hủy.")

def process_update(item):
    global AUTO_COINS, MANUAL_COINS, user_state
    if "callback_query" in item:
        data = item["callback_query"]["data"]
        if data.startswith("menu_"): execute_command(data.replace("menu_", ""))
        return
    if "message" in item:
        text = item["message"].get("text", "")
        if text in ['/menu', '/start']: send_main_menu()
        elif user_state and user_state.get('step') == 'WAITING_CA':
            # Ở bản Solana này ta đơn giản hóa việc thêm coin thủ công
            MANUAL_COINS.append({"name": f"Manual_{text[:4]}", "ca": text, "lp": text, "chain": "solana"})
            send_telegram_alert("✅ Đã thêm coin vào danh sách Thủ Công!")
            user_state.clear()

def listen_telegram_commands():
    last_update_id = 0
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    while True:
        try:
            res = requests.get(url, params={"offset": last_update_id + 1, "timeout": 10}).json()
            for item in res.get("result", []):
                last_update_id = item["update_id"]
                process_update(item) 
        except Exception: pass
        time.sleep(2)

# --- RADAR TỰ ĐỘNG BẮT COIN MỚI ---
def auto_scan_dexscreener():
    seen_tokens = set()
    while True:
        if CONFIG.get('AUTO_SCAN'):
            try:
                # Lấy danh sách token mới nhất từ DexScreener
                res = requests.get("https://api.dexscreener.com/token-profiles/latest/v1", timeout=10).json()
                for item in res:
                    ca = item.get('tokenAddress')
                    if item.get('chainId') == 'solana' and ca not in seen_tokens:
                        seen_tokens.add(ca)
                        sec = check_solana_security(ca)
                        # Chỉ lấy coin sạch (Khóa Mint & Freeze)
                        if sec and not sec['mintable'] and not sec['freezable']:
                            if len(AUTO_COINS) >= CONFIG['MAX_AUTO_COINS']: AUTO_COINS.pop(0)
                            AUTO_COINS.append({"name": f"Dex_{ca[:4]}", "ca": ca, "lp": ca})
                            send_telegram_alert(f"🚨 <b>PHÁT HIỆN GEM SOLANA MỚI!</b>\n📝 CA: <code>{ca}</code>\n✅ Bảo mật an toàn!")
            except Exception: pass
        time.sleep(60)

# --- LUỒNG QUÉT CÁ MẬP (SMART MONEY) GOM HÀNG ---
def run_bot():
    alerted_wallets = set()
    while True:
        all_lists = [("AUTO", AUTO_COINS), ("MANUAL", MANUAL_COINS)]
        for list_type, coin_list in all_lists:
            time_frame = CONFIG[f"{list_type}_TIME_FRAME"]
            min_buys = CONFIG[f"{list_type}_MIN_BUYS"]
            
            for coin in list(coin_list):
                try:
                    ca = coin["ca"]
                    url = f"https://solana-gateway.moralis.io/token/mainnet/{ca}/transfers"
                    response = requests.get(url, headers=get_current_headers(), timeout=10).json()
                    
                    # Moralis Solana trả về một mảng trực tiếp
                    buy_counts = defaultdict(int)
                    time_ago = datetime.now(timezone.utc) - timedelta(hours=time_frame)
                    
                    for tx in response:
                        tx_time = datetime.strptime(tx['timestamp'][:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
                        if tx_time < time_ago: break
                        
                        # Logic Solana: Mua là transfer từ LP/Pool đến ví người dùng
                        receiver = tx.get('toUserAccount')
                        if receiver: buy_counts[receiver] += 1
                        
                    for buyer, count in buy_counts.items():
                        if count >= min_buys and buyer not in alerted_wallets:
                            # ĐÂY LÀ DÒNG 292 (HOẶC TƯƠNG ĐƯƠNG) ĐÃ ĐƯỢC SỬA TÊN HÀM CHUẨN:
                            sec_info = format_solana_security(ca)
                            price = get_solana_token_price(ca)
                            
                            msg = (f"💎 <b>CÁ MẬP GOM HÀNG ({list_type})</b>\n\n"
                                   f"🪙 CA: <code>{ca}</code>\n"
                                   f"👤 Ví: <code>{buyer}</code>\n"
                                   f"🟢 Mua {count} lệnh\n"
                                   f"💰 Giá: {price}\n{sec_info}")
                            send_telegram_alert(msg)
                            alerted_wallets.add(buyer)
                except Exception: pass
                time.sleep(2)
        time.sleep(300)

if __name__ == "__main__":
    # Khởi động các luồng
    Thread(target=listen_telegram_commands, daemon=True).start()
    Thread(target=auto_scan_dexscreener, daemon=True).start()
    Thread(target=run_bot, daemon=True).start()
    run_server()
