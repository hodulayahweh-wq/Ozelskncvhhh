# bot.py
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import os
import json
import threading
from flask import Flask

# Flask kısmı - Render health check için zorunlu
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot çalışıyor - polling aktif"

@flask_app.route('/health')
def health():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))  # Render otomatik PORT verir
    flask_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# ────────────────────────────────────────────────
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable eksik!")

ADMIN_ID = 8258235296
CHANNEL = "@lordsystemv3"

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid == ADMIN_ID:
        kb = [["📤 Dosya Yükle"], ["📊 API Listesi"]]
        await update.message.reply_text("👑 ADMIN PANEL", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return

    try:
        member = await context.bot.get_chat_member(CHANNEL, uid)
        if member.status in ["member", "administrator", "creator", "restricted"]:
            await update.message.reply_text(
                "✅ Hoş geldin!\n\n"
                "• /dosyalar → yüklü dosyaları gör\n"
                "• /api <isim> → sorgula (ör: /api tc)\n"
                "Dosya yüklemek için admin olmalısın.",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await update.message.reply_text(f"❌ Kanala katıl:\n{CHANNEL}\n\nSonra /start yaz.")
    except Exception as e:
        print("Kanal kontrol hatası:", e)
        await update.message.reply_text(f"❌ Kanala katıl:\n{CHANNEL}")

async def dosyalar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    files = [f.replace(".json", "") for f in os.listdir(DATA_DIR) if f.endswith(".json")]
    if not files:
        await update.message.reply_text("📂 Henüz dosya yok.")
        return
    files.sort()
    msg = "Mevcut dosyalar:\n\n" + "\n".join(f"/api/{f}" for f in files)
    await update.message.reply_text(msg)

async def api_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Kullanım: /api <dosya_ismi>\nÖrnek: /api tc")
        return

    name = context.args[0].strip()
    path = os.path.join(DATA_DIR, f"{name}.json")

    if not os.path.exists(path):
        await update.message.reply_text(f"❌ Dosya yok: {name}\n/dosyalar ile bak.")
        return

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Temiz json çıktısı
        await update.message.reply_text(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"Dosya okuma hatası {name}: {e}")
        await update.message.reply_text("❌ Dosya bozuk veya okunamıyor.")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    doc = update.message.document
    if not doc:
        return

    if not doc.file_name.lower().endswith((".json", ".txt")):
        await update.message.reply_text("❌ Sadece .json veya .txt yükle.")
        return

    try:
        file = await doc.get_file()
        raw = await file.download_as_bytearray()
        text = raw.decode("utf-8")
        data = json.loads(text)
    except Exception as e:
        print("Yükleme hatası:", e)
        await update.message.reply_text("❌ Dosya okunamadı veya geçersiz JSON.")
        return

    if not isinstance(data, dict):
        await update.message.reply_text("❌ JSON bir obje olmalı ({{ }})")
        return

    created = []
    for key, value in data.items():
        safe_key = "".join(c for c in str(key) if c.isalnum() or c in ("-", "_"))
        if not safe_key:
            continue
        path = os.path.join(DATA_DIR, f"{safe_key}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(value, f, ensure_ascii=False, indent=2)
        created.append(safe_key)

    if created:
        msg = "✅ Oluşturuldu:\n" + "\n".join(f"/api/{x}" for x in sorted(created))
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("❌ Hiçbir dosya oluşturulmadı.")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    text = update.message.text
    if text == "📤 Dosya Yükle":
        await update.message.reply_text("JSON veya TXT dosyasını buraya at.")
    elif text == "📊 API Listesi":
        await dosyalar(update, context)

def main():
    # Flask'ı ayrı thread'de başlat (Render için)
    threading.Thread(target=run_flask, daemon=True).start()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("dosyalar", dosyalar))
    app.add_handler(CommandHandler("api", api_command))

    app.add_handler(MessageHandler(filters.Document.ALL & ~filters.COMMAND, handle_file))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("Bot başladı - polling çalışıyor")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
