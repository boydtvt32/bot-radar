import requests
import time
import os
import json
import traceback
from datetime import datetime, timedelta, timezone 
from flask import Flask, request
from threading import Thread

# =========================================================
# BSC SNIPER BOT (V32 PRO - FULL LOGS RESTORED)
# Features: Strict LP Lock >=95% & >=7 Days, Case Fix, Full Console Logs
# =========================================================

app = Flask(__name__)

@app.route('/')
def home():
    return "BSC Sniper Bot (V32 Pro - Full Logs) đang hoạt động!"

def run_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)

RAW_API_KEYS = [
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImU0Y2QxMTFlLTE3YzYtNDU2My1iOGM5LTFjZWZkMjNmMjJhYiIsIm9yZ0lkIjoiNTA3MDc2IiwidXNlcklkIjoiNTIxNzQ5IiwidHlwZUlkIjoiZDhjZmE3NTEtNTAyMC00MTZkLWJkOGItZWJlMWM3Y2Q0NGJiIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQ0ODczODMsImV4cCI6NDkzMDI0NzM4M30.EdCGoN5pzZEuiDmvbEbHvLLGtQU2D2O_gSHX0t2JKug',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjczZTU1ZWQxLTNjYzQtNGM3ZC05MTVmLThiMDc5MTQ3YjAyYiIsIm9yZ0lkIjoiNTA3MDc4IiwidXNlcklkIjoiNTIxNzUxIiwidHlwZUlkIjoiODFkY2ZiNTgtNTAxNC00NjRkLTg3ZDYtMTM0ZjQzZTVkZmRkIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQ0ODg3NTksImV4cCI6NDkzMDI0ODc1OX0.6hBFIZcOM1rVa6sUPNUZEUUEfSKanrurzqKQPbffiSI',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjVkZTJkNDIzLTY4NmItNDQ1ZS1iNjQ3LTBjNDA5Y2NhZjhiOCIsIm9yZ0lkIjoiNTA3MDc5IiwidXNlcklkIjoiNTIxNzUyIiwidHlwZUlkIjoiMGZhMWU1ZTItYTE1Ny00ODc5LTkxNzktZDA5ZmNlNGJkZjY3IiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQ0ODkxNDUsImV4cCI6NDkzMDI0OTE0NX0.iSlSkU4z_HtWHRQAPRl0H6ZcX1jBbusE9dxjGdIqNp0',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjM3NWFiODUxLWJkN2ItNGRjYy05OWU4LTY3YWExZTY5NjVmNyIsIm9yZ0lkIjoiNTA2NzE3IiwidXNlcklkIjoiNTIxMzgxIiwidHlwZUlkIjoiZTkzYzUwZjctOGI2ZC00ZDkyLTk4MDItMGIyNDllMTUzMzNiIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQyNTkyNjEsImV4cCI6NDkzMDAxOTI2MX0.-ERcEVFm28TLwIr5udsgMWBAvaUaHf5cf5Qd0vLzb18',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImUzYzYyNzRhLWMxZGItNDhlYS1hMjkxLWMzZGQ0YTU0YmM0NiIsIm9yZ0lkIjoiNTA3MDI0IiwidXNlcklkIjoiNTIxNjk2IiwidHlwZUlkIjoiMGExM2FmMGEtNDU2Yi00YTgwLWE0ZjMtZjNlZTc4N2Q0N2M1IiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQ0NTYyMzEsImV4cCI6NDkzMDIxNjIzMX0.gCOXCBjaTjWSo5XskcX4jdvo5fZDptZ-VsI6NuQZwvY',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjZhYzI0NTU0LWI4OTMtNDA5YS1hYThjLTllMjY3YzYzZGUyOCIsIm9yZ0lkIjoiNTA3MTk5IiwidXNlcklkIjoiNTIxODc2IiwidHlwZUlkIjoiNzQyY2JlMWUtZjI4My00OWU0LWE4ZTMtYjk5MTE1ODUzNDRmIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQ1NzYyMzgsImV4cCI6NDkzMDMzNjIzOH0.57uFGZ8ME6Aa6UXayEUMuY6_aWZ8-yO6ESwQ71UweDc',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjM5MzcxZGI4LTQ2ZTMtNDQyOS05MGUzLTlkZDEzNzI1YTliMSIsIm9yZ0lkIjoiNTA3MjAwIiwidXNlcklkIjoiNTIxODc3IiwidHlwZUlkIjoiZTlmMGEzMDUtZjcwZC00YjI5LTkxYzktNGZkY2Y4YjAyOTYzIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQ1NzY3NzYsImV4cCI6NDkzMDMzNjc3Nn0.yMOh0meKfi4sVg7eSNHNtGniiQ53qAk7J-r4rrz5S4g'
]
API_KEYS = list(set(RAW_API_KEYS))
TELEGRAM_BOT_TOKEN = '8526113763:AAH3wANXx126AloxzAKJQrKJAPWiQm7Kb6Q'
TELEGRAM_CHAT_ID = '1976782751'

CONFIG = {
    "MAX_AUTO_COINS": 10,     
    "MAX_MANUAL_COINS": 20,    
    "AUTO_SCAN": True,
    "MIN_LP_BNB": 1.0,       
    "NOTIFY_NEW_COIN": True  
}

MANUAL_COINS = []
AUTO_COINS = [] 
user_state = {} 
current_api_index = 0 
BLACKLIST_COINS = ["0x55d398326f99059ff775485246999027b3197955".lower()]
WBNB_CA = "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c".lower()

