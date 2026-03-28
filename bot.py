import requests
import time
import os
import json
import traceback
from datetime import datetime, timedelta, timezone 
from flask import Flask, request
from threading import Thread

# =========================================================
# MULTI-CHAIN SNIPER BOT (V40 PRO - CHAIN-SPECIFIC LOCK)
# Chains: BSC (BNB) & BASE (ETH)
# Features: Independent LP Lock Toggle & Days for BSC/BASE
# =========================================================

app = Flask(__name__)

@app.route('/')
def home():
    return "Multi-Chain Sniper Bot (V40 Pro) đang hoạt động!"

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
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjM5MzcxZGI4LTQ2ZTMtNDQyOS05MGUzLTlkZDEzNzI1YTliMSIsIm9yZ0lkIjoiNTA3MjAwIiwidXNlcklkIjoiNTIxODc3IiwidHlwZUlkIjoiZTlmMGEzMDUtZjcwZC00YjI5LTkxYzktNGZkY2Y4YjAyOTYzIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQ1NzY3NzYsImV4cCI6NDkzMDMzNjc3Nn0.yMOh0meKfi4sVg7eSNHNtGniiQ53qAk7J-r4rrz5S4g',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjI5ZjBjYzM1LWIwZDgtNDMwNi04NzI3LTVjYmY3YTQ3NWNmMSIsIm9yZ0lkIjoiNTA3MzQ2IiwidXNlcklkIjoiNTIyMDI2IiwidHlwZUlkIjoiZDZhZDY5YzQtMmQ5YS00YWU3LWE5ZGUtNjdkNDg1YzQ0NjViIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQ2NzA1MDQsImV4cCI6NDkzMDQzMDUwNH0.DHVVQ3magI2CHp-k7NqaVU4bd0w4NR2-8ynTze_BKLk',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjNhZmM4NGU0LTY4MDYtNDlkMy1iZmExLTUwMmE3MmU0ZjMzNCIsIm9yZ0lkIjoiNTA3MzQ4IiwidXNlcklkIjoiNTIyMDI4IiwidHlwZUlkIjoiZDU0OTExZTEtYmZlZS00MTFkLTg1OTMtMjkyYjczNjE0ZGZlIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzQ2NzE5MjAsImV4cCI6NDkzMDQzMTkyMH0.oBltZLERdBtWrObhJVCWppoKvudSzjpzSW-hkJ_eDgQ'
]
API_KEYS = list(set(RAW_API_KEYS))
TELEGRAM_BOT_TOKEN = '8526113763:AAH3wANXx126AloxzAKJQrKJAPWiQm7Kb6Q'
TELEGRAM_CHAT_ID = '1976782751'

# 🔥 V40: TÁCH RIÊNG CẤU HÌNH KHÓA CHO BSC VÀ BASE
CONFIG = {
    "MAX_AUTO_COINS": 10,     
    "MAX_MANUAL_COINS": 20,    
    "AUTO_SCAN_BSC": True,   
    "AUTO_SCAN_BASE": True,  
    "MIN_LP_BSC": 1.0,       
    "MIN_LP_BASE": 0.3,      
    "NOTIFY_NEW_COIN": True,
    "REQUIRE_LP_LOCK_BSC": True,   # Công tắc khóa BSC
    "REQUIRE_LP_LOCK_BASE": True,  # Công tắc khóa BASE
    "MIN_LOCK_DAYS_BSC": 7,        # Ngày khóa BSC
    "MIN_LOCK_DAYS_BASE": 7        # Ngày khóa BASE
}

MANUAL_COINS = []
AUTO_COINS = [] 
user_state = {} 
current_api_index = 0 
BLACKLIST_COINS = ["0x55d398326f99059ff775485246999027b3197955".lower()]

DAILY_COIN_STATS = {
    "bsc": [],
    "base": []
}

NATIVE_CA = {
    "bsc": "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c".lower(),
    "base": "0x4200000000000000000000000000000000000006".lower()
}
GOPLUS_CHAIN_ID = {"bsc": "56", "base": "8453"}
NATIVE_SYM = {"bsc": "BNB", "base": "ETH"}

KNOWN_AGGREGATORS = {
    "bsc": ["0x8D0119F280C5562762a4928bE627a8d504505315".lower(), "0x1111111254EEB25477B68fB85Ed929f73A960582".lower(), "0x10ED43C718714eb63d5aA57B78B54704E256024E".lower()],
    "base": [
        "0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad".lower(), 
        "0xcf77a3ba9a5ca399b7c97c74d54e5b1beb874e43".lower(), 
        "0x2626664c2603336e57b271c5c0b26f421741e481".lower(), 
        "0x198ef79f1f515f02dfe9e3115ed9fc07183f02fc".lower()  
    ]
}

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

