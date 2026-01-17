from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# --- KAYNAK LİNKLER (Veri Buradan Gelecek) ---
# Bu linkler internetteki halka açık gerçek veri havuzlarıdır.
# Sen başka bir link bulursan buraya ekleyebilirsin.
DATA_SOURCES = {
    "kisi": "https://jsonplaceholder.typicode.com/users",
    "post": "https://jsonplaceholder.typicode.com/posts"
}

@app.route('/api/sorgu')
def master_sorgu():
    tip = request.args.get('tip') # 'kisi' veya 'post'
    sorgu_id = request.args.get('id') # Aranan ID (Örn: 1, 2, 3)

    if not tip or not sorgu_id:
        return jsonify({"hata": "Eksik parametre! Tip ve ID girilmelidir."}), 400

    target_link = DATA_SOURCES.get(tip)
    
    try:
        # 1. Dışarıdaki linke bağlanıyoruz
        r = requests.get(f"{target_link}/{sorgu_id}", timeout=10)
        
        # 2. Gelen veriyi kontrol ediyoruz
        if r.status_code == 200:
            gercek_veri = r.json()
            
            # 3. Veriyi senin panelin için düzenliyoruz
            return jsonify({
                "durum": "BAŞARILI",
                "kaynak": target_link,
                "sonuc": {
                    "isim": gercek_veri.get("name", "Bilinmiyor"),
                    "detay": gercek_veri.get("email") or gercek_veri.get("title"),
                    "sistem_no": gercek_veri.get("id")
                }
            })
        else:
            return jsonify({"durum": "HATA", "mesaj": "Veri bulunamadı"}), 404

    except Exception as e:
        return jsonify({"durum": "HATA", "mesaj": "Linke ulaşılamadı"}), 500

if __name__ == "__main__":
    app.run()
