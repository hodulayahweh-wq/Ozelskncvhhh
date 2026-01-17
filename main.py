import os
import re
import asyncio
import threading
import httpx 
import io
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- AYARLAR ---
ANA_TOKEN = "8231219914:AAH8H0IQRc4mNHJe0Wth5GM5vx1WBv-8VAs"
ADMIN_ID = 7690743437  # Sadece bu ID yönetim komutlarını kullanabilir
AKTIF_BOTLAR = {} 

def veri_temizle(metin):
    metin = re.sub(r'(https?://)?t\.me/\S+', '', metin)
    metin = re.sub(r'@[A-Za-z0-9_]+', '', metin)
    return metin.strip()

def komut_yap(url):
    url = url.lower()
    if "adres" in url: return "tc_adres"
    if "gsmtc" in url: return "gsm_tc"
    if "adsoyad" in url: return "ad_soyad"
    if "tcgsm" in url: return "tc_gsm"
    if "recete" in url: return "recete"
    if "bakiye" in url: return "kart_bakiye"
    if "borc" in url: return "borc_sorgu"
    if "fatura" in url: return "su_fatura"
    return f"sorgu_{abs(hash(url)) % 100}"

# --- ALT BOT MOTORU ---
async def alt_bot_baslat(token, api_links, aciklama):
    try:
        app = ApplicationBuilder().token(token).build()

        # ALT BOT /START KOMUTU - SENİN YAZDIĞIN AÇIKLAMAYI VE KOMUTLARI VERİR
        async def sub_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
            komutlar = "\n".join([f"🔹 /{komut_yap(l)}" for l in api_links])
            await update.message.reply_text(
                f"📋 **BOT BİLGİSİ**\n{aciklama}\n\n"
                f"🎮 **Sorgu Komutları:**\n{komutlar}\n\n"
                f"Sorgulamak istediğiniz veriyi komutun yanına yazın.",
                parse_mode="Markdown"
            )

        async def sorgula(update: Update, context: ContextTypes.DEFAULT_TYPE, link: str):
            if not context.args:
                await update.message.reply_text("❌ Lütfen sorgulanacak değeri girin!")
                return
            
            val = "%20".join(context.args)
            clean_url = re.sub(r'=[Xx0-9]+', '=', link)
            url = clean_url + val if "=" in clean_url else f"{clean_url}?tc={val}"
            
            await update.message.reply_text("⏳ Sorgulanıyor...")
            async with httpx.AsyncClient() as client:
                try:
                    r = await client.get(url, timeout=30.0)
                    sonuc = veri_temizle(r.text)
                    if len(sonuc) > 900:
                        f = io.BytesIO(sonuc.encode()); f.name = f"{context.args[0]}.txt"
                        await update.message.reply_document(f, caption="📄 Veri uzun olduğu için dosya yapıldı.")
                    else:
                        await update.message.reply_text(f"✅ **Sonuç:**\n\n`{sonuc}`", parse_mode="Markdown")
                except:
                    await update.message.reply_text("❌ API Hatası.")

        app.add_handler(CommandHandler("start", sub_start))
        for l in api_links:
            app.add_handler(CommandHandler(komut_yap(l), lambda u, c, link=l: sorgula(u, c, link)))

        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        
        while token in AKTIF_BOTLAR:
            await asyncio.sleep(5)
            
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
    except Exception as e:
        print(f"Hata: {e}")
        if token in AKTIF_BOTLAR: del AKTIF_BOTLAR[token]

# --- ANA BOT YÖNETİM ---
async def ana_isleyici(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return # Admin değilse işlem yapma

    mesaj = update.message.text
    token_match = re.search(r'(\d+:[A-Za-z0-9_-]{30,})', mesaj)
    links = re.findall(r'(https?://\S+)', mesaj)
    
    satirlar = mesaj.split('\n')
    aciklama = " ".join([s for s in satirlar if not re.search(r'(\d+:|https?://)', s) and s.strip()]) or "Özel Sorgu Botu"

    if token_match and links:
        token = token_match.group(1)
        if token in AKTIF_BOTLAR:
            await update.message.reply_text("⚠️ Bu bot zaten çalışıyor.")
            return
        
        AKTIF_BOTLAR[token] = True
        threading.Thread(target=lambda: asyncio.run(alt_bot_baslat(token, links, aciklama)), daemon=True).start()
        await update.message.reply_text("🚀 Bot başarıyla kuruldu ve özellikler tanımlandı!")
    else:
        await update.message.reply_text("❌ Hatalı format. Token, Linkler ve Açıklama gönderin.")

async def liste_goster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not AKTIF_BOTLAR: return await update.message.reply_text("📭 Aktif bot yok.")
    msg = "🤖 **Aktif Botlar:**\n" + "\n".join([f"• `{t[:15]}...`" for t in AKTIF_BOTLAR.keys()])
    await update.message.reply_text(msg, parse_mode="Markdown")

async def bot_sil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not context.args: return await update.message.reply_text("❌ Token yazın.")
    token = context.args[0]
    if token in AKTIF_BOTLAR:
        del AKTIF_BOTLAR[token]
        await update.message.reply_text("✅ Bot kapatıldı.")
    else:
        await update.message.reply_text("❌ Bulunamadı.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(ANA_TOKEN).build()
    app.add_handler(CommandHandler("liste", liste_goster))
    app.add_handler(CommandHandler("sil", bot_sil))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ana_isleyici))
    print("Yönetici Sistemi Aktif!")
    app.run_polling(drop_pending_updates=True)
