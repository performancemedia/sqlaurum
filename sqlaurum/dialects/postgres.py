from __future__ import annotations
from sqlalchemy.dialects.postgresql import insert
from sqlaurum.manager import ModelQueryManager


class PostgresQueryManager(ModelQueryManager, abstract=True):

    supports_returning = True
    supports_on_conflict = True

    _insert = staticmethod(insert)
