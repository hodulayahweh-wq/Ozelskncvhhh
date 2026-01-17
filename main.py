import os
import datetime
import base64
import re
import httpx
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for

# Environment'tan güvenli okuma
ADMIN_SIFRE = os.environ.get("ADMIN_SIFRE", "19786363")
VIP_SIFRE   = os.environ.get("VIP_SIFRE",   "2026lordfreepanel")
SECRET_KEY  = os.environ.get("SECRET_KEY",  "super-secret-lord-panel-2026-random-xyz")

SISTEM = {
    "apis": {},
    "admin_sifre": ADMIN_SIFRE,
    "sorgu_sifre": VIP_SIFRE,
    "resim_url": "https://i.ibb.co/XfXvXzH/1000012099.png",
    "baslangic": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
}

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['SESSION_COOKIE_SAMESITE'] = "Lax"
app.config['SESSION_COOKIE_SECURE'] = False

def temizle(metin):
    if not isinstance(metin, str):
        metin = str(metin)
    metin = re.sub(r'(https?://)?t\.me/\S+', '', metin)
    metin = re.sub(r'@\S+', '', metin)
    metin = re.sub(r'(Sorgu Paneli|Reklam|Iletisim|Telegram|Satin Al|zyrdaware|2026tr)', '', metin, flags=re.I)
    return metin.strip()