def check_security(ca, chain="bsc"):
    try:
        chain_id = GOPLUS_CHAIN_ID.get(chain, "56")
        url = f"https://api.gopluslabs.io/api/v1/token_security/{chain_id}?contract_addresses={ca}"
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
                
                # 🔥 Lấy số ngày min theo từng chain
                min_req_days = CONFIG.get(f"MIN_LOCK_DAYS_{chain.upper()}", 7) 
                
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
                                    try: days_left = (int(end_ts_str) - int(time.time())) // 86400
                                    except: pass
                            
                            if days_left > max_days_left: max_days_left = days_left
                            if days_left >= min_req_days: total_valid_locked_percent += pct

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

def format_security(sec):
    if not sec: return "🛡 <b>Bảo mật:</b> ⚠️ Lỗi quét.\n"
    hp_str = "🔴 CÓ (Lừa đảo)" if sec['is_honeypot'] else "🟢 Không"
    return f"🛡 <b>Bảo mật:</b> Honeypot: {hp_str} | Thuế: {sec['buy_tax']:.1f}%/{sec['sell_tax']:.1f}%\n💧 <b>Tình trạng LP:</b> {sec.get('lock_detail', 'N/A')}\n"

def get_coin_balance(wallet, ca, decimals, chain="bsc"):
    try:
        res = requests.get(f"https://deep-index.moralis.io/api/v2.2/{wallet}/erc20?chain={chain}&token_addresses={ca}", headers=get_current_headers(), timeout=5)
        if res.status_code == 200 and len(res.json()) > 0: return float(res.json()[0].get('balance', '0')) / (10**decimals)
    except: pass
    return 0.0

def get_native_balance(wallet, chain="bsc"):
    try:
        res = requests.get(f"https://deep-index.moralis.io/api/v2.2/{wallet}/balance?chain={chain}", headers=get_current_headers(), timeout=5)
        if res.status_code == 200: return int(res.json().get('balance', '0')) / (10**18)
    except: pass
    return 0.0

def init_coin_dict(name, ca, lp, chain="bsc"):
    return {
        "name": name, "chain": chain, "ca": ca.lower(), "lp": lp.lower(), 
        "time_frame": 2, "min_buys": 2, "min_bnb": 0.1, "scan_interval": 5, 
        "tx_limit": 100, "last_scan_time": 0, "last_alert_at": time.time(), "prompt_sent": False, 
        "tx_cache": [], "last_fetch_timestamp": "",
        "accumulators": {}, "alerted_wallets": {} 
    }

def process_new_coin_async(new_token, lp_address, chain="bsc"):
    global AUTO_COINS, CONFIG, MANUAL_COINS
    new_token = new_token.lower()
    lp_address = lp_address.lower()
    sym = NATIVE_SYM[chain]
    prefix = "BASE" if chain == "base" else "BSC"
    coin_name = f"{prefix}_{new_token[:4]}"
    
    try:
        res = requests.get(f"https://deep-index.moralis.io/api/v2.2/erc20/metadata?chain={chain}&addresses={new_token}", headers=get_current_headers(), timeout=5)
        if res.status_code == 200 and len(res.json()) > 0 and res.json()[0].get('symbol'): coin_name = f"[{prefix}] " + res.json()[0].get('symbol')
    except: pass

    print(f"\n   => [{prefix}] [LOC RAC] Dang kiem tra thanh khoan Pool cua {coin_name}...", flush=True)
    
    min_lp = CONFIG[f'MIN_LP_{prefix}']
    lp_native_bal = get_coin_balance(lp_address, NATIVE_CA[chain], 18, chain)
    
    if lp_native_bal < min_lp:
        print(f"   => [{prefix}] 🚫 [TU CHOI] Pool {coin_name} qua beo! ({lp_native_bal:.3f} {sym} < Min {min_lp} {sym}). Suut!!", flush=True)
        return

    print(f"   => [{prefix}] ✅ [DUYET] Thanh khoan tot ({lp_native_bal:.3f} {sym}). Kiem tra bao mat...", flush=True)

    sec_info = None
    is_clean = False
    
    # 🔥 Lấy yêu cầu khóa theo chain hiện tại
    require_lock = CONFIG.get(f'REQUIRE_LP_LOCK_{prefix}', True)
    min_days_req = CONFIG.get(f'MIN_LOCK_DAYS_{prefix}', 7)
    
    for attempt in range(40):
        sec_info = check_security(new_token, chain)
        
        if sec_info and not sec_info['is_honeypot'] and sec_info['buy_tax'] < 10 and sec_info['sell_tax'] < 10:
            if require_lock:
                if sec_info.get('is_lp_locked'): is_clean = True
            else:
                is_clean = True 
                
        if is_clean:
            print(f"   => [{prefix}] 🟢 [PASS] Dat chuan o lan check thu {attempt+1}! Chuan bi len song!", flush=True)
            break
            
        detail = sec_info['lock_detail'] if sec_info else "Chua co data"
        if require_lock:
            print(f"   => [{prefix}] Chua dat chuan khoa >=95% (>{min_days_req} ngay). Hien tai: {detail}. Doi 15s... (Lan {attempt+1}/40)", flush=True)
        else:
            print(f"   => [{prefix}] Cho GoPlus cap nhat du lieu HP/Thue... Doi 15s... (Lan {attempt+1}/40)", flush=True)
        time.sleep(15) 

    if not is_clean:
        print(f"   => [{prefix}] 🗑 [LOAI BO] Het 10 phut Dev {coin_name} van chua dat yeu cau bao mat.", flush=True)

    if is_clean:
        msg = f"🆕 <b>SIÊU PHẨM MỚI MẠNG {prefix}!</b>\n\n🪙 Tên Coin: <b>{coin_name}</b>\n📝 CA: <code>{new_token}</code>\n🏦 Pool gốc: <b>{lp_native_bal:.2f} {sym}</b>\n{format_security(sec_info)}\n"
        
        if not require_lock:
            msg += f"⚠️ <i>Chú ý: Chế độ 'Bỏ Qua Khóa LP' mạng {prefix} đang BẬT. Cẩn thận Rug Pull!</i>\n"
            
        send_telegram_alert(msg)
        if len(AUTO_COINS) >= CONFIG['MAX_AUTO_COINS']: AUTO_COINS.pop(0)
        AUTO_COINS.append(init_coin_dict(coin_name, new_token, lp_address, chain))
        print(f"   => [{prefix}] Da them {coin_name} vao ro AUTO quet ca map.", flush=True)

