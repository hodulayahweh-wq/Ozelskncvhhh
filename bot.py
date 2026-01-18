# bot.py  (tam güncel hali – kopyala-yapıştır yap)

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

flask_app = Flask(__name__)

# Mutlak yol – Render'da dosya yolu sorunu çıkmasın diye
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
os.makedirs(DATA_DIR, exist_ok=True)

print(f"DATA_DIR: {DATA_DIR}")  # Render loglarında göreceksin

API_BASE = "https://ozel-hacker-egitim.onrender.com"

@flask_app.route('/')
def home():
    return f"Bot & API aktif → {API_BASE}/api/dosyaadi deneyin"

@flask_app.route('/health')
def health():
    return "OK", 200

@flask_app.route('/api/<path:filename>')
def serve_api(filename):
    path = os.path.join(DATA_DIR, f"{filename}.json")
    print(f"API isteği: {filename} → {path}")
    if not os.path.isfile(path):
        return jsonify({"error": "Dosya bulunamadı"}), 404
    try:
        with open(path, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# Telegram Bot Kısmı
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN eksik!")

ADMIN_ID = 8258235296
CHANNEL = "@lordsystemv3"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid == ADMIN_ID:
        kb = [["📤 Dosya Yükle"], ["📊 Dosya Listesi"], ["🗑 Dosya Sil"]]
        await update.message.reply_text("👑 ADMIN PANEL", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return

    try:
        m = await context.bot.get_chat_member(CHANNEL, uid)
        if m.status in ["member", "administrator", "creator", "restricted"]:
            await update.message.reply_text(
                "✅ Hoş geldin!\n\n"
                "/dosyalar → listeyi gör\n"
                f"API örnek: {API_BASE}/api/dosyaadi",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await update.message.reply_text(f"❌ Kanala katıl:\n{CHANNEL}")
    except:
        await update.message.reply_text(f"❌ Kanala katıl:\n{CHANNEL}")

async def dosyalar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    files = [f.replace(".json", "") for f in os.listdir(DATA_DIR) if f.endswith(".json")]
    if not files:
        await update.message.reply_text("Henüz dosya yok.")
        return
    files.sort()
    msg = "Dosyalar:\n\n" + "\n".join(f"• {f} → {API_BASE}/api/{f}" for f in files)
    await update.message.reply_text(msg)

async def handle_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    doc = update.message.document
    if not doc:
        return

    await update.message.reply_text("Yükleme başladı...")

    try:
        file = await doc.get_file()
        raw = await file.download_as_bytearray()
        text = raw.decode("utf-8").strip()
    except Exception as e:
        await update.message.reply_text(f"Dosya okunamadı: {str(e)}")
        return

    if not text:
        await update.message.reply_text("Dosya boş.")
        return

    data = None

    # 1. Deneme: Zaten JSON mu?
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # 2. TXT / düz metin ise → satırları listeye çevir
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if lines:
            data = {"content": lines}
        else:
            # En kötü durumda tek string olarak sakla
            data = {"raw_content": text}

    name_base = os.path.splitext(doc.file_name or "dosya")[0]
    safe_name = "".join(c for c in name_base if c.isalnum() or c in "-_")
    path = os.path.join(DATA_DIR, f"{safe_name}.json")

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        await update.message.reply_text(f"Kaydetme hatası: {str(e)}")
        return

    api_url = f"{API_BASE}/api/{safe_name}"
    await update.message.reply_text(
        f"✅ Dosya kabul edildi ve API oluşturuldu!\n\n"
        f"Adı: {safe_name}\n"
        f"API adresi: {api_url}\n\n"
        f"Silmek için: /sil {safe_name}"
    )

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
    t = update.message.text
    if t == "📤 Dosya Yükle":
        await update.message.reply_text("Herhangi bir dosyayı atabilirsin (.txt, .json vs.)")
    elif t == "📊 Dosya Listesi":
        await dosyalar(update, context)
    elif t == "🗑 Dosya Sil":
        await update.message.reply_text("Silmek için /sil <dosyaadi> yaz.")

def main():
    threading.Thread(target=run_flask, daemon=True).start()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("dosyalar", dosyalar))
    app.add_handler(CommandHandler("sil", sil))

    app.add_handler(MessageHandler(filters.Document.ALL & ~filters.COMMAND, handle_file_upload))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("Bot & API başladı")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
