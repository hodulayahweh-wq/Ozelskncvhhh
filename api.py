# api.py   ← Render'da bu dosya adıyla çalıştıracağız
from flask import Flask, jsonify, request
import json
import os
import logging

app = Flask(__name__)

# Logging (Render konsolunda görmek için)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

ALLOWED_FILENAMES = set()  # İstersen buraya whitelist koyabilirsin

def safe_read_json(filename: str):
    """Güvenli dosya okuma"""
    # Tehlikeli karakterleri / ../ gibi yolları engelle
    if ".." in filename or "/" in filename or "\\" in filename:
        return {"error": "Geçersiz dosya adı"}

    yol = os.path.join(DATA_DIR, filename)
    
    if not os.path.isfile(yol):
        logger.warning(f"Dosya bulunamadı: {filename}")
        return {"error": "Dosya bulunamadı"}

    try:
        with open(yol, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error(f"JSON parse hatası: {filename}")
        return {"error": "Dosya bozuk (JSON formatı hatalı)"}
    except Exception as e:
        logger.exception(f"Dosya okuma hatası: {filename}")
        return {"error": "Sunucu hatası"}

@app.route("/")
def index():
    return jsonify({
        "status": "active",
        "message": "API çalışıyor",
        "endpoints": ["/api/<dosya_adi>", "/api/tc", "/api/gsm", "/api/adres"]
    })

@app.route("/api/tc")
def tc_sorgu():
    return jsonify(safe_read_json("tc_sorgu.json"))

@app.route("/api/gsm")
def gsm_sorgu():
    return jsonify(safe_read_json("gsm_sorgu.json"))

@app.route("/api/adres")
def adres_sorgu():
    return jsonify(safe_read_json("adres_sorgu.json"))

@app.route("/api/<ad>")
def dinamik(ad):
    # İstersen burada ekstra kısıtlama koyabilirsin
    # örneğin: if ad not in ["tc_sorgu", "gsm_sorgu", "adres_sorgu", "pubg", "diger"]:
    #     return jsonify({"error": "Bu endpoint mevcut değil"}), 404
    
    return jsonify(safe_read_json(f"{ad}.json"))

# Render health check için (opsiyonel ama önerilir)
@app.route("/health")
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    # Development için
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
