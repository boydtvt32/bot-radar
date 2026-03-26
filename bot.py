import requests
import time
import os
import json 
import traceback 
from datetime import datetime, timedelta, timezone 
from collections import defaultdict
from flask import Flask, request
from threading import Thread

# --- PHẦN 1: TẠO WEB SERVER & NHẬN STREAMS API ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Siêu Bot Săn Gem Toàn Diện đang hoạt động!"

# CỔNG NHẬN DỮ LIỆU TỪ MORALIS STREAMS
@app.route('/webhook', methods=['POST'])
def moralis_webhook():
    global COINS_TO_TRACK, CONFIG
    
    # KIỂM TRA CÔNG TẮC BẬT/TẮT TÍNH NĂNG QUÉT TỰ ĐỘNG
    if not CONFIG.get('AUTO_SCAN', True):
        return "Auto scan is disabled", 200

    try:
        data = request.json
        if data and data.get('logs'):
            chain_id = data.get('chainId', '56')
            chain = "bsc" if str(chain_id) == "56" else "eth"
            
            for log in data['logs']:
                if log.get('topic0') == '0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9':
                    token0 = "0x" + log.get('topic1', '')[-40:]
                    token1 = "0x" + log.get('topic2', '')[-40:]
                    pair = "0x" + log.get('data', '')[26:66] 
                    
                    wbnb_weth = ["0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c", "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"]
                    new_token = token0 if token1.lower() in wbnb_weth else token1
                    
                    if new_token.lower() in wbnb_weth: continue 
                    
                    if any(c['ca'].lower() == new_token.lower() for c in COINS_TO_TRACK):
                        continue
                        
                    sec_info = check_token_security(new_token, chain)
                    
                    if sec_info and not sec_info['honeypot'] and sec_info['buy_tax'] <= 10 and sec_info['sell_tax'] <= 10:
                        if len(COINS_TO_TRACK) >= CONFIG['MAX_AUTO_COINS']:
                            dropped = COINS_TO_TRACK.pop(0) 
                            send_telegram_alert(f"🗑 Hệ thống tự động xóa <b>{dropped['name']}</b> để nhường chỗ cho Gem mới.")
                        
                        new_coin_obj = {
                            "name": f"AutoGem_{new_token[:4]}",
                            "chain": chain,
                            "ca": new_token,
                            "lp": pair
                        }
                        COINS_TO_TRACK.append(new_coin_obj)
                        
                        alert_msg = (
                            f"🚨 <b>HỆ THỐNG STREAMS VỪA TÓM ĐƯỢC GEM MỚI!</b> 🚨\n\n"
                            f"🌐 <b>Mạng:</b> {chain.upper()}\n"
                            f"📝 <b>CA:</b> <code>{new_token}</code>\n"
                            f"✅ <b>Kiểm định an toàn:</b> Thuế Mua {sec_info['buy_tax']}% | Bán {sec_info['sell_tax']}%\n"
                            f"🛡 Không cài mã độc Honeypot.\n\n"
                            f"<i>👉 Đã tự động đưa vào Radar theo dõi Cá mập gom hàng.</i>"
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
    "TIME_FRAME": 6,  
    "MIN_BUYS": 2,
    "LANGUAGE": "vi",
    "MAX_AUTO_COINS": 5,
    "AUTO_SCAN": True # CÔNG TẮC QUÉT TỰ ĐỘNG (Mặc định: BẬT)
}

COINS_TO_TRACK = [] 
SMART_WALLETS = [] 
user_state = {} 
current_api_index = 0 

