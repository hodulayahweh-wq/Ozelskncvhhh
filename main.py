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

print("APP STARTED")  # Render test satırı

# =======================
# FLASK APP
# =======================
flask_app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

API_PREFIX = "/api/v1/search"

def normalize(value):
    if value is None:
        return ""
    v = str(value).strip().upper()
    v = re.sub(r"\s+", "", v)
    if v.isdigit():
        if v.startswith("90") and len(v) > 10:
            v = v[2:]
        if v.startswith("0") and len(v) > 10:
            v = v[1:]
    return v

@flask_app.route("/")
def home():
    return jsonify({
        "status": "API aktif",
        "example": f"{API_PREFIX}/dosyaadi?alan=deger"
    })

@flask_app.route(f"{API_PREFIX}/<string:filename>")
def search_api(filename):
    file_path = os.path.join(DATA_DIR, f"{filename}.json")

    if not os.path.isfile(file_path):
        return jsonify({"error": "Dosya bulunamadı"}), 404

    if not request.args:
        return jsonify({"error": "Parametre gerekli"}), 400

    key, value = next(iter(request.args.items()))
    value = normalize(value)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        return jsonify({"error": "JSON okunamadı"}), 500

    for row in data:
        if key in row and normalize(row[key]) == value:
            return jsonify(row)

    return jsonify({"error": "Kayıt bulunamadı"}), 404

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port, debug=False)

# =======================
# TELEGRAM BOT
# =======================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN ENV YOK")

ADMIN_ID = 8258235296
CHANNEL = "@lordsystemv3"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid == ADMIN_ID:
        keyboard = [
            ["📤 Dosya Yükle"],
            ["📊 Dosya Listesi"],
            ["🗑 Dosya Sil"]
        ]
        await update.message.reply_text(
            "👑 LORD SYSTEM ADMIN PANEL",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return

    try:
        member = await context.bot.get_chat_member(CHANNEL, uid)
        if member.status in ["member", "administrator", "creator"]:
            await update.message.reply_text(
                "✨ LORD SORGU BOTUNA HOŞ GELDİN",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await update.message.reply_text(f"❌ Kanala katıl: {CHANNEL}")
    except:
        await update.message.reply_text(f"❌ Kanala katıl: {CHANNEL}")

async def dosyalar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    files = [f[:-5] for f in os.listdir(DATA_DIR) if f.endswith(".json")]
    await update.message.reply_text("\n".join(files) if files else "Dosya yok")

async def dosya_yukle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not update.message.document:
        return

    doc = update.message.document
    tg_file = await doc.get_file()
    raw = await tg_file.download_as_bytearray()

    try:
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, list):
            raise ValueError
    except:
        await update.message.reply_text("❌ JSON liste formatında olmalı")
        return

    name = os.path.splitext(doc.file_name)[0].lower()
    name = re.sub(r"[^a-z0-9_-]", "", name)

    with open(os.path.join(DATA_DIR, f"{name}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    await update.message.reply_text(
        f"✅ API hazır:\n{API_PREFIX}/{name}?alan=deger"
    )

async def sil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("/sil dosyaadi")
        return

    path = os.path.join(DATA_DIR, f"{context.args[0]}.json")
    if os.path.isfile(path):
        os.remove(path)
        await update.message.reply_text("🗑 Silindi")
    else:
        await update.message.reply_text("Dosya yok")

def main():
    threading.Thread(target=run_flask, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("dosyalar", dosyalar))
    app.add_handler(CommandHandler("sil", sil))
    app.add_handler(MessageHandler(filters.Document.ALL, dosya_yukle))

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
