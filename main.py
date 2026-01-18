import os
import json
import re
import threading
from datetime import datetime

from flask import Flask, request, jsonify, Response

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ======================
# AYARLAR
# ======================
DATA_DIR = "data"
PORT = int(os.environ.get("PORT", 10000))

BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_KEY = os.environ.get("API_KEY")  # opsiyonel

ADMIN_ID = 8258235296
CHANNEL = "@lordsystemv3"

os.makedirs(DATA_DIR, exist_ok=True)

# ======================
# FLASK (Render ayakta tutsun diye)
# ======================
app = Flask(__name__)

@app.route("/")
def home():
    return "LORD API FREE aktif", 200

@app.route("/health")
def health():
    return "OK", 200

# ======================
# API SEARCH
# ======================
def normalize(v):
    if not v:
        return ""
    return re.sub(r"\s+", "", str(v)).upper()

@app.route("/api/search/<name>")
def search(name):
    if API_KEY and request.args.get("key") != API_KEY:
        return {"error": "API KEY hatalı"}, 401

    path = os.path.join(DATA_DIR, f"{name}.json")
    if not os.path.isfile(path):
        return {"error": "Dosya yok"}, 404

    if not request.args:
        return {"error": "Parametre yok"}, 400

    key, value = next(iter(request.args.items()))
    if key == "key":
        return {"error": "Arama alanı yok"}, 400

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    value = normalize(value)
    results = [
        r for r in data
        if key in r and normalize(r.get(key, "")) == value
    ]

    if not results:
        return {"error": "Eşleşme yok"}, 404

    if len(results) == 1:
        return jsonify(results[0])

    txt = ""
    for i, r in enumerate(results, 1):
        txt += f"--- KAYIT {i} ---\n"
        for k, v in r.items():
            txt += f"{k}: {v}\n"
        txt += "\n"

    return Response(txt, mimetype="text/plain")

# ======================
# TELEGRAM BOT HANDLER'LAR
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid == ADMIN_ID:
        kb = [["📤 Dosya Yükle"], ["📄 Dosyalar"]]
        await update.message.reply_text(
            "👑 ADMIN PANEL",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=False),
        )
        return

    try:
        member = await context.bot.get_chat_member(CHANNEL, uid)
        if member.status in ("member", "administrator", "creator"):
            await update.message.reply_text("✅ Hoş geldin")
        else:
            await update.message.reply_text(f"❌ Kanala katıl: {CHANNEL}")
    except Exception:
        await update.message.reply_text(f"❌ Kanala katıl: {CHANNEL}")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not update.message.document:
        await update.message.reply_text("Lütfen bir dosya gönder.")
        return

    doc = update.message.document
    file = await doc.get_file()
    raw_bytes = await file.download_as_bytearray()
    
    try:
        text = raw_bytes.decode("utf-8", errors="ignore")
        data = json.loads(text)
        if not isinstance(data, list):
            raise ValueError("JSON liste olmalı")
    except Exception:
        # JSON parse edilemedi → satır satır oku
        lines = text.splitlines()
        data = [{"value": line.strip()} for line in lines if line.strip()]

    name = os.path.splitext(doc.file_name or "data")[0].lower()
    safe_name = "".join(c for c in name if c.isalnum() or c in "-_")

    file_path = os.path.join(DATA_DIR, f"{safe_name}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    await update.message.reply_text(
        f"✅ Yüklendi: /{safe_name}\n"
        f"Örnek kullanım:\n"
        f"/api/search/{safe_name}?key=deger"
    )

# ======================
# BOT BAŞLATMA
# ======================
def run_bot():
    if not BOT_TOKEN:
        print("HATA: BOT_TOKEN environment variable tanımlı değil!")
        return

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    print("Bot polling başlıyor...")
    application.run_polling(
        poll_interval=0.5,
        timeout=10,
        drop_pending_updates=True,      # restart sonrası eski mesajları at
        allowed_updates=Update.ALL_TYPES
    )

# ======================
# MAIN
# ======================
if __name__ == "__main__":
    # Flask'ı ayrı thread'de çalıştır
    flask_thread = threading.Thread(
        target=app.run,
        kwargs={
            "host": "0.0.0.0",
            "port": PORT,
            "debug": False,
            "use_reloader": False
        },
        daemon=True
    )
    flask_thread.start()

    # Bot'u ana thread'de çalıştır (asyncio gerektiği için)
    run_bot()
