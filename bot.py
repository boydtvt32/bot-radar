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
    return "Bot Radar Hội Thoại Thông Minh đang hoạt động!"

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
    "MIN_BUYS": 2     
}

COINS_TO_TRACK = [
    {
        "name": "Token 4", 
        "chain": "base",   
        "ca": "0x9f86dB9fc6f7c9408e8Fda3Ff8ce4e78ac7a6b07", 
        "lp": "0xCD55381a53da35Ab1D7Bc5e3fE5F76cac976FAc3"
    }
]

# Trạng thái hội thoại đang diễn ra của người dùng
user_state = {} 

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
                return f"🏦 Sàn / Két Lớn ({len(tokens)} token)"
            return f"👤 Cá Nhân ({len(tokens)} token)"
    except Exception: 
        pass
    return "Không xác định"

# --- LẮNG NGHE LỆNH TỪ TELEGRAM ---
def listen_telegram_commands():
    global user_state
    last_update_id = 0
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    
    print("Khởi động bộ phận nghe lệnh Telegram...", flush=True)
    while True:
        try:
            # KIỂM TRA TIMEOUT 5 PHÚT (300 giây) CHO TẤT CẢ CÁC TRẠNG THÁI HỘI THOẠI
            if user_state and (time.time() - user_state.get('last_time', 0) > 300):
                send_telegram_alert("⏳ <b>Quá 5 phút không phản hồi!</b>\nĐã tự động hủy tác vụ đang làm dở.")
                user_state.clear()

            res = requests.get(url, params={"offset": last_update_id + 1, "timeout": 10}, timeout=15).json()
            for item in res.get("result", []):
                last_update_id = item["update_id"]
                process_update(item) 
        except Exception as e:
            if "Timeout" not in str(e):
                print(f"Lỗi nhẹ ở luồng Telegram: {e}", flush=True)
        time.sleep(2)

