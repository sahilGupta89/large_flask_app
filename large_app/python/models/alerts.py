from sqlalchemy import Boolean, Column, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from .database import db
from .mixins import LifeCycleMixin, StandardObjectMixin


class AlertType(StandardObjectMixin, db.Model):
    name = Column(Text)
    description = Column(Text)


class AlertSubscription(LifeCycleMixin, db.Model):
    alert_type_id = Column(Integer, ForeignKey(AlertType.id), primary_key=True)
    alert_type = relationship(AlertType, uselist=False, lazy="joined")
    user_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    enabled = Column(Boolean, default=False, server_default="false")
    channels = Column(JSONB)

    @property
    def name(self):
        return self.alert_type.name

    @property
    def description(self):
        return self.alert_type.description
