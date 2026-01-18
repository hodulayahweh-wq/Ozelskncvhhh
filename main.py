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

TOKEN = os.environ.get("BOT_TOKEN")          # Render → Environment → BOT_TOKEN
ADMIN_ID = 8258235296                        # Senin Telegram ID'n
CHANNEL = "@lordsystemv3"                    # Kanal username ( @ ile)

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid == ADMIN_ID:
        kb = [["📤 Dosya Yükle"], ["📊 API Listesi"]]
        await update.message.reply_text(
            "👑 ADMIN PANELİ",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=False)
        )
        return

    # Normal kullanıcı - kanal kontrolü
    try:
        member = await context.bot.get_chat_member(CHANNEL, uid)
        if member.status in ["member", "administrator", "creator"]:
            await update.message.reply_text(
                "✅ Hoş geldin!\n\n"
                "Mevcut API'leri görmek için: /dosyalar\n"
                "Bir API'yi kullanmak için:   /api isim\n\n"
                "Örnek: /api testapi",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await update.message.reply_text(
                f"❌ Önce şu kanala katılmalısın:\n\n{CHANNEL}\n\n"
                "Katıldıktan sonra tekrar /start yaz."
            )
    except Exception:
        await update.message.reply_text(
            f"❌ Kanala katıl:\n{CHANNEL}\n\nSonra tekrar /start yaz."
        )


async def dosyalar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    files = [
        f.replace(".json", "")
        for f in os.listdir(DATA_DIR)
        if f.endswith(".json") and os.path.isfile(os.path.join(DATA_DIR, f))
    ]

    if not files:
        text = "📂 Henüz hiç API yüklenmemiş."
    else:
        files.sort()
        if uid == ADMIN_ID:
            text = "👑 Admin API Listesi:\n\n"
            text += f"Toplam: {len(files)} adet\n\n"
            for name in files:
                size_kb = os.path.getsize(os.path.join(DATA_DIR, f"{name}.json")) / 1024
                text += f"→ /{name:<15}  ({size_kb:5.1f} KB)\n"
        else:
            text = "📋 Mevcut API'ler:\n\n"
            text += "Kullanmak istediğin komutu yaz:\n\n"
            text += "\n".join(f"/api/{name}" for name in files)
            text += "\n\nÖrnek:   /api ornek"

    await update.message.reply_text(text, disable_web_page_preview=True)


async def api_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Kullanım: /api <isim>\nÖrnek: /api test")
        return

    api_name = context.args[0].strip()
    path = os.path.join(DATA_DIR, f"{api_name}.json")

    if not os.path.isfile(path):
        await update.message.reply_text(
            f"❌ Böyle bir API yok: {api_name}\n"
            "Listeyi görmek için /dosyalar yaz."
        )
        return

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        # Markdown code block ile güzel gösterim
        content = json.dumps(data, ensure_ascii=False, indent=2)
        text = f"**API: {api_name}**\n\n```json\n{content}\n```"
        await update.message.reply_text(text, parse_mode="MarkdownV2", disable_web_page_preview=True)

    except json.JSONDecodeError:
        await update.message.reply_text("❌ Bu API dosyası bozuk (JSON formatı hatalı).")
    except Exception as e:
        print(f"Hata api {api_name}: {e}")
        await update.message.reply_text("❌ API okunurken sorun çıktı.")


async def handle_admin_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    document = update.message.document
    if not document:
        return

    file_name = document.file_name or "bilinmeyen"
    if not file_name.lower().endswith((".json", ".txt")):
        await update.message.reply_text("❌ Sadece .json veya .txt dosyası yükleyebilirsin.")
        return

    try:
        file = await document.get_file()
        bytes_data = await file.download_as_bytearray()
        text = bytes_data.decode("utf-8")
        data = json.loads(text)
    except Exception as e:
        print("Dosya okuma/JSON parse hatası:", e)
        await update.message.reply_text("❌ Dosya okunamadı veya geçersiz JSON.")
        return

    if not isinstance(data, dict):
        await update.message.reply_text("❌ JSON bir obje ({{ }}) olmalı.")
        return

    created = []
    for key, value in data.items():
        safe_key = "".join(c for c in str(key) if c.isalnum() or c in ("-", "_", "."))
        if not safe_key:
            continue
        path = os.path.join(DATA_DIR, f"{safe_key}.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(value, f, ensure_ascii=False, indent=2)
            created.append(safe_key)
        except Exception as e:
            print(f"{safe_key} kaydedilemedi:", e)

    if created:
        msg = "✅ Başarılı:\n\n" + "\n".join(f"/api/{x}" for x in sorted(created))
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("❌ Hiçbir API oluşturulmadı (isim sorunu olabilir).")


async def admin_list_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    # Admin "API Listesi" butonuna bastığında aynı /dosyalar komutunu çalıştır
    await dosyalar(update, context)


async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        if update.message.text in ["📤 Dosya Yükle", "📊 API Listesi"]:
            if update.message.text == "📊 API Listesi":
                await admin_list_button(update, context)
                return
            # Dosya Yükle için ekstra mesaj gerekmez, direkt dosya bekler
            await update.message.reply_text("JSON dosyasını buraya atabilirsin.")
            return

    await update.message.reply_text("🤔 Anlamadım...\n/dosyalar veya /start dene.")


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Komutlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("dosyalar", dosyalar))
    app.add_handler(CommandHandler("api", api_command))

    # Admin dosya yükleme (sadece document)
    app.add_handler(MessageHandler(
        filters.Document.ALL & ~filters.COMMAND,
        handle_admin_file_upload
    ))

    # Admin butonları ve diğer mesajlar
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        unknown_message
    ))

    print("Bot başlatılıyor...")
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()
