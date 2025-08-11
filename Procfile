web: gunicorn app:app --bind 0.0.0.0:$PORT --workers ${WORKERS:-2} --threads ${THREADS:-2} --timeout ${TIMEOUT:-120} --graceful-timeout 30 --keep-alive 5 --worker-tmp-dir /tmp --log-level info