# --- TỪ ĐIỂN ĐA NGÔN NGỮ ---
TEXTS = {
    "vi": {
        "start": "🚀 <b>Siêu Bot Auto Sniper Đã Kích Hoạt!</b>\nGõ /help để xem lệnh.",
        "timeout": "⏳ <b>Quá 5 phút không phản hồi!</b> Hủy tác vụ.",
        "choose_chain": "👇 Chọn Mạng lưới (Chain):",
        "chain_selected": "✅ Đã chọn mạng: <b>{}</b>\n📝 Nhập <b>CA</b> của coin:",
        "invalid_ca": "❌ <b>CA không hợp lệ!</b> Mời nhập lại:",
        "valid_ca": "✅ CA hợp lệ!\n📝 Nhập <b>địa chỉ Pool (LP)</b>:",
        "invalid_lp": "❌ <b>LP không hợp lệ!</b> Mời nhập lại:",
        "valid_lp": "✅ LP hợp lệ!\n📝 Nhập <b>Tên của đồng coin</b>:",
        "coin_added": "🎉 <b>ĐÃ THÊM COIN MỚI!</b>",
        "cancel": "🚫 Đã hủy tác vụ.",
        "del_prompt": "🗑 Nhập <b>CA</b> hoặc <b>Tên</b> coin muốn xóa:",
        "del_success": "🗑 <b>Đã xóa coin khỏi radar!</b>",
        "del_fail": "❌ <b>Không tìm thấy coin!</b>",
        "status_header": "⚙️ <b>CẤU HÌNH HIỆN TẠI</b>\n⏱ Quét: <b>{}h</b> | Gom: >= <b>{}</b>\n🔑 API: <b>{}/{}</b> | Giới hạn Auto: <b>{} Coin</b>\n🤖 Auto Scan Streams: <b>{}</b>\n\n📋 <b>Coin theo dõi ({}):</b>\n",
        "status_item": "🔹 {} ({})\n",
        "status_smart": "\n🐋 <b>Ví Smart Money ({}):</b>\n",
        "help": "🤖 <b>LỆNH ĐIỀU KHIỂN</b>\n🔹 /status - Xem cấu hình\n🔹 /auto_scan - Bật/Tắt quét coin tự động\n🔹 /add - Thêm coin thủ công\n🔹 /del - Xóa coin\n🔹 /add_wallet - Theo dõi Cá mập\n🔹 /add_key - Nạp API Key\n🔹 /keys - Xem kho API Key\n🔹 /cancel - Hủy",
        "invalid_cmd": "⚠️ Lệnh không hợp lệ!",
        "api_switch": "🔄 <b>ĐỔI API KEY TỰ ĐỘNG</b>: Chuyển sang <b>Key số {}</b>!",
        "api_dead": "💀 <b>BÁO ĐỘNG ĐỎ</b>: Hết Key! Nghỉ 30 phút.",
        "diamond": "💎 <b>CÁ MẬP GOM KÍN ({}H)</b>\n\n🪙 <b>Coin:</b> {}\n💳 <code>{}</code>\n🟢 Đã mua {} lệnh.\n{}\n{}\n🔍 <a href='https://{}/address/{}'>Xem ví gom hàng</a>",
        "sec_title": "🛡 <b>Bảo mật:</b>\n",
        "sec_hp": " ├ Honeypot: {}\n",
        "sec_tax": " └ Thuế: Mua {}% | Bán {}%\n",
        "defi_info": "📊 <b>Thị trường:</b>\n └ Giá token: {}\n",
        "hp_yes": "🔴 CÓ (SCAM)",
        "hp_no": "🟢 KHÔNG (An toàn)",
        "sec_error": "🛡 <b>Bảo mật:</b> ⚠️ Lỗi quét contract.\n",
        "smart_wallet_prompt": "🐋 <b>THEO DÕI VÍ SMART MONEY</b>\n👇 Chọn Mạng lưới:",
        "smart_address_prompt": "✅ Mạng: <b>{}</b>\n📝 Dán địa chỉ Ví Cá Mập:",
        "smart_name_prompt": "✅ Ví hợp lệ!\n📝 Đặt tên cho ví này:",
        "smart_added": "🎉 <b>ĐÃ THEO DÕI VÍ SMART MONEY!</b>",
        "smart_alert": "🚨 <b>SMART MONEY MUA HÀNG!</b>\n\n👤 <b>{}</b>\n💰 Nhận: {:,.2f} <b>{}</b>\n📝 CA: <code>{}</code>\n🔗 <a href='https://{}/tx/{}'>Xem TX</a>",
        "auto_on": "🟢 <b>Quét Coin Tự Động: BẬT</b>\nHệ thống sẽ tự động bắt coin mới từ Streams API.",
        "auto_off": "🔴 <b>Quét Coin Tự Động: TẮT</b>\nHệ thống sẽ bỏ qua các thông báo coin mới từ Streams.",
        "on_text": "🟢 BẬT",
        "off_text": "🔴 TẮT"
    },
    "en": {
        "start": "🚀 <b>Super Bot Auto Sniper Activated!</b>\nType /help for commands.",
        "timeout": "⏳ <b>Timeout!</b> Operation canceled.",
        "choose_chain": "👇 Select Chain:",
        "chain_selected": "✅ Chain: <b>{}</b>\n📝 Enter <b>CA</b>:",
        "invalid_ca": "❌ <b>Invalid CA!</b> Try again:",
        "valid_ca": "✅ Valid CA!\n📝 Enter <b>LP Address</b>:",
        "invalid_lp": "❌ <b>Invalid LP!</b> Try again:",
        "valid_lp": "✅ Valid LP!\n📝 Enter <b>Token Name</b>:",
        "coin_added": "🎉 <b>NEW COIN ADDED!</b>",
        "cancel": "🚫 Operation canceled.",
        "del_prompt": "🗑 Enter <b>CA</b> or <b>Name</b> to delete:",
        "del_success": "🗑 <b>Coin removed!</b>",
        "del_fail": "❌ <b>Coin not found!</b>",
        "status_header": "⚙️ <b>CURRENT CONFIG</b>\n⏱ Time: <b>{}h</b> | Min Buys: >= <b>{}</b>\n🔑 API: <b>{}/{}</b> | Auto Limit: <b>{} Coins</b>\n🤖 Auto Scan Streams: <b>{}</b>\n\n📋 <b>Tracked Coins ({}):</b>\n",
        "status_item": "🔹 {} ({})\n",
        "status_smart": "\n🐋 <b>Smart Wallets ({}):</b>\n",
        "help": "🤖 <b>COMMANDS</b>\n🔹 /status - View config\n🔹 /auto_scan - Toggle auto Streams scan\n🔹 /add - Add new coin\n🔹 /del - Delete coin\n🔹 /add_wallet - Track Whale\n🔹 /add_key - Add API Key\n🔹 /keys - View API Keys\n🔹 /cancel - Cancel",
        "invalid_cmd": "⚠️ Invalid command!",
        "api_switch": "🔄 <b>SWITCH API KEY</b>: Switched to <b>Key #{}</b>!",
        "api_dead": "💀 <b>RED ALERT</b>: All Keys exhausted! Pausing 30 mins.",
        "diamond": "💎 <b>DIAMOND HANDS ({}H)</b>\n\n🪙 <b>Coin:</b> {}\n💳 <code>{}</code>\n🟢 Bought {} times.\n{}\n{}\n🔍 <a href='https://{}/address/{}'>View Wallet</a>",
        "sec_title": "🛡 <b>Security:</b>\n",
        "sec_hp": " ├ Honeypot: {}\n",
        "sec_tax": " └ Tax: Buy {}% | Sell {}%\n",
        "defi_info": "📊 <b>Market:</b>\n └ Token Price: {}\n",
        "hp_yes": "🔴 YES (SCAM)",
        "hp_no": "🟢 NO (Safe)",
        "sec_error": "🛡 <b>Security:</b> ⚠️ Error scanning contract.\n",
        "smart_wallet_prompt": "🐋 <b>TRACK SMART MONEY</b>\n👇 Select Chain:",
        "smart_address_prompt": "✅ Chain: <b>{}</b>\n📝 Paste Wallet Address:",
        "smart_name_prompt": "✅ Valid Wallet!\n📝 Enter a Name:",
        "smart_added": "🎉 <b>SMART WALLET ADDED!</b>",
        "smart_alert": "🚨 <b>SMART MONEY BOUGHT!</b>\n\n👤 <b>{}</b>\n💰 Received: {:,.2f} <b>{}</b>\n📝 CA: <code>{}</code>\n🔗 <a href='https://{}/tx/{}'>View TX</a>",
        "auto_on": "🟢 <b>Auto Scan Streams: ON</b>",
        "auto_off": "🔴 <b>Auto Scan Streams: OFF</b>",
        "on_text": "🟢 ON",
        "off_text": "🔴 OFF"
    }
}

