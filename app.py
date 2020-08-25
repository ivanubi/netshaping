import sys
import pathlib
import os

sys.path.append(str(pathlib.Path().absolute()))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from celery import Celery


def make_celery(app):
    celery = Celery(
        app.import_name,
        backend="redis://localhost:6379",
        broker="redis://localhost:6379",
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
        "schedule": 30.0,
        "options": {"queue": "celery1"},
    },
    "check-policy-schedule": {
        "task": "app.check_policy_schedule",
        "schedule": 60.0,
        "options": {"queue": "celery2"},
    },
    "policy-changes": {
        "task": "app.policy_changes",
        "schedule": 60.0,
        "options": {"queue": "celery3"},
    },
}
app.config.update(DEBUG=True, SECRET_KEY=b"ACEDEJEADEJE")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database/database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

from views import *
from datetime import datetime
from net import Connection


@celery.task
def check_policy_schedule():
    print("EXECUTING POLICY SCHEDULE")
    policy_schedules = InterfacePolicySchedule.query.all()

    now = datetime.today()
    week_day = now.isoweekday()
    print("—X— Day: {}, Hour: {}, Minute: {}".format(week_day, now.hour, now.minute))
    for policy_schedule in policy_schedules:
        print(
            "—Z— Day: {}, Hour: {} Minute: {}".format(
                policy_schedule.day,
                policy_schedule.time.hour,
                policy_schedule.time.minute,
            )
        )
        try:
            if (
                policy_schedule.day
                and policy_schedule.time
                and policy_schedule.time.hour == now.hour
                and policy_schedule.time.minute == now.minute
                and policy_schedule.day == week_day
            ):
                interface = policy_schedule.interface
                policy = Policy.query.get(policy_schedule.policy_id)
                connection = Connection(
                    host=interface.device.host,
                    username=interface.device.ssh_username,
                    password=interface.device.ssh_password,
                )
                commands = connection.generate_policy_to_int(policy, interface)
                was_succesful = connection.check_policy_interface(
                    interface.name, policy.name
                )
                if commands and was_succesful == True:
                    interface.policy_id = policy.id
                    interface.policy = policy
                    interface.update()
        except Exception as e:
            print(e)
            continue


@celery.task
def policy_changes():
    print("EXECUTING POLICY CHANGES")
    policies_changed = Policy.query.filter(Policy.changed == True)
    if policies_changed:
        for policy in policies_changed:
            policy.changed = False
            policy.update()
            for interface in policy.interfaces:
                try:
                    connection = Connection(
                        host=interface.device.host,
                        username=interface.device.ssh_username,
                        password=interface.device.ssh_password,
                    )
                    commands = connection.generate_policy_to_int(policy, interface)
                    was_succesful = connection.check_policy_interface(
                        interface.name, policy.name
                    )
                    if commands and was_succesful == True:
                        interface.policy_id = policy.id
                        interface.policy = policy
                        interface.update()
                except:
                    continue


@celery.task
def policy_stats():
    try:
        print("EXECUTING POLICY STATS")
        check_active_devices()
        interfaces = Interface.query.filter(Interface.policy_id != None).all()
        for interface in interfaces:
            device = interface.device
            router = Connection(
                device.host, username=device.ssh_username, password=device.ssh_password,
            )
            snapshot = router.stats_policy_interface(interface.name)
            if snapshot["success"] == True and ("classes" in snapshot):
                for class_name, stats in snapshot["classes"].items():
                    interface.policy_stats.append(
                        Stat(
                            created_on=datetime.now(),
                            policy_name=snapshot["output_policy"],
                            class_name=stats["class_name"],
                            offered_rate=int(stats["offered_rate"]),
                            drop_rate=int(stats["drop_rate"]),
                        )
                    )
                interface.update()
    except Exception as e:
        print(e)


def check_active_devices():
    devices = Device.query.all()
    for device in devices:
        connection = Connection(
            device.host, username=device.ssh_username, password=device.ssh_password
        )

        if connection.try_connection() == "success":
            device.state = "active"
        else:
            device.state = "inactive"
        device.update()
