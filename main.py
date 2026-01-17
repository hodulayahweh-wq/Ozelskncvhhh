import os, datetime, base64, json, re, httpx
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for

# --- SISTEM AYARLARI ---
SISTEM = {
    "apis": {}, 
    "admin_sifre": "19786363",         # Admin Giriş Şifresi
    "sorgu_sifre": "2026lordfreepanel", # VIP Panel Giriş Keyi
    "resim_url": "https://share.google/Y6jQivMUWZlRyBfzh",
    "baslangic": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
}

web_app = Flask(__name__)
web_app.secret_key = "lord_v39_final_fixed"

def temizle(metin):
    if not isinstance(metin, str): metin = str(metin)
    metin = re.sub(r'(https?://)?t\.me/\S+', '', metin)
    metin = re.sub(r'@\S+', '', metin)
    metin = re.sub(r'(Sorgu Paneli|Reklam|İletişim|Telegram|Satın Al|zyrdaware|2026tr)', '', metin, flags=re.I)
    return metin.strip()

# --- TASARIM: ADMIN PANELI ---
HTML_ADMIN = """
<body style="background:#000; color:white; font-family:sans-serif; padding:20px;">
    <div style="max-width:800px; margin:auto; background:#111; padding:30px; border-radius:20px; border:1px solid #222;">
        <h2>LORD Admin Kontrol</h2>
        <div style="background:#1a1a1a; padding:15px; border-radius:12px; margin-bottom:20px;">
            <h3>Gorsel ve Sifre Ayarlari</h3>
            <input type="text" id="rurl" value="{{resim}}" placeholder="Resim URL" style="width:100%; padding:10px; background:#000; color:white; border:1px solid #333; margin-bottom:10px;">
            <div style="display:flex; gap:10px;">
                <input type="text" id="as" value="{{asifre}}" style="flex:1; padding:8px; background:#000; color:white; border:1px solid #333;">
                <input type="text" id="ss" value="{{ssifre}}" style="flex:1; padding:8px; background:#000; color:white; border:1px solid #333;">
            </div>
            <button onclick="updateSettings()" style="width:100%; background:#34c759; color:white; border:none; padding:12px; border-radius:8px; margin-top:10px; cursor:pointer;">AYARLARI KAYDET</button>
        </div>
        <div id="list">
            {% for name in apis %}
                <div style="display:flex; justify-content:space-between; background:#0a0a0a; padding:12px; margin-bottom:8px; border-radius:8px; border-left:4px solid #0095f6;">
                    <span>Sorgu: {{ name }}</span>
                    <button onclick="del('{{name}}')" style="background:red; color:white; border:none; border-radius:4px; padding:5px 10px;">SIL</button>
                </div>
            {% endfor %}
        </div>
    </div>
    <script>
    function del(n){fetch('/del_api?name='+n).then(()=>location.reload());}
    function updateSettings(){
        let a = document.getElementById('as').value;
        let s = document.getElementById('ss').value;
        let r = btoa(document.getElementById('rurl').value);
        fetch('/update_settings?admin='+a+'&sorgu='+s+'&resim='+r).then(()=>alert('Guncellendi!'));
    }
    </script>
</body>"""

