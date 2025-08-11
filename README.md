Deploy on Render:
- Build: pip install -r requirements.txt
- Start: (use Procfile) or set Start Command to the same gunicorn line from Procfile (but not both).
- Health Check Path: /health
- Optional env vars: WORKERS=2, THREADS=2, TIMEOUT=120