def process_update(item):
    global COINS_TO_TRACK, CONFIG, user_state
    try:
        # 1. NẾU BẤM NÚT (CALLBACK QUERY CHO LỆNH ADD)
        if "callback_query" in item:
            callback = item["callback_query"]
            chat_id = str(callback["message"]["chat"]["id"])
            data = callback["data"]
            
            if chat_id == TELEGRAM_CHAT_ID and user_state and user_state.get('step') == 'WAITING_CHAIN':
                user_state['chain'] = data
                user_state['step'] = 'WAITING_CA'
                user_state['last_time'] = time.time() 
                send_telegram_alert(f"✅ Đã chọn mạng: <b>{data.upper()}</b>\n\n📝 BƯỚC 2/4: Nhập <b>CA</b> của coin:")
            return

        # 2. NẾU NHẮN TIN NHẮN VĂN BẢN
        if "message" in item:
            chat_id = str(item["message"]["chat"]["id"])
            text = item["message"].get("text", "").strip()
            
            if chat_id != TELEGRAM_CHAT_ID or not text:
                return

            # ==========================================
            # A. ĐANG TRONG TRẠNG THÁI HỘI THOẠI TƯƠNG TÁC
            # ==========================================
            if user_state:
                if text == '/cancel':
                    send_telegram_alert("🚫 Đã hủy tác vụ đang thực hiện.")
                    user_state.clear()
                    return
                    
                user_state['last_time'] = time.time()
                
                # --- Nhóm thêm Coin ---
                if user_state['step'] == 'WAITING_CA':
                    if len(text) == 42 and text.startswith("0x"):
                        user_state['ca'] = text
                        user_state['step'] = 'WAITING_LP'
                        send_telegram_alert("✅ CA hợp lệ!\n\n📝 BƯỚC 3/4: Nhập <b>địa chỉ Pool (LP)</b>:")
                    else:
                        send_telegram_alert("❌ <b>CA không hợp lệ!</b>\nMời bạn nhập lại CA (hoặc /cancel để hủy):")
                    return
                    
                elif user_state['step'] == 'WAITING_LP':
                    if len(text) == 42 and text.startswith("0x"):
                        user_state['lp'] = text
                        user_state['step'] = 'WAITING_NAME'
                        send_telegram_alert("✅ LP hợp lệ!\n\n📝 BƯỚC 4/4: Nhập <b>Tên của đồng coin</b>:")
                    else:
                        send_telegram_alert("❌ <b>LP không hợp lệ!</b>\nMời bạn nhập lại địa chỉ Pool (LP) (hoặc /cancel để hủy):")
                    return
                    
                elif user_state['step'] == 'WAITING_NAME':
                    COINS_TO_TRACK.append({
                        "name": text, "chain": user_state['chain'], 
                        "ca": user_state['ca'], "lp": user_state['lp']
                    })
                    send_telegram_alert(f"🎉 <b>ĐÃ THÊM COIN MỚI!</b>\nBắt đầu quét ở chu kỳ tiếp theo.")
                    user_state.clear()
                    return

                # --- Nhóm Xóa Coin ---
                elif user_state['step'] == 'WAITING_DEL_COIN':
                    target = text.lower()
                    original_len = len(COINS_TO_TRACK)
                    # Lọc bỏ coin có CA hoặc Tên trùng với chữ người dùng nhập
                    COINS_TO_TRACK = [c for c in COINS_TO_TRACK if c['ca'].lower() != target and c['name'].lower() != target]
                    
                    if len(COINS_TO_TRACK) < original_len:
                        send_telegram_alert("🗑 <b>Đã xóa coin thành công khỏi radar!</b>")
                        user_state.clear()
                    else:
                        send_telegram_alert("❌ <b>Không tìm thấy coin nào!</b>\nBạn nhập sai Tên hoặc CA rồi. Mời nhập lại (hoặc gõ /cancel để hủy):")
                    return

                # --- Nhóm Đổi Số Lệnh Mua ---
                elif user_state['step'] == 'WAITING_SET_BUY':
                    try:
                        val = int(text)
                        if val <= 0:
                            send_telegram_alert("❌ Số lệnh mua phải lớn hơn 0. Mời nhập lại:")
                            return
                        CONFIG['MIN_BUYS'] = val
                        send_telegram_alert(f"✅ Đã đổi điều kiện mua thành: <b>{val} lệnh</b>")
                        user_state.clear()
                    except ValueError:
                        send_telegram_alert("❌ Vui lòng chỉ nhập số (VD: 2, 5). Mời nhập lại:")
                    return

                # --- Nhóm Đổi Khung Giờ ---
                elif user_state['step'] == 'WAITING_SET_TIME':
                    try:
                        val = int(text)
                        if val <= 0:
                            send_telegram_alert("❌ Số giờ phải lớn hơn 0. Mời nhập lại:")
                            return
                        CONFIG['TIME_FRAME'] = val
                        send_telegram_alert(f"✅ Đã đổi khung thời gian quét thành: <b>{val} giờ</b>")
                        user_state.clear()
                    except ValueError:
                        send_telegram_alert("❌ Vui lòng chỉ nhập số (VD: 6, 24). Mời nhập lại:")
                    return

            # ==========================================
            # B. CÁC LỆNH KÍCH HOẠT BAN ĐẦU
            # ==========================================
            if text == '/status':
                msg = f"⚙️ <b>CẤU HÌNH HIỆN TẠI</b>\n⏱ Khung quét: <b>{CONFIG['TIME_FRAME']} giờ</b>\n🛒 Lệnh mua: >= <b>{CONFIG['MIN_BUYS']}</b>\n\n📋 <b>Danh sách coin:</b>\n"
                for c in COINS_TO_TRACK: msg += f"🔹 {c['name']} ({c['chain'].upper()})\n"
                send_telegram_alert(msg)
                
            elif text == '/add':
                user_state = {'step': 'WAITING_CHAIN', 'last_time': time.time()}
                keyboard = {"inline_keyboard": [[{"text": "BSC", "callback_data": "bsc"}, {"text": "ETH", "callback_data": "eth"}, {"text": "BASE", "callback_data": "base"}]]}
                send_telegram_alert("👇 <b>BƯỚC 1/4:</b> Chọn Mạng lưới (Chain):", reply_markup=keyboard)
                
            elif text == '/del':
                user_state = {'step': 'WAITING_DEL_COIN', 'last_time': time.time()}
                send_telegram_alert("🗑 <b>XÓA COIN KHỎI RADAR</b>\n\n👉 Mời bạn nhập <b>CA</b> hoặc <b>Tên</b> của đồng coin muốn xóa:")
                
            elif text == '/set_buy':
                user_state = {'step': 'WAITING_SET_BUY', 'last_time': time.time()}
                send_telegram_alert("🛒 <b>CÀI ĐẶT ĐIỀU KIỆN MUA</b>\n\n👉 Mời bạn nhập số lệnh mua tối thiểu để báo động (Ví dụ: 2, 5, 10):")
                
            elif text == '/set_time':
                user_state = {'step': 'WAITING_SET_TIME', 'last_time': time.time()}
                send_telegram_alert("⏱ <b>CÀI ĐẶT KHUNG GIỜ QUÉT</b>\n\n👉 Mời bạn nhập số giờ muốn bot quét (Ví dụ: 6, 12, 24):")
                
            elif text == '/help':
                help_msg = (
                    "🤖 <b>BẢNG LỆNH ĐIỀU KHIỂN</b>\n\n"
                    "🔹 /status - Xem cấu hình hiện tại\n"
                    "🔹 /add - Thêm coin mới\n"
                    "🔹 /del - Xóa coin khỏi danh sách\n"
                    "🔹 /set_time - Cài đặt khung giờ quét\n"
                    "🔹 /set_buy - Cài đặt số lệnh mua\n"
                    "🔹 /cancel - Hủy thao tác đang làm dở\n"
                )
                send_telegram_alert(help_msg)
            elif not user_state:
                send_telegram_alert("⚠️ Lệnh không hợp lệ! Hãy gõ /help để xem danh sách lệnh.")
                
    except Exception as e:
        print(f"Lỗi xử lý lệnh Telegram: {e}", flush=True)

