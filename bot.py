import requests
import time
import os
import json 
import traceback # Thư viện mới để in chi tiết lỗi
from datetime import datetime, timedelta, timezone 
from collections import defaultdict
from flask import Flask
from threading import Thread

# --- PHẦN 1: TẠO WEB SERVER ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot Radar Kháng Lỗi đang hoạt động!"

def run_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

# --- PHẦN 2: THÔNG SỐ CỐ ĐỊNH ---
API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjM3NWFiODUxLWJkN2ItNGRjYy05OWU4LTY3YWExZTY5NjVmNyIsIm9yZ0lkIjoiNTA2NzE3IiwidXNlcklkIjoiNTIxMzgxIiwidHlwZUlkIjoiZTkzYzUwZjctOGI2ZC00ZDkyLTk4MDItMGIyNDllMTUzMzNiIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQyNTkyNjEsImV4cCI6NDkzMDAxOTI2MX0.-ERcEVFm28TLwIr5udsgMWBAvaUaHf5cf5Qd0vLzb18'
TELEGRAM_BOT_TOKEN = '8356674324:AAGS0gSxLanjRUonSwN0PluimJsyn1prTyQ'
TELEGRAM_CHAT_ID = '1976782751'

EXPLORERS = {
    "base": "basescan.org",
    "bsc": "bscscan.com",
    "eth": "etherscan.io"
}

