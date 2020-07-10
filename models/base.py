import sys
import pathlib

sys.path.append(str(pathlib.Path().absolute()).replace("/models", ""))

from app import db


class BaseModel(db.Model):
    __abstract__ = True

    created_on = db.Column(db.DateTime, index=False, unique=False, nullable=True)
    last_login = db.Column(db.DateTime, index=False, unique=False, nullable=True)

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def create(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()