KNOWN_AGGREGATORS = [
    "0x8D0119F280C5562762a4928bE627a8d504505315".lower(), 
    "0x1111111254EEB25477B68fB85Ed929f73A960582".lower(), 
    "0x10ED43C718714eb63d5aA57B78B54704E256024E".lower(), 
    "0xDef1C0ded9bec7F1a1670819833240f027b25EfF".lower(), 
    "0x57A5B1812674e14D2A4d2b3F30C8fA26A281E1BF".lower()  
]

def get_current_headers():
    global current_api_index
    if not API_KEYS: return {"accept": "application/json"}
    if current_api_index >= len(API_KEYS): current_api_index = 0
    header = {"accept": "application/json", "X-API-Key": API_KEYS[current_api_index]}
    current_api_index += 1
    return header

def send_telegram_alert(message, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True}
    if reply_markup: data["reply_markup"] = json.dumps(reply_markup)
    try: requests.post(url, data=data, timeout=10)
    except: pass

def setup_telegram_commands():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setMyCommands"
    try: requests.post(url, json={"commands": [{"command": "menu", "description": "🎛 Mở Bảng Điều Khiển Bot"}]}, timeout=5)
    except: pass

def check_bsc_security(ca):
    try:
        url = f"https://api.gopluslabs.io/api/v1/token_security/56?contract_addresses={ca}"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            result = res.json().get("result", {}).get(ca.lower(), {})
            if result:
                is_hp = str(result.get("is_honeypot", "0")) == "1"
                b_tax = float(result.get("buy_tax", 0) or 0) * 100
                s_tax = float(result.get("sell_tax", 0) or 0) * 100
                
                is_lp_locked = False
                total_locked_percent = 0.0        
                total_valid_locked_percent = 0.0  
                max_days_left = 0
                is_burn_majority = False
                
                lp_holders = result.get("lp_holders", [])
                if lp_holders:
                    for h in lp_holders:
                        addr = str(h.get("address", "")).lower()
                        is_lck = str(h.get("is_locked", "0")) == "1"
                        is_burn = addr in ["0x0000000000000000000000000000000000000000", "0x000000000000000000000000000000000000dead"]
                        
                        try:
                            pct_str = str(h.get("percent", "0"))
                            pct = float(pct_str)
                            if pct > 1.0: pct = pct / 100.0 
                        except: pct = 0.0

                        if is_burn:
                            total_locked_percent += pct
                            total_valid_locked_percent += pct 
                            if pct > 0.5: is_burn_majority = True
                        elif is_lck:
                            total_locked_percent += pct
                            days_left = 0
                            lock_detail = h.get("locked_detail", [])
                            if lock_detail:
                                end_ts_str = lock_detail[0].get("end_time", "")
                                if end_ts_str:
                                    try:
                                        days_left = (int(end_ts_str) - int(time.time())) // 86400
                                    except: pass
                            
                            if days_left > max_days_left: max_days_left = days_left
                            if days_left >= 7: total_valid_locked_percent += pct

                if total_valid_locked_percent >= 0.95:
                    is_lp_locked = True
                    if is_burn_majority: lock_info = f"🔥 ĐÃ ĐỐT (Vĩnh viễn) | Đạt {total_valid_locked_percent*100:.1f}%"
                    else: lock_info = f"🟢 ĐÃ KHÓA ({max_days_left} ngày) | Đạt {total_valid_locked_percent*100:.1f}%"
                else:
                    is_lp_locked = False 
                    if total_locked_percent >= 0.95: lock_info = f"🔴 KHÓA QUÁ NGẮN (Chỉ {max_days_left} ngày) | Bỏ qua!"
                    elif total_locked_percent > 0: lock_info = f"⚠️ KHÓA GIẢ MẠO (Khóa {total_locked_percent*100:.1f}%) | Bỏ qua!"
                    else: lock_info = "🔓 MỞ (Chưa khóa)"
                
                return {"is_honeypot": is_hp, "buy_tax": b_tax, "sell_tax": s_tax, "is_lp_locked": is_lp_locked, "lock_detail": lock_info}
    except: pass
    return None

def format_bsc_security(sec):
    if not sec: return "🛡 <b>Bảo mật:</b> ⚠️ Lỗi quét.\n"
    hp_str = "🔴 CÓ (Lừa đảo)" if sec['is_honeypot'] else "🟢 Không"
    return f"🛡 <b>Bảo mật:</b> Honeypot: {hp_str} | Thuế: {sec['buy_tax']:.1f}%/{sec['sell_tax']:.1f}%\n💧 <b>Tình trạng LP:</b> {sec.get('lock_detail', 'N/A')}\n"

def get_coin_balance(wallet, ca, decimals):
    try:
        res = requests.get(f"https://deep-index.moralis.io/api/v2.2/{wallet}/erc20?chain=bsc&token_addresses={ca}", headers=get_current_headers(), timeout=5)
        if res.status_code == 200 and len(res.json()) > 0: return float(res.json()[0].get('balance', '0')) / (10**decimals)
    except: pass
    return 0.0

def get_bnb_balance(wallet):
    try:
        res = requests.get(f"https://deep-index.moralis.io/api/v2.2/{wallet}/balance?chain=bsc", headers=get_current_headers(), timeout=5)
        if res.status_code == 200: return int(res.json().get('balance', '0')) / (10**18)
    except: pass
    return 0.0