def t(key, *args):
    lang = CONFIG["LANGUAGE"]
    text = TEXTS[lang].get(key, key)
    if args: return text.format(*args)
    return text

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

def check_wallet_type(wallet, chain):
    return "👤 Cá Nhân/Smart Money"

def listen_telegram_commands():
    global user_state
    last_update_id = 0
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    
    while True:
        try:
            if user_state and (time.time() - user_state.get('last_time', 0) > 300):
                send_telegram_alert(t("timeout"))
                user_state.clear()

            res = requests.get(url, params={"offset": last_update_id + 1, "timeout": 10}, timeout=15).json()
            for item in res.get("result", []):
                last_update_id = item["update_id"]
                process_update(item) 
        except Exception: pass
        time.sleep(2)

def process_update(item):
    global COINS_TO_TRACK, CONFIG, user_state, API_KEYS, SMART_WALLETS
    try:
        if "callback_query" in item:
            callback = item["callback_query"]
            chat_id = str(callback["message"]["chat"]["id"])
            data = callback["data"]
            if chat_id != TELEGRAM_CHAT_ID: return

            if data.startswith("chain_") and user_state:
                selected_chain = data.split("_")[1]
                if user_state.get('step') == 'WAITING_CHAIN':
                    user_state['chain'] = selected_chain
                    user_state['step'] = 'WAITING_CA'
                    send_telegram_alert(t("chain_selected", selected_chain.upper()))
                elif user_state.get('step') == 'WAITING_SMART_CHAIN':
                    user_state['chain'] = selected_chain
                    user_state['step'] = 'WAITING_SMART_ADDRESS'
                    send_telegram_alert(t("smart_address_prompt", selected_chain.upper()))
            return

        if "message" in item:
            chat_id = str(item["message"]["chat"]["id"])
            text = item["message"].get("text", "").strip()
            if chat_id != TELEGRAM_CHAT_ID or not text: return

            if user_state:
                if text == '/cancel':
                    send_telegram_alert(t("cancel"))
                    user_state.clear()
                    return
                user_state['last_time'] = time.time()
                
                if user_state['step'] == 'WAITING_CA':
                    user_state['ca'] = text
                    user_state['step'] = 'WAITING_LP'
                    send_telegram_alert(t("valid_ca"))
                    return
                elif user_state['step'] == 'WAITING_LP':
                    user_state['lp'] = text
                    user_state['step'] = 'WAITING_NAME'
                    send_telegram_alert(t("valid_lp"))
                    return
                elif user_state['step'] == 'WAITING_NAME':
                    COINS_TO_TRACK.append({"name": text, "chain": user_state['chain'], "ca": user_state['ca'], "lp": user_state['lp']})
                    send_telegram_alert(t("coin_added"))
                    user_state.clear()
                    return
                elif user_state['step'] == 'WAITING_DEL_COIN':
                    target = text.lower()
                    original_len = len(COINS_TO_TRACK)
                    COINS_TO_TRACK = [c for c in COINS_TO_TRACK if c['ca'].lower() != target and c['name'].lower() != target]
                    if len(COINS_TO_TRACK) < original_len: send_telegram_alert(t("del_success"))
                    else: send_telegram_alert(t("del_fail"))
                    user_state.clear()
                    return
                elif user_state['step'] == 'WAITING_ADD_KEY':
                    if text not in API_KEYS: API_KEYS.append(text)
                    send_telegram_alert(f"✅ Đã thêm Key. Tổng băng đạn: {len(API_KEYS)}")
                    user_state.clear()
                    return
                elif user_state['step'] == 'WAITING_SMART_ADDRESS':
                    user_state['address'] = text
                    user_state['step'] = 'WAITING_SMART_NAME'
                    send_telegram_alert(t("smart_name_prompt"))
                    return
                elif user_state['step'] == 'WAITING_SMART_NAME':
                    SMART_WALLETS.append({"name": text, "chain": user_state['chain'], "address": user_state['address']})
                    send_telegram_alert(t("smart_added"))
                    user_state.clear()
                    return

            if text == '/status':
                total_keys = len(API_KEYS)
                auto_state = t("on_text") if CONFIG['AUTO_SCAN'] else t("off_text")
                msg = t("status_header", CONFIG['TIME_FRAME'], CONFIG['MIN_BUYS'], current_api_index + 1 if total_keys > 0 else 0, total_keys, CONFIG['MAX_AUTO_COINS'], auto_state, len(COINS_TO_TRACK))
                for c in COINS_TO_TRACK: msg += t("status_item", c['name'], c['chain'].upper())
                if SMART_WALLETS:
                    msg += t("status_smart", len(SMART_WALLETS))
                    for w in SMART_WALLETS: msg += t("status_item", w['name'], w['chain'].upper())
                send_telegram_alert(msg)
            elif text == '/auto_scan':
                CONFIG['AUTO_SCAN'] = not CONFIG.get('AUTO_SCAN', True)
                if CONFIG['AUTO_SCAN']:
                    send_telegram_alert(t("auto_on"))
                else:
                    send_telegram_alert(t("auto_off"))
            elif text == '/add':
                user_state = {'step': 'WAITING_CHAIN', 'last_time': time.time()}
                keyboard = {"inline_keyboard": [[{"text": "BSC", "callback_data": "chain_bsc"}, {"text": "ETH", "callback_data": "chain_eth"}, {"text": "BASE", "callback_data": "chain_base"}]]}
                send_telegram_alert(t("choose_chain"), reply_markup=keyboard)
            elif text == '/del':
                user_state = {'step': 'WAITING_DEL_COIN', 'last_time': time.time()}
                send_telegram_alert(t("del_prompt"))
            elif text == '/add_wallet':
                user_state = {'step': 'WAITING_SMART_CHAIN', 'last_time': time.time()}
                keyboard = {"inline_keyboard": [[{"text": "BSC", "callback_data": "chain_bsc"}, {"text": "ETH", "callback_data": "chain_eth"}, {"text": "BASE", "callback_data": "chain_base"}]]}
                send_telegram_alert(t("smart_wallet_prompt"), reply_markup=keyboard)
            elif text == '/add_key':
                user_state = {'step': 'WAITING_ADD_KEY', 'last_time': time.time()}
                send_telegram_alert("Nhập API Key mới:")
            elif text == '/keys':
                msg = f"🔑 <b>KHO CHỨA API KEYS ({len(API_KEYS)} Keys)</b>\n\n"
                for i, k in enumerate(API_KEYS):
                    is_active = "(Đang dùng 🟢)" if i == current_api_index else ""
                    msg += f"🔹 Key {i+1}: <code>{k[:10]}...{k[-10:]}</code> {is_active}\n"
                send_telegram_alert(msg)
            elif text == '/help': send_telegram_alert(t("help"))
    except Exception: pass

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
                                ca = tx.get('address', '')
                                send_telegram_alert(t("smart_alert", w['name'], amount, token_name, ca, explorer, tx_hash))
                elif res.status_code in [401, 429, 403]:
                    current_api_index = (current_api_index + 1) % len(API_KEYS)
            except Exception: pass
            time.sleep(2)
        time.sleep(120) 

