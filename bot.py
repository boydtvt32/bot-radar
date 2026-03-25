import requests
import time
import os
import json 
import traceback 
from datetime import datetime, timedelta, timezone 
from collections import defaultdict
from flask import Flask
from threading import Thread

# --- PHẦN 1: TẠO WEB SERVER ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot Radar Đa Ngôn Ngữ đang hoạt động!"

def run_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

# --- PHẦN 2: THÔNG SỐ CỐ ĐỊNH ---
API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImUzYzYyNzRhLWMxZGItNDhlYS1hMjkxLWMzZGQ0YTU0YmM0NiIsIm9yZ0lkIjoiNTA3MDI0IiwidXNlcklkIjoiNTIxNjk2IiwidHlwZUlkIjoiMGExM2FmMGEtNDU2Yi00YTgwLWE0ZjMtZjNlZTc4N2Q0N2M1IiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQ0NTYyMzEsImV4cCI6NDkzMDIxNjIzMX0.gCOXCBjaTjWSo5XskcX4jdvo5fZDptZ-VsI6NuQZwvY'
TELEGRAM_BOT_TOKEN = '8356674324:AAGS0gSxLanjRUonSwN0PluimJsyn1prTyQ'
TELEGRAM_CHAT_ID = '1976782751'

EXPLORERS = {
    "base": "basescan.org",
    "bsc": "bscscan.com",
    "eth": "etherscan.io"
}

# --- PHẦN ĐỘNG (CÓ THỂ ĐỔI QUA TELEGRAM) ---
CONFIG = {
    "TIME_FRAME": 6,  
    "MIN_BUYS": 2,
    "LANGUAGE": "vi" 
}

COINS_TO_TRACK = [
    {
        "name": "Token 4", 
        "chain": "base",   
        "ca": "0x9f86dB9fc6f7c9408e8Fda3Ff8ce4e78ac7a6b07", 
        "lp": "0xCD55381a53da35Ab1D7Bc5e3fE5F76cac976FAc3"
    }
]

user_state = {} 

