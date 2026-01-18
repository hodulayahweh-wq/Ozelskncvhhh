from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import os, json

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 8258235296
CHANNEL = "@lordsystemv3"

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid == ADMIN_ID:
        kb = [["📤 Dosya Yükle"], ["📊 API Listesi"]]
        await update.message.reply_text(
            "👑 ADMIN PANEL",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return

    try:
        m = await context.bot.get_chat_member(CHANNEL, uid)
        if m.status in ["member", "administrator", "creator"]:
            await update.message.reply_text("✅ Hoş geldin\nKomut: /dosyalar")
        else:
            await update.message.reply_text(f"❌ Kanala katıl:\n{CHANNEL}")
    except:
        await update.message.reply_text(f"❌ Kanala katıl:\n{CHANNEL}")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    doc = update.message.document
    file = await doc.get_file()
    raw = await file.download_as_bytearray()

    try:
        text = raw.decode("utf-8")
        data = json.loads(text)
    except:
        await update.message.reply_text("❌ Geçersiz JSON")
        return

    if not isinstance(data, dict):
        await update.message.reply_text("❌ JSON nesne olmalı")
        return

    created = []

    for api_name, api_data in data.items():
        path = os.path.join(DATA_DIR, f"{api_name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(api_data, f, ensure_ascii=False, indent=2)
        created.append(api_name)

    msg = "✅ Çoklu API oluşturuldu:\n\n"
    msg += "\n".join(f"/api/{x}" for x in created)
    await update.message.reply_text(msg)

async def dosyalar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    files = [f.replace(".json", "") for f in os.listdir(DATA_DIR)]
    if not files:
        await update.message.reply_text("📂 Dosya yok")
        return

    msg = "📂 Mevcut API’ler:\n\n"
    msg += "\n".join(f"/{f}" for f in files)
    await update.message.reply_text(msg)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("dosyalar", dosyalar))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.run_polling()

if __name__ == "__main__":
    main()
