# bot.py
import os
import json
import threading
from flask import Flask, jsonify
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Flask app - Render health check ve API için
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot & API çalışıyor - https://your-project.onrender.com/api/dosyaadi deneyin"

@flask_app.route('/health')
def health():
    return "OK", 200

@flask_app.route('/api/<path:filename>')
def serve_api(filename):
    path = os.path.join("data", f"{filename}.json")
    if not os.path.isfile(path):
        return jsonify({"error": "Dosya bulunamadı"}), 404
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": f"JSON okuma hatası: {str(e)}"}), 500

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# ──────────────────────────────────────────────── Telegram Bot Kısmı
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN eksik!")

ADMIN_ID = 8258235296
CHANNEL = "@lordsystemv3"
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid == ADMIN_ID:
        kb = [["📤 Dosya Yükle"], ["📊 Dosya Listesi"], ["🗑 Dosya Sil"]]
        await update.message.reply_text("👑 ADMIN PANEL", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return

    try:
        member = await context.bot.get_chat_member(CHANNEL, uid)
        if member.status in ["member", "administrator", "creator", "restricted"]:
            await update.message.reply_text(
                "✅ Hoş geldin!\n\n"
                "/dosyalar → dosyaları gör ve indir\n"
                "Destek: @LordDestekHat",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await update.message.reply_text(f"❌ Kanala katıl:\n{CHANNEL}\n\nKatıldıktan sonra /start yaz.")
    except:
        await update.message.reply_text(f"❌ Kanala katıl:\n{CHANNEL}")

async def dosyalar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    files = [f.replace(".json", "") for f in os.listdir(DATA_DIR) if f.endswith(".json")]
    if not files:
        await update.message.reply_text("📂 Henüz dosya yok.")
        return
    files.sort()
    msg = "📋 Mevcut dosyalar:\n\n" + "\n".join(f"• {f} → /api/{f}" for f in files)
    await update.message.reply_text(msg)

    # Kullanıcıya dosyaları göndermek (indirme)
    uid = update.effective_user.id
    if uid != ADMIN_ID:
        for f in files:
            path = os.path.join(DATA_DIR, f"{f}.json")
            if os.path.getsize(path) > 50 * 1024 * 1024:
                await update.message.reply_text(f"{f}.json büyük (>50MB), web'den indir: /api/{f}")
                continue
            await update.message.reply_document(document=open(path, 'rb'), filename=f"{f}.json")

async def handle_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    doc = update.message.document
    if not doc:
        return

    await update.message.reply_text("📤 Yükleme başladı...")

    try:
        file = await doc.get_file()
        raw = await file.download_as_bytearray()
        text = raw.decode("utf-8")
        data = json.loads(text)
    except Exception as e:
        await update.message.reply_text(f"❌ Geçersiz dosya veya JSON: {str(e)}")
        return

    if not isinstance(data, dict):
        await update.message.reply_text("❌ JSON obje olmalı")
        return

    name_base = os.path.splitext(doc.file_name or "dosya")[0]
    safe_name = "".join(c for c in name_base if c.isalnum() or c in "-_")
    path = os.path.join(DATA_DIR, f"{safe_name}.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    await update.message.reply_text(f"✅ Yüklendi ve API hazır:\n/api/{safe_name}\nSilmek için: /sil {safe_name}")

async def sil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Kullanım: /sil <dosyaadi>")
        return
    name = context.args[0].strip()
    path = os.path.join(DATA_DIR, f"{name}.json")
    if os.path.isfile(path):
        os.remove(path)
        await update.message.reply_text(f"🗑 {name} silindi.")
    else:
        await update.message.reply_text("Dosya bulunamadı.")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    text = update.message.text
    if text in ["📤 Dosya Yükle", "📊 Dosya Listesi", "🗑 Dosya Sil"]:
        if text == "📤 Dosya Yükle":
            await update.message.reply_text("JSON/TXT dosyasını at.")
        elif text == "📊 Dosya Listesi":
            await dosyalar(update, context)
        elif text == "🗑 Dosya Sil":
            await update.message.reply_text("Silmek için: /sil <dosyaadi>")

def main():
    threading.Thread(target=run_flask, daemon=True).start()

    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("dosyalar", dosyalar))
    application.add_handler(CommandHandler("sil", sil))

    application.add_handler(MessageHandler(filters.Document.ALL & ~filters.COMMAND, handle_file_upload))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("Bot & API başladı")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