# --- TỪ ĐIỂN ĐA NGÔN NGỮ ---
TEXTS = {
    "vi": {
        "start": "🚀 <b>Hệ Thống Đã Được Cập Nhật Đa Ngôn Ngữ!</b>\nGõ /help để trải nghiệm.",
        "timeout": "⏳ <b>Quá 5 phút không phản hồi!</b>\nĐã tự động hủy tác vụ đang làm dở.",
        "choose_chain": "👇 <b>BƯỚC 1/4:</b> Chọn Mạng lưới (Chain):",
        "chain_selected": "✅ Đã chọn mạng: <b>{}</b>\n\n📝 BƯỚC 2/4: Nhập <b>CA</b> của coin:",
        "invalid_ca": "❌ <b>CA không hợp lệ!</b>\nMời bạn nhập lại CA (hoặc /cancel để hủy):",
        "valid_ca": "✅ CA hợp lệ!\n\n📝 BƯỚC 3/4: Nhập <b>địa chỉ Pool (LP)</b>:",
        "invalid_lp": "❌ <b>LP không hợp lệ!</b>\nMời bạn nhập lại địa chỉ Pool (LP) (hoặc /cancel để hủy):",
        "valid_lp": "✅ LP hợp lệ!\n\n📝 BƯỚC 4/4: Nhập <b>Tên của đồng coin</b>:",
        "coin_added": "🎉 <b>ĐÃ THÊM COIN MỚI!</b>\nBắt đầu quét ở chu kỳ tiếp theo.",
        "cancel": "🚫 Đã hủy tác vụ đang thực hiện.",
        "del_prompt": "🗑 <b>XÓA COIN KHỎI RADAR</b>\n\n👉 Mời bạn nhập <b>CA</b> hoặc <b>Tên</b> của đồng coin muốn xóa:",
        "del_success": "🗑 <b>Đã xóa coin thành công khỏi radar!</b>",
        "del_fail": "❌ <b>Không tìm thấy coin nào!</b>\nBạn nhập sai Tên hoặc CA rồi. Mời nhập lại (hoặc /cancel):",
        "set_buy_prompt": "🛒 <b>CÀI ĐẶT ĐIỀU KIỆN MUA</b>\n\n👉 Nhập số lệnh mua tối thiểu (VD: 2, 5):",
        "set_buy_success": "✅ Đã đổi điều kiện mua thành: <b>{} lệnh</b>",
        "set_time_prompt": "⏱ <b>CÀI ĐẶT KHUNG GIỜ QUÉT</b>\n\n👉 Nhập số giờ muốn quét (VD: 6, 12):",
        "set_time_success": "✅ Đã đổi khung giờ quét thành: <b>{} giờ</b>",
        "invalid_num": "❌ Vui lòng nhập số lớn hơn 0. Mời nhập lại:",
        "invalid_format": "❌ Vui lòng chỉ nhập số. Mời nhập lại:",
        "status_header": "⚙️ <b>CẤU HÌNH HIỆN TẠI</b>\n⏱ Khung quét: <b>{} giờ</b>\n🛒 Lệnh mua: >= <b>{}</b>\n🌐 Ngôn ngữ: <b>Tiếng Việt</b>\n\n📋 <b>Danh sách coin:</b>\n",
        "status_item": "🔹 {} ({})\n",
        "help": "🤖 <b>BẢNG LỆNH ĐIỀU KHIỂN</b>\n\n🔹 /status - Xem cấu hình\n🔹 /add - Thêm coin mới\n🔹 /del - Xóa coin\n🔹 /set_time - Cài khung giờ\n🔹 /set_buy - Cài số lệnh mua\n🔹 /language - Đổi ngôn ngữ\n🔹 /cancel - Hủy thao tác",
        "invalid_cmd": "⚠️ Lệnh không hợp lệ! Hãy gõ /help.",
        "lang_prompt": "🌐 <b>Chọn ngôn ngữ / Select Language:</b>",
        "lang_changed": "✅ Đã chuyển ngôn ngữ sang Tiếng Việt!",
        "api_warning": "⚠️ <b>CẢNH BÁO API MORALIS</b>\nLỗi {} khi quét {}.",
        "diamond": "💎 <b>GOM KÍN (TRỮ {}H)</b>\n\n🪙 <b>Coin:</b> {}\n💳 <code>{}</code>\n🟢 Đã mua {} lệnh.\n🔍 <a href='https://{}/address/{}'>Xem ví</a>",
        "trace": "🕵️‍♂️ <b>TRUY VẾT DÒNG TIỀN</b>\n\n🪙 <b>Coin:</b> {}\n🟢 Gom: {} lệnh.\n🔄 Đi: {}\n🎯 Đích: <code>{}</code>\n📊 Loại: {}\n🔍 <a href='https://{}/address/{}'>Xem đích</a>",
        "wallet_cex": "🏦 Sàn / Két Lớn ({} token)",
        "wallet_per": "👤 Cá Nhân ({} token)",
        "wallet_unk": "Không xác định",
        "sold": "HỒ THANH KHOẢN (ĐÃ BÁN)"
    },
    "en": {
        "start": "🚀 <b>System Updated with Bilingual Support!</b>\nType /help to start.",
        "timeout": "⏳ <b>Timeout (5 minutes)!</b>\nCurrent operation automatically canceled.",
        "choose_chain": "👇 <b>STEP 1/4:</b> Select the Chain:",
        "chain_selected": "✅ Chain selected: <b>{}</b>\n\n📝 STEP 2/4: Enter the <b>CA</b>:",
        "invalid_ca": "❌ <b>Invalid CA!</b>\nPlease enter again (or /cancel):",
        "valid_ca": "✅ Valid CA!\n\n📝 STEP 3/4: Enter the <b>LP (Pool) Address</b>:",
        "invalid_lp": "❌ <b>Invalid LP!</b>\nPlease enter again (or /cancel):",
        "valid_lp": "✅ Valid LP!\n\n📝 STEP 4/4: Enter the <b>Token Name</b>:",
        "coin_added": "🎉 <b>NEW COIN ADDED!</b>\nWill start scanning in the next cycle.",
        "cancel": "🚫 Operation canceled.",
        "del_prompt": "🗑 <b>DELETE COIN</b>\n\n👉 Enter the <b>CA</b> or <b>Name</b> of the coin to delete:",
        "del_success": "🗑 <b>Coin successfully removed from radar!</b>",
        "del_fail": "❌ <b>Coin not found!</b>\nWrong Name or CA. Try again (or /cancel):",
        "set_buy_prompt": "🛒 <b>SET MINIMUM BUYS</b>\n\n👉 Enter minimum buys to trigger alert (e.g., 2, 5):",
        "set_buy_success": "✅ Min buys set to: <b>{}</b>",
        "set_time_prompt": "⏱ <b>SET TIME FRAME</b>\n\n👉 Enter scanning time frame in hours (e.g., 6, 12):",
        "set_time_success": "✅ Time frame set to: <b>{} hours</b>",
        "invalid_num": "❌ Number must be > 0. Try again:",
        "invalid_format": "❌ Please enter numbers only. Try again:",
        "status_header": "⚙️ <b>CURRENT CONFIG</b>\n⏱ Time frame: <b>{} hours</b>\n🛒 Min buys: >= <b>{}</b>\n🌐 Language: <b>English</b>\n\n📋 <b>Tracked Coins:</b>\n",
        "status_item": "🔹 {} ({})\n",
        "help": "🤖 <b>COMMAND PANEL</b>\n\n🔹 /status - View current config\n🔹 /add - Add new coin\n🔹 /del - Delete a coin\n🔹 /set_time - Set time frame\n🔹 /set_buy - Set min buys\n🔹 /language - Change language\n🔹 /cancel - Cancel operation",
        "invalid_cmd": "⚠️ Invalid command! Type /help.",
        "lang_prompt": "🌐 <b>Select Language / Chọn ngôn ngữ:</b>",
        "lang_changed": "✅ Language successfully changed to English!",
        "api_warning": "⚠️ <b>MORALIS API WARNING</b>\nError {} when scanning {}.",
        "diamond": "💎 <b>DIAMOND HANDS ({}H)</b>\n\n🪙 <b>Coin:</b> {}\n💳 <code>{}</code>\n🟢 Bought {} times.\n🔍 <a href='https://{}/address/{}'>View Wallet</a>",
        "trace": "🕵️‍♂️ <b>FUND TRACING</b>\n\n🪙 <b>Coin:</b> {}\n🟢 Buys: {} times.\n🔄 Path: {}\n🎯 Dest: <code>{}</code>\n📊 Type: {}\n🔍 <a href='https://{}/address/{}'>View Dest</a>",
        "wallet_cex": "🏦 CEX / Whale ({} tokens)",
        "wallet_per": "👤 Personal ({} tokens)",
        "wallet_unk": "Unknown",
        "sold": "LIQUIDITY POOL (SOLD)"
    }
}

