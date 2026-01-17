import os, datetime, base64, json, re, httpx
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for

# --- SİSTEM AYARLARI ---
SISTEM = {
    "apis": {}, 
    "panel_sifre": "19786363", # Panel giriş şifren
    "baslangic": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
}

web_app = Flask(__name__)
web_app.secret_key = "nabi_ultra_secure_2026"

# --- REKLAM VE TELEGRAM LİNKİ TEMİZLEYİCİ ---
def temizle(metin):
    if not isinstance(metin, str): metin = str(metin)
    # t.me linklerini, @ kullanıcı adlarını ve reklam kelimelerini siler
    metin = re.sub(r'(https?://)?t\.me/\S+', '', metin)
    metin = re.sub(r'@\S+', '', metin)
    metin = re.sub(r'(Sorgu Paneli|Reklam|İletişim|Telegram|Satın Al)', '', metin, flags=re.I)
    return metin.strip()

# --- TASARIMLAR ---
HTML_ADMIN = """
<body style="background:#050505; color:white; font-family:sans-serif; padding:20px;">
    <div style="max-width:700px; margin:auto; background:#111; padding:30px; border-radius:20px; border:1px solid #222;">
        <h2 style="color:#0095f6">⚙️ Admin Paneli</h2>
        <div style="background:#1a1a1a; padding:15px; border-radius:12px; margin-bottom:20px;">
            <input type="text" id="an" placeholder="Sorgu Adı" style="padding:10px; background:#000; color:white; border:1px solid #333; width:35%; border-radius:5px;">
            <input type="text" id="au" placeholder="API Link (Sonu =)" style="padding:10px; background:#000; color:white; border:1px solid #333; width:40%; border-radius:5px;">
            <button onclick="save()" style="padding:10px; background:#0095f6; color:white; border:none; border-radius:5px; cursor:pointer;">EKLE</button>
        </div>
        <div id="list">
            {% for name in apis %}
                <div style="display:flex; justify-content:space-between; background:#0a0a0a; padding:12px; margin-bottom:8px; border-radius:8px; border-left:4px solid #0095f6;">
                    <span>✅ {{ name }}</span>
                    <button onclick="del('{{name}}')" style="background:red; color:white; border:none; border-radius:4px; cursor:pointer; padding:5px 10px;">SİL</button>
                </div>
            {% endfor %}
        </div>
        <br><a href="/site" target="_blank" style="display:block; text-align:center; background:#34c759; color:white; padding:15px; text-decoration:none; border-radius:10px; font-weight:bold;">🌐 SORGULAMA SİTESİNİ AÇ</a>
    </div>
    <script>
    function save(){let n=document.getElementById('an').value;let u=document.getElementById('au').value;if(n&&u)fetch('/add_api?name='+n+'&url='+btoa(u)).then(()=>location.reload());}
    function del(n){fetch('/del_api?name='+n).then(()=>location.reload());}
    </script>
</body>"""

HTML_SITE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sorgu Merkezi</title>
    <style>
        body { background:#000; color:white; font-family:sans-serif; margin:0; display:flex; align-items:center; justify-content:center; height:100vh; }
        .box { width:90%; max-width:400px; text-align:center; }
        .tik { display:inline-block; width:18px; height:18px; background:url('https://upload.wikimedia.org/wikipedia/commons/e/e4/Twitter_Verified_Badge.svg') no-repeat center; background-size:contain; margin-left:5px; vertical-align:middle; }
        select, input, button { width:100%; padding:15px; border-radius:12px; border:1px solid #333; background:#111; color:white; margin-bottom:10px; box-sizing:border-box; font-size:16px; }
        button { background:#0095f6; border:none; font-weight:bold; cursor:pointer; }
        #res { margin-top:20px; background:#0a0a0a; padding:15px; border-radius:12px; text-align:left; display:none; white-space:pre-wrap; font-family:monospace; font-size:13px; border:1px solid #222; color:#4ade80; max-height:250px; overflow-y:auto; }
    </style>
</head>
<body>
    <div class="box">
        <h1>Nabi Verified<span class="tik"></span></h1>
        <select id="api_select">{% for name in apis %}<option value="{{name}}">{{name}}</option>{% endfor %}</select>
        <input type="text" id="target" placeholder="Sorgulanacak veriyi girin...">
        <button onclick="sorgula()">HIZLI SORGULA</button>
        <div id="res"></div>
    </div>
    <script>
    async function sorgula() {
        const api = document.getElementById('api_select').value;
        const val = document.getElementById('target').value;
        const resDiv = document.getElementById('res');
        if(!val) return;
        resDiv.style.display = "block"; resDiv.innerText = "⚡ Sorgulanıyor...";
        try {
            const r = await fetch('/do_sorgu?name='+api+'&val='+val);
            const data = await r.json();
            resDiv.innerText = typeof data.result === 'object' ? JSON.stringify(data.result, null, 2) : data.result;
        } catch { resDiv.innerText = "❌ Hata oluştu!"; }
    }
    </script>
</body>
</html>"""

# --- BACKEND ---
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
    n=request.args.get('name'); u=request.args.get('url')
    if n and u: SISTEM["apis"][n] = base64.b64decode(u).decode()
    return jsonify({"status":"ok"})

@web_app.route('/del_api')
def del_api():
    n=request.args.get('name')
    if n in SISTEM["apis"]: del SISTEM["apis"][n]
    return jsonify({"status":"ok"})

@web_app.route('/do_sorgu')
def do_sorgu():
    name=request.args.get('name'); val=request.args.get('val')
    api_url = SISTEM["apis"].get(name)
    if not api_url: return jsonify({"result": "API Tanımsız!"})
    try:
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            r = client.get(api_url + val)
            temiz_veri = temizle(r.text)
            try:
                return jsonify({"result": json.loads(temiz_veri)})
            except:
                return jsonify({"result": temiz_veri})
    except Exception as e:
        return jsonify({"result": f"Bağlantı Hatası: {str(e)}"})

if __name__ == "__main__":
    web_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