def init_coin_dict(name, ca, lp):
    return {
        "name": name, "chain": "bsc", "ca": ca.lower(), "lp": lp.lower(), 
        "time_frame": 2, "min_buys": 2, "min_bnb": 0.1, "scan_interval": 5, 
        "tx_limit": 100, "last_scan_time": 0, "last_alert_at": time.time(), "prompt_sent": False, 
        "tx_cache": [], "last_fetch_timestamp": "",
        "accumulators": {}, "alerted_wallets": {} 
    }

def process_new_coin_async(new_token, lp_address):
    global AUTO_COINS, CONFIG, MANUAL_COINS, WBNB_CA
    new_token = new_token.lower()
    lp_address = lp_address.lower()
    coin_name = f"BSC_{new_token[:4]}"
    
    try:
        res = requests.get(f"https://deep-index.moralis.io/api/v2.2/erc20/metadata?chain=bsc&addresses={new_token}", headers=get_current_headers(), timeout=5)
        if res.status_code == 200 and len(res.json()) > 0 and res.json()[0].get('symbol'): coin_name = res.json()[0].get('symbol')
    except: pass

    # 🔥 LOG HIỂN THỊ TRÊN RENDER: Check thanh khoản
    print(f"\n   => [LOC RAC] Dang kiem tra thanh khoan Pool cua {coin_name}...", flush=True)
    lp_wbnb_bal = get_coin_balance(lp_address, WBNB_CA, 18)
    
    if lp_wbnb_bal < CONFIG['MIN_LP_BNB']:
        print(f"   => 🚫 [TU CHOI] Pool qua beo bot! ({lp_wbnb_bal:.3f} BNB < Min {CONFIG['MIN_LP_BNB']} BNB). Suut!!", flush=True)
        return

    print(f"   => ✅ [DUYET] Thanh khoan tot ({lp_wbnb_bal:.3f} BNB). Dang cho check LP Lock (10 phut)...", flush=True)

    sec_info = None
    for attempt in range(40):
        sec_info = check_bsc_security(new_token)
        if sec_info and not sec_info['is_honeypot'] and sec_info['buy_tax'] < 10 and sec_info['sell_tax'] < 10 and sec_info.get('is_lp_locked'):
            print(f"   => 🔒 ĐÃ KHÓA LP HOP LE o lan check thu {attempt+1}! Chuan bi len song!", flush=True)
            break
        
        # 🔥 LOG HIỂN THỊ TRÊN RENDER: Đếm ngược chờ LP
        detail = sec_info['lock_detail'] if sec_info else "Chua co data"
        print(f"   => [GoPlus] Chua dat chuan khoa >=95% (>7 ngay). Hien tai: {detail}. Doi 15s... (Lan {attempt+1}/40)", flush=True)
        time.sleep(15) 

    is_clean = sec_info and not sec_info['is_honeypot'] and sec_info['buy_tax'] < 10 and sec_info['sell_tax'] < 10 and sec_info.get('is_lp_locked')

    if not is_clean:
        print(f"   => 🗑 [LOAI BO] Het 10 phut Dev {coin_name} van khong khoa LP hoac la Honeypot.", flush=True)

    if CONFIG.get("NOTIFY_NEW_COIN", True) and is_clean:
        msg = f"🆕 <b>SIÊU PHẨM MỚI VỪA KHÓA THANH KHOẢN!</b>\n\n🪙 Tên Coin: <b>{coin_name}</b>\n📝 CA: <code>{new_token}</code>\n🏦 Thanh khoản gốc: <b>{lp_wbnb_bal:.2f} BNB</b>\n{format_bsc_security(sec_info)}\n"
        send_telegram_alert(msg)

    if is_clean:
        if len(AUTO_COINS) >= CONFIG['MAX_AUTO_COINS']: AUTO_COINS.pop(0)
        AUTO_COINS.append(init_coin_dict(coin_name, new_token, lp_address))
        print(f"   => Da them {coin_name} vao ro AUTO quet ca map.", flush=True)

@app.route('/webhook', methods=['POST'])
def moralis_webhook():
    global AUTO_COINS, CONFIG, BLACKLIST_COINS
    if not CONFIG.get('AUTO_SCAN', True): return "Auto scan is disabled", 200
    try:
        data = request.json
        if data and data.get('confirmed'):
            for log in data.get('logs', []):
                if log.get('topic0') == '0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9':
                    t0, t1 = "0x" + log.get('topic1', '')[-40:], "0x" + log.get('topic2', '')[-40:]
                    new_token = t1.lower() if t0.lower() == WBNB_CA else t0.lower()
                    
                    if new_token in BLACKLIST_COINS: continue
                    if any(c['ca'] == new_token for c in AUTO_COINS + MANUAL_COINS): continue
                    
                    # 🔥 LOG HIỂN THỊ TRÊN RENDER: Có Webhook nổ
                    print(f"\n📥 [WEBHOOK] Bat duoc coin moi tao: {new_token}. Kiem tra an ninh...", flush=True)
                    
                    lp = "0x" + log.get('data', '')[26:66]
                    Thread(target=process_new_coin_async, args=(new_token, lp), daemon=True).start()
    except: pass
    return "OK", 200

