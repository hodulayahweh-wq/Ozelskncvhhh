import os, re, asyncio, threading, httpx, json, datetime, base64
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- SİSTEM AYARLARI ---
SISTEM = {
    "apis": {}, 
    "admin_id": 7690743437,
    "ana_token": "8586246924:AAEdEGEQn9tjBBAQKw-nJ_NvDG5P-G3T8cc", # Kendi bot tokenini buraya yaz
    "panel_sifre": "19786363",
    "toplam_sorgu": 0,
    "bakim": False,
    "baslangic": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
}

web_app = Flask(__name__)
web_app.secret_key = "nabi_gizli_anahtar"

# --- HTML TASARIMLARI (TÜMÜ EKLENDİ) ---

HTML_LOGIN = """
<body style="background:#0b0e14; color:white; font-family:sans-serif; text-align:center; padding-top:100px;">
    <div style="display:inline-block; background:#151921; padding:40px; border-radius:15px; border:1px solid #232936; box-shadow: 0 0 20px #00aaff33;">
        <h2 style="color:#00aaff">🔐 Nabi System Giriş</h2>
        <form method="POST" action="/login">
            <input type="password" name="sifre" placeholder="Giriş Şifresi" style="padding:12px; border-radius:5px; border:none; width:220px; background:#0b0e14; color:white; border:1px solid #333;"><br><br>
            <button type="submit" style="padding:10px 30px; background:#00aaff; color:white; border:none; border-radius:5px; cursor:pointer; font-weight:bold;">SİSTEME GİRİŞ</button>
        </form>
        {% if error %}<p style="color:#ff4444; margin-top:15px;">❌ Hatalı Şifre!</p>{% endif %}
    </div>
</body>
"""

HTML_ADMIN = """
<body style="background:#0b0e14; color:white; font-family:sans-serif; padding:20px;">
    <div style="max-width:1100px; margin:auto;">
        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #232936; padding-bottom:15px; margin-bottom:20px;">
            <h1 style="color:#00aaff; margin:0;">🚀 Nabi V19 Pro Panel</h1>
            <div style="text-align:right;">
                <small style="color:#555">Başlangıç: {{ stats.baslangic }}</small><br>
                <a href="/logout" style="color:#ff4444; text-decoration:none; font-weight:bold;">Çıkış Yap</a>
            </div>
        </div>
        
        <div style="display:grid; grid-template-columns: 320px 1fr; gap:25px;">
            <div style="background:#151921; padding:20px; border-radius:12px; border:1px solid #232936;">
                <h3 style="color:#00aaff; margin-top:0;">🌐 Sorgu Sitesi Kur</h3>
                <input type="text" id="api_name" placeholder="Site Adı (Örn: gsm)" style="width:90%; padding:10px; margin-bottom:10px; border-radius:5px; background:#0b0e14; color:white; border:1px solid #333;">
                <input type="text" id="api_url" placeholder="API URL (sonu = olsun)" style="width:90%; padding:10px; margin-bottom:15px; border-radius:5px; background:#0b0e14; color:white; border:1px solid #333;">
                <button onclick="siteKur()" style="width:100%; padding:12px; background:#00aaff; color:white; border:none; border-radius:8px; cursor:pointer; font-weight:bold;">SİTEYİ OLUŞTUR</button>
                <hr style="border:0.5px solid #232936; margin:20px 0;">
                <h4 style="margin-bottom:10px;">📍 Aktif Sitelerin:</h4>
                <div style="max-height:200px; overflow-y:auto;">
                {% for name in apis %}
                    <div style="background:#0b0e14; padding:8px; border-radius:5px; margin-bottom:5px; font-size:13px; border-left:3px solid #00aaff;">
                        <b>{{name}}</b> <br>
                        <a href="/sorgu/{{name}}" target="_blank" style="color:#00ff00; font-size:11px;">Siteye Git 🔗</a>
                    </div>
                {% endfor %}
                </div>
            </div>

            <div style="background:#151921; padding:20px; border-radius:12px; border:1px solid #232936;">
                <h3 style="color:#00aaff; margin-top:0;">🛠 30 Panel Özelliği</h3>
                <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:10px;">
                    <button class="btn" onclick="cmd('Bakim')">🚧 Bakım</button>
                    <button class="btn" onclick="cmd('Reklam')">🧹 Reklam</button>
                    <button class="btn" onclick="cmd('JSON')">💎 JSON</button>
                    <button class="btn" onclick="cmd('VIP')">👑 VIP</button>
                    <button class="btn" onclick="cmd('Kanal')">📣 Kanal</button>
                    <button class="btn" onclick="cmd('Log')">📝 Log</button>
                    <button class="btn" onclick="cmd('Hiz')">⚡ Hız</button>
                    <button class="btn" onclick="cmd('Spam')">🛡 Spam</button>
                    <button class="btn" onclick="cmd('Ping')">📶 Ping</button>
                    <button class="btn" onclick="cmd('Ban')">🚫 Ban</button>
                    <button class="btn" onclick="cmd('Proxy')">🌐 Proxy</button>
                    <button class="btn" onclick="cmd('Yedek')">💾 Yedek</button>
                    <button class="btn" style="background:#444" onclick="location.reload()">🔄 Yenile</button>
                </div>
                <div id="logs" style="margin-top:20px; background:#000; color:#00ff00; padding:15px; border-radius:8px; height:120px; font-family:monospace; font-size:12px; overflow-y:auto; border:1px solid #333;">
                    >> [SİSTEM]: Yönetici Bağlandı.<br>>> [STATUS]: Bot Aktif.
                </div>
            </div>
        </div>
    </div>
    <style> .btn { padding:12px 5px; background:#2a3241; color:white; border:none; border-radius:8px; cursor:pointer; font-size:11px; font-weight:bold; } .btn:hover { background:#00aaff; } </style>
    <script>
        function siteKur() {
            let n = document.getElementById('api_name').value;
            let u = document.getElementById('api_url').value;
            if(!n || !u) return alert('Boş Bırakma!');
            fetch('/add_api?name='+n+'&url='+btoa(u)).then(() => location.reload());
        }
        function cmd(t) {
            document.getElementById('logs').innerHTML += "<br>>> [ADMİN]: " + t + " komutu gönderildi.";
            fetch('/admin_action?q=' + t);
        }
    </script>
</body>
"""

