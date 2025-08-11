Deploy on Render:
- Build: pip install -r requirements.txt
- Start: leave blank so Procfile is used, or set the same gunicorn command (not both)
- Health Check Path: /health

Troubleshooting:
- /debug shows template & static directories
- /repair recreates missing templates
- /csv downloads saved records
- Put your logo at static/logo.png