def send_main_menu():
    notify_text = "🔔 Báo Coin Mới: BẬT" if CONFIG.get("NOTIFY_NEW_COIN", True) else "🔕 Báo Coin Mới: TẮT"
    kb = {"inline_keyboard": [
        [{"text": "📊 Xem Tổng Quan", "callback_data": "menu_status"}, {"text": "📋 Danh Sách Cấu Hình", "callback_data": "menu_list"}],
        [{"text": "📒 Xem Sổ Tay Ví Gom", "callback_data": "menu_wallet_ledger"}],
        [{"text": "⚙️ Cài Đặt Riêng Biệt (Từng Coin)", "callback_data": "menu_config_coin_list"}],
        [{"text": "🗑 Xóa Coin", "callback_data": "menu_del"}, {"text": "➕ Thêm Coin Thủ Công", "callback_data": "menu_add"}],
        [{"text": "⛔ Chặn CA (Blacklist)", "callback_data": "menu_blacklist_add"}, {"text": "👁 Xem Blacklist", "callback_data": "menu_blacklist_view"}],
        [{"text": "📦 Giới Hạn Lưu Trữ", "callback_data": "menu_set_max"}, {"text": "🏦 Cài Min Pool (BNB)", "callback_data": "menu_set_minlp"}],
        [{"text": notify_text, "callback_data": "menu_toggle_new"}, {"text": "🚫 Hủy Lệnh", "callback_data": "menu_cancel"}]
    ]}
    send_telegram_alert("🎛 <b>BSC SNIPER BOT (V32 PRO)</b>\n👉 Chọn chức năng bên dưới:", reply_markup=kb)

def send_coin_config_menu(coin):
    ca_short = coin['ca'][:10]
    msg = (f"⚙️ <b>BẢNG CẤU HÌNH CÁ NHÂN</b>\n\n"
           f"🪙 <b>{coin['name']}</b> (<code>{ca_short}...</code>)\n"
           f"⏱ Khung giờ soi: <b>{coin.get('time_frame', 2)}h</b>\n"
           f"🛒 Ví phải gom: <b>>= {coin.get('min_buys', 2)} lệnh</b>\n"
           f"🐋 Mức Tay to: <b>>= {coin.get('min_bnb', 0.1)} BNB</b>\n"
           f"⏳ Tần suất quét: <b>{coin.get('scan_interval', 5)} phút/lần</b>\n\n"
           f"👉 Chọn thông số bạn muốn thay đổi:")
    
    kb = {"inline_keyboard": [
        [{"text": f"⏱ Đổi Khung giờ ({coin.get('time_frame', 2)}h)", "callback_data": f"cfg_time_{ca_short}"}],
        [{"text": f"🛒 Đổi Số lệnh gom ({coin.get('min_buys', 2)})", "callback_data": f"cfg_buy_{ca_short}"}],
        [{"text": f"🐋 Đổi Mức Tay to ({coin.get('min_bnb', 0.1)} BNB)", "callback_data": f"cfg_bnb_{ca_short}"}],
        [{"text": f"⏳ Đổi Tần suất ({coin.get('scan_interval', 5)}p)", "callback_data": f"cfg_freq_{ca_short}"}],
        [{"text": "🔙 Quay lại Danh Sách", "callback_data": "menu_config_coin_list"}]
    ]}
    send_telegram_alert(msg, reply_markup=kb)

