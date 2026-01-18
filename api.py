from flask import Flask, jsonify, abort
import os, json

app = Flask(__name__)

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

@app.route("/")
def home():
    return {
        "status": "LORD 2026 API AKTIF",
        "usage": "/api/<dosya_adi>"
    }

@app.route("/api/<name>")
def get_data(name):
    file_path = os.path.join(DATA_DIR, f"{name}.json")

    if not os.path.exists(file_path):
        abort(404, "Dosya bulunamadı")

    with open(file_path, "r", encoding="utf-8") as f:
        return jsonify(json.load(f))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
