from flask import Flask, jsonify, request
from flask_cors import CORS
import traceback

# our ML functions
from model.predictor import predict, model_stats
from model.trainer import train

# create flask app
app = Flask(__name__)

# allow frontend (running on different port) to talk to backend
CORS(app)


# ---------------- MAIN API ----------------
# this is what your frontend calls when user clicks "Check email"
@app.route("/api/detect", methods=["POST"])
def detect():

    # get JSON data sent from frontend
    data = request.get_json()

    # if nothing sent → error
    if not data:
        return jsonify({"error": "No JSON body provided"}), 400

    # safely extract subject & body (avoid None errors)
    subject = data.get("subject", "").strip()
    body = data.get("body", "").strip()

    # basic validation (don’t allow empty input)
    if not subject and not body:
        return jsonify({"error": "Provide at least a subject or body"}), 400

    try:
        # call ML model → returns spam/ham + confidence
        result = predict(subject, body)

        # send result back to frontend
        return jsonify(result)

    except Exception as e:
        # print full error in terminal (very useful for debugging)
        traceback.print_exc()

        # send simple error to frontend
        return jsonify({"error": str(e)}), 500


# ---------------- MODEL INFO ----------------
# gives stats like accuracy, dataset size, etc.
@app.route("/api/stats", methods=["GET"])
def stats():
    try:
        return jsonify(model_stats())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- RETRAIN MODEL ----------------
# manually retrain model (useful when data changes)
@app.route("/api/retrain", methods=["POST"])
def retrain():
    try:
        # train model again and save it
        bundle = train(save=True)

        # send summary back
        return jsonify({
            "message": "Model retrained successfully",
            "training_size": bundle["training_size"],
            "accuracy": bundle["accuracy"]   # NOTE: make sure this key exists in trainer
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ---------------- HEALTH CHECK ----------------
# quick way to check if server is running
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    print("Starting Email Spam Detector API...")

    # debug=True → auto reload on changes (good for development)
    # port=5000 → must match frontend fetch URL
    app.run(debug=True, port=5000)