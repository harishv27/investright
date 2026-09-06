import io
import re
import base64
from PIL import Image
from pypdf import PdfReader

from app.config import settings


def _amount(value: str) -> float:
    cleaned = re.sub(r"[^0-9.]", "", value.replace(",", ""))
    return float(cleaned) if cleaned else 0


def extract_candidates(text: str) -> dict[str, float | None]:
    labels = {
        "income": [
            r"net\s+pay", r"take[- ]home", r"monthly\s+(?:gross\s+)?(?:salary|income)",
            r"total\s+earnings", r"net\s+salary", r"salary\s+credited", r"earnings"
        ],
        "expenses": [
            r"monthly\s+(?:total\s+)?expenses?", r"total\s+expenses?", r"total\s+debits?",
            r"expenses?", r"outflows?"
        ],
        "savings": [
            r"(?:(?:total\s+)?savings?|balance|closing\s+balance|available\s+balance)",
            r"bank\s+balance", r"deposit\s+balance"
        ],
        "gross_earnings": [
            r"total\s+earnings", r"gross\s+(?:salary|pay|earnings)", r"basic\s+pay"
        ],
        "net_pay": [
            r"net\s+pay", r"take[- ]home", r"net\s+amount", r"net\s+salary"
        ],
        "deductions": [
            r"total\s+deductions?", r"deductions?", r"provident\s+fund", r"pf\s+deduction"
        ],
    }
    candidates = {key: None for key in labels}
    for key, patterns in labels.items():
        for label in patterns:
            match = re.search(rf"{label}\D{{0,35}}(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)", text, re.I)
            if match:
                candidates[key] = _amount(match.group(1))
                break
    return candidates


def _extract_image_with_vision(content: bytes, media_type: str = "image/jpeg") -> str:
    if not settings.groq_api_key:
        raise ValueError("Groq API key not configured")

    b64_img = base64.b64encode(content).decode("utf-8")
    mime = media_type if media_type.startswith("image/") else "image/jpeg"

    from groq import Groq
    client = Groq(api_key=settings.groq_api_key)
    response = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Extract all text, numbers, monthly salary, net pay, total earnings, deductions, expenses, and savings from this document verbatim. List each item clearly."
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{b64_img}"}
                }
            ]
        }],
        max_tokens=1500,
        temperature=0.1,
    )
    return response.choices[0].message.content or ""


def extract_media(content: bytes, media_type: str) -> str:
    # 1. Handle PDF
    if media_type == "application/pdf":
        try:
            reader = PdfReader(io.BytesIO(content))
            extracted = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
            if len(extracted) >= 40:
                return extracted
        except Exception:
            pass

    # 2. Handle Images or Scanned PDFs: Primary = Groq Vision (no system binary needed)
    try:
        return _extract_image_with_vision(content, media_type)
    except Exception as vision_err:
        # 3. Fallback: Local pytesseract if installed
        try:
            import pytesseract
            image = Image.open(io.BytesIO(content))
            return pytesseract.image_to_string(image)
        except Exception as ocr_err:
            raise RuntimeError(
                f"Could not extract text from document: {vision_err}. (Local OCR fallback: {ocr_err})"
            )