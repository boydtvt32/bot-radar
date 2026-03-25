import requests
import time
import os
from collections import defaultdict
from flask import Flask
from threading import Thread

# --- PHẦN 1: TẠO WEB SERVER GIẢ ĐỂ CHỐNG NGỦ ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Radar DCA đang thức và hoạt động 24/7!"

def run_server():
    # Render tự động cấp một Port, ta cần bắt lấy nó bằng os.environ
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

# --- PHẦN 2: THÔNG SỐ CỦA BẠN ---
API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjM3NWFiODUxLWJkN2ItNGRjYy05OWU4LTY3YWExZTY5NjVmNyIsIm9yZ0lkIjoiNTA2NzE3IiwidXNlcklkIjoiNTIxMzgxIiwidHlwZUlkIjoiZTkzYzUwZjctOGI2ZC00ZDkyLTk4MDItMGIyNDllMTUzMzNiIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQyNTkyNjEsImV4cCI6NDkzMDAxOTI2MX0.-ERcEVFm28TLwIr5udsgMWBAvaUaHf5cf5Qd0vLzb18'
CA = '0x0A43fC31a73013089DF59194872Ecae4cAe14444' 
LP_ADDRESS = '0xF0a949d3D93B833C183a27Ee067165B6F2C9625e' 
TELEGRAM_BOT_TOKEN = '8356674324:AAGS0gSxLanjRUonSwN0PluimJsyn1prTyQ'
TELEGRAM_CHAT_ID = '1976782751'

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        res = requests.post(url, data=data)
        # In thẳng trạng thái phản hồi của Telegram ra màn hình (flush=True ép log hiện ngay)
        print("Trạng thái gửi Telegram:", res.text, flush=True)
    except Exception as e:
        print("Lỗi kết nối khi gửi Telegram:", e, flush=True)

# --- PHẦN 3: LOGIC BOT CHÍNH ---
def run_bot():
    url = f"https://deep-index.moralis.io/api/v2.2/erc20/{CA}/transfers"
    params = {"chain": "bsc", "limit": 100}
    headers = {"accept": "application/json", "X-API-Key": API_KEY}
    alerted_wallets = set()

    # Dòng này sẽ in ra màn hình Log của Render
    print("🚀 Bot Radar Đám Mây đã khởi động! Đang theo dõi token 4...", flush=True)
    # Dòng này gửi về Telegram
    send_telegram_alert("🚀 <b>Bot Radar Đám Mây đã khởi động!</b> Đang theo dõi token 4...")

    while True:
        try:
            print(f"\n[{time.strftime('%H:%M:%S')}] Đang quét dữ liệu mới...", flush=True)
            response = requests.get(url, params=params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                buy_history = defaultdict(lambda: {"count": 0, "total_amount": 0.0})
                
                for tx in data['result']:
                    if tx['from_address'].lower() == LP_ADDRESS.lower():
                        buyer_wallet = tx['to_address']
                        value = float(tx['value']) / (10 ** 18) 
                        buy_history[buyer_wallet]["count"] += 1
                        buy_history[buyer_wallet]["total_amount"] += value

                found = False
                for wallet, info in buy_history.items():
                    if info["count"] > 1 and wallet not in alerted_wallets:
                        found = True
                        print(f"🚨 Phát hiện cá mập: {wallet} - Đang gửi Telegram...", flush=True)
                        alert_msg = (
                            f"🚨 <b>PHÁT HIỆN CÁ MẬP DCA</b> 🚨\n\n"
                            f"💳 <b>Ví:</b> <code>{wallet}</code>\n"
                            f"🔄 <b>Tần suất:</b> {info['count']} lệnh\n"
                            f"💰 <b>Tổng gom:</b> {info['total_amount']:,.2f} token 4\n"
                            f"🔍 <a href='https://bscscan.com/address/{wallet}'>Xem trên BscScan</a>"
                        )
                        send_telegram_alert(alert_msg)
                        alerted_wallets.add(wallet)
                
                if not found:
                    print("Chưa có cá mập mới. Đang ngủ 5 phút...", flush=True)
            else:
                print("Lỗi API Moralis:", response.status_code, response.text, flush=True)
        except Exception as e:
            print("Lỗi hệ thống Bot:", e, flush=True)
            
        time.sleep(300) # Đợi 5 phút

# --- KÍCH HOẠT CHẠY SONG SONG CẢ 2 ---
if __name__ == "__main__":
    t = Thread(target=run_bot)
    t.daemon = True
    t.start()
    run_server()
