import sqlite3

from sqlalchemy.dialects.sqlite import insert

from sqlaurum.repository import SQLAlchemyModelRepository


class SqliteModelRepository(SQLAlchemyModelRepository, abstract=True):
    _insert = staticmethod(insert)
    supports_returning = sqlite3.sqlite_version > "3.35"
    supports_on_conflict = True
