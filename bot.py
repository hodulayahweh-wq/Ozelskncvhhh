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
    filters,
    ContextTypes,
)

# =======================
# FLASK APP
# =======================
flask_app = Flask(__name__)

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
os.makedirs(DATA_DIR, exist_ok=True)

API_PREFIX = "/api/v1/search"

def normalize(value):
    if not value:
        return ""
    v = re.sub(r"\s+", "", str(value))
    v = re.sub(r"\D", "", v) if v.isdigit() else v.upper()
    if v.startswith("90") and len(v) > 10:
        v = v[2:]
    if v.startswith("0") and len(v) > 10:
        v = v[1:]
    return v

@flask_app.route("/")
def home():
    return jsonify({
        "status": "API aktif",
        "usage": f"{API_PREFIX}/dosyaadi?alan=deger"
    })

@flask_app.route("/health")
def health():
    return "OK", 200

@flask_app.route(f"{API_PREFIX}/<path:filename>")
def serve_api(filename):
    path = os.path.join(DATA_DIR, f"{filename}.json")

    if not os.path.isfile(path):
        return jsonify({"error": "Dosya bulunamadı"}), 404

    if not request.args:
        return jsonify({"error": "arama parametresi gerekli"}), 400

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return jsonify({"error": "JSON okunamadı", "detail": str(e)}), 500

    if not isinstance(data, list):
        return jsonify({"error": "JSON liste formatında olmalı"}), 500

    query_key, query_value = next(iter(request.args.items()))
    query_value = normalize(query_value)

    for row in data:
        if query_key in row and normalize(row.get(query_key)) == query_value:
            return jsonify(row)

    return jsonify({"error": "Kayıt bulunamadı"}), 404

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# =======================
# TELEGRAM BOT
# =======================
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 8258235296
CHANNEL = "@lordsystemv3"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid == ADMIN_ID:
        kb = [["📤 Dosya Yükle"], ["📊 Dosya Listesi"], ["🗑 Dosya Sil"]]
        await update.message.reply_text(
            "👑 ADMIN PANEL",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return

    try:
        m = await context.bot.get_chat_member(CHANNEL, uid)
        if m.status in ["member", "administrator", "creator", "restricted"]:
            await update.message.reply_text(
                "✅ Hoş geldin",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await update.message.reply_text(f"❌ Kanala katıl: {CHANNEL}")
    except:
        await update.message.reply_text(f"❌ Kanala katıl: {CHANNEL}")

async def dosyalar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    files = [f[:-5] for f in os.listdir(DATA_DIR) if f.endswith(".json")]
    await update.message.reply_text("\n".join(files) if files else "Dosya yok")

async def handle_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    doc = update.message.document
    file = await doc.get_file()
    raw = await file.download_as_bytearray()

    try:
        data = json.loads(raw.decode("utf-8", errors="ignore"))
    except:
        await update.message.reply_text("❌ JSON formatı geçersiz")
        return

    if not isinstance(data, list):
        await update.message.reply_text("❌ JSON liste ([]) olmalı")
        return

    name = os.path.splitext(doc.file_name)[0].lower()
    name = "".join(c for c in name if c.isalnum() or c in "-_")

    path = os.path.join(DATA_DIR, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    await update.message.reply_text(
        f"✅ API hazır:\n"
        f"/api/v1/search/{name}?alan=deger"
    )

async def sil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Kullanım: /sil dosyaadi")
        return

    name = context.args[0]
    path = os.path.join(DATA_DIR, f"{name}.json")

    if os.path.isfile(path):
        os.remove(path)
        await update.message.reply_text("🗑 Silindi")
    else:
        await update.message.reply_text("Dosya yok")

def main():
    threading.Thread(target=run_flask, daemon=True).start()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("dosyalar", dosyalar))
    app.add_handler(CommandHandler("sil", sil))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file_upload))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
