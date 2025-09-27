
import pytesseract
from PIL import Image
from typing import Tuple



def ocr_from_image(image_path: str) -> Tuple[str, float]:
    """
    Reads text from an image and returns the extracted text and confidence (0–1).
    """
    try:
        tsv = pytesseract.image_to_data(Image.open(image_path), output_type=pytesseract.Output.DICT)
        text = " ".join([w for w in tsv.get("text", []) if w.strip()])
        
        
        confs = []
        for c in tsv.get("conf", []):
            if isinstance(c, (int, float)) and c >= 0:
                confs.append(float(c))
            elif isinstance(c, str) and c.replace('-', '').replace('.', '').isdigit() and float(c) >= 0:
                confs.append(float(c))
        
        confidence = (sum(confs) / len(confs) / 100.0) if confs else 0.6
        return text.strip(), max(0.0, min(confidence, 1.0))
    
    except Exception as e:
        print(f"OCR Error: {e}")
        # Fallback - return empty text with low confidence
        return "", 0.1

def passthrough_text(text: str) -> Tuple[str, float]:
    """
    Directly returns the text with high confidence (used when user submits plain text).
    """
    return text.strip(), 0.95 if text.strip() else 0.0 