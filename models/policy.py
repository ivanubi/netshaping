import sys
import pathlib

sys.path.append(str(pathlib.Path().absolute()).replace("/models", ""))

from .base import BaseModel
from . import Service
from app import db


class Policy(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(2000))
    changed = db.Column(db.Boolean, default=False)
    services = db.relationship("ServicePolicySettings", back_populates="policy")
    interfaces = db.relationship("Interface", back_populates="policy")
    policy_schedules = db.relationship(
        "InterfacePolicySchedule", back_populates="policy", cascade="all"
    )

    def validate(self):
        if self.name and len(self.name) > 80:
            return "name is too large"
        elif self.description and len(self.description) > 2000:
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

    def validate(self):
        if self.min_bandwidth and self.min_bandwidth < 8001:
            return "minimum bandwidth should be greater than 8000kbps"
        elif self.max_bandwidth and self.max_bandwidth < 8001:
            return "shape bandwidth should be greater than 8000kbps"
        else:
            return None

    def create(self):
        self.service = Service.query.get(self.service_id)
        self.policy = Policy.query.get(self.policy_id)
        db.session.add(self)
        db.session.commit()
