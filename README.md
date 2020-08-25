# Dependencies

Redis
SQLite3
Python3

# Ubuntu Setup

pip install -r requirements.txt
redis-server &
celery -A app.celery beat --loglevel=info
celery -A app.celery worker --loglevel=info --concurrency=1 -Q celery1
celery -A app.celery worker --loglevel=info --concurrency=1 -Q celery2
celery -A app.celery worker --loglevel=info --concurrency=1 -Q celery3
export FLASK_APP=app.py
flask run

celery -A app.celery worker --loglevel=info