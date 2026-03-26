import requests
import time
import os
import json
from datetime import datetime, timedelta, timezone 
from flask import Flask, request
from threading import Thread

# --- PHẦN 1: TẠO WEB SERVER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "BSC Sniper Bot (Forensics V2) đang hoạt động!"

def run_server():
    port = int(os.environ.get('PORT', 10000))
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
    "AUTO_SCAN": True
}

MANUAL_COINS = []
AUTO_COINS = [] 
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

# --- BẢO MẬT GOPLUS CHO BSC ---
def check_bsc_security(ca):
    try:
        url = f"https://api.gopluslabs.io/api/v1/token_security/56?contract_addresses={ca}"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            result = res.json().get("result", {}).get(ca.lower(), {})
            if result:
                is_honeypot = result.get("is_honeypot", "0") == "1"
                buy_tax = float(result.get("buy_tax", 0)) * 100
                sell_tax = float(result.get("sell_tax", 0)) * 100
                return {"is_honeypot": is_honeypot, "buy_tax": buy_tax, "sell_tax": sell_tax}
    except Exception: pass
    return None

def format_bsc_security(ca):
    sec = check_bsc_security(ca)
    if not sec: return "🛡 <b>Bảo mật:</b> ⚠️ Không thể quét contract.\n"
    hp_str = "🔴 CÓ (Lừa đảo)" if sec['is_honeypot'] else "🟢 Không"
    return f"🛡 <b>Bảo mật (BSC):</b>\n ├ Honeypot: {hp_str}\n └ Thuế: Mua {sec['buy_tax']:.1f}% | Bán {sec['sell_tax']:.1f}%\n"

# --- WEBHOOK NHẬN KÈO TỪ MORALIS STREAMS ---
@app.route('/webhook', methods=['POST'])
def moralis_webhook():
    global AUTO_COINS, CONFIG
    if not CONFIG.get('AUTO_SCAN', True): return "Auto scan is disabled", 200
    try:
        data = request.json
        if data and data.get('confirmed'):
            logs = data.get('logs', [])
            for log in logs:
                # Bắt sự kiện PairCreated trên PancakeSwap
                if log.get('topic0') == '0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9':
                    token0 = "0x" + log.get('topic1', '')[-40:]
                    token1 = "0x" + log.get('topic2', '')[-40:]
                    wbnb = "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"
                    
                    new_token = token1 if token0.lower() == wbnb else token0
                    lp_address = "0x" + log.get('data', '')[26:66]

                    if any(c['ca'].lower() == new_token.lower() for c in AUTO_COINS + MANUAL_COINS): continue

                    sec_info = check_bsc_security(new_token)
                    # Chỉ lấy coin sạch (Không honeypot, thuế < 10%)
                    if sec_info and not sec_info['is_honeypot'] and sec_info['buy_tax'] < 10 and sec_info['sell_tax'] < 10:
                        if len(AUTO_COINS) >= CONFIG['MAX_AUTO_COINS']: AUTO_COINS.pop(0)
                        
                        AUTO_COINS.append({
                            "name": f"AutoBSC_{new_token[:4]}", 
                            "chain": "bsc", "ca": new_token, "lp": lp_address,
                            "last_alert_at": time.time(), "prompt_sent": False
                        })
                        msg = f"🚨 <b>STREAMS PHÁT HIỆN GEM BSC MỚI!</b>\n📝 CA: <code>{new_token}</code>\n✅ Đã qua kiểm duyệt, đưa vào theo dõi Cá mập."
                        send_telegram_alert(msg)
    except Exception as e: print(f"Webhook Error: {e}")
    return "OK", 200

# --- XỬ LÝ LỆNH TELEGRAM ---
def send_main_menu():
    keyboard = {"inline_keyboard": [
        [{"text": "📊 Xem Cấu Hình", "callback_data": "menu_status"}, {"text": "📋 List Đang Quét", "callback_data": "menu_list"}],
        [{"text": "➕ Thêm Coin BSC", "callback_data": "menu_add"}, {"text": "🗑 Xóa Coin", "callback_data": "menu_del"}],
        [{"text": "🚫 Hủy Lệnh", "callback_data": "menu_cancel"}]
    ]}
    send_telegram_alert("🎛 <b>BẢNG ĐIỀU KHIỂN BSC SNIPER</b>", reply_markup=keyboard)

