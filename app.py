import os
import base64
from flask import Flask, request, jsonify
from database_ops import init_db, add_item_to_db, get_items_from_db, delete_item_from_db
from OCR import detect_text_from_bytes, extract_expiry_date, extract_item_name

app = Flask(__name__)

# Initialize Turso table on server boot
init_db()

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200

@app.route("/items", methods=["GET"])
def fetch_items():
    rows = get_items_from_db()
    items = [{"id": r[0], "name": r[1], "expiry_date": r[2]} for r in rows]
    return jsonify(items)

@app.route("/items", methods=["POST"])
def create_item():
    data = request.json or {}
    name = data.get("name", "Unnamed Item")
    expiry_date = data.get("expiry_date")
    add_item_to_db(name, expiry_date)
    return jsonify({"status": "created"}), 201

@app.route("/items/<int:item_id>", methods=["DELETE"])
def remove_item(item_id):
    delete_item_from_db(item_id)
    return jsonify({"status": "deleted"}), 200

@app.route("/ocr/name", methods=["POST"])
def ocr_name():
    data = request.json or {}
    image_bytes = base64.b64decode(data.get("image_b64", ""))
    lines = detect_text_from_bytes(image_bytes)
    name = extract_item_name(lines)
    return jsonify({"name": name})

@app.route("/ocr/date", methods=["POST"])
def ocr_date():
    data = request.json or {}
    image_bytes = base64.b64decode(data.get("image_b64", ""))
    lines = detect_text_from_bytes(image_bytes)
    exp_date = extract_expiry_date(lines)
    return jsonify({"expiry_date": exp_date})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)