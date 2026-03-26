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
                    new_token = token0 if token1.lower() in wbnb_weth else token1
                    if new_token.lower() in wbnb_weth: continue 
                    
                    if any(c['ca'].lower() == new_token.lower() for c in AUTO_COINS + MANUAL_COINS): 
                        continue
                        
                    sec_info = check_token_security(new_token, chain)
                    if sec_info and not sec_info['honeypot'] and sec_info['buy_tax'] <= 10 and sec_info['sell_tax'] <= 10:
                        
                        if len(AUTO_COINS) >= CONFIG['MAX_AUTO_COINS']:
                            dropped = AUTO_COINS.pop(0) 
                            send_telegram_alert(f"🗑 Đã xóa <b>{dropped['name']}</b> để nhường chỗ cho Gem mới (Đầy {CONFIG['MAX_AUTO_COINS']} coin).")
                        
                        new_coin_obj = {
                            "name": f"Auto_{new_token[:4]}", 
                            "chain": chain, 
                            "ca": new_token, 
                            "lp": pair,
                            "last_alert_at": time.time(), 
                            "prompt_sent": False,
                            "prompt_time": 0
                        }
                        AUTO_COINS.append(new_coin_obj)
                        
                        alert_msg = (
                            f"🚨 <b>STREAMS BẮT ĐƯỢC GEM MỚI!</b> 🚨\n\n"
                            f"🌐 <b>Mạng:</b> {chain.upper()}\n"
                            f"📝 <b>CA:</b> <code>{new_token}</code>\n"
                            f"✅ Thuế Mua {sec_info['buy_tax']}% | Bán {sec_info['sell_tax']}%\n"
                            f"🛡 Không Honeypot.\n"
                            f"<i>👉 Tự động nạp vào Radar (Sẽ tự xóa nếu 24h ko ai gom).</i>"
                        )
                        send_telegram_alert(alert_msg)
    except Exception as e:
        print(f"Lỗi Webhook: {e}", flush=True)
    return "OK", 200

def run_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

# --- PHẦN 2: THÔNG SỐ CỐ ĐỊNH ---
API_KEYS = [
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImU0Y2QxMTFlLTE3YzYtNDU2My1iOGM5LTFjZWZkMjNmMjJhYiIsIm9yZ0lkIjoiNTA3MDc2IiwidXNlcklkIjoiNTIxNzQ5IiwidHlwZUlkIjoiZDhjZmE3NTEtNTAyMC00MTZkLWJkOGItZWJlMWM3Y2Q0NGJiIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQ0ODczODMsImV4cCI6NDkzMDI0NzM4M30.EdCGoN5pzZEuiDmvbEbHvLLGtQU2D2O_gSHX0t2JKug',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjczZTU1ZWQxLTNjYzQtNGM3ZC05MTVmLThiMDc5MTQ3YjAyYiIsIm9yZ0lkIjoiNTA3MDc4IiwidXNlcklkIjoiNTIxNzUxIiwidHlwZUlkIjoiODFkY2ZiNTgtNTAxNC00NjRkLTg3ZDYtMTM0ZjQzZTVkZmRkIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQ0ODg3NTksImV4cCI6NDkzMDI0ODc1OX0.6hBFIZcOM1rVa6sUPNUZEUUEfSKanrurzqKQPbffiSI',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImUzYzYyNzRhLWMxZGItNDhlYS1hMjkxLWMzZGQ0YTU0YmM0NiIsIm9yZ0lkIjoiNTA3MDI0IiwidXNlcklkIjoiNTIxNjk2IiwidHlwZUlkIjoiMGExM2FmMGEtNDU2Yi00YTgwLWE0ZjMtZjNlZTc4N2Q0N2M1IiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQ0NTYyMzEsImV4cCI6NDkzMDIxNjIzMX0.gCOXCBjaTjWSo5XskcX4jdvo5fZDptZ-VsI6NuQZwvY'
]

TELEGRAM_BOT_TOKEN = '8356674324:AAGS0gSxLanjRUonSwN0PluimJsyn1prTyQ'
TELEGRAM_CHAT_ID = '1976782751'

