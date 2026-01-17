import os, asyncio, threading, httpx, datetime, base64
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from telegram.ext import ApplicationBuilder

# --- SİSTEM AYARLARI ---
SISTEM = {
    "apis": {}, 
    "admin_id": 7690743437,
    "ana_token": "8586246924:AAEdEGEQn9tjBBAQKw-nJ_NvDG5P-G3T8cc",
    "panel_sifre": "19786363",
    "baslangic": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
}

web_app = Flask(__name__)
web_app.secret_key = "nabi_ultra_fix"

# --- HIZ VE TAKILMA ENGELLEYİCİ (Global Client) ---
# Bağlantıları canlı tutar (Keep-Alive), böylece sorgular takılmaz.
limits = httpx.Limits(max_connections=100, max_keepalive_connections=50)
global_client = httpx.AsyncClient(timeout=20.0, limits=limits, follow_redirects=True)

# --- TASARIMLAR (Hamburger & Meta Verified) ---
# (Önceki tasarımların en stabil hali entegre edilmiştir)
HTML_ADMIN = """ ... (Admin tasarımı aynı kalsın) ... """
HTML_SITE = """ ... (Sorgu ekranı tasarımı aynı kalsın) ... """

# --- YOLLAR (ROUTES) ---

@web_app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template_string('<body style="background:#000;color:white;text-align:center;padding-top:100px;font-family:sans-serif;"><h2>🔐 Giriş</h2><form method="POST" action="/login"><input type="password" name="s" style="padding:10px; border-radius:5px;"><br><br><button style="padding:10px 20px; background:#0095f6; color:white; border:none; border-radius:5px;">GİRİŞ</button></form></body>')
    return redirect(url_for('admin'))

@web_app.route('/login', methods=['POST'])
def login():
    if request.form.get('s') == SISTEM["panel_sifre"]:
        session['logged_in'] = True
        return redirect(url_for('admin'))
    return "Hatalı Şifre!"

@web_app.route('/admin')
def admin():
    if not session.get('logged_in'): return redirect(url_for('home'))
    return render_template_string(HTML_ADMIN, apis=SISTEM["apis"])

@web_app.route('/site')
def site():
    return render_template_string(HTML_SITE, apis=SISTEM["apis"])

@web_app.route('/add_api')
def add_api():
    name = request.args.get('name')
    url_b64 = request.args.get('url')
    if name and url_b64:
        SISTEM["apis"][name] = base64.b64decode(url_b64).decode()
    return jsonify({"status":"ok"})

@web_app.route('/del_api')
def del_api():
    name = request.args.get('name')
    if name in SISTEM["apis"]: del SISTEM["apis"][name]
    return jsonify({"status":"ok"})

# --- KRİTİK: SORGULAMA FONKSİYONU ---
@web_app.route('/do_web_sorgu')
async def do_web_sorgu():
    name = request.args.get('name')
    val = request.args.get('val')
    api_url = SISTEM["apis"].get(name)
    
    if not api_url:
        return jsonify({"result": "❌ Hata: Bu sorgu için API tanımlanmamış!"})

    try:
        # Global client kullanarak asenkron sorgu (Takılmayı önleyen kısım)
        response = await global_client.get(api_url + val)
        
        # Yanıt boşsa veya hata kodu döndüyse yakala
        if response.status_code != 200:
            return jsonify({"result": f"⚠️ API Sunucusu Hata Döndürdü (Kod: {response.status_code})"})
            
        return jsonify({"result": response.text})
    except httpx.TimeoutException:
        return jsonify({"result": "⏰ Hata: API sunucusu çok geç yanıt veriyor (Zaman aşımı)."})
    except Exception as e:
        return jsonify({"result": f"❌ Sistemsel Hata: {str(e)}"})

# --- BOT VE ÇALIŞTIRMA ---
async def bot_start():
    try:
        app = ApplicationBuilder().token(SISTEM["ana_token"]).build()
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
    except:
        pass

if __name__ == "__main__":
    # Botu ayrı bir thread'de, Web app'i ana thread'de çalıştırıyoruz.
    threading.Thread(target=lambda: asyncio.run(bot_start())).start()
    # threaded=True ekleyerek Render'da çoklu istekleri hızlandırıyoruz.
    web_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), threaded=True)
