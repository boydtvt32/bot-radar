import requests
import time
import os
import json # Thư viện mới để tạo nút bấm Telegram
from datetime import datetime, timedelta, timezone 
from collections import defaultdict
from flask import Flask
from threading import Thread

# --- PHẦN 1: TẠO WEB SERVER ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot Radar Tương Tác Trực Tiếp đang hoạt động!"

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
    except:
        pass

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
    except: pass
    return "Không xác định"

# --- LẮNG NGHE & XỬ LÝ LỆNH TỪ TELEGRAM ---
def listen_telegram_commands():
    global user_state
    last_update_id = 0
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    
    print("Bắt đầu luồng lắng nghe lệnh Telegram...", flush=True)
    while True:
        try:
            # KIỂM TRA TIMEOUT 5 PHÚT (300 giây)
            if user_state and (time.time() - user_state.get('last_time', 0) > 300):
                send_telegram_alert("⏳ <b>Quá 5 phút không phản hồi!</b>\nĐã tự động hủy quá trình thêm coin.")
                user_state.clear()

            res = requests.get(url, params={"offset": last_update_id + 1, "timeout": 10}, timeout=15).json()
            for item in res.get("result", []):
                last_update_id = item["update_id"]
                process_update(item) # Chuyển nguyên kiện dữ liệu đi xử lý
        except Exception:
            pass
        time.sleep(2)

def process_update(item):
    global COINS_TO_TRACK, CONFIG, user_state
    
    # 1. NẾU NGƯỜI DÙNG BẤM NÚT (CALLBACK QUERY)
    if "callback_query" in item:
        callback = item["callback_query"]
        chat_id = str(callback["message"]["chat"]["id"])
        data = callback["data"]
        
        if chat_id == TELEGRAM_CHAT_ID and user_state and user_state.get('step') == 'WAITING_CHAIN':
            user_state['chain'] = data
            user_state['step'] = 'WAITING_CA'
            user_state['last_time'] = time.time() # Reset đồng hồ 5 phút
            send_telegram_alert(f"✅ Đã chọn mạng: <b>{data.upper()}</b>\n\n📝 Tiếp theo, mời bạn nhập <b>địa chỉ CA</b> của coin:")
        return

    # 2. NẾU NGƯỜI DÙNG NHẮN TIN NHẮN VĂN BẢN
    if "message" in item:
        chat_id = str(item["message"]["chat"]["id"])
        text = item["message"].get("text", "").strip()
        
        if chat_id != TELEGRAM_CHAT_ID or not text:
            return

        # A. NẾU ĐANG TRONG QUÁ TRÌNH THÊM COIN (CÓ TRẠNG THÁI)
        if user_state:
            if text == '/cancel':
                send_telegram_alert("🚫 Đã hủy quá trình thêm coin.")
                user_state.clear()
                return
                
            user_state['last_time'] = time.time() # Reset đồng hồ
            
            # Đang đợi nhập CA
            if user_state['step'] == 'WAITING_CA':
                if len(text) == 42 and text.startswith("0x"):
                    user_state['ca'] = text
                    user_state['step'] = 'WAITING_LP'
                    send_telegram_alert("✅ CA hợp lệ!\n\n📝 Cuối cùng, mời bạn nhập <b>địa chỉ Pool (LP)</b>:")
                else:
                    send_telegram_alert("❌ <b>CA không hợp lệ!</b>\n(Địa chỉ phải bắt đầu bằng '0x' và dài đúng 42 ký tự).\n\n👉 Mời bạn nhập lại CA:")
                return
                
            # Đang đợi nhập LP
            elif user_state['step'] == 'WAITING_LP':
                if len(text) == 42 and text.startswith("0x"):
                    lp = text
                    chain = user_state['chain']
                    ca = user_state['ca']
                    
                    # Tự động tạo tên coin ngắn gọn dựa vào CA
                    name = f"Coin_{ca[:4]}...{ca[-4:]}" 
                    
                    COINS_TO_TRACK.append({
                        "name": name, "chain": chain, "ca": ca, "lp": lp
                    })
                    send_telegram_alert(f"🎉 <b>HOÀN TẤT THÊM COIN MỚI!</b> 🎉\n\n🌐 <b>Mạng:</b> {chain.upper()}\n📝 <b>CA:</b> <code>{ca}</code>\n🏦 <b>LP:</b> <code>{lp}</code>\n\n<i>Hệ thống sẽ bắt đầu quét đồng coin này ở chu kỳ tiếp theo.</i>")
                    user_state.clear() # Xóa trạng thái, trở về bình thường
                else:
                    send_telegram_alert("❌ <b>LP không hợp lệ!</b>\n(Địa chỉ phải bắt đầu bằng '0x' và dài đúng 42 ký tự).\n\n👉 Mời bạn nhập lại địa chỉ Pool (LP):")
                return

        # B. CÁC LỆNH ĐIỀU KHIỂN BÌNH THƯỜNG
        if text.startswith('/status'):
            msg = f"⚙️ <b>CẤU HÌNH HIỆN TẠI</b>\n"
            msg += f"⏱ Khung quét: <b>{CONFIG['TIME_FRAME']} giờ</b>\n"
            msg += f"🛒 Tối thiểu: <b>{CONFIG['MIN_BUYS']} lệnh mua</b>\n\n"
            msg += f"📋 <b>Đang theo dõi ({len(COINS_TO_TRACK)} coin):</b>\n"
            for c in COINS_TO_TRACK:
                msg += f"🔹 {c['name']} ({c['chain'].upper()})\n"
            send_telegram_alert(msg)

        elif text.startswith('/set_time'):
            parts = text.split()
            if len(parts) < 2:
                send_telegram_alert("❌ Thiếu số. Gõ: `/set_time 12`")
                return
            CONFIG['TIME_FRAME'] = int(parts[1])
            send_telegram_alert(f"✅ Đã đổi khung thời gian quét thành: <b>{CONFIG['TIME_FRAME']} giờ</b>")

        elif text.startswith('/set_buy'):
            parts = text.split()
            if len(parts) < 2:
                send_telegram_alert("❌ Thiếu số. Gõ: `/set_buy 3`")
                return
            CONFIG['MIN_BUYS'] = int(parts[1])
            send_telegram_alert(f"✅ Đã đổi điều kiện mua thành: <b>{CONFIG['MIN_BUYS']} lệnh</b>")

        elif text == '/add':
            # Khởi tạo trạng thái hội thoại
            user_state = {
                'step': 'WAITING_CHAIN',
                'last_time': time.time()
            }
            # Tạo các nút bấm hiển thị ngay dưới tin nhắn
            keyboard = {
                "inline_keyboard": [
                    [
                        {"text": "🟡 BSC", "callback_data": "bsc"},
                        {"text": "🔵 ETH", "callback_data": "eth"},
                        {"text": "🔵 BASE", "callback_data": "base"}
                    ]
                ]
            }
            send_telegram_alert("👇 <b>BƯỚC 1/3:</b> Mời bạn chọn Mạng lưới (Chain):", reply_markup=keyboard)

        elif text.startswith('/del'):
            parts = text.split()
            if len(parts) < 2:
                send_telegram_alert("❌ Vui lòng nhập CA của coin muốn xóa. \nVí dụ: `/del 0x123...`")
                return
            ca_to_del = parts[1].strip().lower()
            original_len = len(COINS_TO_TRACK)
            COINS_TO_TRACK = [c for c in COINS_TO_TRACK if c['ca'].lower() != ca_to_del]
            if len(COINS_TO_TRACK) < original_len:
                send_telegram_alert(f"🗑 Đã xóa coin thành công khỏi danh sách.")
            else:
                send_telegram_alert(f"❌ Không tìm thấy coin nào có CA đó đang được theo dõi.")

        elif text.startswith('/help'):
            help_msg = (
                "🤖 <b>BẢNG LỆNH ĐIỀU KHIỂN</b>\n\n"
                "🔹 /status - Xem cấu hình hiện tại\n"
                "🔹 /add - Mở trình thêm coin tương tác\n"
                "🔹 /del [CA] - Xóa coin bằng mã CA\n"
                "🔹 /set_time [số] - Đổi khung giờ quét\n"
                "🔹 /set_buy [số] - Đổi số lệnh mua\n"
                "🔹 /cancel - Hủy bỏ tác vụ đang làm dở\n"
            )
            send_telegram_alert(help_msg)

