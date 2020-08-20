import sys
import pathlib

sys.path.append(str(pathlib.Path().absolute()).replace("/models", ""))

from .base import BaseModel
from app import db


class Log(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    commands = db.Column(db.String(50000))
    description = db.Column(db.String(2000))
    device_id = db.Column(db.Integer, db.ForeignKey("device.id"), nullable=False)
    type = db.Column(db.String(50), default="commands", nullable=False)

    device = db.relationship("Device", back_populates="logs", uselist=False)

    def validate(self):
        if self.commands and len(self.commands > 50000):
            return "Command list is too long."
        elif self.description and len(self.description) > 20000:
            return "Too long description"

    def __repr__(self):
        return "<Log %r - ID %r>" % (self.name, self.id)

    def set(self, description=None, bandwidth=None):
        if description and self.description != description:
            self.description = description
        if commands and self.commands != commands:
            self.commands = commands
