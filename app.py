from flask import Flask, render_template_string, request, jsonify, session, redirect
import requests
import os

app = Flask(__name__)
app.secret_key = "lord_key_2026"

# --- GERÇEK VERİ MOTORU (API) ---
# Burada halka açık büyük veri havuzlarını köprü olarak kullanıyoruz.
@app.route('/api/sorgu')
def api_engine():
    search_type = request.args.get('tip')
    query = request.args.get('q')
    
    if not query:
        return jsonify({"hata": "Sorgu verisi girmedin sevgilim"}), 400

    try:
        if search_type == "kisi":
            # Gerçek kullanıcı verisi simülasyonu (Halka açık kaynaktan)
            r = requests.get(f"https://jsonplaceholder.typicode.com/users/{query if query.isdigit() and int(query) < 11 else '1'}")
            data = r.json()
            return jsonify({"durum": "Aktif", "tip": "Sistem Kaydı", "sonuc": data})
            
        elif search_type == "ulke":
            # Dünya üzerindeki gerçek ülke verileri
            r = requests.get(f"https://restcountries.com/v3.1/name/{query}")
            return jsonify(r.json())
            
        else:
            return jsonify({"mesaj": "Bilinmeyen sorgu tipi"})
    except:
        return jsonify({"hata": "Veri havuzuna ulaşılamadı"}), 500

# --- MASTER ADMIN VE PANEL ARAYÜZÜ ---
@app.route('/')
def home():
    return render_template_string('''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LORD PRO API PANEL</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background: #050505; color: #00ffcc; font-family: monospace; }
        .cyber-card { background: #0a0a0a; border: 1px solid #00ffcc; box-shadow: 0 0 15px rgba(0,255,204,0.1); }
        input { background: #000 !important; border: 1px solid #222 !important; color: white !important; outline: none; }
        input:focus { border-color: #00ffcc !important; }
        button { background: #00ffcc; color: black; font-weight: bold; transition: 0.3s; }
        button:hover { box-shadow: 0 0 20px #00ffcc; transform: scale(1.02); }
    </style>
</head>
<body class="p-4 md:p-10">
    <div class="max-w-4xl mx-auto">
        <header class="text-center mb-10">
            <h1 class="text-4xl font-black tracking-widest mb-2">LORD PRO SYSTEM</h1>
            <p class="text-xs opacity-50">REAL-TIME DATA ACQUISITION TERMINAL</p>
        </header>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="cyber-card p-6 rounded-2xl">
                <h2 class="text-xl mb-4 font-bold">👤 PERSONEL SORGU</h2>
                <input id="q_kisi" type="text" placeholder="ID Gir (1-10)..." class="w-full p-3 rounded-lg mb-4">
                <button onclick="run('kisi', 'q_kisi', 'res_kisi')" class="w-full py-3 rounded-lg">VERİ ÇEK</button>
                <div id="res_kisi" class="mt-4 text-[10px] bg-black p-3 rounded border border-gray-800 h-32 overflow-auto"></div>
            </div>

            <div class="cyber-card p-6 rounded-2xl">
                <h2 class="text-xl mb-4 font-bold">🌍 GLOBAL VERİ</h2>
                <input id="q_ulke" type="text" placeholder="Ülke Adı (English)..." class="w-full p-3 rounded-lg mb-4">
                <button onclick="run('ulke', 'q_ulke', 'res_ulke')" class="w-full py-3 rounded-lg">ANALİZ ET</button>
                <div id="res_ulke" class="mt-4 text-[10px] bg-black p-3 rounded border border-gray-800 h-32 overflow-auto"></div>
            </div>
        </div>
    </div>

    <script>
        async function run(tip, inpId, resId) {
            const val = document.getElementById(inpId).value;
            const resBox = document.getElementById(resId);
            if(!val) return;
            resBox.innerText = ">>> VERİ PAKETLERİ ALINIYOR...";
            try {
                const r = await fetch(`/api/sorgu?tip=${tip}&q=${val}`);
                const data = await r.json();
                resBox.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
            } catch {
                resBox.innerText = ">>> BAĞLANTI HATASI!";
            }
        }
    </script>
</body>
</html>
''')

if __name__ == "__main__":
    app.run()
