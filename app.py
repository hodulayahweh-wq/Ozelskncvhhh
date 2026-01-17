from flask import Flask, render_template_string, request, jsonify, redirect, session
import json, os, requests

app = Flask(__name__)
app.secret_key = "lord_ozel_anahtar_2026"

DB_FILE = "veritabani.json"

# --- VERİTABANI İŞLEMLERİ ---
def get_db():
    if not os.path.exists(DB_FILE):
        return {"siteler": {}}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

# --- API PROXY (VERİ ÇEKİLMEME HATASINI ÇÖZER) ---
@app.route('/api/proxy')
def proxy():
    url = request.args.get('url')
    if not url: return jsonify({"error": "URL eksik"}), 400
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=15)
        return jsonify(r.json())
    except:
        return jsonify({"error": "API Yanıt Vermedi"}), 500

# --- 1. DİNAMİK KULLANICI SİTESİ (ozelskncvhhh.onrender.com/siteadi) ---
@app.route('/<site_slug>')
def render_user_site(site_slug):
    # Admin paneli çakışmaması için
    if site_slug == "admin": return redirect('/lord-admin')
    
    db = get_db()
    site = db["siteler"].get(site_slug)
    if not site:
        return f"<h1>⚠️ '{site_slug}' Adlı Site Henüz Kurulmamış!</h1>", 404
    
    return render_template_string('''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ s.title }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background: #000; color: #00ffcc; font-family: sans-serif; }
        .card { background: rgba(15,15,15,0.9); border: 1px solid #00ffcc; border-radius: 20px; box-shadow: 0 0 15px rgba(0,255,204,0.2); }
        input { background: #000 !important; border: 1px solid #333 !important; color: white !important; }
        button { background: #00ffcc !important; color: #000 !important; font-weight: bold; transition: 0.3s; }
        button:hover { box-shadow: 0 0 20px #00ffcc; transform: translateY(-2px); }
    </style>
</head>
<body class="min-h-screen p-6 flex flex-col items-center">
    <h1 class="text-4xl font-black mb-10 tracking-tighter">{{ s.title.upper() }}</h1>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-5xl">
        {% for api in s.apis %}
        <div class="card p-6">
            <h3 class="text-xl mb-4 font-bold border-b border-gray-800 pb-2">{{ api.name }}</h3>
            <input id="in_{{ loop.index }}" type="text" placeholder="Sorgu verisi gir..." class="w-full p-3 rounded-lg mb-4 outline-none">
            <button onclick="sorgula('{{ api.url }}', 'in_{{ loop.index }}', 'res_{{ loop.index }}')" class="w-full py-3 rounded-lg">SORGULA</button>
            <div id="res_{{ loop.index }}" class="mt-4 text-xs bg-black p-3 border border-gray-800 rounded-lg max-h-40 overflow-auto text-green-400"></div>
        </div>
        {% endfor %}
    </div>
    <script>
        async function sorgula(url, inpId, resId) {
            const v = document.getElementById(inpId).value;
            const r = document.getElementById(resId);
            if(!v) return; r.innerText = "Sistem Sorgulanıyor...";
            try {
                const res = await fetch('/api/proxy?url=' + encodeURIComponent(url + v));
                const data = await res.json();
                r.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
            } catch { r.innerText = "Hata oluştu!"; }
        }
    </script>
</body>
</html>
''', s=site)

# --- 2. MASTER ADMIN PANELİ ---
@app.route('/lord-admin', methods=['GET', 'POST'])
def master_admin():
    if request.method == 'POST' and request.form.get('key') == "lord2026":
        session['auth'] = True
    if not session.get('auth'):
        return '<body style="background:#000;color:#00ffcc;display:flex;justify-content:center;align-items:center;height:100vh;"><form method="post">🔑 KEY: <input type="password" name="key"><button>GİRİŞ</button></form></body>'

    db = get_db()
    return render_template_string('''
<!DOCTYPE html>
<html>
<head><title>Admin Control</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-gray-900 text-white p-10">
    <div class="max-w-6xl mx-auto">
        <h1 class="text-3xl font-bold text-[#00ffcc] mb-10">MASTER SİTE YÖNETİMİ</h1>
        
        <div class="bg-black p-8 rounded-3xl border border-gray-700 mb-10">
            <h2 class="text-xl mb-4 text-blue-400 font-bold">Yeni Site (Alt Dizin) Kur</h2>
            <form action="/admin/create" method="post" class="flex gap-4">
                <input name="slug" placeholder="Site Uzantısı (Örn: orneksite)" class="bg-gray-800 p-3 rounded-xl flex-1 outline-none border border-gray-600 focus:border-[#00ffcc]">
                <input name="title" placeholder="Site Başlığı" class="bg-gray-800 p-3 rounded-xl flex-1 outline-none border border-gray-600 focus:border-[#00ffcc]">
                <button class="bg-[#00ffcc] text-black px-8 font-bold rounded-xl">SİTEYİ OLUŞTUR</button>
            </form>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
            {% for slug, data in siteler.items() %}
            <div class="bg-black p-6 rounded-3xl border border-gray-800 relative">
                <div class="flex justify-between items-start mb-6">
                    <div>
                        <h3 class="text-2xl font-bold text-[#00ffcc]">{{ data.title }}</h3>
                        <p class="text-blue-500 text-xs">Link: /{{ slug }}</p>
                    </div>
                    <a href="/admin/delete_site/{{ slug }}" class="text-red-500 text-xs font-bold bg-red-900/20 px-3 py-1 rounded">SİTEYİ SİL</a>
                </div>

                <form action="/admin/add_api/{{ slug }}" method="post" class="space-y-3 mb-6 bg-gray-900 p-4 rounded-xl">
                    <input name="name" placeholder="API İsmi" class="w-full bg-black p-2 rounded-lg text-sm border border-gray-700">
                    <input name="url" placeholder="API Link (Sonu =)" class="w-full bg-black p-2 rounded-lg text-sm border border-gray-700">
                    <button class="w-full bg-green-600 py-2 rounded-lg text-sm font-bold">YENİ API EKLE</button>
                </form>

                <div class="space-y-2">
                    {% for api in data.apis %}
                    <div class="flex justify-between items-center bg-gray-800 p-3 rounded-xl">
                        <span class="text-sm font-bold">{{ api.name }}</span>
                        <a href="/admin/delete_api/{{ slug }}/{{ loop.index0 }}" class="text-red-500 font-bold">Sil</a>
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
''', siteler=db["siteler"])

# --- ADMIN İŞLEMLERİ ---
@app.route('/admin/create', methods=['POST'])
def create_site():
    db = get_db()
    slug = request.form['slug'].lower().strip().replace(" ", "-")
    if slug:
        db["siteler"][slug] = {"title": request.form['title'], "apis": []}
        save_db(db)
    return redirect('/lord-admin')

@app.route('/admin/add_api/<slug>', methods=['POST'])
def add_api(slug):
    db = get_db()
    db["siteler"][slug]["apis"].append({"name": request.form['name'], "url": request.form['url']})
    save_db(db)
    return redirect('/lord-admin')

@app.route('/admin/delete_api/<slug>/<int:idx>')
def delete_api(slug, idx):
    db = get_db()
    db["siteler"][slug]["apis"].pop(idx)
    save_db(db)
    return redirect('/lord-admin')

@app.route('/admin/delete_site/<slug>')
def delete_site(slug):
    db = get_db()
    if slug in db["siteler"]: del db["siteler"][slug]
    save_db(db)
    return redirect('/lord-admin')

if __name__ == "__main__":
    app.run()