@app.route('/webhook', methods=['POST'])
def moralis_webhook():
    global AUTO_COINS, CONFIG, BLACKLIST_COINS, DAILY_COIN_STATS
    try:
        data = request.json
        if data and data.get('confirmed'):
            chain_hex = data.get('chainId', '0x38').lower()
            chain_name = "base" if chain_hex == "0x2105" else "bsc"
            
            if chain_name == "bsc" and not CONFIG.get('AUTO_SCAN_BSC', True): return "Disabled", 200
            if chain_name == "base" and not CONFIG.get('AUTO_SCAN_BASE', True): return "Disabled", 200

            for log in data.get('logs', []):
                if log.get('topic0') == '0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9':
                    t0, t1 = "0x" + log.get('topic1', '')[-40:], "0x" + log.get('topic2', '')[-40:]
                    w_native = NATIVE_CA[chain_name]
                    new_token = t1.lower() if t0.lower() == w_native else t0.lower()
                    
                    vn_now = datetime.now(timezone.utc) + timedelta(hours=7)
                    DAILY_COIN_STATS[chain_name] = [ts for ts in DAILY_COIN_STATS[chain_name] if ts.date() == vn_now.date()]
                    DAILY_COIN_STATS[chain_name].append(vn_now)
                    
                    if new_token in BLACKLIST_COINS: continue
                    if any(c['ca'] == new_token for c in AUTO_COINS + MANUAL_COINS): continue
                    
                    print(f"\n📥 [WEBHOOK] Bat duoc coin moi {chain_name.upper()}: {new_token}. Kiem tra an ninh...", flush=True)
                    
                    lp = "0x" + log.get('data', '')[26:66]
                    Thread(target=process_new_coin_async, args=(new_token, lp, chain_name), daemon=True).start()
    except: pass
    return "OK", 200

