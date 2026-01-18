import os
import json
import re
from datetime import datetime
from flask import Flask, request, jsonify, Response

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ======================
# AYARLAR (ENV)
# ======================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # https://gordonvp.onrender.com
PORT = int(os.environ.get("PORT", 10000))

ADMIN_ID = 8258235296
CHANNEL = "@lordsystemv3"

DATA_DIR = "data"
LOG_FILE = "api.log"
API_PREFIX = "/api/search"

os.makedirs(DATA_DIR, exist_ok=True)

# ======================
# FLASK APP
# ======================
app = Flask(__name__)

def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {msg}\n")

def normalize(v):
    if not v:
        return ""
    v = str(v).strip()
    v = re.sub(r"\s+", "", v)
    return v.upper()

# ======================
# TELEGRAM BOT
# ======================
tg_app = Application.builder().token(BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid == ADMIN_ID:
        kb = [
            ["📤 Dosya Yükle"],
            ["📂 Dosya Listesi"],
        ]
        await update.message.reply_text(
            "👑 ADMIN PANEL\nDosya gönderebilirsin.",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return

    try:
        m = await context.bot.get_chat_member(CHANNEL, uid)
        if m.status in ("member", "administrator", "creator"):
            await update.message.reply_text(
                "✅ Hoş geldin\nBot aktif.",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await update.message.reply_text(f"❌ Kanala katıl: {CHANNEL}")
    except:
        await update.message.reply_text(f"❌ Kanala katıl: {CHANNEL}")

async def list_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    files = [f[:-5] for f in os.listdir(DATA_DIR) if f.endswith(".json")]
    await update.message.reply_text("\n".join(files) if files else "Dosya yok")

async def upload_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    doc = update.message.document
    file = await doc.get_file()
    raw = await file.download_as_bytearray()
    text = raw.decode("utf-8", errors="ignore").strip()

    try:
        data = json.loads(text)
        if not isinstance(data, list):
            raise ValueError
    except:
        data = [{"value": l.strip()} for l in text.splitlines() if l.strip()]

    name = os.path.splitext(doc.file_name)[0].lower()
    safe = "".join(c for c in name if c.isalnum() or c in "-_")

    path = os.path.join(DATA_DIR, f"{safe}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    await update.message.reply_text(
        f"✅ Yüklendi\n"
        f"API: {API_PREFIX}/{safe}?alan=deger"
    )

tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(CommandHandler("dosyalar", list_files))
tg_app.add_handler(MessageHandler(filters.Document.ALL, upload_file))

# ======================
# FLASK ROUTES
# ======================
@app.route("/", methods=["GET"])
def index():
    return "LORD API FREE aktif", 200

@app.route("/health")
def health():
    return "OK", 200

@app.route(f"{API_PREFIX}/<name>")
def search(name):
    path = os.path.join(DATA_DIR, f"{name}.json")
    if not os.path.isfile(path):
        return {"error": "Dosya yok"}, 404

    if not request.args:
        return {"error": "Parametre gerekli"}, 400

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    key, value = next(iter(request.args.items()))
    value = normalize(value)

    results = [
        r for r in data
        if key in r and normalize(r.get(key)) == value
    ]

    log(f"SORGU | {name} | {key}={value} | {len(results)}")

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

@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), tg_app.bot)
    tg_app.update_queue.put_nowait(update)
    return "OK", 200

@app.before_first_request
def setup_webhook():
    tg_app.bot.set_webhook(
        url=f"{WEBHOOK_URL}/webhook/{BOT_TOKEN}"
    )

# ======================
# RUN
# ======================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
