import os
import datetime
import base64
import json
import re
import httpx
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for

# --- SISTEM AYARLARI ---
SISTEM = {
    "apis": {},
    "admin_sifre": "19786363",          # Admin şifresi
    "sorgu_sifre": "2026lordfreepanel", # VIP panel giriş key'i
    "resim_url": "https://i.ibb.co/XfXvXzH/1000012099.png",
    "baslangic": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "lord_ultimate_v41_final_2026_default")

def temizle(metin):
    if not isinstance(metin, str):
        metin = str(metin)
    metin = re.sub(r'(https?://)?t\.me/\S+', '', metin)
    metin = re.sub(r'@\S+', '', metin)
    metin = re.sub(r'(Sorgu Paneli|Reklam|Iletisim|Telegram|Satin Al|zyrdaware|2026tr)', '', metin, flags=re.I)
    return metin.strip()

# ── ADMIN PANEL HTML ────────────────────────────────────────
HTML_ADMIN = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LORD Admin</title>
    <style>
        body {background:#000;color:#fff;font-family:sans-serif;margin:0;padding:20px;}
        .container {max-width:800px;margin:auto;background:#111;padding:25px;border-radius:16px;border:1px solid #333;}
        h2 {color:#0095f6;text-align:center;}
        .card {background:#1a1a1a;padding:20px;border-radius:12px;margin:15px 0;}
        input {width:100%;padding:12px;margin:8px 0;background:#000;color:#fff;border:1px solid #444;border-radius:8px;box-sizing:border-box;}
        button {width:100%;padding:14px;background:#34c759;color:white;border:none;border-radius:8px;font-weight:bold;cursor:pointer;margin:10px 0;}
        .api-item {display:flex;justify-content:space-between;align-items:center;background:#0a0a0a;padding:12px;border-radius:8px;margin:8px 0;border-left:4px solid #0095f6;}
        .del-btn {background:#ff3b30;padding:8px 14px;border:none;border-radius:6px;color:white;cursor:pointer;}
    </style>
</head>
<body>
    <div class="container">
        <h2>LORD Admin Kontrol Paneli</h2>
        
        <div class="card">
            <h3>Ayarlar</h3>
            <input id="rurl" value="{{resim}}" placeholder="Resim URL">
            <div style="display:flex;gap:12px;">
                <input id="as" value="{{asifre}}" placeholder="Admin Şifresi">
                <input id="ss" value="{{ssifre}}" placeholder="VIP Şifresi">
            </div>
            <button onclick="updateSettings()">KAYDET</button>
        </div>

        <div id="api-list">
            {% for name in apis %}
            <div class="api-item">
                <span>{{ name }}</span>
                <button class="del-btn" onclick="del('{{name}}')">SİL</button>
            </div>
            {% else %}
            <p style="text-align:center;color:#888;">Henüz API eklenmemiş</p>
            {% endfor %}
        </div>
    </div>

    <script>
    function del(name) {
        if (confirm(name + " silinsin mi?")) {
            fetch('/del_api?name=' + encodeURIComponent(name))
                .then(() => location.reload());
        }
    }
    function updateSettings() {
        const admin = document.getElementById('as').value;
        const sorgu = document.getElementById('ss').value;
        const resim = btoa(document.getElementById('rurl').value || '');
        fetch(`/update_settings?admin=\( {encodeURIComponent(admin)}&sorgu= \){encodeURIComponent(sorgu)}&resim=${resim}`)
            .then(r => r.json())
            .then(data => alert(data.status === 'ok' ? 'Güncellendi!' : 'Hata!'));
    }
    </script>
</body>
</html>
"""

# ── VIP / ANA SAYFA HTML (öncekiyle aynı, ufak düzeltmeler) ──
HTML_SITE = """(buraya senin orijinal HTML_SITE kodunu olduğu gibi koyabilirsin - çok uzun olduğu için burada tekrar yazmıyorum, sadece aşağıdaki route'larda kullanıyoruz)"""

# Senin orijinal HTML_SITE kodunu buraya yapıştır (kısaltmamak için atladım)
# Eğer istersen onu da güncel haliyle verebilirim, ama şimdilik değişmedi varsayıyorum

# ── ROUTES ──────────────────────────────────────────────────

@app.route('/')
def home():
    return redirect(url_for('vip_login'))

@app.route('/vip_login', methods=['GET', 'POST'])
def vip_login():
    if request.method == 'POST':
        if request.form.get('p') == SISTEM["sorgu_sifre"]:
            session['vip'] = True
            session.permanent = True
            return redirect(url_for('site'))
        else:
            return "<h2 style='color:red;text-align:center;'>Yanlış Key!</h2>"
    return '''
    <body style="background:#000;color:white;text-align:center;padding:80px 20px;">
        <h2>LORD VIP PANEL GİRİŞ</h2><br>
        <form method="POST">
            <input type="password" name="p" placeholder="VIP Key girin" style="padding:14px;width:90%;max-width:400px;border-radius:10px;border:1px solid #444;background:#111;color:white;font-size:18px;"><br><br>
            <button type="submit" style="padding:14px 40px;background:#0095f6;color:white;border:none;border-radius:10px;font-size:18px;font-weight:bold;cursor:pointer;">GİRİŞ YAP</button>
        </form>
    </body>
    '''

@app.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('p') == SISTEM["admin_sifre"]:
            session['admin'] = True
            session.permanent = True
            return redirect(url_for('admin'))
        else:
            return "<h2 style='color:red;text-align:center;'>Yanlış Şifre!</h2>"
    return '''
    <body style="background:#000;color:white;text-align:center;padding:80px 20px;">
        <h2>ADMIN GİRİŞ</h2><br>
        <form method="POST">
            <input type="password" name="p" placeholder="Admin Şifresi" style="padding:14px;width:90%;max-width:400px;border-radius:10px;border:1px solid #444;background:#111;color:white;font-size:18px;"><br><br>
            <button type="submit" style="padding:14px 40px;background:#0095f6;color:white;border:none;border-radius:10px;font-size:18px;font-weight:bold;cursor:pointer;">GİRİŞ</button>
        </form>
    </body>
    '''

@app.route('/admin')
def admin():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    return render_template_string(HTML_ADMIN,
                                 apis=SISTEM["apis"],
                                 asifre=SISTEM["admin_sifre"],
                                 ssifre=SISTEM["sorgu_sifre"],
                                 resim=SISTEM["resim_url"])

@app.route('/site')
def site():
    if not session.get('vip'):
        return redirect(url_for('vip_login'))
    return render_template_string(HTML_SITE, apis=SISTEM["apis"], resim=SISTEM["resim_url"])

@app.route('/update_settings')
def update_settings():
    if not session.get('admin'):
        return jsonify({"status": "no_auth"})
    SISTEM["admin_sifre"] = request.args.get('admin', SISTEM["admin_sifre"])
    SISTEM["sorgu_sifre"] = request.args.get('sorgu', SISTEM["sorgu_sifre"])
    res_b64 = request.args.get('resim')
    if res_b64:
        try:
            SISTEM["resim_url"] = base64.b64decode(res_b64).decode('utf-8')
        except:
            pass
    return jsonify({"status": "ok"})

# ── Diğer route'lar (do_sorgu, add_api, del_api) aynı kalabilir ──
# Senin orijinal kodundaki bu kısımları olduğu gibi bırakabilirsin

@app.route('/do_sorgu')
def do_sorgu():
    if not session.get('vip'):
        return jsonify({"result": "Yetkisiz erişim"})
    # ... geri kalan aynı ...

@app.route('/add_api')
def add_api():
    if not session.get('admin'):
        return "No"
    name = request.args.get('name')
    url_b64 = request.args.get('url')
    if name and url_b64:
        try:
            SISTEM["apis"][name] = base64.b64decode(url_b64).decode('utf-8')
        except:
            return "Hatalı URL formatı"
    return "ok"

@app.route('/del_api')
def del_api():
    if not session.get('admin'):
        return "No"
    name = request.args.get('name')
    if name in SISTEM["apis"]:
        del SISTEM["apis"][name]
    return "ok"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)login'))
    return render_template_string(HTML_SITE, apis=SISTEM["apis"], resim=SISTEM["resim_url"])

@web_app.route('/update_settings')
def update_settings():
    if not session.get('admin'): return "No"
    SISTEM["admin_sifre"] = request.args.get('admin')
    SISTEM["sorgu_sifre"] = request.args.get('sorgu')
    res_b64 = request.args.get('resim')
    if res_b64: SISTEM["resim_url"] = base64.b64decode(res_b64).decode()
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
