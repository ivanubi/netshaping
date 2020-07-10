import sys
import pathlib
sys.path.append(str(pathlib.Path().absolute()).replace('/models',''))

from .base import BaseModel
from app import db
import re


class Service(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    type = db.Column(db.String(20), default='standard')
    match_protocol = db.Column(db.String(20))
    description = db.Column(db.String(2000))
    match_ips = db.Column(db.String(2000))
    match_tcp_ports = db.Column(db.String(2000))
    match_udp_ports = db.Column(db.String(2000))
    match_dscp = db.Column(db.String(2000))
    policies = db.relationship("ServicePolicySettings", back_populates="service")

    def supported_protocols_services(self):
        return self.query.filter_by(type='protocol').all()

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
