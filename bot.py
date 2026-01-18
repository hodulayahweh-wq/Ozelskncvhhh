# bot.py (veya api.py olarak kaydet)
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import os
import json

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN yok!")

ADMIN_ID = 8258235296
CHANNEL = "@lordsystemv3"

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid == ADMIN_ID:
        kb = [["📤 Dosya Yükle"], ["📊 API Listesi"]]
        await update.message.reply_text("👑 ADMIN PANEL", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return

    try:
        member = await context.bot.get_chat_member(CHANNEL, uid)
        if member.status in ["member", "administrator", "creator", "restricted"]:
            await update.message.reply_text(
                "✅ Hoş geldin!\n\n/dosyalar → API listesi\n/api <isim> → sorgu yap\nÖrnek: /api gsm",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await update.message.reply_text(f"❌ Kanala katıl:\n{CHANNEL}")
    except:
        await update.message.reply_text(f"❌ Kanala katıl:\n{CHANNEL}")

async def dosyalar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    files = [f[:-5] for f in os.listdir(DATA_DIR) if f.lower().endswith(".json")]
    if not files:
        await update.message.reply_text("Henüz dosya yok.")
        return
    files.sort()
    text = "Mevcut dosyalar:\n\n" + "\n".join(f"/api/{f}" for f in files)
    await update.message.reply_text(text)

async def api_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Kullanım: /api dosya_adi")
        return
    name = context.args[0].strip()
    path = os.path.join(DATA_DIR, f"{name}.json")
    if not os.path.isfile(path):
        await update.message.reply_text(f"Dosya yok: {name}")
        return
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        await update.message.reply_text(json.dumps(data, ensure_ascii=False, indent=2))
    except:
        await update.message.reply_text("Dosya okunamadı (JSON hatalı?)")

async def handle_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    doc = update.message.document
    if not doc:
        return
    if not doc.file_name.lower().endswith((".json", ".txt")):
        await update.message.reply_text("Sadece .json veya .txt")
        return
    try:
        file = await doc.get_file()
        raw = await file.download_as_bytearray()
        text = raw.decode("utf-8")
        data = json.loads(text)
    except:
        await update.message.reply_text("Geçersiz dosya / JSON")
        return

    if not isinstance(data, dict):
        await update.message.reply_text("JSON obje olmalı {}")
        return

    created = []
    for key, val in data.items():
        safe = "".join(c for c in str(key) if c.isalnum() or c in "-_")
        if not safe: continue
        p = os.path.join(DATA_DIR, f"{safe}.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(val, f, ensure_ascii=False, indent=2)
        created.append(safe)

    if created:
        await update.message.reply_text("Başarılı:\n" + "\n".join(f"/api/{x}" for x in sorted(created)))
    else:
        await update.message.reply_text("Hiçbir şey oluşturulmadı")

async def text_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    t = update.message.text
    if t == "📤 Dosya Yükle":
        await update.message.reply_text("Dosyayı atabilirsin")
    elif t == "📊 API Listesi":
        await dosyalar(update, context)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("dosyalar", dosyalar))
    app.add_handler(CommandHandler("api", api_cmd))
    app.add_handler(MessageHandler(filters.Document.ALL & ~filters.COMMAND, handle_upload))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_btn))
    print("Bot başladı")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
