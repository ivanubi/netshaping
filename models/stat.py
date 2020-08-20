import sys
import pathlib

sys.path.append(str(pathlib.Path().absolute()).replace("/models", ""))

from .base import BaseModel
from app import db


class Stat(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    offered_rate = db.Column(db.Integer)
    drop_rate = db.Column(db.Integer)
    policy_name = db.Column(db.String(80))
    class_name = db.Column(db.String(80))
    interface_id = db.Column(db.Integer, db.ForeignKey("interface.id"), nullable=False)
    interface = db.relationship("Interface", back_populates="policy_stats", uselist=False)

    def __repr__(self):
        return "<Stat %r - ID %r>" % (self.name, self.id)