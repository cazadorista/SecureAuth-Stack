from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return {"status": "ok", "message": "Flask backend is running!"}, 200

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "backend"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)