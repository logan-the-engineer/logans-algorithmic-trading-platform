# Trading Platform API (FastAPI skeleton)

## Quickstart
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc:      http://127.0.0.1:8000/redoc
- OpenAPI:    http://127.0.0.1:8000/openapi.json

## Notes
- This is a server skeleton: handlers return placeholder data.
- Base path is `/api/v1`.
- Auth is stubbed as a bearer token check in `app/security.py`.