def send_main_menu():
    st_bsc = "🟢 Quét BSC" if CONFIG.get("AUTO_SCAN_BSC", True) else "🔴 Tắt BSC"
    st_base = "🟢 Quét BASE" if CONFIG.get("AUTO_SCAN_BASE", True) else "🔴 Tắt BASE"
    
    # 🔥 Tách biến Menu hiển thị riêng
    lk_bsc = "🟢 Khóa BSC" if CONFIG.get("REQUIRE_LP_LOCK_BSC", True) else "🔴 Bỏ Khóa BSC"
    lk_base = "🟢 Khóa BASE" if CONFIG.get("REQUIRE_LP_LOCK_BASE", True) else "🔴 Bỏ Khóa BASE"
    md_bsc = CONFIG.get("MIN_LOCK_DAYS_BSC", 7)
    md_base = CONFIG.get("MIN_LOCK_DAYS_BASE", 7)
    
    kb = {"inline_keyboard": [
        [{"text": "📊 Xem Tổng Quan", "callback_data": "menu_status"}, {"text": "📋 Danh Sách Cấu Hình", "callback_data": "menu_list"}],
        [{"text": "📈 Đếm Coin Mới", "callback_data": "menu_count_coins"}, {"text": "📒 Xem Sổ Tay Ví", "callback_data": "menu_wallet_ledger"}],
        [{"text": "⚙️ Cài Đặt Từng Coin", "callback_data": "menu_config_coin_list"}],
        [{"text": "🗑 Xóa Coin", "callback_data": "menu_del"}, {"text": "➕ Thêm Coin Thủ Công", "callback_data": "menu_add"}],
        [{"text": "⛔ Chặn CA (Blacklist)", "callback_data": "menu_blacklist_add"}, {"text": "👁 Xem Blacklist", "callback_data": "menu_blacklist_view"}],
        [{"text": "📦 Giới Hạn Rổ", "callback_data": "menu_set_max"}, {"text": "🏦 Cài Min Pool", "callback_data": "menu_set_minlp"}],
        
        # 🔥 Hàng quản lý Khóa LP TÁCH BIỆT:
        [{"text": lk_bsc, "callback_data": "menu_toggle_lock_bsc"}, {"text": f"⏱ Ngày BSC ({md_bsc}N)", "callback_data": "menu_set_lockdays_bsc"}],
        [{"text": lk_base, "callback_data": "menu_toggle_lock_base"}, {"text": f"⏱ Ngày BASE ({md_base}N)", "callback_data": "menu_set_lockdays_base"}],
        
        [{"text": "🔑 Quản Lý API Keys", "callback_data": "menu_keys"}],
        [{"text": f"{st_bsc}", "callback_data": "menu_toggle_bsc"}, {"text": f"{st_base}", "callback_data": "menu_toggle_base"}],
        [{"text": "🚫 Hủy Lệnh", "callback_data": "menu_cancel"}]
    ]}
    send_telegram_alert("🎛 <b>MULTI-CHAIN SNIPER BOT (V40 PRO)</b>\n👉 Chọn chức năng điều khiển bên dưới:", reply_markup=kb)

def send_coin_config_menu(coin):
    ca_short = coin['ca'][:10]
    sym = NATIVE_SYM[coin['chain']]
    msg = (f"⚙️ <b>BẢNG CẤU HÌNH CÁ NHÂN</b>\n\n"
           f"🪙 <b>{coin['name']}</b> (<code>{ca_short}...</code>)\n"
           f"⏱ Khung giờ soi: <b>{coin.get('time_frame', 2)}h</b>\n"
           f"🛒 Ví phải gom: <b>>= {coin.get('min_buys', 2)} lệnh</b>\n"
           f"🐋 Mức Tay to: <b>>= {coin.get('min_bnb', 0.1)} {sym}</b>\n"
           f"⏳ Tần suất quét: <b>{coin.get('scan_interval', 5)} phút/lần</b>\n\n"
           f"👉 Chọn thông số bạn muốn thay đổi:")
    
    kb = {"inline_keyboard": [
        [{"text": f"⏱ Đổi Khung giờ ({coin.get('time_frame', 2)}h)", "callback_data": f"cfg_time_{ca_short}"}],
        [{"text": f"🛒 Đổi Số lệnh gom ({coin.get('min_buys', 2)})", "callback_data": f"cfg_buy_{ca_short}"}],
        [{"text": f"🐋 Đổi Mức Tay to ({coin.get('min_bnb', 0.1)} {sym})", "callback_data": f"cfg_bnb_{ca_short}"}],
        [{"text": f"⏳ Đổi Tần suất ({coin.get('scan_interval', 5)}p)", "callback_data": f"cfg_freq_{ca_short}"}],
        [{"text": "🔙 Quay lại Danh Sách", "callback_data": "menu_config_coin_list"}]
    ]}
    send_telegram_alert(msg, reply_markup=kb)

