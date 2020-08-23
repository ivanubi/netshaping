import sys
import pathlib

sys.path.append(str(pathlib.Path().absolute()).replace("/models", ""))

from .base import BaseModel
from . import Connection, Interface
from app import db
import re


class Device(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    device_type = db.Column(db.String(50), default="router", nullable=False)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(2000))
    host = db.Column(db.String(200), unique=True)
    ssh_username = db.Column(db.String(40))
    ssh_password = db.Column(db.String(150))
    state = db.Column(db.String(40))

    interfaces = db.relationship("Interface", back_populates="device", cascade="all")
    logs = db.relationship("Log", back_populates="device", cascade="all")

    def update_interfaces(self):
        has_added_new_one = False
        connection = Connection(
            host=self.host, username=self.ssh_username, password=self.ssh_password
        )
        if connection.try_connection() == "success":
            interfaces_name = list(connection.interfaces().keys())
            print(interfaces_name)
            for interface_name in interfaces_name:
                if not Interface.query.filter_by(
                    device_id=self.id, name=interface_name
                ).scalar():
                    self.interfaces.append(Interface(name=interface_name))
                    has_added_new_one = True
            if has_added_new_one:
                db.session.commit()
                return "added_new_one"
            else:
                return "no_new_one"
        elif connection.try_connection() == "timeout":
            return "timeout"
        elif connection.try_connection() == "failed_authentication":
            return "failed_authentication"

    def validate(self):
        if self.host and self.__validate_ip(self.host) == False:
            return "Invalid IP"
        else:
            return None

    def __validate_ip(self, ip):
        regex = re.compile(
            "^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
            re.I,
        )
        match = regex.match(str(ip))
        return bool(match)

    def __repr__(self):
        return "<Device %r - ID %r>" % (self.name, self.id)
