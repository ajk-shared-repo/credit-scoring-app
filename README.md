Use Start Command: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 120 --graceful-timeout 30 --keep-alive 5 --worker-tmp-dir /tmp
