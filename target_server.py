import time
import random
from flask import Flask, jsonify

app = Flask(__name__)

# Simulates a real web service with occasional slowness and errors
REQUEST_COUNT = 0
ERROR_COUNT = 0

@app.route("/")
def home():
    return jsonify({"status": "ok", "service": "target-server"})

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

@app.route("/api/data")
def data():
    global REQUEST_COUNT, ERROR_COUNT
    REQUEST_COUNT += 1

    # Simulate occasional slowness
    if random.random() < 0.1:
        time.sleep(random.uniform(1.0, 3.0))

    # Simulate occasional errors
    if random.random() < 0.05:
        ERROR_COUNT += 1
        return jsonify({"error": "internal error"}), 500

    return jsonify({"data": "ok", "request_count": REQUEST_COUNT})

@app.route("/metrics")
def metrics():
    global REQUEST_COUNT, ERROR_COUNT
    error_rate = ERROR_COUNT / REQUEST_COUNT if REQUEST_COUNT > 0 else 0
    return jsonify({
        "request_count": REQUEST_COUNT,
        "error_count": ERROR_COUNT,
        "error_rate": round(error_rate, 3)
    })

if __name__ == "__main__":
    app.run(port=5000, debug=False)