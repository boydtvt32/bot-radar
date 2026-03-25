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
    "LANGUAGE": "vi" # Ngôn ngữ mặc định
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
        "
