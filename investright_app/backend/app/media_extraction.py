import io
import re

from PIL import Image
import pytesseract
from pypdf import PdfReader


def _amount(value: str) -> float:
    cleaned = re.sub(r"[^0-9.]", "", value.replace(",", ""))
    return float(cleaned) if cleaned else 0


def extract_candidates(text: str) -> dict[str, float | None]:
    labels = {
        "income": [r"net\s+pay", r"monthly\s+(?:gross\s+)?(?:salary|income)", r"total\s+earnings", r"earnings"],
        "expenses": [r"monthly\s+(?:total\s+)?expenses?"],
        "savings": [r"(?:(?:total\s+)?savings?|balance)"],
        "gross_earnings": [r"total\s+earnings", r"gross\s+(?:salary|pay)"],
        "net_pay": [r"net\s+pay", r"take[- ]home"],
        "deductions": [r"total\s+deductions?"],
    }
    candidates = {key: None for key in labels}
    for key, patterns in labels.items():
        for label in patterns:
            match = re.search(rf"{label}\D{{0,30}}(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)", text, re.I)
            if match:
                candidates[key] = _amount(match.group(1))
                break
    return candidates


def extract_media(content: bytes, media_type: str) -> str:
    if media_type == "application/pdf":
        reader = PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    image = Image.open(io.BytesIO(content))
    return pytesseract.image_to_string(image)