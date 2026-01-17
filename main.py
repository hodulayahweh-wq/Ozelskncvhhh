import os
import re
import asyncio
import threading
import httpx 
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import io

# --- AYARLAR ---
# Buraya Kendi Ana Bot Tokenini Yaz
ANA_TOKEN = "8231219914:AAH8H0IQRc4mNHJe0Wth5GM5vx1WBv-8VAs"

# Verideki Telegram reklamlarını ve linklerini siler
def veri_temizle(metin):
    metin = re.sub(r'(https?://)?t\.me/\S+', '', metin)
    metin = re.sub(r'@[A-Za-z0-9_]+', '', metin)
    return metin.strip()

# Linkten komut ismi üretir
def komut_yap(url):
    url = url.lower()
    if "adres" in url: return "tc_adres"
    if "gsmtc" in url: return "gsm_tc"
    if "adsoyad" in url: return "ad_soyad"
    if "tcgsm" in url: return "tc_gsm"
    if "recete" in url: return "recete"
    if "bakiye" in url: return "bakiye"
    if "borc" in url: return "borc_sorgu"
    return f"sorgu_{abs(hash(url)) % 100}"

# --- ALT BOTUN ÇALIŞMASI ---
async def alt_bot_baslat(token, api_linkleri):
    try:
        app = ApplicationBuilder().token(token).build()

        # ALT BOT İÇİN /START KOMUTU (Komutları Otomatik Listeler)
        async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
            komutlar = "\n".join([f"🔹 /{komut_yap(l)}" for l in api_linkleri])
            await update.message.reply_text(
                f"✅ **Botunuz Sorgu Sistemine Bağlandı!**\n\n"
                f"Aşağıdaki komutları kullanarak sorgu yapabilirsiniz:\n\n{komutlar}\n\n"
                f"👉 Örnek kullanım: `/{komut_yap(api_linkleri[0])} 11111111111`",
                parse_mode="Markdown"
            )

        # Sorgu komutlarının ana motoru
        async def sorgula(update: Update, context: ContextTypes.DEFAULT_TYPE, link: str):
            if not context.args:
                await update.message.reply_text(f"❌ Sorgu için değer girin!\nÖrnek: `/{context.invoked_with} 123456789`", parse_mode="Markdown")
                return
            
            deger = "%20".join(context.args)
            # Linki hazırla
            url = link + deger if "=" in link else f"{link}?tc={deger}"
            
            await update.message.reply_text("⏳ Veri kaynağından sorgulanıyor...")
            
            async with httpx.AsyncClient() as client:
                try:
                    r = await client.get(url, timeout=20.0)
                    temiz_sonuc = veri_temizle(r.text)
                    
                    if len(temiz_sonuc) > 800:
                        file = io.BytesIO(temiz_sonuc.encode())
                        file.name = f"{deger}_sonuc.txt"
                        await update.message.reply_document(document=file, caption="📄 Veri uzun olduğu için dosya yapıldı.")
                    else:
                        await update.message.reply_text(f"📝 **Sorgu Sonucu:**\n\n`{temiz_sonuc}`", parse_mode="Markdown")
                except:
                    await update.message.reply_text("❌ API sunucusu yanıt vermedi veya link hatalı.")

        # Komutları bota tanımla
        app.add_handler(CommandHandler("start", start_cmd))
        for l in api_linkleri:
            # Her API linki için ayrı bir komut oluşturur
            cmd = komut_yap(l)
            app.add_handler(CommandHandler(cmd, lambda u, c, link=l: sorgula(u, c, link)))

        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(1000)
    except Exception as e:
        print(f"Alt Bot Hatası: {e}")

# --- ANA BOT İŞLEMLERİ ---
async def ana_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **Ana Bot Kontrol Paneli**\n\n"
        "Yeni bir bot başlatmak için Bot Tokeni ve API linklerini alt alta gönderin."
    )

async def ana_mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mesaj = update.message.text
    token_search = re.search(r'(\d+:[A-Za-z0-9_-]{30,})', mesaj)
    linkler = re.findall(r'(https?://\S+)', mesaj)

    if token_search and linkler:
        token = token_search.group(1)
        # Thread başlat
        threading.Thread(target=lambda: asyncio.run(alt_bot_baslat(token, linkler)), daemon=True).start()
        
        komut_listesi = "\n".join([f"🔹 /{komut_yap(l)}" for l in linkler])
        await update.message.reply_text(f"🚀 **Alt Bot Başarıyla Kuruldu!**\n\n**Aktif Komutlar:**\n{komut_listesi}\n\nDiğer botunuza gidip /start yazabilirsiniz.")
    else:
        await update.message.reply_text("❌ Hatalı format! Lütfen mesajda hem Bot Token hem de en az bir API linki olduğundan emin olun.")

if __name__ == "__main__":
    print("🤖 Sistem Render'da aktif edildi...")
    ana_app = ApplicationBuilder().token(ANA_TOKEN).build()
    ana_app.add_handler(CommandHandler("start", ana_start))
    ana_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ana_mesaj))
    ana_app.run_polling()