# --- TASARIM: VIP SITE ---
HTML_SITE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LORD VIP PANEL</title>
    <style>
        body { margin:0; background: #000; color:white; font-family:sans-serif; overflow:hidden; }
        .sidebar { position:fixed; top:0; left:-280px; width:260px; height:100%; z-index:2000; transition:0.4s; padding:20px; box-sizing:border-box; background: #0a0a0a; border-right:1px solid #333; }
        .sidebar.active { left:0; }
        .nav-item { padding:14px; margin-bottom:8px; border-radius:12px; cursor:pointer; background: rgba(255,255,255,0.05); border:1px solid #222; }
        .header { position:fixed; top:0; width:100%; height:60px; background:rgba(0,0,0,0.9); display:flex; align-items:center; padding:0 20px; z-index:1000; border-bottom:1px solid #222; }
        .img-container { width:280px; height:280px; margin-bottom:20px; border-radius:30px; border:3px solid #0095f6; overflow:hidden; box-shadow: 0 0 20px rgba(0,149,246,0.4); }
        .card { background:#0a0a0a; padding:30px; border-radius:24px; border:1px solid #222; width:90%; max-width:400px; text-align:center; }
        input { width:100%; padding:15px; margin-bottom:15px; border-radius:12px; border:1px solid #333; background:#000; color:white; outline:none; }
        button { width:100%; padding:15px; border-radius:12px; border:none; background:#0095f6; color:white; font-weight:bold; cursor:pointer; }
        #res { margin-top:20px; background:#000; padding:15px; border-radius:12px; text-align:left; white-space:pre-wrap; display:none; color:#4ade80; border-left:4px solid #0095f6; max-height:200px; overflow-y:auto; font-size:12px; }
    </style>
</head>
<body>
    <div class="header"><div onclick="toggleMenu()" style="font-size:24px; cursor:pointer;">☰</div><div style="margin-left:15px; font-weight:bold;">LORD VIP</div></div>
    <div class="sidebar" id="sidebar">
        <h3>LORD MENU</h3>
        <div class="nav-item" onclick="location.reload()">ANA SAYFA</div>
        <hr style="border:0; border-top:1px solid #333;">
        {% for name in apis %}
            <div class="nav-item" onclick="loadSorgu('{{name}}')">{{name}}</div>
        {% endfor %}
        <div style="margin-top:20px;">
            <a href="https://t.me/lordsystemv" style="color:#0095f6; text-decoration:none; display:block; margin-bottom:10px;">Kanal: @lordsystemv</a>
            <a href="https://t.me/LordDestekHat" style="color:gray; text-decoration:none;">Destek: @LordDestekHat</a>
        </div>
    </div>
    <div style="min-height:100vh; display:flex; flex-direction:column; align-items:center; justify-content:center;">
        <div id="home-screen" style="text-align:center;">
            <div class="img-container"><img src="{{resim}}" style="width:100%; height:100%; object-fit:cover;"></div>
            <h1>HOS GELDIN LORD</h1>
            <button onclick="toggleMenu()" style="width:200px; border-radius:30px;">BASLA</button>
        </div>
        <div id="sorgu-screen" style="display:none;" class="card">
            <h2 id="stitle"></h2>
            <div id="input-container"></div>
            <button onclick="execSorgu()">SORGULA</button>
            <div id="res"></div>
            <button id="dbtn" onclick="downloadResult()" style="background:#34c759; margin-top:10px; display:none;">VERILERI INDIR</button>
        </div>
    </div>
    <script>
        function toggleMenu() { document.getElementById('sidebar').classList.toggle('active'); }
        function loadSorgu(name) {
            window.currentSorgu = name;
            document.getElementById('home-screen').style.display = 'none';
            document.getElementById('sorgu-screen').style.display = 'block';
            document.getElementById('stitle').innerText = name;
            document.getElementById('input-container').innerHTML = name.toLowerCase().includes("ad soyad") ? '<input id="v1" placeholder="Ad"><input id="v2" placeholder="Soyad">' : '<input id="v1" placeholder="Veri girin">';
            toggleMenu();
        }
        async function execSorgu() {
            const v1 = document.getElementById('v1').value;
            const v2 = document.getElementById('v2') ? document.getElementById('v2').value : "";
            const resBox = document.getElementById('res');
            resBox.style.display = "block"; resBox.innerText = "Sorgulaniyor...";
            const r = await fetch(`/do_sorgu?name=${window.currentSorgu}&val=${v1}&val2=${v2}`);
            const data = await r.json();
            resBox.innerText = typeof data.result === 'object' ? JSON.stringify(data.result, null, 2) : data.result;
            document.getElementById('dbtn').style.display = "block";
        }
        function downloadResult() {
            const text = document.getElementById('res').innerText;
            const blob = new Blob([text], {type: "text/plain"});
            const a = document.createElement("a");
            a.href = URL.createObjectURL(blob);
            a.download = "lord_sonuc.txt";
            a.click();
        }
    </script>
</body>
</html>"""

# --- BACKEND ---
@web_app.route('/vip_login', methods=['GET', 'POST'])
def vip_login():
    if request.method == 'POST' and request.form.get('p') == SISTEM["sorgu_sifre"]:
        session['vip'] = True
        return redirect(url_for('site'))
    return '<body style="background:#000;color:white;text-align:center;padding-top:100px;"><h2>VIP GIRIS</h2><form method="POST"><input type="password" name="p" placeholder="Key"><button>GIR</button></form></body>'

@web_app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('p') == SISTEM["admin_sifre"]:
        session['admin'] = True
        return redirect(url_for('admin'))
    return '<body style="background:#000;color:white;text-align:center;padding-top:100px;"><h2>Admin</h2><form method="POST"><input type="password" name="p"><button>GIR</button></form></body>'

@web_app.route('/admin')
def admin():
    if not session.get('admin'): return redirect(url_for('login'))
    return render_template_string(HTML_ADMIN, apis=SISTEM["apis"], asifre=SISTEM["admin_sifre"], ssifre=SISTEM["sorgu_sifre"], resim=SISTEM["resim_url"])

@web_app.route('/site')
def site():
    if not session.get('vip'): return redirect(url_for('vip_login'))
    return render_template_string(HTML_SITE, apis=SISTEM["apis"], resim=SISTEM["resim_url"])

@web_app.route('/update_settings')
def update_settings():
    if not session.get('admin'): return "No"
    SISTEM["admin_sifre"] = request.args.get('admin')
    SISTEM["sorgu_sifre"] = request.args.get('sorgu')
    SISTEM["resim_url"] = base64.b64decode(request.args.get('resim')).decode()
    return jsonify({"status":"ok"})

@web_app.route('/do_sorgu')
def do_sorgu():
    if not session.get('vip'): return jsonify({"result":"No"})
    n=request.args.get('name'); v1=request.args.get('val'); v2=request.args.get('val2', '')
    api = SISTEM["apis"].get(n)
    if not api: return jsonify({"result":"API Hata"})
    url = api + v1
    if v2 and "ad=" in api: url = api + v1 + "&soyad=" + v2
    try:
        with httpx.Client(timeout=30.0) as c:
            r = c.get(url)
            return jsonify({"result": temizle(r.text)})
    except: return jsonify({"result":"Hata!"})

@web_app.route('/add_api')
def add_api():
    if session.get('admin'): SISTEM["apis"][request.args.get('name')] = base64.b64decode(request.args.get('url')).decode()
    return "ok"

@web_app.route('/del_api')
def del_api():
    if session.get('admin'):
        n = request.args.get('name')
        if n in SISTEM["apis"]: del SISTEM["apis"][n]
    return "ok"

@web_app.route('/')
def home(): return redirect(url_for('site'))

if __name__ == "__main__":
    web_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
; border:1px solid #333;"><h2>🔐 VIP GİRİŞ</h2><form method="POST"><input type="password" name="p" placeholder="Key Girin" style="padding:15px; border-radius:10px; border:1px solid #444; background:#000; color:white; width:250px; text-align:center;"><br><br><button style="background:#0095f6; color:white; border:none; padding:12px 30px; border-radius:10px; cursor:pointer; font-weight:bold;">SİSTEME GİR</button></form></div></body>'

@web_app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('p') == SISTEM["admin_sifre"]:
        session['admin'] = True
        return redirect(url_for('admin'))
    return '<body style="background:#000;color:white;text-align:center;padding-top:100px;font-family:sans-serif;"><h2>Admin Girişi</h2><form method="POST"><input type="password" name="p" style="padding:10px;"><button style="padding:10px;">GİRİŞ</button></form></body>'

@web_app.route('/admin')
def admin():
    if not session.get('admin'): return redirect(url_for('login'))
    return render_template_string(HTML_ADMIN, apis=SISTEM["apis"], asifre=SISTEM["admin_sifre"], ssifre=SISTEM["sorgu_sifre"], resim=SISTEM["resim_url"])

@web_app.route('/update_settings')
def update_settings():
    if not session.get('admin'): return "No"
    SISTEM["admin_sifre"] = request.args.get('admin')
    SISTEM["sorgu_sifre"] = request.args.get('sorgu')
    SISTEM["resim_url"] = base64.b64decode(request.args.get('resim')).decode()
    return jsonify({"status":"ok"})

@web_app.route('/site')
def site():
    if not session.get('vip'): return redirect(url_for('vip_login'))
    return render_template_string(HTML_SITE, apis=SISTEM["apis"], resim=SISTEM["resim_url"])

@web_app.route('/do_sorgu')
def do_sorgu():
    if not session.get('vip'): return jsonify({"result":"No"})
    n=request.args.get('name'); v1=request.args.get('val'); v2=request.args.get('val2', '')
    api = SISTEM["apis"].get(n)
    if not api: return jsonify({"result":"API Hata"})
    url = api + v1
    if v2 and "ad=" in api: url = api + v1 + "&soyad=" + v2
    try:
        with httpx.Client(timeout=30.0) as c:
            r = c.get(url)
            return jsonify({"result": temizle(r.text)})
    except: return jsonify({"result":"Hata!"})

@web_app.route('/add_api')
def add_api():
    if session.get('admin'): SISTEM["apis"][request.args.get('name')] = base64.b64decode(request.args.get('url')).decode()
    return "ok"

@web_app.route('/del_api')
def del_api():
    if session.get('admin'):
        n = request.args.get('name')
        if n in SISTEM["apis"]: del SISTEM["apis"][n]
    return "ok"

@web_app.route('/')
def home(): return redirect(url_for('site'))

if __name__ == "__main__":
    web_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
ERİLERİ GETİR</button>
            <div id="res"></div>
            <button onclick="downloadResult()" id="dbtn" style="background:#34c759; margin-top:10px; display:none;">📄 SONUÇLARI İNDİR (.TXT)</button>
        </div>
    </div>

    <script>
        let currentSorgu = "";
        function toggleMenu() { document.getElementById('sidebar').classList.toggle('active'); }
        function goHome() {
            document.getElementById('home-screen').style.display = 'block';
            document.getElementById('sorgu-screen').style.display = 'none';
            toggleMenu();
        }
        function loadSorgu(name) {
            currentSorgu = name;
            document.getElementById('home-screen').style.display = 'none';
            document.getElementById('sorgu-screen').style.display = 'block';
            document.getElementById('stitle').innerText = name;
            document.getElementById('res').style.display = 'none';
            document.getElementById('dbtn').style.display = 'none';
            
            const cont = document.getElementById('input-container');
            if(name.toLowerCase().includes("ad soyad")) {
                cont.innerHTML = '<input type="text" id="v1" placeholder="Adını girin..."><input type="text" id="v2" placeholder="Soyadını girin...">';
            } else {
                cont.innerHTML = '<input type="text" id="v1" placeholder="Sorgu verisini girin...">';
            }
            toggleMenu();
        }

        async function execSorgu() {
            const v1 = document.getElementById('v1').value;
            const v2 = document.getElementById('v2') ? document.getElementById('v2').value : "";
            const resBox = document.getElementById('res');
            if(!v1) return;
            resBox.style.display = "block"; resBox.innerText = "⚡ LORD SİSTEM SORGULUYOR...";
            
            try {
                let url = `/do_sorgu?name=${currentSorgu}&val=${v1}`;
                if(v2) url += `&val2=${v2}`;
                const r = await fetch(url);
                const data = await r.json();
                resBox.innerText = typeof data.result === 'object' ? JSON.stringify(data.result, null, 2) : data.result;
                document.getElementById('dbtn').style.display = 'block';
            } catch { resBox.innerText = "❌ Hata: API Bağlantısı Kesildi!"; }
        }

        function downloadResult() {
            const text = document.getElementById('res').innerText;
            const blob = new Blob([text], {type: "text/plain"});
            const a = document.createElement("a");
            a.href = URL.createObjectURL(blob);
            a.download = currentSorgu + "_lord_sonuc.txt";
            a.click();
        }
    </script>
</body>
</html>"""

# --- BACKEND ---
@web_app.route('/')
def index(): return redirect(url_for('site'))

@web_app.route('/vip_login', methods=['GET', 'POST'])
def vip_login():
    if request.method == 'POST':
        if request.form.get('p') == SISTEM["sorgu_sifre"]:
            session['vip'] = True
            return redirect(url_for('site'))
    return '<body style="background:#000;color:white;text-align:center;padding-top:100px;font-family:sans-serif;"><div style="background:#0a0a0a;display:inline-block;padding:40px;border-radius:24px;border:1px solid #333;"><h2>🔐 LORD VIP GİRİŞ</h2><form method="POST"><input type="password" name="p" placeholder="Anahtar Kodu Girin" style="padding:15px; border-radius:12px; border:1px solid #444; background:#000; color:white; width:260px; text-align:center;"><br><br><button style="background:#0095f6;color:white;border:none;padding:12px 40px;border-radius:12px;cursor:pointer;font-weight:bold;">SİSTEME GİR</button></form></div></body>'

@web_app.route('/site')
def site():
    if not session.get('vip'): return redirect(url_for('vip_login'))
    return render_template_string(HTML_SITE, apis=SISTEM["apis"], resim=SISTEM["resim_url"])

@web_app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('p') == SISTEM["admin_sifre"]:
            session['admin'] = True
            return redirect(url_for('admin'))
    return '<body style="background:#000;color:white;text-align:center;padding-top:100px;"><form method="POST"><h2>Admin</h2><input type="password" name="p"><button>GİR</button></form></body>'

@web_app.route('/admin')
def admin():
    if not session.get('admin'): return redirect(url_for('login'))
    return render_template_string(HTML_ADMIN, apis=SISTEM["apis"], asifre=SISTEM["admin_sifre"], ssifre=SISTEM["sorgu_sifre"], resim=SISTEM["resim_url"])

@web_app.route('/update_settings')
def update_settings():
    if not session.get('admin'): return "No"
    SISTEM["admin_sifre"] = request.args.get('admin')
    SISTEM["sorgu_sifre"] = request.args.get('sorgu')
    res_b64 = request.args.get('resim')
    if res_b64: SISTEM["resim_url"] = base64.b64decode(res_b64).decode()
    return jsonify({"status":"ok"})

@web_app.route('/add_api')
def add_api():
    if not session.get('admin'): return "No"
    n=request.args.get('name'); u=request.args.get('url')
    if n and u: SISTEM["apis"][n] = base64.b64decode(u).decode()
    return jsonify({"status":"ok"})

@web_app.route('/del_api')
def del_api():
    if not session.get('admin'): return "No"
    n=request.args.get('name')
    if n in SISTEM["apis"]: del SISTEM["apis"][n]
    return jsonify({"status":"ok"})

@web_app.route('/do_sorgu')
def do_sorgu():
    if not session.get('vip'): return jsonify({"result":"No"})
    name=request.args.get('name'); v1=request.args.get('val'); v2=request.args.get('val2', '')
    api_url = SISTEM["apis"].get(name)
    if not api_url: return jsonify({"result": "API Error"})
    try:
        final_url = api_url + v1
        if v2 and "ad=" in api_url: final_url = api_url + v1 + "&soyad=" + v2
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            r = client.get(final_url)
            temiz_veri = temizle(r.text)
            try: return jsonify({"result": json.loads(temiz_veri)})
            except: return jsonify({"result": temiz_veri})
    except Exception as e: return jsonify({"result": f"Error: {str(e)}"})

if __name__ == "__main__":
    web_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
