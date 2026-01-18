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
LOG_FILE = "api.log"
API_PREFIX = "/api/search"

PORT = int(os.environ.get("PORT", 10000))
API_KEY = os.environ.get("API_KEY")  # yoksa herkese açık
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # bot kullanacaksan şart

ADMIN_ID = 8258235296
CHANNEL = "@lordsystemv3"

os.makedirs(DATA_DIR, exist_ok=True)

# ======================
# FLASK
# ======================
flask_app = Flask(__name__)

def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {msg}\n")

def normalize(v):
    if v is None:
        return ""
    v = str(v).strip()
    v = re.sub(r"\s+", "", v)
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
        "usage": f"{API_PREFIX}/<dosya>?alan=deger",
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

    if not request.args:
        return {"error": "Parametre gerekli"}, 400

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        return {"error": "JSON liste formatında olmalı"}, 500

    key, value = next(iter(request.args.items()))
    if key == "key":
        return {"error": "Arama alanı yok"}, 400

    value = normalize(value)
    results = []

    for row in data:
        if key in row and normalize(row.get(key)) == value:
            results.append(row)

    log(f"SORGU | dosya={name} | {key}={value} | sonuc={len(results)}")

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

    return Response(
        txt,
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment; filename=sonuclar.txt"}
    )

@flask_app.route("/api/upload/<name>", methods=["POST"])
def upload(name):
    if not api_key_ok():
        return {"error": "API KEY hatalı"}, 401

    if "file" not in request.files:
        return {"error": "Dosya yok"}, 400

    raw = request.files["file"].read().decode("utf-8", errors="ignore").strip()
    if not raw:
        return {"error": "Dosya boş"}, 400

    # JSON ise aynen; değilse satır satır JSON
    try:
        data = json.loads(raw)
        if not isinstance(data, list):
            return {"error": "JSON liste ([]) olmalı"}, 400
    except:
        lines = [l.strip() for l in raw.splitlines() if l.strip()]
        data = [{"value": l} for l in lines]

    safe = "".join(c for c in name.lower() if c.isalnum() or c in "-_")
    path = os.path.join(DATA_DIR, f"{safe}.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    log(f"UPLOAD | {safe} | kayıt={len(data)}")

    return {
        "status": "yüklendi",
        "dosya": safe,
        "api": f"{API_PREFIX}/{safe}?alan=deger"
    }

def run_flask():
    flask_app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)

# ======================
# TELEGRAM BOT
# ======================
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
                "✅ Hoş geldin!\n\n"
                "Kullanım:\n"
                f"{API_PREFIX}/dosya?alan=deger",
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
    if not doc:
        return

    file = await doc.get_file()
    raw = await file.download_as_bytearray()
    text = raw.decode("utf-8", errors="ignore").strip()
    if not text:
        await update.message.reply_text("Dosya boş.")
        return

    # JSON ise aynen; değilse satır satır JSON
    try:
        data = json.loads(text)
        if not isinstance(data, list):
            raise ValueError
    except:
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        data = [{"value": l} for l in lines]

    name = os.path.splitext(doc.file_name or "dosya")[0].lower()
    safe = "".join(c for c in name if c.isalnum() or c in "-_")
    path = os.path.join(DATA_DIR, f"{safe}.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    await update.message.reply_text(
        f"✅ Yüklendi\n"
        f"API: {API_PREFIX}/{safe}?alan=deger"
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

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    t = update.message.text
    if t == "📤 Dosya Yükle":
        await update.message.reply_text("Dosyayı gönder (.json/.txt/.csv)")
    elif t == "📊 Dosya Listesi":
        await dosyalar(update, context)
    elif t == "🗑 Dosya Sil":
        await update.message.reply_text("Silmek için: /sil dosyaadi")

def run_bot():
    if not BOT_TOKEN:
        print("BOT_TOKEN yok, bot başlatılmadı.")
        return
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("dosyalar", dosyalar))
    app.add_handler(CommandHandler("sil", sil))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file_upload))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.run_polling(drop_pending_updates=True)

# ======================
# MAIN
# ======================
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    run_bot()
