import os
import json
import threading
import re
from flask import Flask, jsonify, request
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =======================
# FLASK API
# =======================
app = Flask(__name__)

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

API_PREFIX = "/api/v1/search"

def normalize(v):
    if not v:
        return ""
    v = str(v)
    v = re.sub(r"\D", "", v)
    if v.startswith("90") and len(v) > 10:
        v = v[2:]
    if v.startswith("0") and len(v) > 10:
        v = v[1:]
    return v

@app.route("/")
def home():
    return jsonify({
        "status": "API aktif",
        "example": f"{API_PREFIX}/gsm?gsm=05xxxxxxxxx"
    })

@app.route(f"{API_PREFIX}/<filename>")
def search(filename):
    path = os.path.join(DATA_DIR, f"{filename}.json")
    if not os.path.isfile(path):
        return {"error": "Dosya bulunamadı"}, 404

    if not request.args:
        return {"error": "Parametre gerekli"}, 400

    key, value = next(iter(request.args.items()))
    value = normalize(value)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for row in data:
        if key in row and normalize(row[key]) == value:
            return jsonify(row)

    return {"error": "Kayıt bulunamadı"}, 404

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# =======================
# TELEGRAM BOT
# =======================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 8258235296
CHANNEL = "@lordsystemv3"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid == ADMIN_ID:
        kb = [["📤 Dosya Yükle"], ["📊 Dosyalar"]]
        await update.message.reply_text(
            "👑 ADMIN PANEL",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return

    try:
        m = await context.bot.get_chat_member(CHANNEL, uid)
        if m.status in ["member", "administrator", "creator"]:
            await update.message.reply_text(
                "✅ Hoş geldin",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await update.message.reply_text(f"❌ Kanala katıl: {CHANNEL}")
    except:
        await update.message.reply_text(f"❌ Kanala katıl: {CHANNEL}")

async def files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    files = [f for f in os.listdir(DATA_DIR) if f.endswith(".json")]
    await update.message.reply_text("\n".join(files) if files else "Dosya yok")

async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    doc = update.message.document
    file = await doc.get_file()
    raw = await file.download_as_bytearray()

    try:
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, list):
            raise Exception
    except:
        await update.message.reply_text("❌ JSON liste formatında olmalı")
        return

    name = os.path.splitext(doc.file_name)[0].lower()
    path = os.path.join(DATA_DIR, f"{name}.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    await update.message.reply_text(
        f"✅ API hazır:\n/api/v1/search/{name}?alan=deger"
    )

def main():
    threading.Thread(target=run_flask, daemon=True).start()

    bot = ApplicationBuilder().token(BOT_TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("dosyalar", files))
    bot.add_handler(MessageHandler(filters.Document.ALL, upload))

    bot.run_polling()

if __name__ == "__main__":
    main()
