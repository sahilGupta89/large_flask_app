from sqlalchemy import Column, DateTime, func, Integer


class IdMixin(object):
    id = Column(Integer, primary_key=True)


class LifeCycleMixin(object):
    created = Column(
        DateTime, default=func.now(), server_default=func.now(), nullable=False
    )
    updated = Column(
        DateTime,
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted = Column(DateTime, default=None, nullable=True)


class StandardObjectMixin(IdMixin, LifeCycleMixin):
    pass
