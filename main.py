# main.py
# MUAMMONI TOPISH UCHUN MAXSUS DIAGNOSTIK KOD

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
    ADMIN_ID = int(ADMIN_ID_STR)
    CHANNELS = ["@ajoyibkinolaar"]
    DB_FILE = "data.json"
    print("DEBUG: 2-qadam: Sozlamalar (Token, Admin ID) muvaffaqiyatli o'qildi.")
    print(f"   > ADMIN_ID qiymati: {ADMIN_ID}")
except Exception as e:
    print(f"!!! XATOLIK: Sozlamalarni o'qishda muammo chiqdi! Ehtimoliy sabab: Render'dagi BOT_TOKEN yoki ADMIN_ID noto'g'ri. Xato: {e}")
    TOKEN = None # Xatolik bo'lsa, botni ishga tushirmaslik uchun

# --- RENDER UCHUN WEB-SERVER QISMI ---
app = Flask('')
@app.route('/')
def home():
    return "Bot diagnostika rejimida"
def run():
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 8080)))
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- BAZA VA BOSHQA FUNKSIYALAR (O'zgarishsiz) ---
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
        query.answer("Rahmat!", show_alert=True); query.message.delete(); query.message.reply_text("Assalomu alaykum! Kino kodini yuboring.")
    else: query.answer("Siz hali kanalga obuna bo'lmadingiz.", show_alert=True)
def check_admin(update: Update): return update.message.from_user.id == ADMIN_ID
MOVIE_FILE, MOVIE_CODE = range(2)
def add_movie_start(update: Update, context: CallbackContext):
    if not check_admin(update): return ConversationHandler.END
    update.message.reply_text("Yangi kino qo'shish uchun, kino faylini yuboring.")
    return MOVIE_FILE
def get_movie_file(update: Update, context: CallbackContext):
    if update.message.video:
        context.user_data['file_id'] = update.message.video.file_id
        update.message.reply_text("✅ Kino fayli qabul qilindi.\nEndi bu kino uchun unikal kod yuboring.")
        return MOVIE_CODE
    else: update.message.reply_text("Iltimos, video fayl yuboring."); return MOVIE_FILE
def get_movie_code(update: Update, context: CallbackContext):
    code = update.message.text.strip()
    db = load_data()
    if code in db: update.message.reply_text("Bu kod allaqachon band."); return MOVIE_CODE
    file_id = context.user_data.get('file_id')
    if not file_id: return ConversationHandler.END
    db[code] = file_id; save_data(db); update.message.reply_text(f"✅ Muvaffaqiyatli saqlandi!\nKod: {code}"); context.user_data.clear(); return ConversationHandler.END
def list_movies(update: Update, context: CallbackContext):
    if not check_admin(update): return
    db = load_data()
    if not db: update.message.reply_text("Hozircha botda kinolar mavjud emas."); return
    message = "Botdagi barcha kinolar:\n\n"
    for code in db: message += f"Kod: `{code}`\n"
    update.message.reply_text(message, parse_mode='Markdown')
def delete_movie(update: Update, context: CallbackContext):
    if not check_admin(update): return
    try: code_to_delete = context.args[0]
    except (IndexError, ValueError): update.message.reply_text("Namuna: /deletemovie 123"); return
    db = load_data()
    if code_to_delete in db:
        del db[code_to_delete]; save_data(db); update.message.reply_text(f"✅ `{code_to_delete}` kodli kino o'chirildi.")
    else: update.message.reply_text("❌ Bunday kodga ega kino topilmadi.")
def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("Amal bekor qilindi."); context.user_data.clear(); return ConversationHandler.END

# --- BOTNI ISHGA TUSHIRISH ---
def main():
    print("DEBUG: 3-qadam: main() funksiyasi boshlandi.")
    keep_alive()
    print("DEBUG: 4-qadam: Web-server ishga tushirildi.")

    if TOKEN:
        updater = Updater(TOKEN, use_context=True)
        print("DEBUG: 5-qadam: Updater obyekti muvaffaqiyatli yaratildi (Token to'g'ri).")
        
        dp = updater.dispatcher
        add_movie_handler = ConversationHandler(entry_points=[CommandHandler('addmovie', add_movie_start)], states={MOVIE_FILE: [MessageHandler(Filters.video, get_movie_file)], MOVIE_CODE: [MessageHandler(Filters.text & ~Filters.command, get_movie_code)],}, fallbacks=[CommandHandler('cancel', cancel)])
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("listmovies", list_movies))
        dp.add_handler(CommandHandler("deletemovie", delete_movie))
        dp.add_handler(add_movie_handler)
        dp.add_handler(CallbackQueryHandler(check_subscription_callback, pattern='check_subscription'))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_code))
        print("DEBUG: 6-qadam: Barcha handlerlar muvaffaqiyatli qo'shildi.")
        
        updater.start_polling(timeout=30)
        print("DEBUG: 7-qadam: BOT ISHGA TUSHDI! Polling bosh