def execute_command(cmd):
    global CONFIG, user_state, BLACKLIST_COINS, AUTO_COINS, MANUAL_COINS
    if cmd == 'status':
        msg = (f"⚙️ <b>TỔNG QUAN HỆ THỐNG</b>\n"
               f"🤖 Sức chứa Rổ Auto: <b>{CONFIG['MAX_AUTO_COINS']}</b> coin\n"
               f"👤 Sức chứa Rổ VIP: <b>{CONFIG['MAX_MANUAL_COINS']}</b> coin\n"
               f"🏦 Min Pool đón lỏng: <b>>= {CONFIG['MIN_LP_BNB']} BNB</b>\n"
               f"🔒 Điều kiện an toàn: <b>Khóa >= 95% VÀ >= 7 Ngày</b>\n"
               f"⛔ CA cấm (Rác): <b>{len(BLACKLIST_COINS)}</b>\n"
               f"🛡 Auto-Promote: <b>BẬT</b>\n"
               f"<i>* Các thông số Soi ví đã được cài độc lập cho từng coin.</i>")
        send_telegram_alert(msg)
    elif cmd == 'list':
        msg = f"📋 <b>DANH SÁCH & CẤU HÌNH</b>\n\n🤖 <b>AUTO ({len(AUTO_COINS)}/{CONFIG['MAX_AUTO_COINS']})</b>\n"
        for c in AUTO_COINS: msg += f" ├ <b>{c['name']}</b> ({c.get('scan_interval')}p | {c.get('time_frame')}h | {c.get('min_buys')}L | {c.get('min_bnb')}B)\n"
        msg += f"\n👤 <b>THỦ CÔNG / VIP ({len(MANUAL_COINS)}/{CONFIG['MAX_MANUAL_COINS']})</b>\n"
        for c in MANUAL_COINS: msg += f" ├ <b>{c['name']}</b> ({c.get('scan_interval')}p | {c.get('time_frame')}h | {c.get('min_buys')}L | {c.get('min_bnb')}B)\n"
        send_telegram_alert(msg)
    elif cmd == 'config_coin_list':
        all_coins = AUTO_COINS + MANUAL_COINS
        if not all_coins: send_telegram_alert("⚠️ Danh sách trống!"); return
        kb = {"inline_keyboard": []}
        for c in all_coins: kb["inline_keyboard"].append([{"text": f"⚙️ Cài đặt: {c['name']}", "callback_data": f"open_cfg_{c['ca'][:10]}"}])
        send_telegram_alert("👇 Chọn đồng coin bạn muốn <b>Thay đổi Cấu hình</b>:", reply_markup=kb)
    elif cmd == 'wallet_ledger':
        kb = {"inline_keyboard": []}; found = False
        for c in AUTO_COINS + MANUAL_COINS:
            if c.get('accumulators'):
                found = True; kb["inline_keyboard"].append([{"text": f"📒 {c['name']} ({len(c['accumulators'])} ví)", "callback_data": f"w_c_{c['ca'][:10]}"}])
        if not found: send_telegram_alert("⚠️ Hiện tại chưa có cuốn sổ tay nào.")
        else: send_telegram_alert("📒 <b>SỔ TAY VÍ GOM</b>\n👇 Chọn đồng coin để xem danh sách ví:", reply_markup=kb)
    elif cmd == 'del':
        all_coins = AUTO_COINS + MANUAL_COINS
        if not all_coins: send_telegram_alert("⚠️ Danh sách trống!"); return
        kb = {"inline_keyboard": [[{"text": f"🗑 {c['name']}", "callback_data": f"delcoin_{c['ca'][:10]}"}] for c in all_coins]}
        send_telegram_alert("👇 Chọn coin muốn <b>XÓA</b>:", reply_markup=kb)
    elif cmd == 'add': user_state = {'step': 'WAITING_CA', 'last_time': time.time()}; send_telegram_alert("📝 Nhập CA BSC muốn thêm (Rổ Thủ công/VIP):")
    elif cmd == 'blacklist_add': user_state = {'step': 'WAITING_BLACKLIST_CA', 'last_time': time.time()}; send_telegram_alert("⛔ Nhập CA muốn chặn:")
    elif cmd == 'blacklist_view':
        if not BLACKLIST_COINS: send_telegram_alert("🟢 Blacklist trống.")
        else: send_telegram_alert(f"⛔ <b>BLACKLIST:</b>\n" + "\n".join([f" ├ <code>{ca}</code>" for ca in BLACKLIST_COINS]))
    elif cmd == 'toggle_new':
        CONFIG["NOTIFY_NEW_COIN"] = not CONFIG.get("NOTIFY_NEW_COIN", True)
        send_telegram_alert(f"✅ Báo Coin Mới: {'BẬT' if CONFIG['NOTIFY_NEW_COIN'] else 'TẮT'}")
    elif cmd == 'set_max':
        kb = {"inline_keyboard": [[{"text": "🤖 Rổ Auto", "callback_data": "set_max_auto"}, {"text": "👤 Rổ Thủ Công", "callback_data": "set_max_manual"}]]}
        send_telegram_alert(f"Cài sức chứa cho rổ nào?", reply_markup=kb)
    elif cmd == 'set_minlp': user_state = {'step': 'WAITING_MINLP_VAL', 'last_time': time.time()}; send_telegram_alert("🏦 Nhập số BNB Min Pool (Lọc Dev nghèo):")
    elif cmd == 'cancel': user_state.clear(); send_telegram_alert("🚫 Đã hủy thao tác.")

