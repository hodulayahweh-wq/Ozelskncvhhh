import os, asyncio, threading, httpx, datetime, base64
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from telegram.ext import ApplicationBuilder

SISTEM = {
    "apis": {}, 
    "admin_id": 7690743437,
    "ana_token": "8586246924:AAEdEGEQn9tjBBAQKw-nJ_NvDG5P-G3T8cc",
    "panel_sifre": "19786363",
    "baslangic": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
}

web_app = Flask(__name__)
web_app.secret_key = "nabi_ultra_turbo_key"

# HIZ İÇİN GLOBAL CLİENT (Bağlantıları açık tutar)
global_client = httpx.AsyncClient(timeout=10.0, limits=httpx.Limits(max_connections=100, max_keepalive_connections=50))

# --- HTML ŞABLONLARI (Aynı Kaldı) ---
HTML_ADMIN = """ ... (Senin kodundaki admin tasarımı) ... """
HTML_SITE = """ ... (Senin kodundaki site tasarımı) ... """

# --- YOLLAR ---
@web_app.route('/do_web_sorgu')
async def do_web_sorgu():
    name = request.args.get('name')
    val = request.args.get('val')
    api_url = SISTEM["apis"].get(name)
    
    if not api_url:
        return jsonify({"result": "API Tanımlı Değil!"})

    try:
        # YENİ: Tekrardan client oluşturmak yerine açık olan global_client'ı kullanıyoruz
        # Bu işlem bağlantı süresini (handshake) ortadan kaldırır.
        r = await global_client.get(api_url + val)
        return jsonify({"result": r.text})
    except Exception as e:
        return jsonify({"result": f"Bağlantı Hatası: {str(e)}"})

# ... (Diğer Route'lar: login, home, add_api, del_api senin kodunla aynı kalsın) ...

async def bot_start():
    try:
        app = ApplicationBuilder().token(SISTEM["ana_token"]).build()
        await app.initialize(); await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
    except: pass

if __name__ == "__main__":
    # Render'da hızı artırmak için iş parçacığı yönetimi
    threading.Thread(target=lambda: asyncio.run(bot_start())).start()
    web_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), threaded=True)
