import os
import re
import asyncio
import threading
import httpx # Render için daha hızlı ve asenkron
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import io

# --- AYARLAR ---
ANA_TOKEN = "8231219914:AAH8H0IQRc4mNHJe0Wth5GM5vx1WBv-8VAs"

# Verideki Telegram reklamlarını temizleyen fonksiyon
def temizle(metin):
    # t.me linklerini, @kullanıcı adlarını ve reklamları siler
    metin = re.sub(r'(https?://)?t\.me/\S+', '', metin)
    metin = re.sub(r'@[A-Za-z0-9_]+', '', metin)
    metin = metin.replace("Telegram", "").replace("Kanalımıza katılın", "")
    return metin.strip()

def get_cmd_name(url):
    url = url.lower()
    if "adres" in url: return "tc_adres"
    if "gsmtc" in url: return "gsm_tc"
    if "adsoyad" in url: return "ad_soyad"
    if "tcgsm" in url: return "tc_gsm"
    if "recete" in url: return "recete"
    if "bakiye" in url: return "bakiye"
    return f"sorgu_{abs(hash(url)) % 100}"

# --- ALT BOT ÇALIŞMA SİSTEMİ ---
async def start_sub_bot(token, api_links):
    try:
        app = ApplicationBuilder().token(token).build()

        async def sub_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text("👋 Bu bot özel sorgu apilerine bağlıdır.\nKomutlar: " + ", ".join([f"/{get_cmd_name(l)}" for l in api_links]))

        async def sorgu_yapici(update: Update, context: ContextTypes.DEFAULT_TYPE, base_url: str):
            if not context.args:
                await update.message.reply_text("❌ Sorgulanacak değeri girin!")
                return
            
            val = "%20".join(context.args)
            # URL Hazırlama
            clean_url = re.sub(r'=[Xx0-9]+', '=', base_url)
            if "=" not in clean_url: clean_url += "?tc=" if "?" not in clean_url else "&tc="
            target = f"{clean_url}{val}"

            await update.message.reply_text("⏳ Veri getiriliyor...")

            async with httpx.AsyncClient() as client:
                try:
                    r = await client.get(target, timeout=20.0)
                    raw_data = r.text
                    # Reklam Temizliği
                    temiz_veri = temizle(raw_data)

                    if len(temiz_veri) > 600:
                        # Veri çok uzunsa TXT olarak gönder
                        out = io.BytesIO(temiz_veri.encode('utf-8'))
                        out.name = "sonuc.txt"
                        await update.message.reply_document(document=out, caption="✅ Veri yoğunluğu nedeniyle dosya olarak gönderildi.")
                    else:
                        await update.message.reply_text(f"✅ **Sonuç:**\n\n`{temiz_veri}`", parse_mode="Markdown")
                except:
                    await update.message.reply_text("❌ API sunucusu yanıt vermedi.")

        app.add_handler(CommandHandler("start", sub_start))
        for link in api_links:
            app.add_handler(CommandHandler(get_cmd_name(link), lambda u, c, l=link: sorgu_yapici(u, c, l)))

        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)
    except Exception as e:
        print(f"Hata: {e}")

def run_thread(token, links):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_sub_bot(token, links))

# --- ANA BOT ---
async def ana_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Ana Sisteme Hoş Geldiniz.\nToken ve Linkleri gönderin.")

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    token = re.search(r'(\d+:[A-Za-z0-9_-]{30,})', text)
    links = re.findall(r'(https?://\S+)', text)

    if token and links:
        threading.Thread(target=run_thread, args=(token.group(1), links), daemon=True).start()
        await update.message.reply_text("✅ Bot aktif edildi. Telegram reklamları otomatik temizlenecek.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(ANA_TOKEN).build()
    app.add_handler(CommandHandler("start", ana_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.run_polling()
