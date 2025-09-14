# main.py
# BARCHA XATOLARI TO'G'IRLANGAN YAKUNIY VERSIYA

import os
import json
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler, CallbackQueryHandler

print("DEBUG: 1-qadam: Barcha kutubxonalar muvaffaqiyatli import qilindi.")

# --- SOZLAMALAR ---
try:
    TOKEN = os.environ.get("BOT_TOKEN")
    ADMIN_ID_STR = os.environ.get("ADMIN_ID")
    if not TOKEN or not ADMIN_ID_STR:
        raise ValueError("BOT_TOKEN yoki ADMIN_ID topilmadi")
    ADMIN_ID = int(ADMIN_ID_STR)
    CHANNELS = ["@ajoyibkinolaar"]
    DB_FILE = "data.json"
    print("DEBUG: 2-qadam: Sozlamalar (Token, Admin ID) muvaffaqiyatli o'qildi.")
    print(f"   > ADMIN_ID qiymati: {ADMIN_ID}")
except Exception as e:
    print(f"!!! XATOLIK: Sozlamalarni o'qishda muammo chiqdi! Ehtimoliy sabab: Render'dagi BOT_TOKEN yoki ADMIN_ID noto'g'ri. Xato: {e}")
    TOKEN = None

# --- RENDER UCHUN WEB-SERVER QISMI ---
app = Flask('')
@app.route('/')
def home():
    return "Bot ishlamoqda"
def run():
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 8080)))
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- BAZA VA BOSHQA FUNKSIYALAR ---
def load_data():
    if not os.path.exists(DB_FILE): return {}
    try:
        with open(DB_FILE, 'r') as f: return json.load(f)
    except json.JSONDecodeError: return {}
def save_data(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4)
def is_subscribed(user_id: int, context: CallbackContext) -> bool:
    if user_id == ADMIN_ID: return True
    for channel in CHANNELS:
        try:
            member = context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ['creator', 'administrator', 'member']: return False
        except Exception: return False
    return True
def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if is_subscribed(user_id, context):
        update.message.reply_text("Assalomu alaykum! Kino kodini yuboring.")
    else:
        buttons = [[InlineKeyboardButton("📢 Kanalga Obuna Bo'lish", url=f"https://t.me/{str(channel).replace('@', '')}")] for channel in CHANNELS]
        buttons.append([InlineKeyboardButton("✅ Tasdiqlash", callback_data="check_subscription")])
        reply_markup = InlineKeyboardMarkup(buttons)
        update.message.reply_text(f"Botdan to'liq foydalanish uchun, iltimos, {CHANNELS[0]} kanaliga obuna bo'ling:", reply_markup=reply_markup)
def handle_code(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if not is_subscribed(user_id, context):
        start(update, context); return
    code = update.message.text.strip()
    db = load_data()
    if code in db:
        file_id = db[code]
        update.message.reply_video(video=file_id, caption=f"Siz so'ragan kino (kod: {code})")
    else: update.message.reply_text("❌ Bunday kodga ega kino topilmadi.")
def check_subscription_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    if is_subscribed(user_id, context):
        query.answer("Rahmat!", show_alert=True); query.message.delete(); query.message.reply_text("Assalomu alaykum! Kino kodini y
