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
    return "Bot Radar Truy Vết Dòng Tiền đang hoạt động!"

def run_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

# --- PHẦN 2: THÔNG SỐ CỦA BẠN ---
API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjM3NWFiODUxLWJkN2ItNGRjYy05OWU4LTY3YWExZTY5NjVmNyIsIm9yZ0lkIjoiNTA2NzE3IiwidXNlcklkIjoiNTIxMzgxIiwidHlwZUlkIjoiZTkzYzUwZjctOGI2ZC00ZDkyLTk4MDItMGIyNDllMTUzMzNiIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQyNTkyNjEsImV4cCI6NDkzMDAxOTI2MX0.-ERcEVFm28TLwIr5udsgMWBAvaUaHf5cf5Qd0vLzb18'
TELEGRAM_BOT_TOKEN = '8356674324:AAGS0gSxLanjRUonSwN0PluimJsyn1prTyQ'
TELEGRAM_CHAT_ID = '1976782751'

EXPLORERS = {
    "base": "basescan.org",
    "bsc": "bscscan.com",
}

COINS_TO_TRACK = [
    {
        "name": "Token 4 (Base)", 
        "chain": "base",   
        "ca": "0x9f86dB9fc6f7c9408e8Fda3Ff8ce4e78ac7a6b07", 
        "lp": "0xCD55381a53da35Ab1D7Bc5e3fE5F76cac976FAc3"
    }
]

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Lỗi Telegram:", e, flush=True)

# HÀM MỚI: Kiểm tra xem ví cuối cùng có phải là ví Cá Mập/Sàn không
def check_wallet_type(wallet, chain):
    try:
        url = f"https://deep-index.moralis.io/api/v2.2/{wallet}/erc20?chain={chain}"
        headers = {"accept": "application/json", "X-API-Key": API_KEY}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            tokens = response.json()
            # Nếu ví cầm > 15 loại token khác nhau -> Khả năng cao là ví Sàn (CEX) hoặc Cá mập lớn
            if len(tokens) >= 15:
                return f"🏦 Ví Sàn / Cá Mập Lớn (Chứa {len(tokens)} loại token)"
            else:
                return f"👤 Ví Cá Nhân (Chứa {len(tokens)} loại token)"
    except:
        pass
    return "Không xác định được loại ví"

