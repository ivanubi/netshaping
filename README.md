
# NetShaping 
![Image of Netshaping interface](https://i.imgur.com/FPZuacy.png)
### Software Defined Quality of Service (SDQOS)
This is my grad project for the Telematics Engineering degree at PUCMM university. It enables Cisco devices (even very old ones) to have software defined quality of service capabilities. It allows for the quality of service configuration of those devices to be configured by software (code). On top of the main module that generate and sends the instructions to the router (the net.py module) we built a web-app that allows us to configure QoS settings using a beautiful interface.

# Dependencies

- Redis
- SQLite3
- Python3

# Ubuntu Setup

```
pip install -r requirements.txt
redis-server &
celery -A app.celery beat --loglevel=info
celery -A app.celery worker --loglevel=info --concurrency=1 -Q celery1
celery -A app.celery worker --loglevel=info --concurrency=1 -Q celery2
celery -A app.celery worker --loglevel=info --concurrency=1 -Q celery3
celery -A app.celery worker --loglevel=info --concurrency=1 -Q celery4
export FLASK_APP=app.py
flask run
```
