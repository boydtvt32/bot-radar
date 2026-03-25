import requests
import time
import os
from datetime import datetime, timedelta, timezone 
from collections import defaultdict
from flask import Flask
from threading import Thread

# --- PHẦN 1: TẠO WEB SERVER ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot Radar Điều Khiển Qua Telegram đang hoạt động!"

def run_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

# --- PHẦN 2: THÔNG SỐ CỐ ĐỊNH CỦA BẠN ---
API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjM3NWFiODUxLWJkN2ItNGRjYy05OWU4LTY3YWExZTY5NjVmNyIsIm9yZ0lkIjoiNTA2NzE3IiwidXNlcklkIjoiNTIxMzgxIiwidHlwZUlkIjoiZTkzYzUwZjctOGI2ZC00ZDkyLTk4MDItMGIyNDllMTUzMzNiIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQyNTkyNjEsImV4cCI6NDkzMDAxOTI2MX0.-ERcEVFm28TLwIr5udsgMWBAvaUaHf5cf5Qd0vLzb18'
TELEGRAM_BOT_TOKEN = '8356674324:AAGS0gSxLanjRUonSwN0PluimJsyn1prTyQ'
TELEGRAM_CHAT_ID = '1976782751'

EXPLORERS = {
    "base": "basescan.org",
    "bsc": "bscscan.com",
    "eth": "etherscan.io"
}

# --- PHẦN ĐỘNG (CÓ THỂ ĐỔI QUA TELEGRAM) ---
CONFIG = {
    "TIME_FRAME": 24, # Khung giờ mặc định
    "MIN_BUYS": 2     # Số lệnh mua mặc định
}

COINS_TO_TRACK = [
    {
        "name": "Token 4", 
        "chain": "base",   
        "ca": "0x9f86dB9fc6f7c9408e8Fda3Ff8ce4e78ac7a6b07", 
        "lp": "0xCD55381a53da35Ab1D7Bc5e3fE5F76cac976FAc3"
    }
]

# --- CÁC HÀM CÔNG CỤ ---
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=data)
    except:
        pass

def check_wallet_type(wallet, chain):
    try:
        url = f"https://deep-index.moralis.io/api/v2.2/{wallet}/erc20?chain={chain}"
        headers = {"accept": "application/json", "X-API-Key": API_KEY}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            tokens = response.json()
            if len(tokens) >= 15:
                return f"🏦 Ví Sàn / Cá Mập Lớn (Chứa {len(tokens)} loại token)"
            else:
                return f"👤 Ví Cá Nhân (Chứa {len(tokens)} loại token)"
    except:
        pass
    return "Không xác định được"

# --- LẮNG NGHE LỆNH TỪ TELEGRAM ---
def listen_telegram_commands():
    global COINS_TO_TRACK, CONFIG
    last_update_id = 0
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    
    print("Bắt đầu luồng lắng nghe lệnh Telegram...", flush=True)
    while True:
        try:
            # Dùng long-polling để lấy tin nhắn ngay lập tức
            res = requests.get(url, params={"offset": last_update_id + 1, "timeout": 10}).json()
            for item in res.get("result", []):
                last_update_id = item["update_id"]
                msg = item.get("message", {}).get("text", "")
                chat_id = str(item.get("message", {}).get("chat", {}).get("id"))

                # BẢO MẬT: Chỉ nhận lệnh từ đúng Chat ID của bạn
                if chat_id == TELEGRAM_CHAT_ID and msg:
                    process_command(msg)
        except Exception:
            pass
        time.sleep(2)

