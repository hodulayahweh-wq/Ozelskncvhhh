import os
import json
import re
import threading
import asyncio
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
LOG_FILE = "api.log"
API_PREFIX = "/api/search"

PORT = int(os.environ.get("PORT", 10000))
API_KEY = os.environ.get("API_KEY")        # opsiyonel
BOT_TOKEN = os.environ.get("BOT_TOKEN")    # telegram

ADMIN_ID = 8258235296
CHANNEL = "@lordsystemv3"

os.makedirs(DATA_DIR, exist_ok=True)

# ======================
# FLASK APP
# ======================
flask_app = Flask(__name__)

def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {msg}\n")

def normalize(v):
    if not v:
        return ""
    v = re.sub(r"\s+", "", str(v))
    if v.isdigit():
        if v.startswith("90") and len(v) > 10:
            v = v[2:]
        if v.startswith("0") and len(v) > 10:
            v = v[1:]
    return v.upper()

def api_key_ok():
    if not API_KEY:
        return True
    return request.args.get("key") == API_KEY

@flask_app.route("/")
def home():
    return jsonify({
        "status": "API aktif",
        "search": f"{API_PREFIX}/<dosya>?alan=deger",
        "upload": "/api/upload/<dosya> (POST)"
    })

@flask_app.route("/health")
def health():
    return "OK", 200

@flask_app.route(f"{API_PREFIX}/<name>")
def search(name):
    if not api_key_ok():
        return {"error": "API KEY hatalı"}, 401

    path = os.path.join(DATA_DIR, f"{name}.json")
    if not os.path.isfile(path):
        return {"error": "Dosya bulunamadı"}, 404

    args = dict(request.args)
    args.pop("key", None)
    if not args:
        return {"error": "Parametre gerekli"}, 400

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    k, v = next(iter(args.items()))
    v = normalize(v)

    results = [r for r in data if normalize(r.get(k)) == v]

    log(f"SORGU | {name} | {k}={v} | {len(results)}")

    if not results:
        return {"error": "Eşleşme yok"}, 404

    if len(results) == 1:
        return jsonify(results[0])

    txt = ""
    for i, r in enumerate(results, 1):
        txt += f"--- KAYIT {i} ---\n"
        for kk, vv in r.items():
            txt += f"{kk}: {vv}\n"
        txt += "\n"

    return Response(txt, mimetype="text/plain")

@flask_app.route("/api/upload/<name>", methods=["POST"])
def upload(name):
    if not api_key_ok():
        return {"error": "API KEY hatalı"}, 401

    if "file" not in request.files:
        return {"error": "Dosya yok"}, 400

    raw = request.files["file"].read().decode("utf-8", errors="ignore").strip()
    if not raw:
        return {"error": "Dosya boş"}, 400

    try:
        data = json.loads(raw)
        if not isinstance(data, list):
            raise ValueError
    except:
        data = [{"value": l.strip()} for l in raw.splitlines() if l.strip()]

    safe = "".join(c for c in name.lower() if c.isalnum() or c in "-_")
    path = os.path.join(DATA_DIR, f"{safe}.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    log(f"UPLOAD | {safe} | {len(data)}")
    return {"status": "ok", "dosya": safe}

def run_flask():
    flask_app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False,
        use_reloader=False
    )

# ======================
# TELEGRAM BOT
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid == ADMIN_ID:
        kb = [["📤 Dosya Yükle"], ["📊 Dosya Listesi"]]
        await update.message.reply_text(
            "👑 ADMIN PANEL",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return

    try:
        m = await context.bot.get_chat_member(CHANNEL, uid)
        if m.status in ("member", "administrator", "creator"):
            await update.message.reply_text("✅ Hoş geldin")
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
    text = raw.decode("utf-8", errors="ignore").strip()

    try:
        data = json.loads(text)
        if not isinstance(data, list):
            raise ValueError
    except:
        data = [{"value": l.strip()} for l in text.splitlines() if l.strip()]

    name = os.path.splitext(doc.file_name or "dosya")[0]
    safe = "".join(c for c in name.lower() if c.isalnum() or c in "-_")

    with open(os.path.join(DATA_DIR, f"{safe}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    await update.message.reply_text(f"✅ Yüklendi\nAPI: {API_PREFIX}/{safe}?alan=deger")

def run_bot():
    if not BOT_TOKEN:
        print("BOT_TOKEN yok, bot başlatılmadı.")
        return

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("dosyalar", dosyalar))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file_upload))

    app.run_polling(close_loop=False)

# ======================
# MAIN (RENDER SAFE)
# ======================
if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    run_flask()