# --- PHẦN 3: LOGIC BOT CHÍNH ---
def run_bot():
    headers = {"accept": "application/json", "X-API-Key": API_KEY}
    alerted_wallets = set()

    send_telegram_alert("🚀 <b>Hệ Thống Đã Được Nâng Cấp Tương Tác Trực Tiếp Toàn Diện!</b>\nGõ /help để trải nghiệm.")

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

                print(f"[{time.strftime('%H:%M:%S')}] Đang quét {coin_name}...", flush=True)

                while not reached_time_limit and page_count < 50:
                    page_count += 1
                    params = {"chain": chain, "limit": 100}
                    if cursor: params["cursor"] = cursor
                    
                    response = requests.get(url, params=params, headers=headers, timeout=10)
                    
                    if response.status_code != 200:
                        if response.status_code in [429, 401, 402, 403]:
                            send_telegram_alert(f"⚠️ <b>CẢNH BÁO API MORALIS</b>\nLỗi {response.status_code} khi quét {coin_name}.")
                        break
                        
                    data = response.json()
                    
                    if not data.get('result'):
                        break

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
                                path.append("HỒ THANH KHOẢN (ĐÃ BÁN)")
                                break
                            if next_wallet in visited: break 
                            
                            path.append(next_wallet)
                            visited.add(next_wallet)
                            current_wallet = next_wallet

                        if len(path) == 1:
                            msg = f"💎 <b>GOM KÍN (TRỮ {CONFIG['TIME_FRAME']}H)</b>\n\n🪙 <b>Coin:</b> {coin_name}\n💳 <code>{original_buyer}</code>\n🟢 Đã mua {count} lệnh.\n🔍 <a href='https://{explorer}/address/{original_buyer}'>Xem ví</a>"
                            send_telegram_alert(msg)
                            alerted_wallets.add(original_buyer)
                        elif not sold_to_lp:
                            final_wallet = path[-1]
                            wallet_type = check_wallet_type(final_wallet, chain)
                            chain_str = " ➡ ".join([f"<code>{w[:6]}..{w[-4:]}</code>" for w in path])
                            msg = f"🕵️‍♂️ <b>TRUY VẾT DÒNG TIỀN</b>\n\n🪙 <b>Coin:</b> {coin_name}\n🟢 Gom: {count} lệnh.\n🔄 Đi: {chain_str}\n🎯 Đích: <code>{final_wallet}</code>\n📊 Loại: {wallet_type}\n🔍 <a href='https://{explorer}/address/{final_wallet}'>Xem đích</a>"
                            send_telegram_alert(msg)
                            alerted_wallets.add(original_buyer)

            except Exception as e:
                print(f"Lỗi: {e}", flush=True)
            
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