def execute_command(cmd):
    global CONFIG, user_state, BLACKLIST_COINS, AUTO_COINS, MANUAL_COINS, API_KEYS, DAILY_COIN_STATS
    if cmd == 'status':
        st_l_bsc = f">= {CONFIG.get('MIN_LOCK_DAYS_BSC', 7)} Ngày" if CONFIG.get('REQUIRE_LP_LOCK_BSC', True) else "BỎ QUA (Rủi ro)"
        st_l_base = f">= {CONFIG.get('MIN_LOCK_DAYS_BASE', 7)} Ngày" if CONFIG.get('REQUIRE_LP_LOCK_BASE', True) else "BỎ QUA (Rủi ro)"
        msg = (f"⚙️ <b>TỔNG QUAN HỆ THỐNG</b>\n"
               f"🤖 Sức chứa Rổ Auto: <b>{CONFIG['MAX_AUTO_COINS']}</b> coin\n"
               f"👤 Sức chứa Rổ VIP: <b>{CONFIG['MAX_MANUAL_COINS']}</b> coin\n"
               f"🏦 Min Pool BSC: <b>>= {CONFIG['MIN_LP_BSC']} BNB</b>\n"
               f"🏦 Min Pool BASE: <b>>= {CONFIG['MIN_LP_BASE']} ETH</b>\n"
               f"🔒 Khóa LP BSC: <b>{st_l_bsc}</b>\n"
               f"🔒 Khóa LP BASE: <b>{st_l_base}</b>\n"
               f"⛔ CA cấm (Rác): <b>{len(BLACKLIST_COINS)}</b>\n"
               f"🔑 Đạn API: <b>{len(API_KEYS)} Keys</b>\n"
               f"📡 Quét BSC: <b>{'BẬT' if CONFIG['AUTO_SCAN_BSC'] else 'TẮT'}</b>\n"
               f"📡 Quét BASE: <b>{'BẬT' if CONFIG['AUTO_SCAN_BASE'] else 'TẮT'}</b>\n"
               f"🛡 Auto-Promote: <b>BẬT</b>")
        send_telegram_alert(msg)
    elif cmd == 'list':
        msg = f"📋 <b>DANH SÁCH & CẤU HÌNH</b>\n\n🤖 <b>AUTO ({len(AUTO_COINS)}/{CONFIG['MAX_AUTO_COINS']})</b>\n"
        for c in AUTO_COINS: msg += f" ├ <b>{c['name']}</b> ({c.get('scan_interval')}p | {c.get('time_frame')}h | {c.get('min_buys')}L | {c.get('min_bnb')} {NATIVE_SYM[c['chain']]})\n"
        msg += f"\n👤 <b>THỦ CÔNG / VIP ({len(MANUAL_COINS)}/{CONFIG['MAX_MANUAL_COINS']})</b>\n"
        for c in MANUAL_COINS: msg += f" ├ <b>{c['name']}</b> ({c.get('scan_interval')}p | {c.get('time_frame')}h | {c.get('min_buys')}L | {c.get('min_bnb')} {NATIVE_SYM[c['chain']]})\n"
        send_telegram_alert(msg)
        
    elif cmd == 'count_coins':
        vn_now = datetime.now(timezone.utc) + timedelta(hours=7)
        today = vn_now.date()
        
        msg = f"📈 <b>THỐNG KÊ COIN MỚI TRONG NGÀY</b>\n<i>(Tính từ 0h00 ngày {today.strftime('%d/%m/%Y')} - Giờ VN)</i>\n\n"
        
        for chain, name, icon in [("bsc", "BSC (BNB)", "🟡"), ("base", "BASE (ETH)", "🔵")]:
            DAILY_COIN_STATS[chain] = [ts for ts in DAILY_COIN_STATS[chain] if ts.date() == today]
            
            c_0_6 = c_6_12 = c_12_18 = c_18_24 = 0
            for ts in DAILY_COIN_STATS[chain]:
                hr = ts.hour
                if 0 <= hr < 6: c_0_6 += 1
                elif 6 <= hr < 12: c_6_12 += 1
                elif 12 <= hr < 18: c_12_18 += 1
                else: c_18_24 += 1
            
            msg += f"{icon} <b>MẠNG {name}</b>:\n"
            msg += f" ├ Từ 0h - 6h: có <b>{c_0_6}</b> coin mới\n"
            msg += f" ├ Từ 6h - 12h: có <b>{c_6_12}</b> coin mới\n"
            msg += f" ├ Từ 12h - 18h: có <b>{c_12_18}</b> coin mới\n"
            msg += f" └ Từ 18h - 24h: có <b>{c_18_24}</b> coin mới\n\n"
            
        msg += "<i>Lưu ý: Dữ liệu đếm gồm cả coin rác đã bị lọc. Tính từ lúc Bot khởi động.</i>"
        send_telegram_alert(msg)

    elif cmd == 'config_coin_list':
        all_coins = AUTO_COINS + MANUAL_COINS
        if not all_coins: send_telegram_alert("⚠️ Danh sách trống!"); return
        kb = {"inline_keyboard": []}
        for c in all_coins: kb["inline_keyboard"].append([{"text": f"⚙️ {c['name']}", "callback_data": f"open_cfg_{c['ca'][:10]}"}])
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
    
    elif cmd == 'add': 
        kb = {"inline_keyboard": [[{"text": "🟡 Mạng BSC (BNB)", "callback_data": "addchain_bsc"}, {"text": "🔵 Mạng BASE (ETH)", "callback_data": "addchain_base"}]]}
        send_telegram_alert("🌐 <b>Sếp muốn thêm coin vào mạng nào?</b>", reply_markup=kb)

    elif cmd == 'blacklist_add': user_state = {'step': 'WAITING_BLACKLIST_CA', 'last_time': time.time()}; send_telegram_alert("⛔ Nhập CA muốn chặn:")
    elif cmd == 'blacklist_view':
        if not BLACKLIST_COINS: send_telegram_alert("🟢 Blacklist trống.")
        else: send_telegram_alert(f"⛔ <b>BLACKLIST:</b>\n" + "\n".join([f" ├ <code>{ca}</code>" for ca in BLACKLIST_COINS]))
    
    elif cmd == 'toggle_bsc':
        CONFIG["AUTO_SCAN_BSC"] = not CONFIG.get("AUTO_SCAN_BSC", True)
        send_telegram_alert(f"🟡 Báo Coin Mới (BSC): {'BẬT' if CONFIG['AUTO_SCAN_BSC'] else 'TẮT'}")
        send_main_menu()
    elif cmd == 'toggle_base':
        CONFIG["AUTO_SCAN_BASE"] = not CONFIG.get("AUTO_SCAN_BASE", True)
        send_telegram_alert(f"🔵 Báo Coin Mới (BASE): {'BẬT' if CONFIG['AUTO_SCAN_BASE'] else 'TẮT'}")
        send_main_menu()

    # 🔥 V40: Xử lý menu toggle tách biệt
    elif cmd == 'toggle_lock_bsc':
        CONFIG["REQUIRE_LP_LOCK_BSC"] = not CONFIG.get("REQUIRE_LP_LOCK_BSC", True)
        st = "ĐÃ BẬT Khóa LP" if CONFIG["REQUIRE_LP_LOCK_BSC"] else "ĐÃ TẮT Khóa LP (Cảnh báo rủi ro)"
        send_telegram_alert(f"🟡 Mạng BSC: {st}")
        send_main_menu()
    elif cmd == 'toggle_lock_base':
        CONFIG["REQUIRE_LP_LOCK_BASE"] = not CONFIG.get("REQUIRE_LP_LOCK_BASE", True)
        st = "ĐÃ BẬT Khóa LP" if CONFIG["REQUIRE_LP_LOCK_BASE"] else "ĐÃ TẮT Khóa LP (Cảnh báo rủi ro)"
        send_telegram_alert(f"🔵 Mạng BASE: {st}")
        send_main_menu()
        
    elif cmd == 'set_lockdays_bsc':
        user_state = {'step': 'WAITING_LOCK_DAYS_BSC', 'last_time': time.time()}
        send_telegram_alert("🟡 <b>MẠNG BSC</b>: Nhập số ngày khóa LP tối thiểu (VD: 0, 1, 7, 30):")
    elif cmd == 'set_lockdays_base':
        user_state = {'step': 'WAITING_LOCK_DAYS_BASE', 'last_time': time.time()}
        send_telegram_alert("🔵 <b>MẠNG BASE</b>: Nhập số ngày khóa LP tối thiểu (VD: 0, 1, 7, 30):")

    elif cmd == 'set_max':
        kb = {"inline_keyboard": [[{"text": "🤖 Rổ Auto", "callback_data": "set_max_auto"}, {"text": "👤 Rổ Thủ Công", "callback_data": "set_max_manual"}]]}
        send_telegram_alert(f"Cài sức chứa cho rổ nào?", reply_markup=kb)
        
    elif cmd == 'set_minlp': 
        kb = {"inline_keyboard": [[{"text": "🟡 Mạng BSC", "callback_data": "set_minlp_bsc"}, {"text": "🔵 Mạng BASE", "callback_data": "set_minlp_base"}]]}
        send_telegram_alert("🏦 <b>Cài đặt Mức Min Pool (Đón lõng) cho mạng nào?</b>", reply_markup=kb)
    
    elif cmd == 'keys':
        msg = f"🔑 <b>KHO API KEYS HIỆN TẠI ({len(API_KEYS)} Keys)</b>\n"
        kb = {"inline_keyboard": [[{"text": "➕ Thêm API Key Mới", "callback_data": "menu_add_key"}]]}
        send_telegram_alert(msg, reply_markup=kb)
    elif cmd == 'add_key':
        user_state = {'step': 'WAITING_ADD_KEY', 'last_time': time.time()}
        send_telegram_alert("🔑 Vui lòng dán API Key Moralis mới của bạn vào đây:")
        
    elif cmd == 'cancel': user_state.clear(); send_telegram_alert("🚫 Đã hủy thao tác.")

