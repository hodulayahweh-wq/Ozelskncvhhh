import os, asyncio, threading, httpx, datetime, base64
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from telegram.ext import ApplicationBuilder

# --- AYARLAR ---
SISTEM = {
    "apis": {}, 
    "admin_id": 7690743437,
    "ana_token": "8586246924:AAEdEGEQn9tjBBAQKw-nJ_NvDG5P-G3T8cc",
    "panel_sifre": "19786363",
    "baslangic": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
}

web_app = Flask(__name__)
web_app.secret_key = "nabi_mega_turbo"

# HIZ İÇİN GLOBAL CLİENT: Bağlantıları havuzda tutar ve her sorguda yeniden açmaz.
client_limits = httpx.Limits(max_connections=100, max_keepalive_connections=50)
global_client = httpx.AsyncClient(timeout=15.0, limits=client_limits)

# --- TASARIMLAR ---
HTML_ADMIN = """
<body style="background:#050505; color:white; font-family:sans-serif; padding:20px;">
    <div style="max-width:800px; margin:auto; background:#111; padding:30px; border-radius:20px; border:1px solid #222;">
        <h2 style="color:#0095f6">⚙️ Admin Paneli</h2>
        <input type="text" id="an" placeholder="Sorgu Adı" style="padding:10px; background:#000; color:white; border:1px solid #333; width:30%;">
        <input type="text" id="au" placeholder="API Link (sonu =)" style="padding:10px; background:#000; color:white; border:1px solid #333; width:45%;">
        <button onclick="save()" style="padding:10px 20px; background:#0095f6; color:white; border:none; border-radius:5px;">EKLE</button>
        <div id="list" style="margin-top:20px;">
            {% for name in apis %}
            <div style="background:#0a0a0a; padding:10px; margin-bottom:5px; border-radius:8px; display:flex; justify-content:space-between;">
                <span>✅ {{ name }}</span>
                <button onclick="del('{{name}}')" style="background:red; border:none; color:white; border-radius:4px; padding:2px 8px;">SİL</button>
            </div>
            {% endfor %}
        </div>
        <br><a href="/site" target="_blank" style="display:block; text-align:center; background:#31b545; color:white; padding:15px; text-decoration:none; border-radius:10px; font-weight:bold;">SİTEYE GİT</a>
    </div>
    <script>
    function save() {
        let n = document.getElementById('an').value;
        let u = document.getElementById('au').value;
        if(n && u) fetch('/add_api?name='+n+'&url='+btoa(u)).then(() => location.reload());
    }
    function del(n) { fetch('/del_api?name='+n).then(() => location.reload()); }
    </script>
</body>
"""

HTML_SITE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nabi Verified</title>
    <style>
        :root { --blue: #0095f6; --bg: #000; }
        body { margin:0; background: var(--bg); color:white; font-family: -apple-system, sans-serif; overflow:hidden; }
        .tik { display:inline-block; width:18px; height:18px; background:url('https://upload.wikimedia.org/wikipedia/commons/e/e4/Twitter_Verified_Badge.svg') no-repeat center; background-size:contain; margin-left:6px; vertical-align:middle; }
        .h-btn { position:fixed; top:20px; left:50%; transform:translateX(-50%); z-index:100; background:rgba(255,255,255,0.07); padding:10px 25px; border-radius:30px; border:1px solid rgba(255,255,255,0.1); cursor:pointer; backdrop-filter:blur(10px); font-weight:bold; }
        .overlay { position:fixed; top:-100%; left:0; width:100%; height:100%; background:rgba(0,0,0,0.97); z-index:99; transition:0.5s; display:flex; flex-direction:column; align-items:center; justify-content:center; }
        .overlay.active { top:0; }
        .item { font-size:24px; color:white; text-decoration:none; margin:15px; cursor:pointer; font-weight:bold; }
        .main { height:100vh; display:flex; flex-direction:column; align-items:center; justify-content:center; }
        input { width:100%; max-width:400px; padding:15px; border-radius:12px; border:1px solid #222; background:#0a0a0a; color:white; }
        .btn { width:100%; max-width:400px; padding:15px; margin-top:12px; border-radius:12px; border:none; background:var(--blue); color:white; font-weight:bold; cursor:pointer; }
        #res { margin-top:20px; width:100%; max-width:400px; background:#0a0a0a; padding:15px; border-radius:12px; color:#4ade80; display:none; border:1px solid #1a1a1a; white-space:pre-wrap; }
    </style>
</head>
<body>
    <div class="h-btn" onclick="tgl()">☰ SORGULAR</div>
    <div class="overlay" id="menu">
        <h2 style="color:var(--blue)">Sorgu Seç<span class="tik"></span></h2>
        {% for name in apis %}<div class="item" onclick="sel('{{name}}')">{{name}}</div>{% endfor %}
        <div onclick="tgl()" style="margin-top:30px; color:#555; cursor:pointer;">KAPAT</div>
    </div>
    <div class="main">
        <h1 id="title">Nabi System<span class="tik"></span></h1>
        <div id="form" style="display:none; width:90%;">
            <h3 id="sname" style="color:var(--blue)"></h3>
            <input type="text" id="target" placeholder="Veri giriniz...">
            <button class="btn" onclick="sorgu()">HIZLI SORGULA</button>
            <div id="res"></div>
        </div>
    </div>
    <script>
    let cur = "";
    function tgl() { document.getElementById('menu').classList.toggle('active'); }
    function sel(n) { cur = n; document.getElementById('title').style.display = 'none'; document.getElementById('form').style.display = 'block'; document.getElementById('sname').innerText = "📍 " + n; tgl(); }
    async function sorgu() {
        const v = document.getElementById('target').value;
        const r = document.getElementById('res');
        if(!v) return;
        r.style.display = "block"; r.innerText = "⚡ Sorgulanıyor...";
        const res = await fetch('/do_web_sorgu?name='+cur+'&val='+v);
        const data = await res.json();
        r.innerText = data.result;
    }
    </script>
</body>
</html>
"""

# --- YOLLAR ---
@web_app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template_string('<body style="background:#000;color:white;text-align:center;padding-top:100px;"><h2>🔐 Giriş</h2><form method="POST" action="/login"><input type="password" name="s"><br><br><button>GİRİŞ</button></form></body>')
    return redirect(url_for('admin'))

@web_app.route('/login', methods=['POST'])
def login():
    if request.form.get('s') == SISTEM["panel_sifre"]:
        session['logged_in'] = True
        return redirect(url_for('admin'))
    return "Hatalı Şifre"

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

@web_app.route('/do_web_sorgu')
async def do_web_sorgu():
    name = request.args.get('name')
    val = request.args.get('val')
    api_url = SISTEM["apis"].get(name)
    if not api_url: return jsonify({"result": "API Yok!"})
    try:
        # HIZLI SORGULAMA: Açık tutulan global client kullanılır.
        r = await global_client.get(api_url + val)
        return jsonify({"result": r.text})
    except:
        return jsonify({"result": "Bağlantı Hatası!"})

async def bot_start():
    try:
        app = ApplicationBuilder().token(SISTEM["ana_token"]).build()
        await app.initialize(); await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
    except:
        pass

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(bot_start())).start()
    web_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
