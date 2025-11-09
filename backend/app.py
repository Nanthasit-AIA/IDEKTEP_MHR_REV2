from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.get("/api/hello")
def hello():
    return jsonify({"message": "Hello from Flask backend! "})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