# Hàm lấy câu text theo ngôn ngữ hiện tại
def t(key, *args):
    lang = CONFIG["LANGUAGE"]
    text = TEXTS[lang].get(key, key)
    if args:
        return text.format(*args)
    return text

# --- CÁC HÀM CÔNG CỤ ---
def send_telegram_alert(message, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"Lỗi gửi Telegram: {e}", flush=True)

def check_wallet_type(wallet, chain):
    try:
        url = f"https://deep-index.moralis.io/api/v2.2/{wallet}/erc20?chain={chain}"
        headers = {"accept": "application/json", "X-API-Key": API_KEY}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            tokens = response.json()
            if len(tokens) >= 15:
                return t("wallet_cex", len(tokens))
            return t("wallet_per", len(tokens))
    except Exception: pass
    return t("wallet_unk")

# --- LẮNG NGHE LỆNH TỪ TELEGRAM ---
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
        except Exception as e:
            if "Timeout" not in str(e): print(f"Lỗi: {e}", flush=True)
        time.sleep(2)

def process_update(item):
    global COINS_TO_TRACK, CONFIG, user_state
    try:
        # Xử lý nút bấm Callback
        if "callback_query" in item:
            callback = item["callback_query"]
            chat_id = str(callback["message"]["chat"]["id"])
            data = callback["data"]
            
            if chat_id != TELEGRAM_CHAT_ID: return

            # Xử lý đổi ngôn ngữ
            if data in ["lang_vi", "lang_en"]:
                CONFIG["LANGUAGE"] = data.split("_")[1]
                send_telegram_alert(t("lang_changed"))
                return
            
            # Xử lý chọn Chain khi Add Coin
            if data.startswith("chain_") and user_state and user_state.get('step') == 'WAITING_CHAIN':
                selected_chain = data.split("_")[1]
                user_state['chain'] = selected_chain
                user_state['step'] = 'WAITING_CA'
                user_state['last_time'] = time.time() 
                send_telegram_alert(t("chain_selected", selected_chain.upper()))
            return

        # Xử lý Text
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
                    if len(text) == 42 and text.startswith("0x"):
                        user_state['ca'] = text
                        user_state['step'] = 'WAITING_LP'
                        send_telegram_alert(t("valid_ca"))
                    else:
                        send_telegram_alert(t("invalid_ca"))
                    return
                    
                elif user_state['step'] == 'WAITING_LP':
                    if len(text) == 42 and text.startswith("0x"):
                        user_state['lp'] = text
                        user_state['step'] = 'WAITING_NAME'
                        send_telegram_alert(t("valid_lp"))
                    else:
                        send_telegram_alert(t("invalid_lp"))
                    return
                    
                elif user_state['step'] == 'WAITING_NAME':
                    COINS_TO_TRACK.append({
                        "name": text, "chain": user_state['chain'], 
                        "ca": user_state['ca'], "lp": user_state['lp']
                    })
                    send_telegram_alert(t("coin_added"))
                    user_state.clear()
                    return

                elif user_state['step'] == 'WAITING_DEL_COIN':
                    target = text.lower()
                    original_len = len(COINS_TO_TRACK)
                    COINS_TO_TRACK = [c for c in COINS_TO_TRACK if c['ca'].lower() != target and c['name'].lower() != target]
                    if len(COINS_TO_TRACK) < original_len:
                        send_telegram_alert(t("del_success"))
                        user_state.clear()
                    else:
                        send_telegram_alert(t("del_fail"))
                    return

                elif user_state['step'] == 'WAITING_SET_BUY':
                    try:
                        val = int(text)
                        if val <= 0:
                            send_telegram_alert(t("invalid_num"))
                            return
                        CONFIG['MIN_BUYS'] = val
                        send_telegram_alert(t("set_buy_success", val))
                        user_state.clear()
                    except ValueError:
                        send_telegram_alert(t("invalid_format"))
                    return

                elif user_state['step'] == 'WAITING_SET_TIME':
                    try:
                        val = int(text)
                        if val <= 0:
                            send_telegram_alert(t("invalid_num"))
                            return
                        CONFIG['TIME_FRAME'] = val
                        send_telegram_alert(t("set_time_success", val))
                        user_state.clear()
                    except ValueError:
                        send_telegram_alert(t("invalid_format"))
                    return

            # Các lệnh kích hoạt
            if text == '/status':
                msg = t("status_header", CONFIG['TIME_FRAME'], CONFIG['MIN_BUYS'])
                for c in COINS_TO_TRACK: msg += t("status_item", c['name'], c['chain'].upper())
                send_telegram_alert(msg)
                
            elif text == '/language':
                keyboard = {"inline_keyboard": [[{"text": "🇻🇳 Tiếng Việt", "callback_data": "lang_vi"}, {"text": "🇬🇧 English", "callback_data": "lang_en"}]]}
                send_telegram_alert(t("lang_prompt"), reply_markup=keyboard)

            elif text == '/add':
                user_state = {'step': 'WAITING_CHAIN', 'last_time': time.time()}
                keyboard = {"inline_keyboard": [[{"text": "BSC", "callback_data": "chain_bsc"}, {"text": "ETH", "callback_data": "chain_eth"}, {"text": "BASE", "callback_data": "chain_base"}]]}
                send_telegram_alert(t("choose_chain"), reply_markup=keyboard)
                
            elif text == '/del':
                user_state = {'step': 'WAITING_DEL_COIN', 'last_time': time.time()}
                send_telegram_alert(t("del_prompt"))
                
            elif text == '/set_buy':
                user_state = {'step': 'WAITING_SET_BUY', 'last_time': time.time()}
                send_telegram_alert(t("set_buy_prompt"))
                
            elif text == '/set_time':
                user_state = {'step': 'WAITING_SET_TIME', 'last_time': time.time()}
                send_telegram_alert(t("set_time_prompt"))
                
            elif text == '/help':
                send_telegram_alert(t("help"))
            elif not user_state:
                send_telegram_alert(t("invalid_cmd"))
                
    except Exception as e: print(f"Lỗi: {e}", flush=True)

