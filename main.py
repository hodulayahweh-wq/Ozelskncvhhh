import os
import re
import asyncio
import threading
import httpx 
import io
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- AYARLAR ---
ANA_TOKEN = "8257223948:AAFB5N0ImYUSeIJ4sACodQ0OJlgJMOOTKoU"
ADMIN_ID = 7690743437
AKTIF_BOTLAR = {} 

def veri_temizle(metin):
    # Telegram, Discord linklerini ve reklamları temizler
    metin = re.sub(r'(https?://)?(t\.me|discord\.gg|discord\.com|invite)\S*', '', metin)
    metin = re.sub(r'@[A-Za-z0-9_]+', '', metin)
    return metin.strip()

def komut_belirle(url):
    url = url.lower()
    if "adres" in url: return "adres"
    if "gsmtc" in url or "tcgsm" in url: return "gsm_sorgu"
    if "adsoyad" in url: return "ad_soyad"
    if "recete" in url: return "recete"
    if "bakiye" in url: return "bakiye"
    if "plaka" in url: return "plaka"
    return f"sorgu_{abs(hash(url)) % 100}"

# --- ALT BOT ÇALIŞMA MANTIĞI ---
async def alt_bot_baslat(token, api_links, tanitim_metni):
    try:
        app = ApplicationBuilder().token(token).build()

        # /START - SADECE HOŞGELDİN VE BUTONLAR
        async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            keyboard = [
                [InlineKeyboardButton("📢 Resmi Kanal", url="https://t.me/nabisystemyeni")],
                [InlineKeyboardButton("🛠 Komutları Listele", callback_data="list_cmds")] # Manuel komut yazamayanlar için
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            mesaj = (
                f"✨ **Hoş Geldiniz!**\n\n"
                f"📝 **Bot Hakkında:**\n{tanitim_metni}\n\n"
                f"🚀 Sorgu komutlarını görmek için **/komutlar** yazınız."
            )
            await update.message.reply_text(mesaj, reply_markup=reply_markup, parse_mode="Markdown")

        # /KOMUTLAR - ANA BOTUN OTOMATİK OLUŞTURDUĞU LİSTE
        async def komutlar_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            liste = "\n".join([f"🔍 /{komut_belirle(l)}" for l in api_links])
            await update.message.reply_text(f"🛠 **AKTİF SORGULAR:**\n\n{liste}\n\n_Kullanım: /komut <değer>_", parse_mode="Markdown")

        async def sorgu_calistir(update: Update, context: ContextTypes.DEFAULT_TYPE, target_url: str):
            if not context.args:
                await update.message.reply_text("❌ Lütfen sorgulanacak bilgiyi girin!")
                return
            
            val = "%20".join(context.args)
            final_url = target_url + val if "=" in target_url else f"{target_url}?tc={val}"
            
            await update.message.reply_text("🔄 **Sorgulanıyor...**")
            async with httpx.AsyncClient() as client:
                try:
                    r = await client.get(final_url, timeout=30.0)
                    temiz_veri = veri_temizle(r.text)
                    
                    if len(temiz_veri) > 900:
                        f = io.BytesIO(temiz_veri.encode()); f.name = "sonuc.txt"
                        await update.message.reply_document(f, caption="📄 Veri yoğunluğu nedeniyle dosya gönderildi.")
                    else:
                        output = f"💎 **Sorgu Sonucu**\n\n`{temiz_veri}`\n\n✨ @nabisystemyeni"
                        await update.message.reply_text(output, parse_mode="Markdown")
                except:
                    await update.message.reply_text("❌ Servis şu an yanıt vermiyor.")

        # Komutları Kaydet
        app.add_handler(CommandHandler("start", start_handler))
        app.add_handler(CommandHandler("komutlar", komutlar_handler))
        for link in api_links:
            app.add_handler(CommandHandler(komut_belirle(link), lambda u, c, l=link: sorgu_calistir(u, c, l)))

        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        while token in AKTIF_BOTLAR: await asyncio.sleep(5)
        await app.updater.stop(); await app.stop(); await app.shutdown()
    except Exception as e:
        print(f"Hata: {e}")

# --- ANA YÖNETİM BOTU ---
async def ana_isleyici(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    
    msg = update.message.text
    token = re.search(r'(\d+:[A-Za-z0-9_-]{30,})', msg)
    links = re.findall(r'(https?://\S+)', msg)
    
    # Açıklama metni (Token ve Link olmayan her şey)
    lines = msg.split('\n')
    desc = " ".join([l for l in lines if not re.search(r'(\d+:|https?://)', l) and l.strip()])

    if token and links:
        bot_token = token.group(1)
        AKTIF_BOTLAR[bot_token] = True
        threading.Thread(target=lambda: asyncio.run(alt_bot_baslat(bot_token, links, desc)), daemon=True).start()
        await update.message.reply_text("✅ **Bot Aktif Edildi!**\n\n🔹 /start ve /komutlar hazır.\n🔹 API'ler otomatik tanımlandı.")

if __name__ == "__main__":
    application = ApplicationBuilder().token(ANA_TOKEN).build()
    application.add_handler(CommandHandler("liste", lambda u,c: u.message.reply_text(str(list(AKTIF_BOTLAR.keys())))))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ana_isleyici))
    print("Sistem Yayında!")
    application.run_polling(drop_pending_updates=True)
rulduruldu