def process_update(item):
    global AUTO_COINS, MANUAL_COINS, CONFIG, user_state, BLACKLIST_COINS
    try:
        if user_state and time.time() - user_state.get('last_time', time.time()) > 300: user_state.clear()
        if "callback_query" in item:
            data = item["callback_query"]["data"]
            if data.startswith("menu_"): execute_command(data.replace("menu_", "")); return
            
            all_c = AUTO_COINS + MANUAL_COINS
            
            if data.startswith("open_cfg_"):
                ca_short = data.split("_")[2]
                coin = next((c for c in all_c if c['ca'].lower().startswith(ca_short.lower())), None)
                if coin: send_coin_config_menu(coin)
                return
            
            if data.startswith("cfg_"): 
                parts = data.split("_")
                cfg_type, ca_short = parts[1], parts[2]
                coin = next((c for c in all_c if c['ca'].lower().startswith(ca_short.lower())), None)
                if not coin: return
                user_state = {'step': f"WAITING_CFG_{cfg_type.upper()}", 'target_ca': coin['ca'], 'last_time': time.time()}
                if cfg_type == "time": send_telegram_alert(f"🕒 Đang cấu hình: {coin['name']}\n👉 Nhập <b>Khung giờ soi</b> (VD: 2):")
                elif cfg_type == "buy": send_telegram_alert(f"🛒 Đang cấu hình: {coin['name']}\n👉 Nhập <b>Số lệnh gom</b> (VD: 2):")
                elif cfg_type == "bnb": send_telegram_alert(f"🐋 Đang cấu hình: {coin['name']}\n👉 Nhập <b>Số BNB tối thiểu</b> (VD: 0.1):")
                elif cfg_type == "freq": send_telegram_alert(f"⏳ Đang cấu hình: {coin['name']}\n👉 Nhập <b>Tần suất quét</b> (VD: 5):")
                return

            if data.startswith("w_c_"):
                ca_short = data.split("_")[2]
                coin = next((c for c in all_c if c['ca'].lower().startswith(ca_short.lower())), None)
                if not coin or not coin.get('accumulators'): return
                kb = {"inline_keyboard": []}
                for w, buys in coin['accumulators'].items():
                    kb["inline_keyboard"].append([{"text": f"💳 {w[:6]}... ({len(buys)} lệnh)", "callback_data": f"w_w_{ca_short}_{w}"}])
                send_telegram_alert(f"📒 <b>SỔ TAY COIN: {coin['name']}</b>\n👇 Chọn 1 ví để check Info & Dòng tiền:", reply_markup=kb)
                return

            if data.startswith("w_w_"): 
                parts = data.split("_")
                ca_short, wallet = parts[2], parts[3] if len(parts) == 4 else parts[2]
                coin = next((c for c in all_c if c['ca'].lower().startswith(ca_short.lower())), None)
                if not coin: send_telegram_alert("⚠️ Dữ liệu coin đã bị xóa (Hoặc bot vừa khởi động lại)."); return
                
                bnb_bal = get_bnb_balance(wallet)
                token_decimals = 18 
                try:
                    res = requests.get(f"https://deep-index.moralis.io/api/v2.2/erc20/{coin['ca']}/price?chain=bsc", headers=get_current_headers(), timeout=5)
                    if res.status_code == 200: token_decimals = int(res.json().get('tokenDecimals', 18))
                except: pass
                token_bal = get_coin_balance(wallet, coin['ca'], token_decimals)
                
                buys_list = coin.get('accumulators', {}).get(wallet, [])
                last_action, dest_wallet = "Chưa rõ", None
                
                sorted_txs = sorted(coin.get('tx_cache', []), key=lambda x: x.get('block_timestamp', ''))
                for tx in sorted_txs:
                    s, r = tx.get('from_address', '').lower(), tx.get('to_address', '').lower()
                    if s == wallet:
                        if r == coin['lp']: last_action = "🔴 ĐÃ XẢ HÀNG (Bán lại vào Pool)"
                        else: last_action = "➡️ ĐÃ CHUYỂN TOKEN (Tẩu tán)"; dest_wallet = r
                    elif r == wallet:
                        last_action = "🟢 MUA / NHẬN THÊM TOKEN"; dest_wallet = None 
                
                msg = (f"🔍 <b>HỒ SƠ VÍ GOM:</b>\n💳 <code>{wallet}</code>\n\n"
                       f"🪙 <b>Coin:</b> {coin['name']}\n"
                       f"├ Dư (Gas): <b>{bnb_bal:.4f} BNB</b>\n"
                       f"├ Đang Hold: <b>{token_bal:,.2f} {coin['name']}</b>\n"
                       f"├ Số lệnh gom: <b>{len(buys_list)} lệnh</b>\n"
                       f"└ Action cuối: <b>{last_action}</b>\n")
                
                if dest_wallet:
                    msg += f"\n🚨 <b>Phát hiện Chuyển Token đến:</b>\n👉 <code>{dest_wallet}</code>"
                    kb = {"inline_keyboard": [[{"text": "🔍 Truy vết tiếp Ví nhận", "callback_data": f"w_w_{ca_short}_{dest_wallet}"}], [{"text": "🔙 Quay lại Sổ tay", "callback_data": f"w_c_{ca_short}"}]]}
                else: kb = {"inline_keyboard": [[{"text": "🔙 Quay lại Sổ tay", "callback_data": f"w_c_{ca_short}"}]]}
                send_telegram_alert(msg, reply_markup=kb)
                return

            if data.startswith("delcoin_"):
                ca_short = data.split("_")[1]
                coin = next((c for c in all_c if c['ca'].lower().startswith(ca_short.lower())), None)
                if coin:
                    user_state = {'step': 'WAITING_DEL_CONFIRM', 'last_time': time.time(), 'target_ca': coin['ca']}
                    send_telegram_alert(f"❓ Xóa coin <b>{coin['name']}</b>?", reply_markup={"inline_keyboard": [[{"text": "✅ Xóa", "callback_data": f"confirmdel_{coin['ca'][:10]}"}, {"text": "❌ Tôi nhầm", "callback_data": "menu_del"}]]})
                return
            if data.startswith("confirmdel_"):
                if not user_state or user_state.get('step') != 'WAITING_DEL_CONFIRM': return
                ca_short = data.split("_")[1]
                MANUAL_COINS[:] = [c for c in MANUAL_COINS if not c['ca'].lower().startswith(ca_short.lower())]
                AUTO_COINS[:] = [c for c in AUTO_COINS if not c['ca'].lower().startswith(ca_short.lower())]
                send_telegram_alert("🗑 Đã xóa!"); user_state.clear(); return

            if data in ["set_max_auto", "set_max_manual"]:
                lst = "AUTO" if "auto" in data else "MANUAL"
                user_state = {'step': f"WAITING_MAX_VAL_{lst}", 'last_time': time.time()}
                send_telegram_alert(f"📦 Nhập số lượng coin tối đa cho rổ {lst}:")
                return

        if "message" in item:
            text = item["message"].get("text", "").strip()
            if not text: return
            if text in ['/menu', '/start']: send_main_menu()
            elif user_state:
                if text == '/cancel': execute_command('cancel'); return
                step = user_state.get('step')
                target_ca = user_state.get('target_ca')
                
                if step and step.startswith("WAITING_CFG_") and target_ca:
                    try:
                        val = float(text)
                        for c in AUTO_COINS + MANUAL_COINS:
                            if c['ca'] == target_ca:
                                if "TIME" in step: c['time_frame'] = int(val)
                                elif "BUY" in step: c['min_buys'] = int(val)
                                elif "BNB" in step: c['min_bnb'] = val
                                elif "FREQ" in step: c['scan_interval'] = int(val)
                                send_telegram_alert(f"✅ Đã lưu cấu hình mới thành công!")
                                send_coin_config_menu(c) 
                                break
                        user_state.clear()
                    except: send_telegram_alert("❌ Vui lòng nhập số hợp lệ!")
                    return

                if step == 'WAITING_CA':
                    if text.lower() in BLACKLIST_COINS: send_telegram_alert("🚫 CA nằm trong Blacklist."); user_state.clear(); return
                    user_state['ca'] = text.lower(); user_state['step'] = 'WAITING_LP'; user_state['last_time'] = time.time(); send_telegram_alert("✅ Nhập tiếp địa chỉ LP:")
                elif step == 'WAITING_LP':
                    ca, lp = user_state['ca'], text.lower()
                    coin_name = f"BSC_{ca[:4]}" 
                    try:
                        res = requests.get(f"https://deep-index.moralis.io/api/v2.2/erc20/metadata?chain=bsc&addresses={ca}", headers=get_current_headers(), timeout=5)
                        if res.status_code == 200 and len(res.json()) > 0: coin_name = res.json()[0].get('symbol')
                    except: pass
                    if len(MANUAL_COINS) >= CONFIG.get('MAX_MANUAL_COINS', 20): MANUAL_COINS.pop(0)
                    MANUAL_COINS.append(init_coin_dict(coin_name, ca, lp))
                    send_telegram_alert(f"🎉 Đã thêm vào rổ Thủ Công/VIP! (Mặc định: Soi 2h, Gom 2, Min 0.1 BNB, Quét 5p)"); user_state.clear()
                
                elif step == 'WAITING_BLACKLIST_CA':
                    if text.lower() not in BLACKLIST_COINS:
                        BLACKLIST_COINS.append(text.lower())
                        MANUAL_COINS[:] = [c for c in MANUAL_COINS if c['ca'].lower() != text.lower()]
                        AUTO_COINS[:] = [c for c in AUTO_COINS if c['ca'].lower() != text.lower()]
                        send_telegram_alert(f"✅ Đã chặn vĩnh viễn <code>{text.lower()}</code>")
                    user_state.clear()
                elif step == 'WAITING_MINLP_VAL':
                    try: CONFIG['MIN_LP_BNB'] = float(text); send_telegram_alert(f"🏦 Lọc Pool Dev nghèo: <b>Min {text} BNB</b>."); user_state.clear()
                    except: pass
                elif step.startswith('WAITING_MAX_VAL_'):
                    try: 
                        lst_target = step.split('_')[3]
                        CONFIG[f"MAX_{lst_target}_COINS"] = int(text)
                        send_telegram_alert(f"✅ Đã lưu giới hạn rổ {lst_target} = {text} coin."); user_state.clear()
                    except: pass
    except: pass

