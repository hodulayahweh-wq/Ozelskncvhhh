import os
import re
import asyncio
import threading
import httpx 
import io
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- AYARLAR ---
ANA_TOKEN = "8257223948:AAESLf3eah7CKH7eHneV6ynH6vq2b1VferU"
AKTIF_BOTLAR = {} # Çalışan botları takip etmek için

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
    return f"sorgu_{abs(hash(url)) % 100}"

# --- ALT BOT MOTORU ---
async def alt_bot_baslat(token, api_links, aciklama):
    try:
        app = ApplicationBuilder().token(token).build()

        async def sub_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
            komut_list = "\n".join([f"🔹 /{komut_yap(l)}" for l in api_links])
            await update.message.reply_text(
                f"🌟 **BOT PROFİLİ**\n{aciklama}\n\n"
                f"🎮 **Sorgu Komutları:**\n{komut_list}",
                parse_mode="Markdown"
            )

        async def sorgula(update: Update, context: ContextTypes.DEFAULT_TYPE, link: str):
            if not context.args:
                await update.message.reply_text("❌ Değer girin!")
                return
            val = "%20".join(context.args)
            url = link + val if "=" in link else f"{link}?tc={val}"
            async with httpx.AsyncClient() as client:
                try:
                    r = await client.get(url, timeout=25.0)
                    temiz = veri_temizle(r.text)
                    if len(temiz) > 850:
                        f = io.BytesIO(temiz.encode()); f.name = "sonuc.txt"
                        await update.message.reply_document(f, caption="📄 Sonuç dosyada.")
                    else:
                        await update.message.reply_text(f"📝 **Sonuç:**\n\n`{temiz}`", parse_mode="Markdown")
                except:
                    await update.message.reply_text("❌ API Hatası.")

        app.add_handler(CommandHandler("start", sub_start))
        for l in api_links:
            app.add_handler(CommandHandler(komut_yap(l), lambda u, c, link=l: sorgula(u, c, link)))

        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        
        # Botu durdurma sinyali gelene kadar bekle
        while token in AKTIF_BOTLAR:
            await asyncio.sleep(5)
            
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
    except Exception as e:
        print(f"Hata: {e}")
        if token in AKTIF_BOTLAR: del AKTIF_BOTLAR[token]

# --- ANA BOT KOMUTLARI ---
async def liste_goster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not AKTIF_BOTLAR:
        await update.message.reply_text("📭 Şu an çalışan alt bot yok.")
        return
    msg = "🤖 **Aktif Alt Botlar:**\n\n"
    for t in AKTIF_BOTLAR.keys():
        msg += f"🔹 `...{t[-10:]}`\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def bot_durdur(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Durdurmak istediğiniz botun tam tokenini girin.")
        return
    token = context.args[0]
    if token in AKTIF_BOTLAR:
        del AKTIF_BOTLAR[token]
        await update.message.reply_text("✅ Bot durduruldu ve sistemden silindi.")
    else:
        await update.message.reply_text("❌ Bu token ile çalışan bir bot bulunamadı.")

async def ana_isleyici(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mesaj = update.message.text
    token_match = re.search(r'(\d+:[A-Za-z0-9_-]{30,})', mesaj)
    links = re.findall(r'(https?://\S+)', mesaj)
    
    # Açıklama metni: Token ve Link dışındaki kısımlar
    satirlar = mesaj.split('\n')
    aciklama = " ".join([s for s in satirlar if not re.search(r'(\d+:|https?://)', s) and s.strip()])

    if token_match and links:
        token = token_match.group(1)
        if token in AKTIF_BOTLAR:
            await update.message.reply_text("⚠️ Bu bot zaten çalışıyor!")
            return
        
        AKTIF_BOTLAR[token] = True
        threading.Thread(target=lambda: asyncio.run(alt_bot_baslat(token, links, aciklama)), daemon=True).start()
        await update.message.reply_text("🚀 Bot başarıyla kuruldu ve başlatıldı!")
    else:
        await update.message.reply_text("❌ Geçersiz format! Mesajda Token ve API linkleri olmalı.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(ANA_TOKEN).build()
    app.add_handler(CommandHandler("start", lambda u,c: u.message.reply_text("Yönetim Paneline Hoş Geldiniz.")))
    app.add_handler(CommandHandler("liste", liste_goster))
    app.add_handler(CommandHandler("durdur", bot_durdur))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ana_isleyici))
    print("Ana Yönetim Sistemi Aktif!")
    app.run_polling(drop_pending_updates=True)
