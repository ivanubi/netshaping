# Dependencies

Redis
SQLite3
Python3

# Ubuntu Setup

pip install -r requirements.txt
redis-server &
celery -A app.celery beat --loglevel=info
celery -A app.celery worker --loglevel=info
export FLASK_APP=app.py
flask run