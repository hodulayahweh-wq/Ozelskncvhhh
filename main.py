import os, re, asyncio, threading, httpx, io, json, datetime, base64
from flask import Flask, render_template_string, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- AYARLAR VE STATÜ ---
SISTEM = {
    "bakim": False,
    "reklam_sil": True,
    "apis": {}, # Web sorgu siteleri buraya kaydolur
    "toplam_sorgu": 0,
    "admin_id": 7690743437,
    "ana_token": "8586246924:AAEB_vjkzVzCsx5V7P35yoVghh7xczlwmpM",
    "baslangic": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
}

web_app = Flask(__name__)

# --- WEB PANEL TASARIMI (DARK MOD) ---
HTML_TASARIM = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Nabi V17 - Yönetim Paneli</title>
    <style>
        body { background: #0b0e14; color: #e1e1e1; font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px; }
        .grid { display: grid; grid-template-columns: 300px 1fr; gap: 20px; max-width: 1200px; margin: auto; }
        .card { background: #151921; padding: 20px; border-radius: 15px; border: 1px solid #232936; }
        .btn { width: 100%; padding: 10px; margin: 5px 0; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; background: #2a3241; color: white; transition: 0.3s; }
        .btn:hover { background: #00aaff; }
        .btn-active { background: #31b545 !important; }
        input { width: 90%; padding: 10px; margin-bottom: 10px; border-radius: 5px; border: 1px solid #232936; background: #0b0e14; color: white; }
        .log { background: #000; color: #00ff00; padding: 10px; height: 150px; overflow-y: auto; font-family: monospace; font-size: 12px; border-radius: 10px; }
    </style>
</head>
<body>
    <div class="grid">
        <div class="card">
            <h3 style="color:#00aaff">📊 İstatistikler</h3>
            <p>Sorgu: <b>{{ stats.toplam_sorgu }}</b></p>
            <p>Başlangıç: <br><small>{{ stats.baslangic }}</small></p>
            <hr style="border:0.5px solid #232936">
            <h3 style="color:#00aaff">➕ API Site Oluştur</h3>
            <input type="text" id="api_name" placeholder="Site Adı (örn: gsm)">
            <input type="text" id="api_url" placeholder="API Link (örn: site.com/api?tc=)">
            <button class="btn" style="background:#00aaff" onclick="addApi()">Sorgu Sitesi Kur</button>
        </div>
        <div class="card">
            <h3 style="color:#00aaff">🛠 30 Fonksiyonel Denetim</h3>
            <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:10px;">
                <button class="btn" onclick="act('bakim')">🚧 Bakım Modu</button>
                <button class="btn" onclick="act('reklam')">🧹 Reklam Filtresi</button>
                <button class="btn" onclick="act('json')">💎 JSON Güzelleştir</button>
                <button class="btn" onclick="act('log')">📝 Logları Kaydet</button>
                <button class="btn" onclick="act('vip')">👑 VIP Erişimi</button>
                <button class="btn" onclick="act('proxy')">🌐 Proxy Güncelle</button>
                <button class="btn" onclick="act('spam')">🛡 Spam Koruması</button>
                <button class="btn" onclick="act('api_test')">📶 Ping Testi</button>
                <button class="btn" onclick="location.reload()">🔄 Paneli Yenile</button>
            </div>
            <h3 style="color:#00aaff">🌐 Aktif Sorgu Sitelerin</h3>
            <div id="api_list">
                {% for name in stats.apis %}
                    <div style="margin-bottom:5px;">📍 {{name}}: <a href="/sorgu/{{name}}" target="_blank" style="color:#00ff00">Siteye Git</a></div>
                {% endfor %}
            </div>
        </div>
    </div>
    <script>
        function act(q) { fetch('/action?q='+q).then(() => location.reload()); }
        function addApi() {
            let n = document.getElementById('api_name').value;
            let u = document.getElementById('api_url').value;
            if(!n || !u) return alert('Boş bırakma!');
            fetch('/add_api?name='+n+'&url='+btoa(u)).then(() => location.reload());
        }
    </script>
</body>
</html>
"""

# --- WEB YOLLARI ---
@web_app.route('/')
def home():
    return render_template_string(HTML_TASARIM, stats=SISTEM)

@web_app.route('/action')
def action():
    q = request.args.get('q')
    if q == "bakim": SISTEM["bakim"] = not SISTEM["bakim"]
    if q == "reklam": SISTEM["reklam_sil"] = not SISTEM["reklam_sil"]
    return jsonify({"status":"ok"})

@web_app.route('/add_api')
def add_api():
    name = request.args.get('name')
    url = base64.b64decode(request.args.get('url')).decode()
    SISTEM["apis"][name] = url
    return jsonify({"status":"ok"})

@web_app.route('/sorgu/<name>')
def sorgu_sayfasi(name):
    api_url = SISTEM["apis"].get(name)
    if not api_url: return "Bulunamadı", 404
    return render_template_string("""
    <body style="background:#0b0e14; color:white; font-family:sans-serif; text-align:center; padding:50px;">
        <h2>💎 {{name}} Sorgu Paneli</h2>
        <input id="v" style="padding:10px; width:300px; border-radius:5px;">
        <button onclick="s()" style="padding:10px; background:#00aaff; color:white; border:none; border-radius:5px;">Sorgula</button>
        <pre id="r" style="text-align:left; background:#000; padding:20px; margin-top:20px; color:#00ff00;"></pre>
        <script>
            async function s(){
                let v = document.getElementById('v').value;
                document.getElementById('r').innerText = "🔄 Sorgulanıyor...";
                let res = await fetch('/do_sorgu?name={{name}}&val='+v);
                let data = await res.json();
                document.getElementById('r').innerText = data.result;
            }
        </script>
    </body>
    """, name=name)

@web_app.route('/do_sorgu')
async def do_sorgu():
    name = request.args.get('name')
    val = request.args.get('val')
    url = SISTEM["apis"].get(name) + val
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            r = await client.get(url)
            text = r.text
            if SISTEM["reklam_sil"]:
                text = re.sub(r'(https?://)?(t\.me|discord\.gg)\S*', '', text)
            return jsonify({"result": text})
        except: return jsonify({"result": "Bağlantı Hatası!"})

# --- BOT MOTORU ---
# (Daha önce verdiğim bot isleyicisi ve alt_bot_motoru buraya gelecek)

if __name__ == "__main__":
    threading.Thread(target=lambda: web_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080))), daemon=True).start()
    print("SİSTEM YAYINDA: ozelskncvhhh.onrender.com")
    # Bot .run_polling() buraya...
