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

    policy = db.relationship("Policy", back_populates="interfaces", uselist=False)
    device = db.relationship("Device", back_populates="interfaces", uselist=False)

    def validate(self):
        if len(self.description) > 2000:
            return "Too long description"
        elif (self.bandwidth.isdigit() == False) or (int(self.bandwidth) < 1):
            return "Invalid bandwidth"

    def __repr__(self):
        return "<Interface %r - ID %r>" % (self.name, self.id)

    def set(self, description=None, bandwidth=None):
        if description and self.description != description:
            self.description = description
        if bandwidth and self.bandwidth != bandwidth:
            self.bandwidth = bandwidth
