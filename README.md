# Prime Credit Reference Bureau App (Final)

Production-ready Flask app to collect credit-scoring inputs, compute a FICO-like score (range **300–850**), and generate a downloadable **PDF** report.

## Deploy to Render (no Procfile)

This repo intentionally **omits a Procfile** to avoid conflicts. Configure Render like this:

- **Build Command:** `pip install -r requirements.txt`
- **Start Command:**  
  ```
  gunicorn app:app --bind 0.0.0.0:$PORT --workers ${WORKERS:-2} --threads ${THREADS:-2} --timeout ${TIMEOUT:-120} --graceful-timeout 30 --keep-alive 5 --worker-tmp-dir /tmp --log-level info
  ```
- **Health Check Path:** `/health` (GET)
- **Environment Variables (optional, recommended):**
  - `WORKERS=2`
  - `THREADS=2`
  - `TIMEOUT=120`

**Important:** Make sure these files live at the **repo root**:
```
app.py
templates/
  form.html
  result.html
requirements.txt
runtime.txt
README.md
```

If you ever see template errors, hit `/debug` to see what Render actually deployed.

## Local development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py  # dev server on http://127.0.0.1:5000
```

## Notes

- The scoring logic is a heuristic for demonstration and **not** an official FICO implementation.
- PDF is generated with ReportLab.
- Routes:
  - `/` — form (GET), compute (POST)
  - `/health` — GET/HEAD 200
  - `/debug` — shows deployed files & templates