def execute_command(cmd):
    global CONFIG, user_state
    if cmd == 'status':
        send_telegram_alert(f"⚙️ <b>TRẠNG THÁI BSC:</b> Webhook {'🟢 BẬT' if CONFIG['AUTO_SCAN'] else '🔴 TẮT'}")
    elif cmd == 'list':
        msg = f"📋 <b>DANH SÁCH BSC:</b>\n🤖 Auto: {len(AUTO_COINS)}\n👤 Thủ công: {len(MANUAL_COINS)}"
        send_telegram_alert(msg)
    elif cmd == 'add':
        user_state = {'step': 'WAITING_CA', 'last_time': time.time()}
        send_telegram_alert("📝 Nhập CA BSC muốn theo dõi:")
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
            user_state['ca'] = text
            user_state['step'] = 'WAITING_LP'
            send_telegram_alert("✅ Đã nhận CA. Hãy nhập tiếp địa chỉ LP (PancakeSwap Pair):")
        elif user_state and user_state.get('step') == 'WAITING_LP':
            MANUAL_COINS.append({"name": f"Manual_{user_state['ca'][:4]}", "ca": user_state['ca'], "lp": text, "chain": "bsc"})
            send_telegram_alert("🎉 Đã thêm vào Radar Thủ Công BSC!")
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

# --- LÕI ĐIỀU TRA CHUỖI CHÉO (ON-CHAIN FORENSICS) ---
def run_bot():
    alerted_coins = set()
    while True:
        all_lists = [("AUTO", AUTO_COINS), ("MANUAL", MANUAL_COINS)]
        for list_type, coin_list in all_lists:
            time_frame = CONFIG[f"{list_type}_TIME_FRAME"]
            min_buys = CONFIG[f"{list_type}_MIN_BUYS"]
            
            for coin in list(coin_list):
                try:
                    ca = coin["ca"].lower()
                    lp = coin["lp"].lower()
                    coin_name = coin["name"]
                    
                    # Tránh báo liên tục cho 1 đồng
                    alert_key = f"{ca}_{time_frame}"
                    if alert_key in alerted_coins: continue

                    # Gọi Moralis lấy lịch sử giao dịch Token
                    url = f"https://deep-index.moralis.io/api/v2.2/erc20/{ca}/transfers?chain=bsc&limit=100"
                    response = requests.get(url, headers=get_current_headers(), timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        transactions = data.get('result', [])
                        
                        # Lọc giao dịch trong khung thời gian
                        time_ago = datetime.now(timezone.utc) - timedelta(hours=time_frame)
                        valid_txs = []
                        for tx in transactions:
                            tx_time = datetime.strptime(tx['block_timestamp'][:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
                            if tx_time >= time_ago: valid_txs.append(tx)

                        # THUẬT TOÁN VẾT DẦU LOANG
                        # Sắp xếp từ cũ nhất đến mới nhất để lần theo dấu vết
                        valid_txs = sorted(valid_txs, key=lambda x: x.get('block_timestamp', ''))
                        
                        suspect_wallets = set()
                        terminal_holders = set()
                        valid_buy_chains = 0

                        for tx in valid_txs:
                            sender = tx.get('from_address', '').lower()
                            receiver = tx.get('to_address', '').lower()

                            # F0 Mua từ LP
                            if sender == lp:
                                suspect_wallets.add(receiver)
                                terminal_holders.add(receiver)
                                valid_buy_chains += 1
                            
                            # Ví nghi ngờ thực hiện giao dịch
                            elif sender in suspect_wallets:
                                if receiver == lp:
                                    # XẢ HÀNG: Cắt chuỗi
                                    if sender in terminal_holders:
                                        valid_buy_chains -= 1
                                        terminal_holders.remove(sender)
                                else:
                                    # CHUYỂN TAY: Bôi đỏ ví mới
                                    suspect_wallets.add(receiver)
                                    terminal_holders.add(receiver)
                                    if sender in terminal_holders:
                                        terminal_holders.remove(sender)
                        
                        # NẾU CÒN ĐỦ CHUỐI GOM VÀ KHÔNG BỊ XẢ
                        if valid_buy_chains >= min_buys:
                            sec_info = format_bsc_security(ca)
                            top_holders = list(terminal_holders)[:3]
                            holders_str = "\n".join([f"💳 <code>{w}</code>" for w in top_holders])
                            
                            msg = (f"💎 <b>CÁ MẬP BSC GOM HÀNG CHUỖI CHÉO ({list_type})</b>\n\n"
                                   f"🪙 <b>Coin:</b> {coin_name} | CA: <code>{ca}</code>\n"
                                   f"🎯 <b>Phát hiện:</b> {valid_buy_chains} đường dây gom ngầm!\n"
                                   f"🕵️‍♂️ <b>Ví cuối đang găm hàng:</b>\n{holders_str}\n\n"
                                   f"✅ Bot đã bóc trần chiêu trò chuyển tay, tuyệt đối chưa xả ngược lại Pool!\n{sec_info}")
                            send_telegram_alert(msg)
                            alerted_coins.add(alert_key)

                except Exception as e: print(f"Error checking {coin['ca']}: {e}")
                time.sleep(2)
        time.sleep(120)

if __name__ == "__main__":
    Thread(target=listen_telegram_commands, daemon=True).start()
    Thread(target=run_bot, daemon=True).start()
    run_server()
