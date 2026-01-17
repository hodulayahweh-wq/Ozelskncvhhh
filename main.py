import os, re, asyncio, threading, httpx, json, datetime, base64
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- AYARLAR ---
SISTEM = {
    "apis": {}, 
    "admin_id": 7690743437,
    "ana_token": "8586246924:AAEdEGEQn9tjBBAQKw-nJ_NvDG5P-G3T8cc", # Kendi tokenini buraya yaz
    "panel_sifre": "19786363",
    "toplam_sorgu": 0,
    "bakim": False,
    "baslangic": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
}

web_app = Flask(__name__)
web_app.secret_key = "nabi_secret_key"

# --- WEB PANEL TASARIMI ---
HTML_LOGIN = """
<body style="background:#0b0e14; color:white; font-family:sans-serif; text-align:center; padding-top:100px;">
    <div style="display:inline-block; background:#151921; padding:40px; border-radius:15px; border:1px solid #232936;">
        <h2 style="color:#00aaff">🔐 Nabi System Giriş</h2>
        <form method="POST" action="/login">
            <input type="password" name="sifre" placeholder="Giriş Şifresi" style="padding:12px; border-radius:5px; border:none; width:200px;"><br><br>
            <button type="submit" style="padding:10px 30px; background:#00aaff; color:white; border:none; border-radius:5px; cursor:pointer;">GİRİŞ YAP</button>
        </form>
        {% if error %}<p style="color:red;">Hatalı Şifre!</p>{% endif %}
    </div>
</body>
"""

HTML_ADMIN = """
<body style="background:#0b0e14; color:white; font-family:sans-serif; padding:20px;">
    <div style="max-width:1000px; margin:auto;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <h1 style="color:#00aaff">🚀 Nabi System V18 Admin</h1>
            <a href="/logout" style="color:red; text-decoration:none;">Çıkış Yap</a>
        </div>
        
        <div style="display:grid; grid-template-columns: 1fr 2fr; gap:20px;">
            <div style="background:#151921; padding:20px; border-radius:10px; border:1px solid #232936;">
                <h3>🌐 Sorgu Sitesi Oluştur</h3>
                <input type="text" id="n" placeholder="Site Adı" style="width:90%; padding:10px; margin-bottom:10px; border-radius:5px; background:#0b0e14; color:white; border:1px solid #333;">
                <input type="text" id="u" placeholder="API URL (sonu = olsun)" style="width:90%; padding:10px; margin-bottom:10px; border-radius:5px; background:#0b0e14; color:white; border:1px solid #333;">
                <button onclick="addApi()" style="width:100%; padding:10px; background:#00aaff; color:white; border:none; border-radius:5px; cursor:pointer; font-weight:bold;">SİTEYİ KUR</button>
                <hr style="border:0.5px solid #232936; margin:20px 0;">
                <h4>📍 Aktif Sitelerin:</h4>
                {% for name in apis %}
                    <p style="font-size:14px;">✅ {{name}}: <a href="/sorgu/{{name}}" target="_blank" style="color:#00ff00">Linke Git</a></p>
                {% endfor %}
            </div>

            <div style="background:#151921; padding:20px; border-radius:10px; border:1px solid #232936;">
                <h3>🛠 Sistem Özellikleri</h3>
                <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:10px;">
                    <button class="btn" onclick="act('Bakım')">🚧 Bakım Modu</button>
                    <button class="btn" onclick="act('Reklam')">🧹 Reklam Sil</button>
                    <button class="btn" onclick="act('JSON')">💎 JSON Düzenle</button>
                    <button class="btn" onclick="act('VIP')">👑 VIP Modu</button>
                    <button class="btn" onclick="act('Kanal')">📣 Kanal Zorunlu</button>
                    <button class="btn" onclick="act('Log')">📝 Log Kaydı</button>
                    <button class="btn" onclick="act('Hız')">⚡ Hız Limiti</button>
                    <button class="btn" onclick="act('Spam')">🛡 Spam Koruma</button>
                    <button class="btn" onclick="act('Ping')">📶 API Ping</button>
                    <button class="btn" style="background:#444" onclick="location.reload()">🔄 Verileri Yenile</button>
                </div>
                <div id="log-box" style="margin-top:15px; background:#000; color:#31b545; padding:10px; border-radius:5px; height:80px; font-family:monospace; font-size:12px; overflow-y:auto;">
                    >> Sistem Hazır.
                </div>
            </div>
        </div>
    </div>
    <style> .btn { padding:10px; background:#2a3241; color:white; border:none; border-radius:5px; cursor:pointer; font-size:11px; } .btn:hover { background:#3182ce; } </style>
    <script>
        function addApi() {
            let n = document.getElementById('n').value;
            let u = document.getElementById('u').value;
            fetch('/add_api?name='+n+'&url='+btoa(u)).then(() => location.reload());
        }
        function act(type) {
            document.getElementById('log-box').innerHTML += "<br>>> [İŞLEM]: " + type + " tetiklendi.";
            fetch('/admin_action?q=' + type);
        }
    </script>
</body>
"""

# --- WEB YOLLARI ---
@web_app.route('/')
def home():
    if not session.get('logged_in'): return render_template_string(HTML_LOGIN)
    return render_template_string(HTML_ADMIN, apis=SISTEM["apis"])

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
    return render_template_string("...Sorgu Sayfası Kodu...", name=name) # (Önceki V17'deki sorgu sayfası)

# --- BOT BAŞLATMA ---
async def bot_baslat():
    app = ApplicationBuilder().token(SISTEM["ana_token"]).build()
    # Handlerları ekle...
    await app.initialize(); await app.start(); await app.updater.start_polling()

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(bot_baslat())).start()
    web_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
