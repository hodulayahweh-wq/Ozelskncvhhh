import os, re, asyncio, threading, httpx, json, datetime, base64
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

# --- GLOBAL SİSTEM VERİLERİ ---
SISTEM = {
    "apis": {}, 
    "admin_id": 7690743437,
    "ana_token": "8586246924:AAEdEGEQn9tjBBAQKw-nJ_NvDG5P-G3T8cc", # Kendi tokenini kontrol et
    "panel_sifre": "19786363",
    "baslangic": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
    "ayarlar": {"bakim": False, "reklam_filtre": True}
}

web_app = Flask(__name__)
web_app.secret_key = "nabi_turbo_key"

# --- 1. ADMIN PANEL TASARIMI (HIZLI API YÖNETİMİ) ---
HTML_ADMIN = """
<!DOCTYPE html>
<html>
<head>
    <title>Nabi V21 Admin</title>
    <style>
        body { background: #050505; color: white; font-family: sans-serif; padding: 20px; }
        .card { background: #111; padding: 20px; border-radius: 15px; border: 1px solid #222; max-width: 900px; margin: auto; }
        input { padding: 12px; background: #000; border: 1px solid #333; color: white; border-radius: 8px; margin-right: 10px; width: 30%; }
        button { padding: 12px 25px; background: #0095f6; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; }
        .btn-mini { padding: 5px 10px; font-size: 10px; background: #cc3333; }
        .stat-box { display: flex; gap: 20px; margin-bottom: 20px; }
        .stat { background: #1a1a1a; padding: 15px; border-radius: 10px; flex: 1; text-align: center; }
    </style>
</head>
<body>
    <div class="card">
        <h2>⚙️ Nabi Turbo Admin</h2>
        <div class="stat-box">
            <div class="stat">Sistem: <span style="color:#31b545">Aktif</span></div>
            <div class="stat">API Sayısı: {{ apis|length }}</div>
        </div>
        <h3>🚀 Yeni API / Sorgu Ekle</h3>
        <input type="text" id="an" placeholder="Sorgu Adı (Örn: GSM)">
        <input type="text" id="au" placeholder="API Link (sonu =)">
        <button onclick="save()">SİSTEME EKLE</button>
        <hr style="border: 0.5px solid #222; margin: 25px 0;">
        <div id="list">
            {% for name in apis %}
                <div style="display:flex; justify-content:space-between; background:#1a1a1a; padding:10px; margin-bottom:5px; border-radius:8px;">
                    <span>✅ {{ name }}</span>
                    <button class="btn-mini" onclick="del('{{name}}')">SİL</button>
                </div>
            {% endfor %}
        </div>
        <br>
        <a href="/site" target="_blank" style="text-decoration:none; display:block; text-align:center; background:#31b545; color:white; padding:15px; border-radius:10px; font-weight:bold;">🌐 SORGU SİTESİNİ AÇ</a>
    </div>
    <script>
        function save() {
            let n = document.getElementById('an').value;
            let u = document.getElementById('au').value;
            if(!n || !u) return alert('Doldur!');
            fetch('/add_api?name='+n+'&url='+btoa(u)).then(() => location.reload());
        }
        function del(name) {
            fetch('/del_api?name='+name).then(() => location.reload());
        }
    </script>
</body>
</html>
"""