CONFIG = {
    "TIME_FRAME": 24, 
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
    except Exception as e: 
        print(f"Lỗi check ví: {e}", flush=True)
    return "Không xác định"

# --- LẮNG NGHE LỆNH TỪ TELEGRAM ---
def listen_telegram_commands():
    global user_state
    last_update_id = 0
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    
    print("Khởi động bộ phận nghe lệnh Telegram...", flush=True)
    while True:
        try:
            if user_state and (time.time() - user_state.get('last_time', 0) > 300):
                send_telegram_alert("⏳ <b>Quá 5 phút không phản hồi!</b>\nĐã hủy quá trình thêm coin.")
                user_state.clear()

            res = requests.get(url, params={"offset": last_update_id + 1, "timeout": 10}, timeout=15).json()
            for item in res.get("result", []):
                last_update_id = item["update_id"]
                process_update(item) 
        except Exception as e:
            # In ra thay vì bỏ qua để dễ gỡ lỗi
            if "Timeout" not in str(e):
                print(f"Lỗi nhẹ ở luồng Telegram: {e}", flush=True)
        time.sleep(2)

def process_update(item):
    global COINS_TO_TRACK, CONFIG, user_state
    try:
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

        if "message" in item:
            chat_id = str(item["message"]["chat"]["id"])
            text = item["message"].get("text", "").strip()
            
            if chat_id != TELEGRAM_CHAT_ID or not text:
                return

            if user_state:
                if text == '/cancel':
                    send_telegram_alert("🚫 Đã hủy quá trình thêm coin.")
                    user_state.clear()
                    return
                    
                user_state['last_time'] = time.time()
                
                if user_state['step'] == 'WAITING_CA':
                    if len(text) == 42 and text.startswith("0x"):
                        user_state['ca'] = text
                        user_state['step'] = 'WAITING_LP'
                        send_telegram_alert("✅ CA hợp lệ!\n\n📝 BƯỚC 3/4: Nhập <b>địa chỉ Pool (LP)</b>:")
                    else:
                        send_telegram_alert("❌ <b>CA không hợp lệ!</b>\nMời bạn nhập lại CA:")
                    return
                    
                elif user_state['step'] == 'WAITING_LP':
                    if len(text) == 42 and text.startswith("0x"):
                        user_state['lp'] = text
                        user_state['step'] = 'WAITING_NAME'
                        send_telegram_alert("✅ LP hợp lệ!\n\n📝 BƯỚC 4/4: Nhập <b>Tên của đồng coin</b>:")
                    else:
                        send_telegram_alert("❌ <b>LP không hợp lệ!</b>\nMời bạn nhập lại địa chỉ Pool (LP):")
                    return
                    
                elif user_state['step'] == 'WAITING_NAME':
                    COINS_TO_TRACK.append({
                        "name": text, "chain": user_state['chain'], 
                        "ca": user_state['ca'], "lp": user_state['lp']
                    })
                    send_telegram_alert(f"🎉 <b>ĐÃ THÊM COIN MỚI!</b>\nBắt đầu quét ở chu kỳ tiếp theo.")
                    user_state.clear()
                    return

            if text.startswith('/status'):
                msg = f"⚙️ <b>CẤU HÌNH HIỆN TẠI</b>\n⏱ Khung quét: <b>{CONFIG['TIME_FRAME']} giờ</b>\n🛒 Lệnh mua: >= <b>{CONFIG['MIN_BUYS']}</b>\n\n📋 <b>Danh sách coin:</b>\n"
                for c in COINS_TO_TRACK: msg += f"🔹 {c['name']} ({c['chain'].upper()})\n"
                send_telegram_alert(msg)
            elif text.startswith('/set_time'):
                CONFIG['TIME_FRAME'] = int(text.split()[1])
                send_telegram_alert(f"✅ Đã đổi khung quét thành: <b>{CONFIG['TIME_FRAME']} giờ</b>")
            elif text.startswith('/set_buy'):
                CONFIG['MIN_BUYS'] = int(text.split()[1])
                send_telegram_alert(f"✅ Đã đổi lệnh mua thành: <b>{CONFIG['MIN_BUYS']} lệnh</b>")
            elif text == '/add':
                user_state = {'step': 'WAITING_CHAIN', 'last_time': time.time()}
                keyboard = {"inline_keyboard": [[{"text": "BSC", "callback_data": "bsc"}, {"text": "ETH", "callback_data": "eth"}, {"text": "BASE", "callback_data": "base"}]]}
                send_telegram_alert("👇 <b>BƯỚC 1/4:</b> Chọn Mạng lưới (Chain):", reply_markup=keyboard)
            elif text.startswith('/del'):
                ca_to_del = text.split()[1].strip().lower()
                COINS_TO_TRACK = [c for c in COINS_TO_TRACK if c['ca'].lower() != ca_to_del]
                send_telegram_alert(f"🗑 Đã xóa coin khỏi danh sách.")
            elif text.startswith('/help'):
                send_telegram_alert("🤖 <b>BẢNG LỆNH</b>\n🔹 /status - Xem cấu hình\n🔹 /add - Thêm coin\n🔹 /del [CA] - Xóa coin\n🔹 /set_time [số] - Cài khung giờ\n🔹 /set_buy [số] - Cài lệnh mua\n🔹 /cancel - Hủy thêm coin")
    except Exception as e:
        print(f"Lỗi xử lý lệnh Telegram: {e}", flush=True)

# --- PHẦN 3: LOGIC BOT CHÍNH ---
def run_bot():
    headers = {"accept": "application/json", "X-API-Key": API_KEY}
    alerted_wallets = set()

    send_telegram_alert("🚀 <b>Hệ thống Đã Cập Nhật Lớp Bảo Vệ Chống Treo!</b>")

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
                
                # Biến đếm số trang API để phanh khẩn cấp
                page_count = 0 

                print(f"[{time.strftime('%H:%M:%S')}] Đang quét {coin_name}...", flush=True)

                while not reached_time_limit and page_count < 50:
                    page_count += 1
                    params = {"chain": chain, "limit": 100}
                    if cursor: params["cursor"] = cursor
                    
                    response = requests.get(url, params=params, headers=headers, timeout=10)
                    
                    # KIỂM TRA LỖI API CHẶT CHẼ
                    if response.status_code != 200:
                        print(f"❌ LỖI API ({response.status_code}) ở {coin_name}: {response.text}", flush=True)
                        if response.status_code in [429, 402, 403]:
                            send_telegram_alert(f"⚠️ <b>CẢNH BÁO API MORALIS</b>\nLỗi {response.status_code} khi quét {coin_name}. Có thể đã hết giới hạn miễn phí.")
                        break
                        
                    data = response.json()
                    
                    # Nếu mảng dữ liệu rỗng thì kết thúc
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

                if page_count >= 50:
                    print(f"⚠️ Đã chạm mức giới hạn 50 trang (5000 giao dịch) cho {coin_name} để chống kẹt.", flush=True)

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
                # IN CHI TIẾT LỖI RA MÀN HÌNH RENDER ĐỂ GỠ RỐI
                print(f"🔥 LỖI NGHIÊM TRỌNG Ở COIN {coin.get('name')}: {e}", flush=True)
                traceback.print_exc()
            
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
