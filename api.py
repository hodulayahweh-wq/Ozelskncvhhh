from flask import Flask, jsonify, abort
import os, json

app = Flask(__name__)
DATA_DIR = "data"

@app.route("/")
def home():
    return {"status": "LORD API aktif"}

@app.route("/api/<name>")
def api(name):
    path = os.path.join(DATA_DIR, f"{name}.json")
    if not os.path.exists(path):
        return abort(404)

    with open(path, "r", encoding="utf-8") as f:
        return jsonify(json.load(f))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
