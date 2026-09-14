from app import create_app

app = create_app()

@app.route("/")
def home():
    return {"status": "ok", "message": "Backend API is running!"}, 200

@app.route("/health")
def health():
    return {"status": "ok", "service": "backend"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)