# --- PHẦN 3: LOGIC BOT CHÍNH ---
def run_bot():
    headers = {"accept": "application/json", "X-API-Key": API_KEY}
    alerted_wallets = set()

    send_telegram_alert(t("start"))

    while True:
        if not COINS_TO_TRACK:
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
                    
                    response = requests.get(url, params=params, headers=headers, timeout=10)
                    
                    if response.status_code != 200:
                        if response.status_code in [429, 401, 402, 403]:
                            send_telegram_alert(t("api_warning", response.status_code, coin_name))
                        break
                        
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
                        
                        if sender == lp.lower():
                            buy_counts[receiver] += 1
                        elif sender != '0x0000000000000000000000000000000000000000':
                            transfer_graph[sender].append(receiver)
                            
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
                                path.append(t("sold"))
                                break
                            if next_wallet in visited: break 
                            
                            path.append(next_wallet)
                            visited.add(next_wallet)
                            current_wallet = next_wallet

                        if len(path) == 1:
                            msg = t("diamond", CONFIG['TIME_FRAME'], coin_name, original_buyer, count, explorer, original_buyer)
                            send_telegram_alert(msg)
                            alerted_wallets.add(original_buyer)
                        elif not sold_to_lp:
                            final_wallet = path[-1]
                            wallet_type = check_wallet_type(final_wallet, chain)
                            chain_str = " ➡ ".join([f"<code>{w[:6]}..{w[-4:]}</code>" if w.startswith("0x") else w for w in path])
                            msg = t("trace", coin_name, count, chain_str, final_wallet, wallet_type, explorer, final_wallet)
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
    
    run_server()
