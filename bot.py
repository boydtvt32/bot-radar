import requests
import time
import os
from datetime import datetime, timedelta, timezone 
from collections import defaultdict
from flask import Flask
from threading import Thread

# --- PHẦN 1: TẠO WEB SERVER GIẢ ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Radar DCA Base (Khung 24h) đang thức và hoạt động 24/7!"

def run_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

# --- PHẦN 2: THÔNG SỐ CỦA BẠN ---
API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjM3NWFiODUxLWJkN2ItNGRjYy05OWU4LTY3YWExZTY5NjVmNyIsIm9yZ0lkIjoiNTA2NzE3IiwidXNlcklkIjoiNTIxMzgxIiwidHlwZUlkIjoiZTkzYzUwZjctOGI2ZC00ZDkyLTk4MDItMGIyNDllMTUzMzNiIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQyNTkyNjEsImV4cCI6NDkzMDAxOTI2MX0.-ERcEVFm28TLwIr5udsgMWBAvaUaHf5cf5Qd0vLzb18'
CA = '0x9f86dB9fc6f7c9408e8Fda3Ff8ce4e78ac7a6b07' 
LP_ADDRESS = '0xCD55381a53da35Ab1D7Bc5e3fE5F76cac976FAc3' 
TELEGRAM_BOT_TOKEN = '8356674324:AAGS0gSxLanjRUonSwN0PluimJsyn1prTyQ'
TELEGRAM_CHAT_ID = '1976782751'

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Lỗi kết nối khi gửi Telegram:", e, flush=True)

# --- PHẦN 3: LOGIC BOT CHÍNH ---
def run_bot():
    url = f"https://deep-index.moralis.io/api/v2.2/erc20/{CA}/transfers"
    headers = {"accept": "application/json", "X-API-Key": API_KEY}
    alerted_wallets = set()

    print("🚀 Bot Radar Base (Khung 24h - Gom Thuần Túy) đã khởi động!", flush=True)
    send_telegram_alert("🚀 <b>Bot Radar Base đã cập nhật!</b>\n🔍 Chế độ: Quét ví mua >= 2 lần & KHÔNG BÁN trong 24h qua.")

    while True:
        try:
            print(f"\n[{time.strftime('%H:%M:%S')}] Đang quét lịch sử 24h...", flush=True)
            
            # Sổ cái ghi chép cả Mua và Bán
            trade_history = defaultdict(lambda: {"buy_count": 0, "sell_count": 0, "total_buy": 0.0})
            
            # Mốc thời gian 24 giờ trước
            twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
            
            cursor = None
            reached_time_limit = False

            # Vòng lặp lấy dữ liệu lật trang (để đảm bảo lấy đủ 24h dù có hàng ngàn giao dịch)
            while not reached_time_limit:
                params = {"chain": "base", "limit": 100}
                if cursor:
                    params["cursor"] = cursor
                
                response = requests.get(url, params=params, headers=headers)
                if response.status_code != 200:
                    print("Lỗi API Moralis:", response.status_code, flush=True)
                    break
                    
                data = response.json()
                
                for tx in data['result']:
                    tx_time_str = tx['block_timestamp'][:19] 
                    tx_time = datetime.strptime(tx_time_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
                    
                    # Nếu chạm đến giao dịch cũ hơn 24h -> Đánh dấu dừng vòng lặp lật trang
                    if tx_time < twenty_four_hours_ago:
                        reached_time_limit = True
                        break 

                    value = float(tx['value']) / (10 ** 18) 
                    
                    # 1. PHÁT HIỆN LỆNH MUA (Từ LP -> Ví)
                    if tx['from_address'].lower() == LP_ADDRESS.lower():
                        wallet = tx['to_address']
                        trade_history[wallet]["buy_count"] += 1
                        trade_history[wallet]["total_buy"] += value
                        
                    # 2. PHÁT HIỆN LỆNH BÁN (Từ Ví -> LP)
                    elif tx['to_address'].lower() == LP_ADDRESS.lower():
                        wallet = tx['from_address']
                        trade_history[wallet]["sell_count"] += 1
                
                # Cập nhật cursor để lấy trang tiếp theo, nếu hết trang thì dừng
                cursor = data.get("cursor")
                if not cursor:
                    break

            # Bắt đầu kiểm tra điều kiện "Diamond Hands"
            found = False
            for wallet, info in trade_history.items():
                
                # ĐIỀU KIỆN VÀNG: Mua >= 2 lần VÀ Bán == 0 lần
                if info["buy_count"] >= 2 and info["sell_count"] == 0 and wallet not in alerted_wallets:
                    found = True
                    print(f"🚨 Phát hiện cá mập gom thuần túy: {wallet}", flush=True)
                    
                    alert_msg = (
                        f"💎 <b>CÁ MẬP GOM HÀNG THUẦN TÚY</b> 💎\n\n"
                        f"⏱ <b>Khung:</b> 24h qua (Chỉ Mua, Không Bán)\n"
                        f"💳 <b>Ví:</b> <code>{wallet}</code>\n"
                        f"🟢 <b>Lệnh Mua:</b> {info['buy_count']} lệnh\n"
                        f"🔴 <b>Lệnh Bán:</b> 0 lệnh\n"
                        f"💰 <b>Đã gom:</b> {info['total_buy']:,.2f} token\n"
                        f"🔍 <a href='https://basescan.org/address/{wallet}'>Xem ví trên Basescan</a>"
                    )
                    send_telegram_alert(alert_msg)
                    alerted_wallets.add(wallet)
            
            if not found:
                print("Chưa có cá mập mới gom thuần túy (Không xả) trong 24h qua. Ngủ 5 phút...", flush=True)
                
        except Exception as e:
            print("Lỗi hệ thống Bot:", e, flush=True)
            
        time.sleep(300) 

# --- KÍCH HOẠT ---
if __name__ == "__main__":
    t = Thread(target=run_bot)
    t.daemon = True
    t.start()
    run_server()