EXPLORERS = {
    "base": "basescan.org",
    "bsc": "bscscan.com",
    "eth": "etherscan.io"
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

MANUAL_COINS = [
    {
        "name": "Token 4 (Thủ công)", 
        "chain": "base",   
        "ca": "0x9f86dB9fc6f7c9408e8Fda3Ff8ce4e78ac7a6b07", 
        "lp": "0xCD55381a53da35Ab1D7Bc5e3fE5F76cac976FAc3"
    }
]
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

# --- TỪ ĐIỂN ĐA NGÔN NGỮ ---
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
            [{"text": "➕ Thêm Coin", "callback_data": "menu_add"}, {"text": "🗑 Xóa Coin", "callback_data": "menu_del"}],
            [{"text": "🐋 Thêm Ví Cá Mập", "callback_data": "menu_add_wallet"}, {"text": "📦 Giới Hạn Auto", "callback_data": "menu_set_max_auto"}],
            [{"text": "🤖 Bật/Tắt Quét Streams", "callback_data": "menu_auto_scan"}],
            [{"text": "🔑 Kho API Keys", "callback_data": "menu_keys"}, {"text": "➕ Nạp API Key", "callback_data": "menu_add_key"}],
            [{"text": "🌐 Đổi Ngôn Ngữ", "callback_data": "menu_language"}, {"text": "🚫 Hủy Lệnh", "callback_data": "menu_cancel"}]
        ]
    }
    send_telegram_alert("🎛 <b>BẢNG ĐIỀU KHIỂN TRUNG TÂM</b>\n\n👉 Vui lòng chọn chức năng bên dưới:", reply_markup=keyboard)

# --- CÁC HÀM CÔNG CỤ ---
def get_token_price(ca, chain):
    try:
        url = f"https://deep-index.moralis.io/api/v2.2/erc20/{ca}/price?chain={chain}"
        res = requests.get(url, headers=get_current_headers(), timeout=10)
        if res.status_code == 200:
            price = res.json().get("usdPrice", 0)
            return f"${price:.6f}" if price < 1 else f"${price:.2f}"
    except Exception: pass
    return "N/A"

def check_token_security(ca, chain):
    chain_ids = {"bsc": "56", "eth": "1", "base": "8453"}
    chain_id = chain_ids.get(chain.lower())
    if not chain_id: return None
    try:
        url = f"https://api.gopluslabs.io/api/v1/token_security/{chain_id}?contract_addresses={ca.lower()}"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            result = res.json().get("result", {}).get(ca.lower(), {})
            if result:
                buy_tax = round(float(result.get("buy_tax", 0)) * 100, 1)
                sell_tax = round(float(result.get("sell_tax", 0)) * 100, 1)
                is_honeypot = result.get("is_honeypot", "0") == "1"
                return {"honeypot": is_honeypot, "buy_tax": buy_tax, "sell_tax": sell_tax}
    except Exception: pass
    return None

