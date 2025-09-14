# main.py
# MAJBURIY OBUNA FUNKSIYASI QO'SHILGAN VERSİYA

import os
import json
# QO'SHILGAN IMPORTLAR: Tugmalar uchun kerak
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
# QO'SHILGAN IMPORT: Tugma bosilishini ushlash uchun
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler, CallbackQueryHandler

# --- SOZLAMALAR ---
# O'zingizning token va admin ID'ngizni shu yerga yozing.
# YANGI, XAVFSIZ HOLAT
import os # Bu qator faylning eng boshida bo'lishi kerak

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))
# QO'SHILGAN QISM: Majburiy obuna uchun kanal
CHANNELS = ["@ajoyibkinolaar"]

# Ma'lumotlar bazasi fayli
DB_FILE = "data.json"

# --- MA'LUMOTLAR BAZASI BILAN ISHLASH ---
def load_data():
    """data.json faylidan ma'lumotlarni o'qiydi"""
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_data(data):
    """Ma'lumotlarni data.json fayliga saqlaydi"""
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# QO'SHILGAN QISM: A'ZOLIKNI TEKSHIRUVCHI FUNKSIYA
def is_subscribed(user_id: int, context: CallbackContext) -> bool:
    """Foydalanuvchi majburiy kanallarga a'zo bo'lganini tekshiradi"""
    if user_id == ADMIN_ID:
        return True # Adminni tekshirmaymiz

    for channel in CHANNELS:
        try:
            member = context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ['creator', 'administrator', 'member']:
                return False
        except Exception:
            return False # Agar bot kanalda admin bo'lmasa yoki xatolik bo'lsa
    return True

# --- FOYDALANUVCHI FUNKSIYALARI ---

# O'ZGARTIRILGAN FUNKSIYA: Endi a'zolikni tekshiradi
def start(update: Update, context: CallbackContext):
    """/start buyrug'i uchun javob"""
    user_id = update.message.from_user.id

    if is_subscribed(user_id, context):
        update.message.reply_text("Assalomu alaykum! Kino kodini yuboring.")
    else:
        buttons = []
        for channel in CHANNELS:
            link = f"https://t.me/{str(channel).replace('@', '')}"
            buttons.append([InlineKeyboardButton("📢 Kanalga Obuna Bo'lish", url=link)])
        buttons.append([InlineKeyboardButton("✅ Tasdiqlash", callback_data="check_subscription")])
        
        reply_markup = InlineKeyboardMarkup(buttons)
        update.message.reply_text(
            f"Botdan to'liq foydalanish uchun, iltimos, {CHANNELS[0]} kanaliga obuna bo'ling:",
            reply_markup=reply_markup
        )

# O'ZGARTIRILGAN FUNKSIYA: Endi a'zolikni tekshiradi
def handle_code(update: Update, context: CallbackContext):
    """Kino kodini qabul qilib, kinoni yuborish"""
    user_id = update.message.from_user.id
    if not is_subscribed(user_id, context):
        start(update, context) # Agar a'zo bo'lmagan bo'lsa, start xabarini yuboramiz
        return

    code = update.message.text.strip()
    db = load_data()

    if code in db:
        file_id = db[code]
        update.message.reply_video(video=file_id, caption=f"Siz so'ragan kino (kod: {code})")
    else:
        update.message.reply_text("❌ Bunday kodga ega kino topilmadi.")

# QO'SHILGAN QISM: "Tasdiqlash" tugmasi bosilganda ishlaydi
def check_subscription_callback(update: Update, context: CallbackContext):
    """'Tasdiqlash' tugmasi bosilganda ishlaydi"""
    query = update.callback_query
    user_id = query.from_user.id

    if is_subscribed(user_id, context):
        query.answer("Rahmat! Endi botdan foydalanishingiz mumkin.", show_alert=True)
        query.message.delete()
        query.message.reply_text("Assalomu alaykum! Kino kodini yuboring.")
    else:
        query.answer("Siz hali kanalga obuna bo'lmadingiz.", show_alert=True)

# --- ADMIN FUNKSIYALARI (O'ZGARIShSIZ QOLADI) ---
def check_admin(update: Update):
    return update.message.from_user.id == ADMIN_ID
MOVIE_FILE, MOVIE_CODE = range(2)
def add_movie_start(update: Update, context: CallbackContext):
    if not check_admin(update):
        update.message.reply_text("Bu buyruq faqat admin uchun!")
        return ConversationHandler.END
    update.message.reply_text("Yangi kino qo'shish uchun, kino faylini yuboring.")
    return MOVIE_FILE
def get_movie_file(update: Update, context: CallbackContext):
    if update.message.video:
        context.user_data['file_id'] = update.message.video.file_id
        update.message.reply_text("✅ Kino fayli qabul qilindi.\nEndi bu kino uchun unikal kod yuboring (masalan, 101, 222, 007).")
        return MOVIE_CODE
    else:
        update.message.reply_text("Iltimos, video fayl yuboring.")
        return MOVIE_FILE
def get_movie_code(update: Update, context: CallbackContext):
    code = update.message.text.strip()
    db = load_data()
    if code in db:
        update.message.reply_text("Bu kod allaqachon band. Boshqa kod kiriting.")
        return MOVIE_CODE
    file_id = context.user_data.get('file_id')
    if not file_id:
        update.message.reply_text("Xatolik yuz berdi. /addmovie buyrug'ini qayta bering.")
        return ConversationHandler.END
    db[code] = file_id
    save_data(db)
    update.message.reply_text(f"✅ Muvaffaqiyatli saqlandi!\nKod: {code}")
    context.user_data.clear()
    return ConversationHandler.END
def list_movies(update: Update, context: CallbackContext):
    if not check_admin(update): return
    db = load_data()
    if not db:
        update.message.reply_text("Hozircha botda kinolar mavjud emas.")
        return
    message = "Botdagi barcha kinolar:\n\n"
    for code, file_id in db.items():
        message += f"Kod: `{code}`\n"
    update.message.reply_text(message, parse_mode='Markdown')
def delete_movie(update: Update, context: CallbackContext):
    if not check_admin(update): return
    try:
        code_to_delete = context.args[0]
    except (IndexError, ValueError):
        update.message.reply_text("O'chirish uchun kodni kiriting. Namuna: /deletemovie 123")
        return
    db = load_data()
    if code_to_delete in db:
        del db[code_to_delete]
        save_data(db)
        update.message.reply_text(f"✅ `{code_to_delete}` kodli kino muvaffaqiyatli o'chirildi.")
    else:
        update.message.reply_text("❌ Bunday kodga ega kino topilmadi.")
def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("Amal bekor qilindi.")
    context.user_data.clear()
    return ConversationHandler.END

# --- BOTNI ISHGA TUSHIRISH ---
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    add_movie_handler = ConversationHandler(
        entry_points=[CommandHandler('addmovie', add_movie_start)],
        states={
            MOVIE_FILE: [MessageHandler(Filters.video, get_movie_file)],
            MOVIE_CODE: [MessageHandler(Filters.text & ~Filters.command, get_movie_code)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("listmovies", list_movies))
    dp.add_handler(CommandHandler("deletemovie", delete_movie))
    dp.add_handler(add_movie_handler)

    # QO'SHILGAN QISM: "Tasdiqlash" tugmasi uchun handler
    dp.add_handler(CallbackQueryHandler(check_subscription_callback, pattern='check_subscription'))
    
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_code))

    updater.start_polling()
    print("Bot ishga tushdi...")
    updater.idle()

if __name__ == '__main__':
    main()