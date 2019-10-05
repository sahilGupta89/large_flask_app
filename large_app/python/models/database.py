from flask_sqlalchemy import SQLAlchemy


class Wrapper(object):
    def __init__(self, sqlalchemy):
        self._db = sqlalchemy
        self._session = None
        self._nesting = 0

    @property
    def session(self):
        if self._session is None:
            raise RuntimeError("Use in context")

        return self._session

    @session.setter
    def session(self, new_session):
        assert self._nesting == 0
        self._db.session = new_session

    def __enter__(self):
        if self._session is None:
            assert self._nesting == 0
            self._session = self._db.session()
        self._nesting += 1

        return self._session

    def __exit__(self, type, value, _):
        self._nesting -= 1
        dirty = bool(
            self._session.new or self._session.dirty or self._session.deleted
        )

        if self._nesting == 0:
            self._session.close()
            self._session = None

        if value is None and dirty:
            raise RuntimeError("Dirty session!")

    def __getattr__(self, k):
        return getattr(self._db, k)


db = Wrapper(SQLAlchemy())
