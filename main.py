import os
import re
import asyncio
import threading
import httpx 
import io
import json
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- RENDER CANLI TUTMA ---
web_app = Flask('')
@web_app.route('/')
def home(): return "Bot 7/24 Aktif!"
def run_web(): web_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# --- AYARLAR ---
ANA_TOKEN = "8595188359:AAHpbT4AZEFQe1VzZHo6HkjvHGgMtJq153k"
ADMIN_ID = 7690743437
AKTIF_BOTLAR = {} 

def veri_siklastir(ham_veri):
    """JSON verisini şık bir metne dönüştürür ve reklamları siler"""
    try:
        data = json.loads(ham_veri)
        metin = "💎 **Sorgu Detayları**\n\n"
        def parse_dict(d, indent=0):
            res = ""
            for k, v in d.items():
                if isinstance(v, dict):
                    res += f"📍 **{k.upper()}:**\n{parse_dict(v, indent+1)}"
                elif isinstance(v, list):
                    res += f"📝 **{k.upper()}:** (Liste)\n"
                else:
                    # Telegram/Discord linklerini temizle
                    val = str(v)
                    val = re.sub(r'(https?://)?(t\.me|discord\.gg)\S*', '', val)
                    res += f"🔹 **{k}:** `{val}`\n"
            return res
        metin += parse_dict(data)
        return metin
    except:
        # JSON değilse düz metin temizliği yap
        temiz = re.sub(r'(https?://)?(t\.me|discord\.gg)\S*', '', ham_veri)
        return f"📝 **Sonuç:**\n\n`{temiz}`"

def komut_uret(url):
    url = url.lower()
    if "adres" in url: return "adres"
    if "gsmtc" in url or "tcgsm" in url: return "gsm_sorgu"
    if "adsoyad" in url: return "ad_soyad"
    if "recete" in url: return "recete"
    if "plaka" in url: return "plaka"
    return f"sorgu_{abs(hash(url)) % 100}"

# --- ALT BOT ---
async def alt_bot_baslat(token, api_links, tanitim_metni):
    try:
        app = ApplicationBuilder().token(token).build()

        async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            keyboard = [[InlineKeyboardButton("📢 Resmi Kanal", url="https://t.me/nabisystemyeni")]]
            await update.message.reply_text(
                f"✨ **Hoş Geldiniz!**\n\n{tanitim_metni}\n\n🚀 Komutlar için: /komutlar",
                reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
            )

        async def komutlar_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            liste = "\n".join([f"🔍 /{komut_uret(l)}" for l in api_links])
            await update.message.reply_text(f"🛠 **AKTİF SORGULAR**\n\n{liste}", parse_mode="Markdown")

        async def sorgu_yap(update, context, link):
            if not context.args:
                await update.message.reply_text("❌ Değer girin!")
                return
            await update.message.reply_text("🔄 **Sorgulanıyor...**")
            val = "%20".join(context.args)
            url = link + val if "=" in link else f"{link}?tc={val}"
            async with httpx.AsyncClient() as client:
                try:
                    r = await client.get(url, timeout=30.0)
                    sonuc = veri_siklastir(r.text)
                    await update.message.reply_text(f"{sonuc}\n\n✨ @nabisystemyeni", parse_mode="Markdown")
                except:
                    await update.message.reply_text("❌ API Hatası.")

        app.add_handler(CommandHandler("start", start_handler))
        app.add_handler(CommandHandler("komutlar", komutlar_handler))
        for l in api_links:
            app.add_handler(CommandHandler(komut_uret(l), lambda u, c, target=l: sorgu_yap(u, c, target)))

        await app.initialize(); await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        while token in AKTIF_BOTLAR: await asyncio.sleep(10)
    except: pass

# --- ANA BOT ---
async def ana_isleyici(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    mesaj = update.message.text
    token = re.search(r'(\d+:[A-Za-z0-9_-]{30,})', mesaj)
    links = re.findall(r'(https?://\S+)', mesaj)
    lines = mesaj.split('\n')
    # Açıklama: Link ve Token olmayan satırlar
    desc = "\n".join([l for l in lines if not re.search(r'(\d+:|https?://)', l) and l.strip()])

    if token and links:
        t = token.group(1)
        AKTIF_BOTLAR[t] = True
        threading.Thread(target=lambda: asyncio.run(alt_bot_baslat(t, links, desc)), daemon=True).start()
        await update.message.reply_text("✅ Bot kuruldu! /start ve /komutlar otomatik hazırlandı.")

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    app = ApplicationBuilder().token(ANA_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ana_isleyici))
    app.run_polling(drop_pending_updates=True)