# --- 2. SORGULAMA SİTESİ (ANİMASYONLU & HAMBURGER MENÜ & META VERIFIED) ---
HTML_SITE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nabi Search | Verified</title>
    <style>
        :root { --accent: #0095f6; --bg: #000; }
        body { margin:0; background: var(--bg); color:white; font-family: -apple-system, sans-serif; overflow:hidden; }
        
        /* Arka Plan Animasyonu */
        .bg-glow { position: fixed; top: 50%; left: 50%; width: 500px; height: 500px; background: radial-gradient(circle, rgba(0,149,246,0.15) 0%, transparent 70%); transform: translate(-50%, -50%); z-index: -1; filter: blur(50px); animation: move 20s infinite alternate; }
        @keyframes move { 0% { transform: translate(-60%, -40%); } 100% { transform: translate(-40%, -60%); } }

        /* Mavi Tık Rozeti */
        .mavi-tik { display:inline-block; width:20px; height:20px; background:url('https://upload.wikimedia.org/wikipedia/commons/e/e4/Twitter_Verified_Badge.svg'); background-size:contain; margin-left:8px; vertical-align:middle; }

        /* Hamburger Menü (Üst Orta) */
        .nav-trigger { position:fixed; top:20px; left:50%; transform:translateX(-50%); z-index:100; background:rgba(255,255,255,0.05); padding:12px 30px; border-radius:50px; border:1px solid rgba(255,255,255,0.1); cursor:pointer; backdrop-filter:blur(15px); font-weight:bold; transition:0.3s; }
        .nav-trigger:hover { border-color: var(--accent); color: var(--accent); }

        .overlay { position:fixed; top:-100%; left:0; width:100%; height:100%; background:rgba(0,0,0,0.98); z-index:99; transition:0.6s cubic-bezier(0.85, 0, 0.15, 1); display:flex; flex-direction:column; align-items:center; justify-content:center; }
        .overlay.active { top:0; }
        .nav-item { font-size:28px; color:white; text-decoration:none; margin:15px; transition:0.3s; cursor:pointer; font-weight:bold; }
        .nav-item:hover { color: var(--accent); transform:scale(1.1); }

        /* Sorgu Alanı */
        .hero { height:100vh; display:flex; flex-direction:column; align-items:center; justify-content:center; }
        .search-container { width:90%; max-width:450px; text-align:center; animation: slideUp 0.8s ease; }
        @keyframes slideUp { from { opacity:0; transform:translateY(30px); } to { opacity:1; transform:translateY(0); } }

        input { width:100%; padding:18px; border-radius:15px; border:1px solid #222; background:#0a0a0a; color:white; font-size:18px; outline:none; transition:0.3s; box-sizing:border-box; }
        input:focus { border-color: var(--accent); box-shadow: 0 0 20px rgba(0,149,246,0.2); }
        
        .btn-search { width:100%; padding:18px; margin-top:15px; border-radius:15px; border:none; background:var(--accent); color:white; font-size:18px; font-weight:bold; cursor:pointer; transition:0.3s; }
        .btn-search:hover { transform:scale(0.98); opacity:0.9; }

        #out { margin-top:20px; background:#0a0a0a; border:1px solid #1a1a1a; padding:20px; border-radius:15px; text-align:left; font-family:monospace; color:#4ade80; font-size:14px; display:none; max-height:250px; overflow-y:auto; white-space:pre-wrap; }
    </style>
</head>
<body>
    <div class="bg-glow"></div>
    <div class="nav-trigger" onclick="toggle()">☰ SORGULARI GÖRÜNTÜLE</div>

    <div class="overlay" id="menu">
        <h2 style="color:var(--accent)">Sorgu Seçenekleri<span class="mavi-tik"></span></h2>
        {% for name in apis %}
            <div class="nav-item" onclick="selectApi('{{name}}')">{{name}}</div>
        {% endfor %}
        <div onclick="toggle()" style="margin-top:40px; color:#555; cursor:pointer;">KAPAT</div>
    </div>

    <div class="hero">
        <div class="search-container">
            <h1 id="h-title">Nabi System<span class="mavi-tik"></span></h1>
            <p id="h-subtitle" style="color:#666">Başlamak için yukarıdan bir sorgu türü seçin.</p>
            
            <div id="search-form" style="display:none;">
                <h3 id="selected-name" style="color:var(--accent)"></h3>
                <input type="text" id="query-val" placeholder="Sorgulanacak veriyi girin...">
                <button class="btn-search" onclick="runSearch()">HIZLI SORGULA</button>
                <div id="out"></div>
            </div>
        </div>
    </div>

    <script>
        let current = "";
        function toggle() { document.getElementById('menu').classList.toggle('active'); }
        
        function selectApi(name) {
            current = name;
            document.getElementById('h-title').style.display = 'none';
            document.getElementById('h-subtitle').style.display = 'none';
            document.getElementById('search-form').style.display = 'block';
            document.getElementById('selected-name').innerText = "📍 " + name;
            toggle();
        }

        async function runSearch() {
            const v = document.getElementById('query-val').value;
            const o = document.getElementById('out');
            if(!v) return;
            o.style.display = "block";
            o.innerText = "⚡ API Yanıtı bekleniyor...";
            const res = await fetch('/do_web_sorgu?name=' + current + '&val=' + v);
            const data = await res.json();
            o.innerText = data.result;
        }
    </script>
</body>
</html>
"""

# --- 3. FLASK ENDPOINTS ---

@web_app.route('/')
def home():
    if not session.get('logged_in'): 
        return render_template_string('<body style="background:#000;color:white;text-align:center;padding-top:100px;font-family:sans-serif;">'
                                      '<h2>🔐 Nabi Giriş</h2><form method="POST" action="/login">'
                                      '<input type="password" name="s" style="padding:10px; border-radius:5px;"><br><br>'
                                      '<button style="padding:10px 20px; background:#0095f6; color:white; border:none; border-radius:5px;">GİRİŞ</button></form></body>')
    return redirect(url_for('admin'))

@web_app.route('/login', methods=['POST'])
def login():
    if request.form.get('s') == SISTEM["panel_sifre"]:
        session['logged_in'] = True
        return redirect(url_for('admin'))
    return "Hatalı şifre!"

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
    url = base64.b64decode(request.args.get('url')).decode()
    SISTEM["apis"][name] = url
    return jsonify({"status":"ok"})

@web_app.route('/del_api')
def del_api():
    name = request.args.get('name')
    if name in SISTEM["apis"]: del SISTEM["apis"][name]
    return jsonify({"status":"ok"})

@web_app.route('/do_web_sorgu')
async def do_web_sorgu():
    name = request.args.get('name')
    val = request.args.get('val')
    api_url = SISTEM["apis"].get(name)
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            r = await client.get(api_url + val)
            return jsonify({"result": r.text})
        except: return jsonify({"result": "Bağlantı Hatası!"})

# --- 4. BOT VE ÇALIŞTIRMA ---
async def bot_baslat():
    try:
        app = ApplicationBuilder().token(SISTEM["ana_token"]).build()
        await app.initialize(); await app.start(); await app.updater.start_polling()
    except: pass

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(bot_baslat())).start()
    web_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
p.start(); await app.updater.start_polling(drop_pending_updates=True)
    except: pass

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(bot_baslat())).start()
    web_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
