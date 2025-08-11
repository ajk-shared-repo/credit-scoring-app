Render setup:
- Build: pip install -r requirements.txt
- Start: use Procfile OR set Start Command to the same gunicorn line (not both)
- Health Check: /health
- Optional env: WORKERS=2, THREADS=2, TIMEOUT=120
- If templates error persists, open /repair
