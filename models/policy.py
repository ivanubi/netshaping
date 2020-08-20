import sys
import pathlib
sys.path.append(str(pathlib.Path().absolute()).replace('/models',''))

from .base import BaseModel
from . import Service
from app import db


class Policy(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(2000))
    services = db.relationship("ServicePolicySettings", back_populates="policy")
    interfaces = db.relationship("Interface", back_populates="policy")

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

    def create(self):
        self.service = Service.query.get(self.service_id)
        self.policy = Policy.query.get(self.policy_id)
        db.session.add(self)
        db.session.commit()
