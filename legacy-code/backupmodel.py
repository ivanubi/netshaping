from net import Connection
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.attributes import QueryableAttribute

import re


class BaseModel(db.Model):
    __abstract__ = True

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def create(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()


class Device(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    device_type = db.Column(db.String(50), default="router", nullable=False)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(2000))
    host = db.Column(db.String(200), unique=True)
    ssh_username = db.Column(db.String(40))
    ssh_password = db.Column(db.String(150))

    interfaces = db.relationship("Interface", back_populates="device", cascade="all")

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
                    name=interface_name, device_id=self.id
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
        if self.__validate_ip(self.host) == False:
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


class Interface(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    bandwidth = db.Column(db.Integer)
    description = db.Column(db.String(2000))
    policy_id = db.Column(db.Integer, db.ForeignKey("policy.id"))
    device_id = db.Column(db.Integer, db.ForeignKey("device.id"), nullable=False)

    policy = db.relationship("Policy", back_populates="interfaces", uselist=False)
    device = db.relationship("Device", back_populates="interfaces", uselist=False)

    def validate(self):
        if self.description > 2000:
            return "Too long description"
        elif (self.bandwidth.isdigit() == False) or (self.bandwidth < 1):
            return "Invalid bandwidth"

    def __repr__(self):
        return "<Interface %r - ID %r>" % (self.name, self.id)


class Policy(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(2000))
    services = db.relationship("ServicePolicySettings", back_populates="policy")
    interfaces = db.relationship("Interface", back_populates="policy")

    def validate(self):
        if len(self.name) > 80:
            return "name is too large"
        elif len(self.description) > 2000:
            return "description is too large"
        else:
            return None

    def delete(self):
        self.delete_services_settings()
        db.session.delete(self)
        db.session.commit()

    def delete_services_settings(self):
        for service_setting in self.services:
            service_setting.delete()

    def __repr__(self):
        return "<Policy %r - ID %r>" % (self.name, self.id)


class ServicePolicySettings(BaseModel):
    policy_id = db.Column(db.Integer, db.ForeignKey("policy.id"), primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey("service.id"), primary_key=True)
    min_bandwidth = db.Column(db.Integer)
    max_bandwidth = db.Column(db.Integer)
    mark_dscp = db.Column(db.Integer)

    service = db.relationship("Service", back_populates="policies")
    policy = db.relationship("Policy", back_populates="services")

    def create(self):
        self.service = Service.query.get(self.service_id)
        self.policy = Policy.query.get(self.policy_id)
        db.session.add(self)
        db.session.commit()


class Service(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(2000))
    match_ips = db.Column(db.String(2000))
    match_tcp_ports = db.Column(db.String(2000))
    match_udp_ports = db.Column(db.String(2000))
    match_dscp = db.Column(db.String(2000))
    policies = db.relationship("ServicePolicySettings", back_populates="service")

    def __repr__(self):
        return "<Service %r - ID %r>" % (self.name, self.id)

    def validate(self):
        if self.match_ips and self.match_ips.split(",") != []:
            for ip in self.match_ips.split(","):
                if self.__validate_ip(ip.replace(" ", "")) == False:
                    return "Some IPs are not valid"
        elif self.match_tcp_ports and self.match_tcp_ports.split(",") != []:
            for tcp_port in self.match_tcp_ports.split(","):
                if tcp_port.isdigit() == False:
                    return "Some TCP ports are invalid"
        elif self.match_udp_ports and self.match_udp_ports.split(",") != []:
            for udp_port in self.match_udp_ports.split(","):
                if udp_port.isdigit() == False:
                    return "Some UDPs ports are invalid"
        elif self.match_dscp and self.match_dscp.split(",") != []:
            for dscp in self.match_dscp.split(","):
                if dscp.isdigit() == False:
                    return "Some DSCPs ports are invalid"
        else:
            return None

    def create(self):
        db.session.add(self)
        db.session.commit()

    def __validate_ip(self, ip):
        regex = re.compile(
            "^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
            re.I,
        )
        match = regex.match(str(ip))
        return bool(match)