def process_update(item):
    global AUTO_COINS, MANUAL_COINS, CONFIG, user_state, BLACKLIST_COINS, RAW_API_KEYS, API_KEYS, DAILY_COIN_STATS
    try:
        if user_state and time.time() - user_state.get('last_time', time.time()) > 300: user_state.clear()
        if "callback_query" in item:
            data = item["callback_query"]["data"]
            if data.startswith("menu_"): execute_command(data.replace("menu_", "")); return
            
            all_c = AUTO_COINS + MANUAL_COINS
            
            if data.startswith("addchain_"):
                chain_select = data.split("_")[1]
                user_state = {'step': 'WAITING_CA', 'chain': chain_select, 'last_time': time.time()}
                send_telegram_alert(f"📝 Đã chọn mạng <b>{chain_select.upper()}</b>.\n👉 Nhập CA muốn thêm (Rổ VIP):")
                return
            
            if data in ["set_minlp_bsc", "set_minlp_base"]:
                chain_target = "BSC" if "bsc" in data else "BASE"
                sym = "BNB" if chain_target == "BSC" else "ETH"
                user_state = {'step': f"WAITING_MINLP_VAL_{chain_target}", 'last_time': time.time()}
                send_telegram_alert(f"🏦 Nhập <b>Min Pool đón lỏng</b> cho mạng {chain_target} (Ví dụ: 1.0 {sym}):")
                return

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
                sym = NATIVE_SYM[coin['chain']]
                user_state = {'step': f"WAITING_CFG_{cfg_type.upper()}", 'target_ca': coin['ca'], 'last_time': time.time()}
                if cfg_type == "time": send_telegram_alert(f"🕒 Đang cấu hình: {coin['name']}\n👉 Nhập <b>Khung giờ soi</b> (VD: 2):")
                elif cfg_type == "buy": send_telegram_alert(f"🛒 Đang cấu hình: {coin['name']}\n👉 Nhập <b>Số lệnh gom</b> (VD: 2):")
                elif cfg_type == "bnb": send_telegram_alert(f"🐋 Đang cấu hình: {coin['name']}\n👉 Nhập <b>Mức gom Tay to</b> (VD: 0.1 {sym}):")
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
                if not coin: send_telegram_alert("⚠️ Dữ liệu coin đã bị xóa."); return
                
                chain = coin['chain']
                sym = NATIVE_SYM[chain]
                native_bal = get_native_balance(wallet, chain)
                token_decimals = 18 
                try:
                    res = requests.get(f"https://deep-index.moralis.io/api/v2.2/erc20/{coin['ca']}/price?chain={chain}", headers=get_current_headers(), timeout=5)
                    if res.status_code == 200: token_decimals = int(res.json().get('tokenDecimals', 18))
                except: pass
                token_bal = get_coin_balance(wallet, coin['ca'], token_decimals, chain)
                
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
                       f"├ Dư (Gas): <b>{native_bal:.4f} {sym}</b>\n"
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
                
                if step == 'WAITING_ADD_KEY':
                    if text not in API_KEYS:
                        RAW_API_KEYS.append(text)
                        API_KEYS.append(text)
                        send_telegram_alert(f"✅ Thêm Key thành công! Kho hiện tại đang có <b>{len(API_KEYS)} Keys</b>.")
                    else: send_telegram_alert("⚠️ Key này đã tồn tại trong hệ thống rồi sếp!")
                    user_state.clear()
                    return

                # 🔥 V40: Ghi đè số ngày khóa theo từng mạng
                if step and step.startswith("WAITING_LOCK_DAYS_"):
                    try:
                        chain_target = step.split('_')[3]
                        val = int(text)
                        CONFIG[f'MIN_LOCK_DAYS_{chain_target}'] = val
                        send_telegram_alert(f"✅ Mạng {chain_target}: Đã lưu cấu hình khóa LP >= <b>{val}</b> ngày.")
                        send_main_menu()
                        user_state.clear()
                    except: send_telegram_alert("❌ Nhập số nguyên không hợp lệ sếp ơi!")
                    return

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
                    chain = user_state.get('chain', 'bsc')
                    prefix = "BASE" if chain == "base" else "BSC"
                    coin_name = f"{prefix}_{ca[:4]}" 
                    try:
                        res = requests.get(f"https://deep-index.moralis.io/api/v2.2/erc20/metadata?chain={chain}&addresses={ca}", headers=get_current_headers(), timeout=5)
                        if res.status_code == 200 and len(res.json()) > 0: coin_name = f"[{prefix}] " + res.json()[0].get('symbol')
                    except: pass
                    if len(MANUAL_COINS) >= CONFIG.get('MAX_MANUAL_COINS', 20): MANUAL_COINS.pop(0)
                    MANUAL_COINS.append(init_coin_dict(coin_name, ca, lp, chain))
                    send_telegram_alert(f"🎉 Đã thêm vào rổ Thủ Công/VIP! Mạng {chain.upper()}."); user_state.clear()
                
                elif step == 'WAITING_BLACKLIST_CA':
                    if text.lower() not in BLACKLIST_COINS:
                        BLACKLIST_COINS.append(text.lower())
                        MANUAL_COINS[:] = [c for c in MANUAL_COINS if c['ca'].lower() != text.lower()]
                        AUTO_COINS[:] = [c for c in AUTO_COINS if c['ca'].lower() != text.lower()]
                        send_telegram_alert(f"✅ Đã chặn vĩnh viễn <code>{text.lower()}</code>")
                    user_state.clear()
                    
                elif step.startswith('WAITING_MINLP_VAL_'):
                    try: 
                        chain_target = step.split('_')[3]
                        CONFIG[f"MIN_LP_{chain_target}"] = float(text)
                        send_telegram_alert(f"🏦 Đã lưu Min Pool cho mạng {chain_target}: <b>{text}</b>.")
                        user_state.clear()
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
        print("--- LUONG QUET V40 PRO DA KHOI DONG ---", flush=True)
        send_telegram_alert("🚀 <b>Multi-Chain Sniper V40 Pro đã sẵn sàng!</b>\n🛡 Bộ luật Khóa LP hoạt động độc lập cho BSC và BASE.")
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
                        
                        ca, lp, chain = coin["ca"].lower(), coin["lp"].lower(), coin["chain"]
                        sym = NATIVE_SYM[chain]
                        prefix = "BASE" if chain == "base" else "BSC"
                        
                        print(f"\n--- [{prefix}] Dang soi bot ca map gom {coin['name']} (CA: {ca[:6]}...) ---", flush=True)

                        token_price_native, token_decimals = 0, 18
                        price_res = requests.get(f"https://deep-index.moralis.io/api/v2.2/erc20/{ca}/price?chain={chain}", headers=get_current_headers(), timeout=10)
                        if price_res.status_code == 200:
                            token_decimals = int(price_res.json().get('tokenDecimals', 18))
                            token_price_native = float(price_res.json().get("nativePrice", {}).get("value", "0")) / (10**18)

                        new_txs, cursor, hit_old_data = [], "", False
                        max_pages = max(1, (coin.get('tx_limit', 100) + 99) // 100) if not coin['last_fetch_timestamp'] else 20
                        for _ in range(max_pages): 
                            page_url = f"https://deep-index.moralis.io/api/v2.2/erc20/{ca}/transfers?chain={chain}&limit=100" + (f"&cursor={cursor}" if cursor else "")
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
                            print(f"   => [{prefix}] Keo Delta: {len(new_txs)} lenh moi ve Sổ tay.", flush=True)
                        else:
                            print(f"   => [{prefix}] Khong co lenh moi.", flush=True)

                        time_ago = datetime.now(timezone.utc) - timedelta(hours=time_frame)
                        valid_cache = []
                        for tx in coin['tx_cache']:
                            try:
                                if datetime.strptime(tx.get('block_timestamp', '')[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc) >= time_ago: valid_cache.append(tx)
                            except: pass
                        coin['tx_cache'] = valid_cache
                        
                        print(f"   => [{prefix}] Do dai So tay hien tai (sau khi cat tia): {len(valid_cache)} lenh.", flush=True)

                        sorted_txs = sorted(valid_cache, key=lambda x: x.get('block_timestamp', ''))
                        
                        wallet_receipts = {} 
                        router_temporary_sources = {} 
                        
                        valid_aggregators = KNOWN_AGGREGATORS[chain]
                        
                        for tx in sorted_txs:
                            sender, receiver, value_raw = tx.get('from_address', '').lower(), tx.get('to_address', '').lower(), int(tx.get('value', '0'))
                            if value_raw == 0 or not tx.get('block_timestamp', ''): continue
                            nice_time = (datetime.strptime(tx.get('block_timestamp', '')[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc) + timedelta(hours=7)).strftime("%H:%M:%S") 
                            tx_native_value = (value_raw / (10**token_decimals)) * token_price_native

                            if sender == lp:
                                if token_price_native > 0 and tx_native_value >= min_bnb:
                                    if receiver in valid_aggregators: router_temporary_sources[receiver] = {"amount_raw": value_raw, "native": tx_native_value, "time": nice_time}
                                    else: wallet_receipts.setdefault(receiver, []).append({"time": nice_time, "native": tx_native_value})
                            elif sender in valid_aggregators and sender in router_temporary_sources:
                                if value_raw <= router_temporary_sources[sender]["amount_raw"]: 
                                    wallet_receipts.setdefault(receiver, []).append({"time": router_temporary_sources[sender]["time"], "native": router_temporary_sources[sender]["native"]})
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
                                    
                                    native_bal = get_native_balance(wallet, chain)
                                    token_bal = get_coin_balance(wallet, ca, token_decimals, chain)
                                    msg = (f"🚨 <b>PHÁT HIỆN VÍ GOM HÀNG ({prefix})!</b>\n\n🪙 Coin: <b>{coin['name']}</b>\n📝 CA: <code>{ca}</code>\n"
                                           f"💳 <b>Ví gom:</b> <code>{wallet}</code>\n💰 <b>Đang Hold: {token_bal:,.2f}</b>\n⛽ Dư: {native_bal:.4f} {sym}\n\n"
                                           f"📊 <b>Chi tiết {len(buys)} lệnh gom:</b>\n")
                                    for b in buys: msg += f" ├ <i>{b['time']}</i> : Mua <b>{b['native']:.3f} {sym}</b>\n"
                                    
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
                            print(f"   => [{prefix}] [THANG HANG] {coin['name']} da vao ro Thu Cong/VIP!", flush=True)

                    except Exception as e: print(f"   ⚠️ [{prefix}] LOI: {e}", flush=True)
                    time.sleep(2) 
            time.sleep(15) 
    except: traceback.print_exc()

Thread(target=listen_telegram_commands, daemon=True).start()
Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__": run_server()
