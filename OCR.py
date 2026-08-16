import os
import re
from datetime import datetime, timedelta
from dateutil import parser
from google.cloud import vision
from google.oauth2 import service_account

# Set path to your Google Cloud Service Account JSON Key
GCP_KEY_PATH = os.getenv("GCP_KEY_PATH")

def detect_text_from_bytes(image_bytes):
    """Core Cloud Vision API call."""
    try:
        if os.path.exists(GCP_KEY_PATH):
            credentials = service_account.Credentials.from_service_account_file(GCP_KEY_PATH)
            client = vision.ImageAnnotatorClient(credentials=credentials)
        else:
            client = vision.ImageAnnotatorClient()

        image = vision.Image(content=image_bytes)
        response = client.text_detection(image=image)
        texts = response.text_annotations

        if response.error.message:
            print(f"Cloud Vision Error: {response.error.message}")
            return []

        if texts:
            return texts[0].description.splitlines()
    except Exception as e:
        print(f"OCR Exception: {e}")
    return []


def extract_expiry_date(lines):
    """Parses lines specifically looking for date formats."""
    date_pattern = r'(\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b|\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}\b)'
    
    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue
        match = re.search(date_pattern, line_str, re.IGNORECASE)
        if match:
            try:
                parsed_dt = parser.parse(match.group(0), fuzzy=True).date()
                return parsed_dt.strftime("%Y-%m-%d")
            except Exception:
                pass
    
    # Fallback default: +7 days from today
    return (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")


def extract_item_name(lines):
    """Filters out date tokens and keywords to isolate product name."""
    date_pattern = r'(\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b|\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}\b)'
    name_words = []

    for line in lines:
        line_str = line.strip()
        if not line_str or re.search(date_pattern, line_str, re.IGNORECASE):
            continue
        
        cleaned = re.sub(r'(BEST BEFORE|EXP|EXPIRY|USE BY|MFG|LOT|\d{10,})', '', line_str, flags=re.IGNORECASE).strip()
        if cleaned and len(cleaned) > 1:
            name_words.append(cleaned)

    return " ".join(name_words[:2]) if name_words else "Scanned Product"