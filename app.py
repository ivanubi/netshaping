import sys
import pathlib

sys.path.append(str(pathlib.Path().absolute()))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from celery import Celery

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend='redis://localhost:6379',
        broker='redis://localhost:6379'
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

app = Flask(__name__)
celery = make_celery(app)
celery.conf.beat_schedule = {
    "policy-stats": {
        "task": "app.policy_stats",
        "schedule": 30.0
    },
        "check-active-devices": {
        "task": "app.check_active_devices",
        "schedule": 60.0
    }
}
app.config.update(DEBUG=True, SECRET_KEY=b"ACEDEJEADEJE")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database/database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

from views import *
from datetime import datetime

@celery.task
def policy_stats():
    interfaces = Interface.query.filter(Interface.policy_id != None).all()

    for interface in interfaces:
        device = interface.device
        router = Connection(device.host, username = device.ssh_username, password = device.ssh_password)
        snapshot = router.stats_policy_interface(interface.name)
        if snapshot['success'] == True and ('classes' in snapshot):
            for class_name, stats in snapshot['classes'].items():
                interface.policy_stats.append(
                    Stat(
                        created_on=datetime.now(),
                        policy_name=snapshot['output_policy'],
                        class_name=stats['class_name'], 
                        offered_rate = int(stats['offered_rate']), 
                        drop_rate = int(stats['drop_rate'])
                    )
                )
            print(interface.policy_stats)
            interface.update()

@celery.task
def check_active_devices():
    try: 
        devices = Device.query.all()

        for device in devices:
            if device.try_connection() == "success":
                device.state = "active"
            else:
                device.state = "inactive"
            device.update()
    except:
        pass