# ── Admin paneli HTML ────────────────────────────────────────────────
HTML_ADMIN = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LORD Admin</title>
    <style>
        body {background:#000;color:#eee;font-family:Arial,sans-serif;margin:0;padding:15px;}
        .container {max-width:900px;margin:auto;background:#111;padding:20px;border-radius:12px;border:1px solid #333;}
        h2 {color:#0af;text-align:center;margin-bottom:25px;}
        .settings {background:#1a1a1a;padding:18px;border-radius:10px;margin-bottom:20px;}
        input {width:100%;padding:12px;margin:8px 0;background:#000;color:#fff;border:1px solid #444;border-radius:6px;box-sizing:border-box;font-size:15px;}
        .flex {display:flex;gap:12px;}
        button {width:100%;padding:14px;background:#0af;color:#fff;border:none;border-radius:8px;font-weight:bold;cursor:pointer;margin:10px 0;}
        .api {display:flex;justify-content:space-between;align-items:center;background:#0d0d0d;padding:12px;border-radius:8px;margin:6px 0;border-left:4px solid #0af;}
        .del {background:#e00;padding:8px 16px;border:none;border-radius:6px;color:#fff;cursor:pointer;font-size:14px;}
    </style>
</head>
<body>
    <div class="container">
        <h2>LORD Admin Panel</h2>
        <div class="settings">
            <h3>Ayarlar</h3>
            <input id="rurl" value="{{resim}}" placeholder="Resim URL">
            <div class="flex">
                <input id="as" value="{{asifre}}" placeholder="Admin Şifresi">
                <input id="ss" value="{{ssifre}}" placeholder="VIP Key">
            </div>
            <button onclick="kaydet()">KAYDET</button>
        </div>
        <h3>API'ler</h3>
        {% for name in apis %}
        <div class="api">
            <span>{{ name }}</span>
            <button class="del" onclick="sil('{{ name | e }}')">SİL</button>
        </div>
        {% else %}
        <p style="text-align:center;color:#888;">Henüz API yok</p>
        {% endfor %}
    </div>
    <script>
    function sil(name){
        if(confirm(name + " silinecek mi?")){
            fetch("/del_api?name=" + encodeURIComponent(name))
                .then(() => location.reload());
        }
    }
    function kaydet(){
        let as = document.getElementById("as").value;
        let ss = document.getElementById("ss").value;
        let rurl = btoa(document.getElementById("rurl").value.trim());
        let url = "/update_settings?admin=" + encodeURIComponent(as) +
                  "&sorgu=" + encodeURIComponent(ss) +
                  "&resim=" + rurl;
        fetch(url)
            .then(r => r.json())
            .then(d => alert(d.status || "Hata oluştu"));
    }
    </script>
</body>
</html>
"""

# Basit login sayfaları
ADMIN_LOGIN_HTML = """
<!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Admin Giriş</title>
<style>body{background:#000;color:#fff;text-align:center;padding:100px 20px;font-family:sans-serif;}
h2{color:#0af;} input,button{font-size:18px;padding:14px;border-radius:8px;border:1px solid #444;}
input{background:#111;color:#fff;width:90%;max-width:400px;}
button{background:#0af;color:white;border:none;cursor:pointer;}</style></head>
<body><h2>ADMIN GİRİŞ</h2><form method="POST">
<input type="password" name="p" placeholder="Şifre" required><br><br>
<button type="submit">GİRİŞ YAP</button></form></body></html>
"""

VIP_LOGIN_HTML = """
<!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>VIP Giriş</title>
<style>body{background:#000;color:#fff;text-align:center;padding:100px 20px;font-family:sans-serif;}
h2{color:#0af;} input,button{font-size:18px;padding:14px;border-radius:8px;border:1px solid #444;}
input{background:#111;color:#fff;width:90%;max-width:400px;}
button{background:#0af;color:white;border:none;cursor:pointer;}</style></head>
<body><h2>LORD VIP PANEL GİRİŞ</h2><form method="POST">
<input type="password" name="p" placeholder="VIP Key" required><br><br>
<button type="submit">GİRİŞ YAP</button></form></body></html>
"""

@app.route('/')
def ana_sayfa():
    return redirect(url_for('vip_giris'))

@app.route('/vip_giris', methods=['GET', 'POST'])
def vip_giris():
    if request.method == 'POST':
        if request.form.get('p') == SISTEM["sorgu_sifre"]:
            session['vip'] = True
            return redirect(url_for('site'))
        return '<h2 style="color:red;text-align:center;padding:100px;">YANLIŞ KEY!</h2>'
    return VIP_LOGIN_HTML

@app.route('/admin_giris', methods=['GET', 'POST'])
def admin_giris():
    if request.method == 'POST':
        if request.form.get('p') == SISTEM["admin_sifre"]:
            session['admin'] = True
            return redirect(url_for('admin'))
        return '<h2 style="color:red;text-align:center;padding:100px;">YANLIŞ ŞİFRE!</h2>'
    return ADMIN_LOGIN_HTML

@app.route('/admin')
def admin():
    if 'admin' not in session:
        return redirect(url_for('admin_giris'))
    return render_template_string(HTML_ADMIN,
                                  apis=SISTEM["apis"],
                                  asifre=SISTEM["admin_sifre"],
                                  ssifre=SISTEM["sorgu_sifre"],
                                  resim=SISTEM["resim_url"])

@app.route('/update_settings')
def update_settings():
    if 'admin' not in session:
        return jsonify({"status": "yetkisiz"})
    SISTEM["admin_sifre"] = request.args.get('admin', SISTEM["admin_sifre"])
    SISTEM["sorgu_sifre"] = request.args.get('sorgu', SISTEM["sorgu_sifre"])
    b64 = request.args.get('resim')
    if b64:
        try:
            SISTEM["resim_url"] = base64.b64decode(b64).decode('utf-8')
        except:
            pass
    return jsonify({"status": "tamam"})

# ── VIP ana sayfa (senin orijinal büyük HTML'ini buraya koyabilirsin) ──
@app.route('/site')
def site():
    if 'vip' not in session:
        return redirect(url_for('vip_giris'))
    # Placeholder – senin orijinal HTML'ini buraya render_template_string ile koy
    return f"""
    <h1 style="color:#0af;text-align:center;padding:80px;">
        Hoş geldin LORD VIP<br>
        <img src="{SISTEM['resim_url']}" width="200"><br>
        (Buraya tam VIP panel HTML kodun gelecek)
    </h1>
    """

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
