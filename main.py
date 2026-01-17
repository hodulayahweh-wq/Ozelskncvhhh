import os, asyncio, threading, httpx, datetime, base64, re, json
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from telegram.ext import ApplicationBuilder

# --- SİSTEM AYARLARI ---
SISTEM = {
    "apis": {}, 
    "admin_id": 7690743437,
    "ana_token": "8586246924:AAEdEGEQn9tjBBAQKw-nJ_NvDG5P-G3T8cc", # Buraya kendi tokenini yaz
    "panel_sifre": "19786363",
    "baslangic": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
}

web_app = Flask(__name__)
web_app.secret_key = "nabi_mega_turbo_fix"

# HIZLI BAĞLANTI HAVUZU (Takılmayı Önler)
limits = httpx.Limits(max_connections=200, max_keepalive_connections=100)
global_client = httpx.AsyncClient(timeout=25.0, limits=limits)

# --- VERİ TEMİZLEME FONKSİYONU ---
def temizle_reklam(metin):
    if not isinstance(metin, str): metin = str(metin)
    # t.me linklerini ve @username etiketlerini temizler
    metin = re.sub(r'(https?://)?t\.me/\S+', '[TEMİZLENDİ]', metin)
    metin = re.sub(r'@\S+', '[TEMİZLENDİ]', metin)
    return metin.strip()

# --- HTML TASARIMLARI ---
HTML_ADMIN = """
<body style="background:#050505; color:white; font-family:sans-serif; padding:20px;">
    <div style="max-width:800px; margin:auto; background:#111; padding:30px; border-radius:20px; border:1px solid #222;">
        <h2 style="color:#0095f6">⚙️ Admin Paneli</h2>
        <div style="background:#1a1a1a; padding:15px; border-radius:10px; margin-bottom:20px;">
            <input type="text" id="an" placeholder="Sorgu Adı" style="padding:10px; background:#000; color:white; border:1px solid #333; width:30%;">
            <input type="text" id="au" placeholder="API Link (sonu =)" style="padding:10px; background:#000; color:white; border:1px solid #333; width:45%;">
            <button onclick="save()" style="padding:10px 20px; background:#0095f6; color:white; border:none; border-radius:5px; cursor:pointer;">EKLE</button>
        </div>
        <div id="list">
            {% for name in apis %}<div style="display:flex; justify-content:space-between; background:#0a0a0a; padding:12px; margin-bottom:8px; border-radius:8px; border-left:4px solid #0095f6;">
            <span>✅ {{ name }}</span><button onclick="del('{{name}}')" style="background:red; color:white; border:none; border-radius:4px; padding:5px 10px; cursor:pointer;">SİL</button></div>{% endfor %}
        </div>
        <br><a href="/site" target="_blank" style="display:block; text-align:center; background:#31b545; color:white; padding:15px; text-decoration:none; border-radius:10px; font-weight:bold;">SİTEYİ AÇ</a>
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
    <title>Nabi Verified</title>
    <style>
        :root { --blue: #0095f6; --bg: #000; }
        body { margin:0; background: var(--bg); color:white; font-family:-apple-system,sans-serif; overflow:hidden; }
        .h-btn { position:fixed; top:20px; left:50%; transform:translateX(-50%); z-index:100; background:rgba(255,255,255,0.1); padding:10px 25px; border-radius:30px; cursor:pointer; backdrop-filter:blur(10px); font-weight:bold; }
        .overlay { position:fixed; top:-100%; left:0; width:100%; height:100%; background:rgba(0,0,0,0.96); z-index:99; transition:0.4s; display:flex; flex-direction:column; align-items:center; justify-content:center; }
        .overlay.active { top:0; }
        .item { font-size:22px; margin:12px; cursor:pointer; font-weight:bold; }
        .main { height:100vh; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:20px; text-align:center; }
        input { width:100%; max-width:400px; padding:16px; border-radius:12px; border:1px solid #333; background:#0a0a0a; color:white; margin-bottom:10px; box-sizing:border-box; }
        .btn { width:100%; max-width:400px; padding:16px; border-radius:12px; border:none; background:var(--blue); color:white; font-weight:bold; cursor:pointer; }
        #res { margin-top:20px; width:100%; max-width:400px; background:#0a0a0a; padding:15px; border-radius:12px; text-align:left; color:#4ade80; display:none; border:1px solid #222; white-space:pre-wrap; font-family:monospace; overflow-y:auto; max-height:250px; }
    </style>
</head>
<body>
    <div class="h-btn" onclick="tgl()">☰ SORGULARI GÖR</div>
    <div class="overlay" id="menu">
        <h2 style="color:var(--blue)">Sorgu Seçin</h2>
        {% for name in apis %}<div class="item" onclick="sel('{{name}}')">📍 {{name}}</div>{% endfor %}
        <div onclick="tgl()" style="margin-top:30px; color:gray;">KAPAT</div>
    </div>
    <div class="main">
        <h2 id="sname" style="color:var(--blue)">Nabi System</h2>
        <div id="form" style="display:none; width:100%; max-width:400px;">
            <input type="text" id="target" placeholder="Veri giriniz...">
            <button class="btn" onclick="sorgu()">ZORLA SORGULA</button>
            <div id="res"></div>
        </div>
    </div>
    <script>
    let cur = "";
    function tgl(){document.getElementById('menu').classList.toggle('active');}
    function sel(n){cur=n; document.getElementById('form').style.display='block'; document.getElementById('sname').innerText=n; tgl();}
    async function sorgu(){
        const v=document.getElementById('target').value; const r=document.getElementById('res');
        if(!v) return; r.style.display="block"; r.innerText="⚡ Sorgulanıyor...";
        try {
            const res=await fetch('/do_web_sorgu?name='+cur+'&val='+v);
            const data=await res.json();
            r.innerText = typeof data.result === 'object' ? JSON.stringify(data.result, null, 2) : data.result;
        } catch { r.innerText="❌ Hata: API Yanıt Vermedi!"; }
    }
    </script>
</body>
</html>"""

# --- YOLLAR ---
@web_app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template_string('<body style="background:#000;color:white;text-align:center;padding-top:100px;"><h2>🔐 Giriş</h2><form method="POST" action="/login"><input type="password" name="s" style="padding:10px;"><br><br><button style="padding:10px 20px;background:#0095f6;border:none;color:white;">GİRİŞ</button></form></body>')
