import os
import json
import re
import threading
from datetime import datetime

from flask import Flask, request, jsonify, Response

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
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
        if key in r and normalize(r.get(key)) == value
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
# TELEGRAM BOT
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid == ADMIN_ID:
        kb = [["📤 Dosya Yükle"], ["📄 Dosyalar"]]
        await update.message.reply_text(
            "👑 ADMIN PANEL",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return

    try:
        member = await context.bot.get_chat_member(CHANNEL, uid)
        if member.status in ("member", "administrator", "creator"):
            await update.message.reply_text("✅ Hoş geldin")
        else:
            await update.message.reply_text(f"❌ Kanala katıl: {CHANNEL}")
    except:
        await update.message.reply_text(f"❌ Kanala katıl: {CHANNEL}")


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    doc = update.message.document
    file = await doc.get_file()
    raw = await file.download_as_bytearray()
    text = raw.decode("utf-8", errors="ignore")

    try:
        data = json.loads(text)
        if not isinstance(data, list):
            raise ValueError
    except:
        data = [{"value": l.strip()} for l in text.splitlines() if l.strip()]

    name = os.path.splitext(doc.file_name)[0].lower()
    safe = "".join(c for c in name if c.isalnum() or c in "-_")

    with open(os.path.join(DATA_DIR, f"{safe}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    await update.message.reply_text(f"✅ Yüklendi\n/api/search/{safe}?alan=deger")


def run_bot():
    if not BOT_TOKEN:
        print("BOT_TOKEN yok")
        return

    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    application.run_polling()


# ======================
# MAIN
# ======================
if __name__ == "__main__":
    threading.Thread(
        target=lambda: app.run(
            host="0.0.0.0",
            port=PORT,
            debug=False,
            use_reloader=False
        ),
        daemon=True
    ).start()

    run_bot()