# --- PHẦN 3: LOGIC BOT CHÍNH (Giữ nguyên cấu trúc đa luồng, cách ly lỗi) ---
def run_bot():
    headers = {"accept": "application/json", "X-API-Key": API_KEY}
    alerted_wallets = set()

    send_telegram_alert("🚀 <b>Hệ thống Đã Cập Nhật Trình Thêm Coin Mới!</b>\nGõ /add để thử ngay.")

    while True:
        if not COINS_TO_TRACK:
            time.sleep(60)
            continue
            
        for coin in list(COINS_TO_TRACK): # Dùng list() để tránh lỗi nếu đang quét thì bạn xóa coin
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

                while not reached_time_limit:
                    params = {"chain": chain, "limit": 100}
                    if cursor: params["cursor"] = cursor
                    
                    response = requests.get(url, params=params, headers=headers, timeout=10)
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
                            msg = f"💎 <b>GOM KÍN (TRỮ {CONFIG['TIME_FRAME']}H)</b>\n\n💳 <code>{original_buyer}</code>\n🟢 Đã mua liên tục {count} lệnh.\n🔍 <a href='https://{explorer}/address/{original_buyer}'>Xem ví</a>"
                            send_telegram_alert(msg)
                            alerted_wallets.add(original_buyer)
                        elif not sold_to_lp:
                            final_wallet = path[-1]
                            wallet_type = check_wallet_type(final_wallet, chain)
                            chain_str = " ➡ ".join([f"<code>{w[:6]}..{w[-4:]}</code>" for w in path])
                            msg = f"🕵️‍♂️ <b>TRUY VẾT DÒNG TIỀN</b>\n\n🟢 Gom: {count} lệnh.\n🔄 Đi: {chain_str}\n🎯 Đích: <code>{final_wallet}</code>\n📊 Phân tích: {wallet_type}\n🔍 <a href='https://{explorer}/address/{final_wallet}'>Xem đích</a>"
                            send_telegram_alert(msg)
                            alerted_wallets.add(original_buyer)

            except Exception as e:
                pass
            time.sleep(3) 
            
        time.sleep(300) 

# --- KÍCH HOẠT ĐA LUỒNG ---
if __name__ == "__main__":
    t1 = Thread(target=run_bot)
    t1.daemon = True
    t1.start()
    
    t2 = Thread(target=listen_telegram_commands)
    t2.daemon = True
    t2.start()
    
    run_server()