def listen_telegram_commands():
    setup_telegram_commands()
    last_update_id = 0
    while True:
        try:
            res = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates", params={"offset": last_update_id + 1, "timeout": 10}).json()
            for item in res.get("result", []):
                last_update_id = item["update_id"]; process_update(item) 
        except: pass
        time.sleep(2)

def run_bot():
    try:
        print("--- LUONG QUET V32 PRO DA KHOI DONG ---", flush=True)
        send_telegram_alert("🚀 <b>Bot Săn Meme V32 Pro đã sẵn sàng!</b>\n🛡 Kích hoạt bộ lọc thép: Khóa >= 95% VÀ Thời gian >= 7 Ngày.")
        while True:
            now = time.time()
            for list_type, coin_list in [("AUTO", AUTO_COINS), ("MANUAL", MANUAL_COINS)]:
                for coin in list(coin_list):
                    try:
                        time_frame = coin.get('time_frame', 2)
                        min_buys = coin.get('min_buys', 2)
                        min_bnb = coin.get('min_bnb', 0.1)
                        scan_interval_sec = coin.get('scan_interval', 5) * 60
                        
                        if now - coin.get('last_scan_time', 0) < scan_interval_sec: continue 
                        coin['last_scan_time'] = time.time()
                        
                        ca, lp = coin["ca"].lower(), coin["lp"].lower()
                        
                        # 🔥 LOG HIỂN THỊ TRÊN RENDER: Check ví gom
                        print(f"\n--- Dang soi bot xem co ca map gom {coin['name']} (CA: {ca[:6]}...) ---", flush=True)

                        token_price_bnb, token_decimals = 0, 18
                        price_res = requests.get(f"https://deep-index.moralis.io/api/v2.2/erc20/{ca}/price?chain=bsc", headers=get_current_headers(), timeout=10)
                        if price_res.status_code == 200:
                            token_decimals = int(price_res.json().get('tokenDecimals', 18))
                            token_price_bnb = float(price_res.json().get("nativePrice", {}).get("value", "0")) / (10**18)

                        new_txs, cursor, hit_old_data = [], "", False
                        max_pages = max(1, (coin.get('tx_limit', 100) + 99) // 100) if not coin['last_fetch_timestamp'] else 20
                        for _ in range(max_pages): 
                            page_url = f"https://deep-index.moralis.io/api/v2.2/erc20/{ca}/transfers?chain=bsc&limit=100" + (f"&cursor={cursor}" if cursor else "")
                            response = requests.get(page_url, headers=get_current_headers(), timeout=10)
                            if response.status_code == 200:
                                for tx in response.json().get('result', []):
                                    if coin['last_fetch_timestamp'] and tx.get('block_timestamp', '') <= coin['last_fetch_timestamp']: hit_old_data = True; break
                                    new_txs.append(tx)
                                cursor = response.json().get('cursor')
                                if not cursor or hit_old_data: break 
                            else: break
                                
                        if new_txs:
                            max_ts = max([tx.get('block_timestamp', '') for tx in new_txs])
                            if max_ts > coin['last_fetch_timestamp']: coin['last_fetch_timestamp'] = max_ts
                            coin['tx_cache'].extend(new_txs)
                            # 🔥 LOG HIỂN THỊ TRÊN RENDER
                            print(f"   => Keo Delta: {len(new_txs)} lenh moi ve Sổ tay.", flush=True)
                        else:
                            print(f"   => Khong co lenh moi.", flush=True)

                        time_ago = datetime.now(timezone.utc) - timedelta(hours=time_frame)
                        valid_cache = []
                        for tx in coin['tx_cache']:
                            try:
                                if datetime.strptime(tx.get('block_timestamp', '')[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc) >= time_ago: valid_cache.append(tx)
                            except: pass
                        coin['tx_cache'] = valid_cache
                        
                        # 🔥 LOG HIỂN THỊ TRÊN RENDER
                        print(f"   => Do dai So tay hien tai (sau khi cat tia): {len(valid_cache)} lenh.", flush=True)

                        sorted_txs = sorted(valid_cache, key=lambda x: x.get('block_timestamp', ''))
                        
                        wallet_receipts = {} 
                        router_temporary_sources = {} 
                        for tx in sorted_txs:
                            sender, receiver, value_raw = tx.get('from_address', '').lower(), tx.get('to_address', '').lower(), int(tx.get('value', '0'))
                            if value_raw == 0 or not tx.get('block_timestamp', ''): continue
                            nice_time = (datetime.strptime(tx.get('block_timestamp', '')[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc) + timedelta(hours=7)).strftime("%H:%M:%S") 
                            tx_bnb_value = (value_raw / (10**token_decimals)) * token_price_bnb

                            if sender == lp:
                                if token_price_bnb > 0 and tx_bnb_value >= min_bnb:
                                    if receiver in KNOWN_AGGREGATORS: router_temporary_sources[receiver] = {"amount_raw": value_raw, "bnb": tx_bnb_value, "time": nice_time}
                                    else: wallet_receipts.setdefault(receiver, []).append({"time": nice_time, "bnb": tx_bnb_value})
                            elif sender in KNOWN_AGGREGATORS and sender in router_temporary_sources:
                                if value_raw <= router_temporary_sources[sender]["amount_raw"]: 
                                    wallet_receipts.setdefault(receiver, []).append({"time": router_temporary_sources[sender]["time"], "bnb": router_temporary_sources[sender]["bnb"]})
                                    del router_temporary_sources[sender]
                            elif sender in wallet_receipts:
                                if receiver == lp: wallet_receipts.pop(sender, None)
                                else: 
                                    wallet_receipts.setdefault(receiver, []).extend(wallet_receipts[sender])
                                    wallet_receipts.pop(sender, None)

                        is_promoted = False
                        for wallet, buys in wallet_receipts.items():
                            if len(buys) >= min_buys:
                                if len(buys) > coin['alerted_wallets'].get(wallet, 0):
                                    coin['accumulators'][wallet] = buys
                                    coin['alerted_wallets'][wallet] = len(buys)
                                    
                                    bnb_bal = get_bnb_balance(wallet)
                                    token_bal = get_coin_balance(wallet, ca, token_decimals)
                                    msg = (f"🚨 <b>PHÁT HIỆN VÍ GOM HÀNG!</b>\n\n🪙 Coin: <b>{coin['name']}</b>\n📝 CA: <code>{ca}</code>\n"
                                           f"💳 <b>Ví gom:</b> <code>{wallet}</code>\n💰 <b>Đang Hold: {token_bal:,.2f} {coin['name']}</b>\n⛽ Dư: {bnb_bal:.4f} BNB\n\n"
                                           f"📊 <b>Chi tiết {len(buys)} lệnh gom:</b>\n")
                                    for b in buys: msg += f" ├ <i>{b['time']}</i> : Mua <b>{b['bnb']:.3f} BNB</b>\n"
                                    
                                    if list_type == "AUTO":
                                        msg += "\n🛡 <i>Đã thăng hạng lên rổ VIP. Cấu hình săn vẫn được bảo tồn!</i>"
                                        is_promoted = True

                                    ca_short = ca[:10]
                                    kb = {"inline_keyboard": [[{"text": "🔍 Check Ví Này (Dòng tiền)", "callback_data": f"w_w_{ca_short}_{wallet}"}]]}
                                    send_telegram_alert(msg, reply_markup=kb)
                        
                        if is_promoted and list_type == "AUTO":
                            if len(MANUAL_COINS) >= CONFIG.get("MAX_MANUAL_COINS", 20): MANUAL_COINS.pop(0)
                            MANUAL_COINS.append(coin) 
                            try: AUTO_COINS.remove(coin)
                            except: pass
                            # 🔥 LOG HIỂN THỊ TRÊN RENDER
                            print(f"   => [THANG HANG] {coin['name']} da duoc cap The Xanh vao ro Thu Cong/VIP!", flush=True)

                    except Exception as e: print(f"   ⚠️ LOI: {e}", flush=True)
                    time.sleep(2) 
            time.sleep(15) 
    except: traceback.print_exc()

Thread(target=listen_telegram_commands, daemon=True).start()
Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__": run_server()
