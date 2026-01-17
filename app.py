from flask import Flask, render_template_string, request, jsonify
import requests

app = Flask(__name__)

# --- API PROXY (CORS HATASINI ÇÖZEN MOTOR) ---
@app.route('/api/proxy')
def proxy():
    target_url = request.args.get('url')
    if not target_url:
        return jsonify({"error": "URL eksik"}), 400
    try:
        # User-agent ekleyerek API'lerin bizi bot sanıp engellemesini önlüyoruz
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(target_url, headers=headers, timeout=15)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": "API Baglanti Hatasi"}), 500

# --- 3D MOBİL ARAYÜZ ---
@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>LORD 3D PANEL</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        :root { --p: #00ffcc; --bg: #000; }
        body, html { margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; background: #000; color: white; font-family: sans-serif; }
        .scene { width: 100vw; height: 100vh; perspective: 1000px; display: flex; align-items: center; justify-content: center; }
        .cube { width: 280px; height: 280px; position: relative; transform-style: preserve-3d; transition: transform 0.8s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
        .face { position: absolute; width: 280px; height: 280px; background: rgba(15, 15, 15, 0.98); border: 2px solid var(--p); display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 20px; box-sizing: border-box; backface-visibility: hidden; border-radius: 25px; box-shadow: 0 0 30px rgba(0,255,204,0.15); }
        
        .front  { transform: rotateY(0deg) translateZ(140px); }
        .right  { transform: rotateY(90deg) translateZ(140px); }
        .left   { transform: rotateY(-90deg) translateZ(140px); }
        .top    { transform: rotateX(90deg) translateZ(140px); }
        .bottom { transform: rotateX(-90deg) translateZ(140px); }

        input { width: 100%; padding: 12px; margin-bottom: 10px; background: #0a0a0a; border: 1px solid var(--p); color: #fff; border-radius: 10px; outline: none; font-size: 14px; }
        button { width: 100%; padding: 12px; background: var(--p); color: #000; font-weight: bold; border-radius: 10px; cursor: pointer; transition: 0.3s; border:none; }
        .res-box { width: 100%; height: 100px; overflow-y: auto; background: #000; margin-top: 10px; font-size: 11px; padding: 10px; border-radius: 10px; color: #00ffcc; border: 1px solid #222; text-align: left; }
    </style>
</head>
<body>
<div class="scene">
    <div class="cube" id="cube">
        <div class="face front">
            <h1 class="text-2xl font-bold mb-6 text-[#00ffcc]">LORD 3D</h1>
            <div class="grid grid-cols-2 gap-3 w-full">
                <button onclick="move('right')">ADRES</button>
                <button onclick="move('left')">GSM</button>
                <button onclick="move('top')">RECETE</button>
                <button onclick="move('bottom')">VERGI</button>
            </div>
        </div>
        <div class="face right">
            <h2 class="text-[#00ffcc] mb-2 font-bold">ADRES SORGU</h2>
            <input type="text" id="in_adres" placeholder="TC Gir">
            <button onclick="run('https://sorgum.2026tr.xyz/nabi/api/v1/tc/adres?tc=', 'in_adres')">SORGULA</button>
            <div id="res_in_adres" class="res-box"></div>
            <button onclick="move('front')" class="mt-2 !bg-[#222] !text-white">GERI</button>
        </div>
        <div class="face left">
            <h2 class="text-[#00ffcc] mb-2 font-bold">GSM SORGU</h2>
            <input type="text" id="in_gsm" placeholder="GSM Gir">
            <button onclick="run('https://zyrdaware.xyz/api/gsmtc?auth=t.me/zyrdaware&gsm=', 'in_gsm')">SORGULA</button>
            <div id="res_in_gsm" class="res-box"></div>
            <button onclick="move('front')" class="mt-2 !bg-[#222] !text-white">GERI</button>
        </div>
        </div>
</div>
<script>
    const cube = document.getElementById('cube');
    function move(side) {
        if(side==='front') cube.style.transform = 'rotateY(0deg) rotateX(0deg)';
        if(side==='right') cube.style.transform = 'rotateY(-90deg)';
        if(side==='left') cube.style.transform = 'rotateY(90deg)';
        if(side==='top') cube.style.transform = 'rotateX(-90deg)';
        if(side==='bottom') cube.style.transform = 'rotateX(90deg)';
    }
    async function run(url, id) {
        const val = document.getElementById(id).value;
        const resBox = document.getElementById('res_'+id);
        if(!val) return;
        resBox.innerText = "Sorgulanıyor...";
        try {
            const response = await fetch('/api/proxy?url=' + encodeURIComponent(url + val));
            const data = await response.json();
            resBox.innerHTML = "<pre>" + JSON.stringify(data, null, 2) + "</pre>";
        } catch(e) { resBox.innerText = "Hata!"; }
    }
</script>
</body>
</html>
''')

if __name__ == "__main__":
    app.run()
