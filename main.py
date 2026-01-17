import os
import datetime
import base64
import re
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for

# ───────────── SABİT AYARLAR (ENV YOK – ÇAKIŞMA YOK) ─────────────
SECRET_KEY = "super-secret-lord-panel-2026"

SISTEM = {
    "apis": {},
    "admin_sifre": "19786363",
    "sorgu_sifre": "2026lordfreepanel",
    "resim_url": "https://i.ibb.co/XfXvXzH/1000012099.png",
    "baslangic": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
}

# ───────────── APP ─────────────
app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False

# ───────────── ADMIN HTML ─────────────
HTML_ADMIN = """
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>LORD Admin</title>
<style>
body{background:#000;color:#eee;font-family:Arial;padding:20px}
.box{max-width:900px;margin:auto;background:#111;padding:25px;border-radius:12px}
h2{color:#0af;text-align:center}
input,button{width:100%;padding:12px;margin:8px 0;background:#000;color:#fff;border:1px solid #444;border-radius:8px}
button{background:#0af;font-weight:bold;cursor:pointer}
</style>
</head>
<body>
<div class="box">
<h2>LORD ADMIN PANEL</h2>

<label>Logo URL</label>
<input id="rurl" value="{{resim}}">

<label>Admin Şifre</label>
<input id="as" value="{{asifre}}">

<label>VIP Key</label>
<input id="ss" value="{{ssifre}}">

<button onclick="kaydet()">KAYDET</button>
</div>

<script>
function kaydet(){
    let r = btoa(document.getElementById("rurl").value.trim());
    let a = document.getElementById("as").value;
    let s = document.getElementById("ss").value;

    fetch(`/update_settings?admin=${encodeURIComponent(a)}&sorgu=${encodeURIComponent(s)}&resim=${r}`)
    .then(r=>r.json()).then(d=>alert(d.status));
}
</script>
</body>
</html>
"""

# ───────────── LOGIN HTML ─────────────
ADMIN_LOGIN_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8">
<title>Admin Giriş</title>
<style>
body{background:#000;color:#fff;text-align:center;padding:120px;font-family:sans-serif}
input,button{padding:14px;font-size:18px;border-radius:8px;border:1px solid #444}
input{background:#111;color:#fff;width:300px}
button{background:#0af;color:#fff;border:none}
</style></head>
<body>
<h2>ADMIN GİRİŞ</h2>
<form method="POST">
<input type="password" name="p" placeholder="Admin Şifre" required><br><br>
<button>GİRİŞ</button>
</form>
</body></html>
"""

VIP_LOGIN_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8">
<title>VIP Giriş</title>
<style>
body{background:#000;color:#fff;text-align:center;padding:120px;font-family:sans-serif}
input,button{padding:14px;font-size:18px;border-radius:8px;border:1px solid #444}
input{background:#111;color:#fff;width:300px}
button{background:#0af;color:#fff;border:none}
</style></head>
<body>
<h2>LORD VIP PANEL</h2>
<form method="POST">
<input type="password" name="p" placeholder="VIP Key" required><br><br>
<button>GİRİŞ</button>
</form>
</body></html>
"""

# ───────────── ROUTES ─────────────
@app.route("/")
def home():
    return redirect("/vip_giris")

@app.route("/vip_giris", methods=["GET","POST"])
def vip_giris():
    if request.method == "POST":
        if request.form.get("p") == SISTEM["sorgu_sifre"]:
            session.clear()
            session["vip"] = True
            return redirect("/site")
        return "<h2 style='color:red;text-align:center'>YANLIŞ VIP KEY</h2>"
    return VIP_LOGIN_HTML

@app.route("/admin_giris", methods=["GET","POST"])
def admin_giris():
    if request.method == "POST":
        if request.form.get("p") == SISTEM["admin_sifre"]:
            session.clear()
            session["admin"] = True
            return redirect("/admin")
        return "<h2 style='color:red;text-align:center'>YANLIŞ ADMIN ŞİFRE</h2>"
    return ADMIN_LOGIN_HTML

@app.route("/admin")
def admin():
    if "admin" not in session:
        return redirect("/admin_giris")
    return render_template_string(
        HTML_ADMIN,
        asifre=SISTEM["admin_sifre"],
        ssifre=SISTEM["sorgu_sifre"],
        resim=SISTEM["resim_url"]
    )

@app.route("/update_settings")
def update_settings():
    if "admin" not in session:
        return jsonify({"status":"yetkisiz"})

    if request.args.get("admin"):
        SISTEM["admin_sifre"] = request.args["admin"]

    if request.args.get("sorgu"):
        SISTEM["sorgu_sifre"] = request.args["sorgu"]

    if request.args.get("resim"):
        try:
            SISTEM["resim_url"] = base64.b64decode(request.args["resim"]).decode()
        except:
            pass

    return jsonify({"status":"KAYDEDİLDİ"})

@app.route("/site")
def site():
    if "vip" not in session:
        return redirect("/vip_giris")
    return f"""
    <div style='text-align:center;padding:80px;background:#000;color:#0af'>
        <h1>LORD VIP PANEL</h1>
        <img src="{SISTEM['resim_url']}" width="180">
    </div>
    """

# ───────────── RUN ─────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