def execute_command(cmd):
    global CONFIG, user_state
    if cmd == 'status':
        auto_state = "🟢 BẬT" if CONFIG['AUTO_SCAN'] else "🔴 TẮT"
        msg = (
            f"⚙️ <b>CẤU HÌNH HIỆN TẠI</b>\n"
            f"🤖 AUTO: Quét <b>{CONFIG['AUTO_TIME_FRAME']}h</b> | Gom >= <b>{CONFIG['AUTO_MIN_BUYS']}</b>\n"
            f"👤 THỦ CÔNG: Quét <b>{CONFIG['MANUAL_TIME_FRAME']}h</b> | Gom >= <b>{CONFIG['MANUAL_MIN_BUYS']}</b>\n"
            f"🔑 API: <b>{current_api_index + 1}/{len(API_KEYS)}</b>\n"
            f"🔄 Auto Scan Streams: <b>{auto_state}</b>\n"
            f"🌐 Ngôn ngữ: <b>{'Tiếng Việt' if CONFIG['LANGUAGE'] == 'vi' else 'English'}</b>\n\n"
            f"👉 Bấm List Đang Quét để xem chi tiết."
        )
        send_telegram_alert(msg)
    elif cmd == 'list':
        msg = f"📋 <b>DANH SÁCH ĐANG THEO DÕI</b>\n\n"
        msg += f"🤖 <b>TỰ ĐỘNG (AUTO) - {len(AUTO_COINS)}/{CONFIG['MAX_AUTO_COINS']}</b>\n"
        if not AUTO_COINS: msg += " └ (Trống)\n"
        for c in AUTO_COINS: msg += f" ├ {c['name']} - <code>{c['ca'][:4]}..{c['ca'][-4:]}</code>\n"
        msg += f"\n👤 <b>THỦ CÔNG (MANUAL) - {len(MANUAL_COINS)}</b>\n"
        if not MANUAL_COINS: msg += " └ (Trống)\n"
        for c in MANUAL_COINS: msg += f" ├ {c['name']} - <code>{c['ca'][:4]}..{c['ca'][-4:]}</code>\n"
        if SMART_WALLETS:
            msg += f"\n🐋 <b>VÍ SMART MONEY - {len(SMART_WALLETS)}</b>\n"
            for w in SMART_WALLETS: msg += f" ├ {w['name']} - <code>{w['address'][:4]}..{w['address'][-4:]}</code>\n"
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
        user_state = {'step': 'WAITING_CHAIN', 'last_time': time.time()}
        keyboard = {"inline_keyboard": [[{"text": "BSC", "callback_data": "chain_bsc"}, {"text": "ETH", "callback_data": "chain_eth"}, {"text": "BASE", "callback_data": "chain_base"}]]}
        send_telegram_alert("👇 Chọn Mạng lưới để thêm coin Thủ Công:", reply_markup=keyboard)
    elif cmd == 'del':
        user_state = {'step': 'WAITING_DEL_COIN', 'last_time': time.time()}
        send_telegram_alert("🗑 Nhập CA hoặc Tên coin muốn xóa:")
    elif cmd == 'add_wallet':
        user_state = {'step': 'WAITING_SMART_CHAIN', 'last_time': time.time()}
        keyboard = {"inline_keyboard": [[{"text": "BSC", "callback_data": "chain_bsc"}, {"text": "ETH", "callback_data": "chain_eth"}, {"text": "BASE", "callback_data": "chain_base"}]]}
        send_telegram_alert("🐋 Chọn Mạng lưới của Smart Money:", reply_markup=keyboard)
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
        # XỬ LÝ NÚT BẤM (CALLBACK QUERY)
        if "callback_query" in item:
            callback = item["callback_query"]
            chat_id = str(callback["message"]["chat"]["id"])
            data = callback["data"]
            if chat_id != TELEGRAM_CHAT_ID: return

            # Xử lý nút ngôn ngữ
            if data in ["lang_vi", "lang_en"]:
                CONFIG["LANGUAGE"] = data.split("_")[1]
                send_telegram_alert(t("lang_changed"))
                return

            # Xử lý các nút bấm trong MENU CHÍNH
            if data.startswith("menu_"):
                cmd = data.replace("menu_", "")
                execute_command(cmd)
                return

            # Xử lý nút dọn rác (Dead Coin)
            if data.startswith("dead_yes_"):
                ca_to_del = data.split("_")[2]
                AUTO_COINS[:] = [c for c in AUTO_COINS if c['ca'].lower() != ca_to_del.lower()]
                send_telegram_alert(f"✅ Đã dọn dẹp và xóa coin <code>{ca_to_del[:6]}...</code> khỏi hệ thống Auto.")
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
                send_telegram_alert(f"👉 Bạn đang cấu hình Khung giờ cho <b>{list_type}</b>\nNhập số giờ muốn quét (VD: 2, 6):")
                return
            if data in ["set_buy_auto", "set_buy_manual"]:
                list_type = "AUTO_SCAN" if data == "set_buy_auto" else "THỦ CÔNG"
                user_state['step'] = 'WAITING_BUY_VAL_' + data.split('_')[2].upper()
                user_state['last_time'] = time.time()
                send_telegram_alert(f"👉 Bạn đang cấu hình Số lệnh mua cho <b>{list_type}</b>\nNhập số lệnh tối thiểu (VD: 2, 5):")
                return

            if data.startswith("chain_") and user_state:
                selected_chain = data.split("_")[1]
                if user_state.get('step') == 'WAITING_CHAIN':
                    user_state['chain'] = selected_chain
                    user_state['step'] = 'WAITING_CA'
                    send_telegram_alert(f"✅ Chọn mạng: {selected_chain.upper()}\n📝 Nhập CA của coin:")
                elif user_state.get('step') == 'WAITING_SMART_CHAIN':
                    user_state['chain'] = selected_chain
                    user_state['step'] = 'WAITING_SMART_ADDRESS'
                    send_telegram_alert(f"✅ Chọn mạng: {selected_chain.upper()}\n📝 Dán địa chỉ Ví Cá Mập:")
            return

        # XỬ LÝ VĂN BẢN (MESSAGES)
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
                    send_telegram_alert("✅ Hợp lệ. Nhập LP Address:")
                    return
                elif user_state['step'] == 'WAITING_LP':
                    user_state['lp'] = text
                    user_state['step'] = 'WAITING_NAME'
                    send_telegram_alert("✅ Hợp lệ. Đặt tên cho coin này:")
                    return
                elif user_state['step'] == 'WAITING_NAME':
                    MANUAL_COINS.append({"name": text, "chain": user_state['chain'], "ca": user_state['ca'], "lp": user_state['lp']})
                    send_telegram_alert("🎉 <b>ĐÃ THÊM VÀO DANH SÁCH THỦ CÔNG!</b>")
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
                    send_telegram_alert("✅ Hợp lệ. Đặt tên cho Ví Cá Mập:")
                    return
                elif user_state['step'] == 'WAITING_SMART_NAME':
                    SMART_WALLETS.append({"name": text, "chain": user_state['chain'], "address": user_state['address']})
                    send_telegram_alert("🎉 <b>ĐÃ ĐƯA VÍ SMART MONEY VÀO TẦM NGẮM!</b>")
                    user_state.clear()
                    return
                
            if text.startswith('/'):
                cmd = text.replace("/", "")
                execute_command(cmd)

    except Exception: pass