HTML_SORGU_SAYFASI = """
<body style="background:#0b0e14; color:white; font-family:sans-serif; text-align:center; padding:50px;">
    <div style="max-width:500px; margin:auto; background:#151921; padding:30px; border-radius:20px; border:1px solid #232936; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
        <h2 style="color:#00aaff">🔍 {{name}} Sorgu Paneli</h2>
        <p style="color:#888; font-size:14px;">Sorgulanacak numarayı veya TC'yi girin:</p>
        <input id="val" placeholder="Değer giriniz..." style="width:80%; padding:15px; border-radius:10px; border:none; margin-bottom:15px; font-size:16px; background:#0b0e14; color:white; border:1px solid #333;">
        <br>
        <button onclick="ara()" style="width:80%; padding:15px; background:#00aaff; color:white; border:none; border-radius:10px; font-weight:bold; cursor:pointer; font-size:16px;">SORGULA</button>
        <div id="sonuc" style="text-align:left; background:#000; padding:20px; border-radius:10px; margin-top:20px; font-family:monospace; color:#00ff00; font-size:13px; min-height:50px; border:1px solid #232936; overflow-x:auto; white-space:pre-wrap;">Sonuç burada görünecek...</div>
    </div>
    <script>
        async function ara() {
            let v = document.getElementById('val').value;
            if(!v) return alert('Değer girin!');
            const resBox = document.getElementById('sonuc');
            resBox.innerText = "🔄 Sorgulanıyor, lütfen bekleyin...";
            let res = await fetch('/do_sorgu?name={{name}}&val=' + v);
            let data = await res.json();
            resBox.innerText = data.result;
        }
    </script>
</body>
"""

# --- WEB ENDPOINTS ---

@web_app.route('/')
def home():
    if not session.get('logged_in'): return render_template_string(HTML_LOGIN)
    return render_template_string(HTML_ADMIN, apis=SISTEM["apis"], stats=SISTEM)

@web_app.route('/login', methods=['POST'])
def login():
    if request.form.get('sifre') == SISTEM["panel_sifre"]:
        session['logged_in'] = True
        return redirect(url_for('home'))
    return render_template_string(HTML_LOGIN, error=True)

@web_app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

@web_app.route('/add_api')
def add_api():
    if not session.get('logged_in'): return "Yetkisiz", 403
    name = request.args.get('name')
    url = base64.b64decode(request.args.get('url')).decode()
    SISTEM["apis"][name] = url
    return jsonify({"status":"ok"})

@web_app.route('/sorgu/<name>')
def view_sorgu(name):
    if name not in SISTEM["apis"]: return "Site Bulunamadı", 404
    return render_template_string(HTML_SORGU_SAYFASI, name=name)

@web_app.route('/do_sorgu')
async def do_sorgu():
    name = request.args.get('name')
    val = request.args.get('val')
    api_url = SISTEM["apis"].get(name)
    if not api_url: return jsonify({"result": "API Hatası!"})
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            r = await client.get(api_url + val)
            return jsonify({"result": r.text})
        except: return jsonify({"result": "Bağlantı Kurulamadı (API Çevrimdışı)!"})

# --- BOT SİSTEMİ ---
async def start(u, c):
    kb = [[InlineKeyboardButton("📢 Kanal", url="https://t.me/nabisystemyeni")]]
    await u.message.reply_text("🚀 **Nabi System V19 Aktif!**\n\nPanel ve bot senkronize çalışıyor.", reply_markup=InlineKeyboardMarkup(kb))

async def bot_baslat():
    try:
        app = ApplicationBuilder().token(SISTEM["ana_token"]).build()
        app.add_handler(CommandHandler("start", start))
        await app.initialize(); await app.start(); await app.updater.start_polling(drop_pending_updates=True)
    except: pass

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(bot_baslat())).start()
    web_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
