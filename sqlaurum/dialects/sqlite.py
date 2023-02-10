import sqlite3

from sqlalchemy.dialects.sqlite import insert

from sqlaurum.manager import ModelQueryManager


class SQLiteQueryManager(ModelQueryManager, abstract=True):

    supports_returning = sqlite3.sqlite_version > "3.35"
    supports_on_conflict = True
    _insert = staticmethod(insert)