# --- WALLET API: LUỒNG SMART MONEY ---
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
                chain = w['chain']
                explorer = EXPLORERS.get(chain, "etherscan.io")
                url = f"https://deep-index.moralis.io/api/v2.2/{address}/erc20/transfers?chain={chain}&limit=10"
                res = requests.get(url, headers=get_current_headers(), timeout=10)
                if res.status_code == 200:
                    for tx in res.json().get('result', []):
                        tx_hash = tx['transaction_hash']
                        if tx['to_address'].lower() == address.lower() and tx_hash not in alerted_txs:
                            alerted_txs.add(tx_hash)
                            tx_time = datetime.strptime(tx['block_timestamp'][:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
                            if tx_time > datetime.now(timezone.utc) - timedelta(hours=1):
                                token_name = tx.get('token_symbol', 'Unknown')
                                decimals = int(tx.get('token_decimals', 18))
                                amount = float(tx.get('value', 0)) / (10 ** decimals)
                                msg = f"🚨 <b>SMART MONEY MUA HÀNG!</b>\n\n👤 <b>{w['name']}</b>\n💰 Nhận: {amount:,.2f} <b>{token_name}</b>\n📝 CA: <code>{tx.get('address', '')}</code>\n🔗 <a href='https://{explorer}/tx/{tx_hash}'>Xem TX</a>"
                                send_telegram_alert(msg)
                elif res.status_code in [401, 429, 403]:
                    current_api_index = (current_api_index + 1) % len(API_KEYS)
            except Exception: pass
            time.sleep(2)
        time.sleep(120) 

# --- LOGIC BOT CHÍNH (QUÉT CÁ MẬP + AUTO CLEANUP) ---
def run_bot():
    global current_api_index, AUTO_COINS
    alerted_wallets = set()
    if not API_KEYS: return
    send_telegram_alert("🚀 <b>Siêu Bot (Bản Bảng Điều Khiển Nút Bấm) Đã Khởi Động!</b>\n👉 Hãy gõ <b>/menu</b> để mở Bảng Điều Khiển.")

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
                    send_telegram_alert(f"⏳ Lệnh hỏi xóa <b>{coin['name']}</b> đã tự hủy do quá 5 phút.\nHệ thống tự động gia hạn theo dõi thêm 24h.")
            elif now - coin.get('last_alert_at', now) > 86400:
                coin['prompt_sent'] = True
                coin['prompt_time'] = now
                keyboard = {"inline_keyboard": [
                    [{"text": "✅ Xóa Coin Này", "callback_data": f"dead_yes_{coin['ca']}"}],
                    [{"text": "❌ Giữ lại theo dõi 24h", "callback_data": f"dead_no_{coin['ca']}"}]
                ]}
                send_telegram_alert(f"🗑 <b>DỌN RÁC AUTO SCAN:</b>\n\nĐồng coin <b>{coin['name']}</b> không có cá mập nào gom sau 24h. Bạn có muốn xóa nó khỏi rổ theo dõi không?", reply_markup=keyboard)

        all_configs = [("AUTO", AUTO_COINS), ("MANUAL", MANUAL_COINS)]
        
        for list_type, coin_list in all_configs:
            time_frame = CONFIG[f"{list_type}_TIME_FRAME"]
            min_buys = CONFIG[f"{list_type}_MIN_BUYS"]
            
            for coin in list(coin_list): 
                try:
                    coin_name = coin["name"]
                    chain = coin["chain"]
                    ca = coin["ca"]
                    lp = coin["lp"]
                    explorer = EXPLORERS.get(chain, "etherscan.io")
                    
                    url = f"https://deep-index.moralis.io/api/v2.2/erc20/{ca}/transfers"
                    time_ago = datetime.now(timezone.utc) - timedelta(hours=time_frame)
                    
                    buy_counts = defaultdict(int)
                    transfer_graph = defaultdict(list) 
                    cursor = None
                    reached_time_limit = False
                    page_count = 0 

                    while not reached_time_limit and page_count < 50:
                        page_count += 1
                        params = {"chain": chain, "limit": 100}
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
                        if not data.get('result'): break

                        for tx in data['result']:
                            tx_time_str = tx['block_timestamp'][:19] 
                            tx_time = datetime.strptime(tx_time_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
                            
                            if tx_time < time_ago:
                                reached_time_limit = True
                                break 

                            sender = tx['from_address'].lower()
                            receiver = tx['to_address'].lower()
                            
                            if sender == lp.lower(): buy_counts[receiver] += 1
                            elif sender != '0x0000000000000000000000000000000000000000': transfer_graph[sender].append(receiver)
                                
                        cursor = data.get("cursor")
                        if not cursor: break
                        time.sleep(0.5) 

                    for original_buyer, count in buy_counts.items():
                        if count >= min_buys and original_buyer not in alerted_wallets:
                            path = [original_buyer]
                            current_wallet = original_buyer
                            visited = {original_buyer}
                            sold_to_lp = False
                            
                            while current_wallet in transfer_graph:
                                receivers = transfer_graph[current_wallet]
                                next_wallet = receivers[0] 
                                if next_wallet == lp.lower():
                                    sold_to_lp = True
                                    break
                                if next_wallet in visited: break 
                                path.append(next_wallet)
                                visited.add(next_wallet)
                                current_wallet = next_wallet

                            sec_info = format_security_info(ca, chain)
                            defi_info = f"📊 Giá token: {get_token_price(ca, chain)}"

                            if len(path) == 1:
                                msg = f"💎 <b>CÁ MẬP GOM KÍN ({time_frame}H) - {list_type}</b>\n\n🪙 <b>Coin:</b> {coin_name}\n💳 <code>{original_buyer}</code>\n🟢 Đã mua {count} lệnh.\n{sec_info}{defi_info}\n🔍 <a href='https://{explorer}/address/{original_buyer}'>Xem ví gom</a>"
                                send_telegram_alert(msg)
                                alerted_wallets.add(original_buyer)
                                
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
