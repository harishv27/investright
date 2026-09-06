| Layer | Technology |
|---|---|
| Frontend | React 19 (Vite 8) |
| Backend / API | Python 3.13, FastAPI 0.115 |
| Database | SQLite (dev) / PostgreSQL (prod-ready via SQLAlchemy 2.0) |
| Auth | JWT (python-jose), bcrypt/passlib password hashing |
| Data processing | Pure Python deterministic modules (analytics.py, risk.py, capacity.py, recommendation.py) |
| OCR / document extraction | pypdf, pytesseract, Pillow |
| Agent / LLM | Groq-hosted LLM, function calling (groq==0.31.0) |
| Testing | pytest (11/11 backend tests passing) |
