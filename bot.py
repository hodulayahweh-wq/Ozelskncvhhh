import os, json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

TOKEN = "8430322228:AAE0kAxUqO4cfXKDUyp0-PGPaFOe4zP56jY"
ADMIN_ID = 8258235296
DATA_DIR = "data"
DB_FILE = "db.json"

os.makedirs(DATA_DIR, exist_ok=True)

def load_db():
    if not os.path.exists(DB_FILE):
        return {"files": {}}
    return json.load(open(DB_FILE))

def save_db(db):
    json.dump(db, open(DB_FILE, "w"), indent=2)

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text("👑 Admin Panel\nDosya gönder, açıklamaya /komut yaz")
        return

    db = load_db()
    buttons = [
        [InlineKeyboardButton(f"📂 {k}", callback_data=k)]
        for k in db["files"]
    ]
    await update.message.reply_text(
        "📦 Dosya Listesi",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ---------- BUTON ----------
async def buton(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    db = load_db()
    komut = q.data

    if komut in db["files"]:
        await q.message.reply_document(db["files"][komut]["file_id"])

# ---------- DOSYA YÜKLE (ADMIN) ----------
async def dosya(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not update.message.caption:
        await update.message.reply_text("❌ Açıklamaya /komut yaz")
        return

    komut = update.message.caption.replace("/", "").strip()
    doc = update.message.document

    path = f"{DATA_DIR}/{komut}.json"
    file = await doc.get_file()
    await file.download_to_drive(path)

    # JSON kontrol
    try:
        json.load(open(path))
    except:
        await update.message.reply_text("❌ Dosya JSON değil")
        os.remove(path)
        return

    db = load_db()
    db["files"][komut] = {
        "file_id": doc.file_id,
        "api": f"/api/{komut}"
    }
    save_db(db)

    await update.message.reply_text(
        f"✅ Yüklendi\n"
        f"📦 Kullanıcıda görünecek\n"
        f"🌐 API: /api/{komut}"
    )

# ---------- RUN ----------
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buton))
app.add_handler(MessageHandler(filters.Document.ALL, dosya))

print("Bot çalışıyor")
app.run_polling()