# --- PHẦN 3: LOGIC TRUY VẾT CHUỖI ---
def run_bot():
    headers = {"accept": "application/json", "X-API-Key": API_KEY}
    alerted_wallets = set() # Tránh báo cáo lại 1 ví gom đầu tiên

    print("🚀 Bot Radar Truy Vết đã khởi động!", flush=True)

    while True:
        print(f"\n[{time.strftime('%H:%M:%S')}] Đang quét và phân tích đường đi của coin...", flush=True)
        
        for coin in COINS_TO_TRACK:
            coin_name = coin["name"]
            chain = coin["chain"]
            ca = coin["ca"]
            lp = coin["lp"]
            explorer = EXPLORERS.get(chain, "etherscan.io")
            
            url = f"https://deep-index.moralis.io/api/v2.2/erc20/{ca}/transfers"
            twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
            
            buy_counts = defaultdict(int)
            # Sổ cái ghi chú: Ví này chuyển coin cho Ví nào
            transfer_graph = defaultdict(list) 
            
            cursor = None
            reached_time_limit = False

            # BƯỚC 1: Thu thập toàn bộ giao dịch trong 24h
            try:
                while not reached_time_limit:
                    params = {"chain": chain, "limit": 100}
                    if cursor:
                        params["cursor"] = cursor
                    
                    response = requests.get(url, params=params, headers=headers)
                    if response.status_code != 200:
                        break
                        
                    data = response.json()
                    for tx in data['result']:
                        tx_time_str = tx['block_timestamp'][:19] 
                        tx_time = datetime.strptime(tx_time_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
                        
                        if tx_time < twenty_four_hours_ago:
                            reached_time_limit = True
                            break 

                        sender = tx['from_address'].lower()
                        receiver = tx['to_address'].lower()
                        
                        # Ghi nhận người mua từ LP
                        if sender == lp.lower():
                            buy_counts[receiver] += 1
                        # Ghi nhận biểu đồ chuyển tiền ra ngoài (bỏ qua ví burn/mint)
                        elif sender != '0x0000000000000000000000000000000000000000':
                            transfer_graph[sender].append(receiver)
                            
                    cursor = data.get("cursor")
                    if not cursor:
                        break
                    time.sleep(0.5) 

                # BƯỚC 2: TRUY VẾT TỪNG VÍ GOM HÀNG
                for original_buyer, count in buy_counts.items():
                    if count >= 2 and original_buyer not in alerted_wallets:
                        
                        path = [original_buyer]
                        current_wallet = original_buyer
                        visited = {original_buyer} # Tránh lặp vòng tròn A->B->A
                        sold_to_lp = False
                        
                        # Lần theo dấu vết chuyển tiền
                        while current_wallet in transfer_graph:
                            receivers = transfer_graph[current_wallet]
                            # Lấy địa chỉ đầu tiên nó chuyển đến để theo dõi
                            next_wallet = receivers[0] 
                            
                            if next_wallet == lp.lower():
                                sold_to_lp = True
                                path.append("HỒ THANH KHOẢN (ĐÃ BÁN)")
                                break
                                
                            if next_wallet in visited:
                                break # Tránh kẹt vòng lặp
                                
                            path.append(next_wallet)
                            visited.add(next_wallet)
                            current_wallet = next_wallet

                        # XÂY DỰNG TIN NHẮN CẢNH BÁO
                        # Trường hợp 1: Mua xong để im, không chuyển đi đâu
                        if len(path) == 1:
                            alert_msg = (
                                f"💎 <b>CÁ MẬP GOM THUẦN TÚY (TRỮ KÍN)</b> 💎\n\n"
                                f"💳 <b>Ví:</b> <code>{original_buyer}</code>\n"
                                f"🟢 Đã mua liên tục {count} lệnh và giữ im không di chuyển.\n"
                                f"🔍 <a href='https://{explorer}/address/{original_buyer}'>Xem ví</a>"
                            )
                            send_telegram_alert(alert_msg)
                            alerted_wallets.add(original_buyer)

                        # Trường hợp 2: Chuyển đi lòng vòng và BỊ BÁN ở cuối chuỗi
                        elif sold_to_lp:
                            chain_str = " ➡ ".join([f"<code>{w[:6]}...{w[-4:]}</code>" if w.startswith("0x") else w for w in path])
                            alert_msg = (
                                f"⚠️ <b>PHÁT HIỆN TẨU TÁN & XẢ HÀNG</b> ⚠️\n\n"
                                f"🟢 <b>Khởi điểm:</b> Ví <code>{original_buyer}</code> gom {count} lệnh.\n"
                                f"🔄 <b>Đường đi:</b> {chain_str}\n"
                                f"❌ <b>Kết quả:</b> Coin đã bị xả vào Pool thanh khoản!"
                            )
                            send_telegram_alert(alert_msg)
                            alerted_wallets.add(original_buyer)

                        # Trường hợp 3: Chuyển lòng vòng và NẰM LẠI ở ví cuối cùng (Chưa bán)
                        else:
                            final_wallet = path[-1]
                            wallet_type = check_wallet_type(final_wallet, chain) # Kiểm tra xem có phải ví Sàn không
                            
                            chain_str = " ➡ ".join([f"<code>{w[:6]}...{w[-4:]}</code>" for w in path])
                            alert_msg = (
                                f"🕵️‍♂️ <b>THEO DÕI TÀI SẢN DI CHUYỂN</b> 🕵️‍♂️\n\n"
                                f"🟢 <b>Khởi điểm:</b> Ví <code>{original_buyer}</code> gom {count} lệnh.\n"
                                f"🔄 <b>Đường đi:</b> {chain_str}\n"
                                f"🎯 <b>Điểm đến cuối:</b> <code>{final_wallet}</code>\n"
                                f"📊 <b>Phân tích ví đích:</b> {wallet_type}\n"
                                f"🔍 <a href='https://{explorer}/address/{final_wallet}'>Xem ví cuối cùng</a>"
                            )
                            send_telegram_alert(alert_msg)
                            alerted_wallets.add(original_buyer)

            except Exception as e:
                print(f"     Lỗi truy vết {coin_name}:", e, flush=True)

            time.sleep(3) 

        print("Hoàn thành vòng quét phân tích chuỗi. Nghỉ 5 phút...", flush=True)
        time.sleep(300) 

# --- KÍCH HOẠT ---
if __name__ == "__main__":
    t = Thread(target=run_bot)
    t.daemon = True
    t.start()
    run_server()
