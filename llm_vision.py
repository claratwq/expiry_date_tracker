import os
import json
from google import genai
from google.genai import types

# Initialize Gemini Client (uses GEMINI_API_KEY environment variable)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

PROMPT = """
You are an expert product and grocery label parser. Analyze the provided image(s) of a product label or packaging.

Extract the following information:
1. "item_name": Identify the full product name including the brand if visible (e.g., "HL Chocolate Milk", "Marigold Strawberry Yogurt", "Laughing Cow Cheese Cubes", "Eggs"). If the brand is missing or unclear, provide just the item name (e.g., "Whole Milk").
2. "date_type": Determine whether the date label represents an "Expiry Date" or a "Best Before Date". Return strictly "Expiry" or "Best Before". If unclear, infer based on the product.
3. "expiry_date": Extract the date shown on the label. Standardize the date into ISO format "YYYY-MM-DD". If the year is ambiguous or missing (e.g., "15 AUG"), infer the current or upcoming year. If no date is found, return null.

Return ONLY a JSON object adhering to this schema:
{
  "item_name": "string",
  "date_type": "Expiry" | "Best Before",
  "expiry_date": "YYYY-MM-DD" | null
}
"""

def extract_product_info_from_images(image_bytes_list: list[bytes]) -> dict:
    """
    Accepts a list of raw image bytes, sends them to Gemini 2.5 Flash,
    and returns a structured dictionary with item_name, date_type, and expiry_date.
    """
    if not image_bytes_list:
        return {
            "item_name": "Unknown Product",
            "date_type": "Best Before",
            "expiry_date": None
        }

    try:
        # Convert raw bytes list into Gemini Part contents
        contents = []
        for img_bytes in image_bytes_list:
            contents.append(
                types.Part.from_bytes(
                    data=img_bytes,
                    mime_type="image/jpeg",
                )
            )
        
        # Append the system prompt instructions
        contents.append(PROMPT)

        # Request structured JSON response
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1
            ),
        )

        # Parse output
        result = json.loads(response.text)
        return {
            "item_name": result.get("item_name", "Unknown Product"),
            "date_type": result.get("date_type", "Expiry"),
            "expiry_date": result.get("expiry_date")
        }

    except Exception as e:
        print(f"Gemini Vision Inference Error: {e}")
        return {
            "item_name": "Scanned Item",
            "date_type": "Best Before",
            "expiry_date": None
        }