import sys
import pathlib

sys.path.append(str(pathlib.Path().absolute()).replace("/models", ""))

from .base import BaseModel
from app import db


class Interface(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    bandwidth = db.Column(db.Integer)
    description = db.Column(db.String(2000))
    policy_id = db.Column(db.Integer, db.ForeignKey("policy.id"))
    device_id = db.Column(db.Integer, db.ForeignKey("device.id"), nullable=False)

    policy_stats = db.relationship("Stat", back_populates="interface", cascade="all")
    policy_schedules = db.relationship("InterfacePolicySchedule", back_populates="interface", cascade="all")
    policy = db.relationship("Policy", back_populates="interfaces", uselist=False)
    device = db.relationship("Device", back_populates="interfaces", uselist=False)

    def validate(self):
        if self.description and len(self.description) > 2000:
            return "Too long description"
        elif self.bandwidth and (self.bandwidth.isdigit() == False) or (int(self.bandwidth) < 1):
            return "Invalid bandwidth"

    def __repr__(self):
        return "<Interface %r - ID %r>" % (self.name, self.id)

    def set(self, description=None, bandwidth=None):
        if description and self.description != description:
            self.description = description
        if bandwidth and self.bandwidth != bandwidth:
            self.bandwidth = bandwidth

class InterfacePolicySchedule(BaseModel):
    id = db.Column(db.Integer primary_key=True)
    interface_id = db.Column(db.Integer, db.ForeignKey("interface.id"), nullable=False)
    policy_id = db.Column(db.Integer, db.ForeignKey("policy.id"), nullable=False)
    day = db.Column(db.Integer, default=1)
    time = db.Column(db.Time)

    interface = db.relationship("Interface", back_populates="policy_schedules")

    def create(self):
        self.interface = Interface.query.get(self.interface_id)
        db.session.add(self)
        db.session.commit()
