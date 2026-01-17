import os
import datetime
import base64
import re
import httpx
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for

# ── Environment'tan oku ────────────────────────────────────────────────
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

# ── VIP GİRİŞ HTML (çalışan hali aynı kaldı) ───────────────────────────
VIP_LOGIN_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LORD VIP Giriş</title>
    <style>
        body {background:#000;color:#fff;text-align:center;padding:80px 20px;font-family:sans-serif;}
        h2 {color:#0095f6;}
        input, button {padding:14px;font-size:17px;border-radius:8px;border:1px solid #444;}
        input {background:#111;color:#fff;width:90%;max-width:380px;}
        button {background:#0095f6;color:#fff;border:none;cursor:pointer;font-weight:bold;}
    </style>
</head>
<body>
    <h2>LORD VIP PANEL</h2><br>
    <form method="POST">
        <input type="password" name="p" placeholder="VIP Key" required><br><br>
        <button type="submit">GİRİŞ YAP</button>
    </form>
</body>
</html>
"""

# ── ADMIN GİRİŞ HTML (VIP ile aynı yapı) ───────────────────────────────
ADMIN_LOGIN_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Giriş</title>
    <style>
        body {background:#000;color:#fff;text-align:center;padding:80px 20px;font-family:sans-serif;}
        h2 {color:#0095f6;}
        input, button {padding:14px;font-size:17px;border-radius:8px;border:1px solid #444;}
        input {background:#111;color:#fff;width:90%;max-width:380px;}
        button {background:#0095f6;color:#fff;border:none;cursor:pointer;font-weight:bold;}
    </style>
</head>
<body>
    <h2>ADMIN PANEL GİRİŞ</h2><br>
    <form method="POST">
        <input type="password" name="p" placeholder="Admin Şifresi" required><br><br>
        <button type="submit">GİRİŞ YAP</button>
    </form>
</body>
</html>
"""

# ── ROUTES ─────────────────────────────────────────────────────────────

@app.route('/')
def home():
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
        girilen = request.form.get('p', '').strip()
        beklenen = SISTEM["admin_sifre"]
        
        # Log için debug çıktısı
        print(f"[ADMIN GİRİŞ DENEMESİ] Girilen: '{girilen}' | Beklenen: '{beklenen}'")
        
        if girilen == beklenen:
            session['admin'] = True
            print("[ADMIN] Giriş BAŞARILI → session admin=True")
            return redirect(url_for('admin'))
        else:
            print("[ADMIN] Giriş BAŞARISIZ")
            return '<h2 style="color:red;text-align:center;padding:100px;">YANLIŞ ŞİFRE!</h2>'
    
    return ADMIN_LOGIN_HTML

@app.route('/admin')
def admin():
    if 'admin' not in session:
        print("[ADMIN SAYFA] Session'da admin yok → yönlendirme")
        return redirect(url_for('admin_giris'))
    
    print("[ADMIN SAYFA] Giriş başarılı, panel gösteriliyor")
    return render_template_string(HTML_ADMIN, 
                                 apis=SISTEM["apis"],
                                 asifre=SISTEM["admin_sifre"],
                                 ssifre=SISTEM["sorgu_sifre"],
                                 resim=SISTEM["resim_url"])

# Senin orijinal admin panel HTML'i (kısaltılmış hali, tam halini sen koyabilirsin)
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
        input {width:100%;padding:12px;margin:8px 0;background:#000;color:#fff;border:1px solid #444;border-radius:6px;}
        button {width:100%;padding:14px;background:#0af;color:#fff;border:none;border-radius:8px;font-weight:bold;cursor:pointer;margin:10px 0;}
    </style>
</head>
<body>
    <div class="container">
        <h2>LORD Admin Panel</h2>
        <h3>Hoş geldin! (Giriş başarılı)</h3>
        <p>Şu anki admin şifresi: {{ asifre }}</p>
        <p>VIP şifresi: {{ ssifre }}</p>
        <p>Resim URL: {{ resim }}</p>
        <!-- Buraya senin tam admin panel içeriğini koyabilirsin -->
    </div>
</body>
</html>
"""

# VIP site (senin orijinal büyük HTML'ini buraya koy)
@app.route('/site')
def site():
    if 'vip' not in session:
        return redirect(url_for('vip_giris'))
    # Senin orijinal VIP panel HTML'ini buraya render_template_string ile koy
    return "<h1 style='color:#0095f6;text-align:center;padding:100px;'>VIP PANEL (çalışıyor)</h1>"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