def process_command(text):
    global COINS_TO_TRACK, CONFIG
    try:
        if text.startswith('/status'):
            msg = f"⚙️ <b>CẤU HÌNH HIỆN TẠI</b>\n"
            msg += f"⏱ Khung quét: <b>{CONFIG['TIME_FRAME']} giờ</b>\n"
            msg += f"🛒 Điều kiện Mua: >= <b>{CONFIG['MIN_BUYS']} lệnh</b>\n\n"
            msg += f"📋 <b>Danh sách đang theo dõi ({len(COINS_TO_TRACK)} coin):</b>\n"
            for c in COINS_TO_TRACK:
                msg += f"🔹 {c['name']} ({c['chain'].upper()})\n"
            send_telegram_alert(msg)

        elif text.startswith('/set_time'):
            val = int(text.split()[1])
            CONFIG['TIME_FRAME'] = val
            send_telegram_alert(f"✅ Đã đổi khung thời gian quét thành: <b>{val} giờ</b>")

        elif text.startswith('/set_buy'):
            val = int(text.split()[1])
            CONFIG['MIN_BUYS'] = val
            send_telegram_alert(f"✅ Đã đổi điều kiện mua tối thiểu thành: <b>{val} lệnh</b>")

        elif text.startswith('/add_coin'):
            # Cú pháp: /add_coin mạng, tên, CA, LP
            parts = text.replace("/add_coin", "").strip().split(',')
            if len(parts) == 4:
                chain = parts[0].strip().lower()
                name = parts[1].strip()
                ca = parts[2].strip()
                lp = parts[3].strip()
                COINS_TO_TRACK.append({"name": name, "chain": chain, "ca": ca, "lp": lp})
                send_telegram_alert(f"✅ Đã thêm <b>{name}</b> vào radar!")
            else:
                send_telegram_alert("❌ Sai cú pháp. Dùng:\n<code>/add_coin mạng, tên coin, CA, LP</code>\nVí dụ:\n/add_coin bsc, CAKE, 0x123..., 0xabc...")

        elif text.startswith('/del_coin'):
            name_to_del = text.replace("/del_coin", "").strip().lower()
            original_len = len(COINS_TO_TRACK)
            COINS_TO_TRACK = [c for c in COINS_TO_TRACK if c['name'].lower() != name_to_del]
            if len(COINS_TO_TRACK) < original_len:
                send_telegram_alert(f"🗑 Đã xóa coin thành công khỏi danh sách.")
            else:
                send_telegram_alert(f"❌ Không tìm thấy coin nào khớp tên đó.")

        elif text.startswith('/help'):
            help_msg = (
                "🤖 <b>BẢNG LỆNH ĐIỀU KHIỂN BOT</b>\n\n"
                "🔹 /status - Xem cấu hình & coin đang theo dõi\n"
                "🔹 /set_time 12 - Đổi khung giờ quét (VD: 12 tiếng)\n"
                "🔹 /set_buy 3 - Đổi mốc số lệnh mua (VD: gom 3 lệnh)\n"
                "🔹 /add_coin mạng, tên, CA, LP - Thêm coin mới\n"
                "🔹 /del_coin tên - Xóa coin\n"
            )
            send_telegram_alert(help_msg)
            
    except Exception:
        send_telegram_alert("❌ Lỗi cú pháp lệnh! Hãy gõ /help để xem hướng dẫn.")

# --- PHẦN 3: LOGIC BOT CHÍNH ---
def run_bot():
    headers = {"accept": "application/json", "X-API-Key": API_KEY}
    alerted_wallets = set()

    send_telegram_alert("🚀 <b>Hệ thống Đã Khởi Động</b>\nGõ /help để mở bảng điều khiển.")

    while True:
        try:
            for coin in COINS_TO_TRACK:
                coin_name = coin["name"]
                chain = coin["chain"]
                ca = coin["ca"]
                lp = coin["lp"]
                explorer = EXPLORERS.get(chain, "etherscan.io")
                
                url = f"https://deep-index.moralis.io/api/v2.2/erc20/{ca}/transfers"
                
                # Áp dụng thông số cấu hình ĐỘNG từ Telegram
                time_ago = datetime.now(timezone.utc) - timedelta(hours=CONFIG['TIME_FRAME'])
                
                buy_counts = defaultdict(int)
                transfer_graph = defaultdict(list) 
                cursor = None
                reached_time_limit = False

                while not reached_time_limit:
                    params = {"chain": chain, "limit": 100}
                    if cursor: params["cursor"] = cursor
                    
                    response = requests.get(url, params=params, headers=headers)
                    if response.status_code != 200: break
                        
                    data = response.json()
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
                    # Áp dụng điều kiện gom hàng tối thiểu từ Telegram
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
                            msg = f"💎 <b>GOM KÍN (TRỮ {CONFIG['TIME_FRAME']}H)</b>\n\n💳 {original_buyer}\n🟢 Đã mua liên tục {count} lệnh.\n🔍 <a href='https://{explorer}/address/{original_buyer}'>Xem ví</a>"
                            send_telegram_alert(msg)
                            alerted_wallets.add(original_buyer)
                        elif not sold_to_lp:
                            final_wallet = path[-1]
                            wallet_type = check_wallet_type(final_wallet, chain)
                            chain_str = " ➡ ".join([f"<code>{w[:6]}..{w[-4:]}</code>" for w in path])
                            msg = f"🕵️‍♂️ <b>TRUY VẾT DÒNG TIỀN</b>\n\n🟢 Gom: {count} lệnh.\n🔄 Đi: {chain_str}\n🎯 Đích: <code>{final_wallet}</code>\n📊 Loại đích: {wallet_type}\n🔍 <a href='https://{explorer}/address/{final_wallet}'>Xem đích</a>"
                            send_telegram_alert(msg)
                            alerted_wallets.add(original_buyer)

                time.sleep(3) # Nghỉ giữa các coin
        except:
            pass
        time.sleep(300) # Nghỉ 5 phút mỗi vòng lặp

# --- KÍCH HOẠT ĐA LUỒNG ---
if __name__ == "__main__":
    # Luồng 1: Chạy Bot Quét On-chain
    t1 = Thread(target=run_bot)
    t1.daemon = True
    t1.start()
    
    # Luồng 2: Lắng nghe lệnh Telegram 24/24
    t2 = Thread(target=listen_telegram_commands)
    t2.daemon = True
    t2.start()
    
    # Luồng 3: Web Server chống ngủ
    run_server()