def run_bot():
    global current_api_index
    alerted_wallets = set()
    if not API_KEYS: return
    send_telegram_alert(t("start"))

    while True:
        if not COINS_TO_TRACK or not API_KEYS:
            time.sleep(60)
            continue
            
        for coin in list(COINS_TO_TRACK): 
            try:
                coin_name = coin["name"]
                chain = coin["chain"]
                ca = coin["ca"]
                lp = coin["lp"]
                explorer = EXPLORERS.get(chain, "etherscan.io")
                
                url = f"https://deep-index.moralis.io/api/v2.2/erc20/{ca}/transfers"
                time_ago = datetime.now(timezone.utc) - timedelta(hours=CONFIG['TIME_FRAME'])
                
                buy_counts = defaultdict(int)
                transfer_graph = defaultdict(list) 
                cursor = None
                reached_time_limit = False
                page_count = 0 

                while not reached_time_limit and page_count < 50:
                    page_count += 1
                    params = {"chain": chain, "limit": 100}
                    if cursor: params["cursor"] = cursor
                    
                    headers = get_current_headers()
                    response = requests.get(url, params=params, headers=headers, timeout=10)
                    
                    if response.status_code != 200:
                        if response.status_code in [429, 401, 402, 403]:
                            old_index = current_api_index
                            current_api_index += 1
                            
                            if current_api_index >= len(API_KEYS):
                                current_api_index = 0 
                                send_telegram_alert(t("api_dead", len(API_KEYS)))
                                time.sleep(1800) 
                                break 
                            else:
                                send_telegram_alert(t("api_switch", old_index + 1, current_api_index + 1))
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
                    if count >= CONFIG['MIN_BUYS'] and original_buyer not in alerted_wallets:
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
                        defi_info = t("defi_info", get_token_price(ca, chain))

                        if len(path) == 1:
                            msg = t("diamond", CONFIG['TIME_FRAME'], coin_name, original_buyer, count, sec_info, defi_info, explorer, original_buyer)
                            send_telegram_alert(msg)
                            alerted_wallets.add(original_buyer)

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
