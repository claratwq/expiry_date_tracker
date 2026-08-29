import os
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from database_ops import init_db, add_item_to_db, get_items_from_db, delete_item_from_db
from llm_vision import extract_product_info_from_images

app = Flask(__name__)
CORS(app)

# Add limiter to manage requests from Streamlit
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "60 per minute"],
    storage_uri="memory://"
)

_db_initialized = False

@app.before_request
def ensure_db_ready():
    global _db_initialized
    if not _db_initialized:
        try:
            init_db()
            _db_initialized = True
        except Exception as e:
            app.logger.error(f"Database initialization failed: {e}")

@app.route("/", methods=["GET"])
def index():
    return jsonify({"message": "Expiry Tracker API is running!"}), 200

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200

@app.route("/items", methods=["GET"])
@limiter.exempt  # Exempt read operations so page reruns don't trigger 429 errors
def fetch_items():
    try:
        rows = get_items_from_db()
        items = [{"id": r[0], "name": r[1], "expiry_date": r[2], "date_type": r[3]} for r in rows]
        return jsonify(items), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/items", methods=["POST"])
@limiter.limit("30 per minute")
def create_item():
    data = request.json or {}
    name = data.get("name", "Unnamed Item")
    date_type = data.get("date_type", "Expiry")
    expiry_date = data.get("expiry_date")
    
    if not expiry_date:
        return jsonify({"error": "expiry_date is required"}), 400
        
    try:
        add_item_to_db(name, date_type, expiry_date)
        return jsonify({"status": "created"}), 201
    except Exception as e:
        app.logger.error(f"Error creating item: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/items/<int:item_id>", methods=["DELETE"])
def remove_item(item_id):
    delete_item_from_db(item_id)
    return jsonify({"status": "deleted"}), 200

@app.route("/analyze-label", methods=["POST"])
@limiter.limit("20 per minute")
def analyze_label():
    data = request.json or {}
    images_b64 = data.get("images_b64", [])
    
    if isinstance(images_b64, str):
        images_b64 = [images_b64]

    image_bytes_list = []
    for b64_str in images_b64:
        try:
            image_bytes_list.append(base64.b64decode(b64_str))
        except Exception:
            continue

    product_data = extract_product_info_from_images(image_bytes_list)
    return jsonify(product_data), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)