from __future__ import annotations

import uuid
from typing import Any, Generic, TypeVar

import sqlalchemy as sa
from sqlalchemy import CHAR, TypeDecorator
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.sql.type_api import TypeEngine

from .types import PydanticP

_T = TypeVar("_T", bound=PydanticP)


class JSON(TypeDecorator):
    """
    JSON type that returns SQLAlchemy's dialect-specific JSON types, where
    possible. Uses generic JSON otherwise.

    The "base" type is postgresql.JSONB to expose useful methods prior
    to SQL compilation
    """

    impl = postgresql.JSONB
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.JSONB(none_as_null=True))
        elif dialect.name == "sqlite":
            return dialect.type_descriptor(sqlite.JSON(none_as_null=True))
        else:
            return dialect.type_descriptor(sa.JSON(none_as_null=True))


class UUID(TypeDecorator):
    """
    Platform-independent UUID type.

    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(36), storing as stringified hex values with
    hyphens.
    """

    impl = TypeEngine
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.UUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        elif dialect.name == "postgresql":
            return str(value)
        elif isinstance(value, uuid.UUID):
            return str(value)
        else:
            return str(uuid.UUID(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value


class Pydantic(TypeDecorator, Generic[_T]):

    impl = JSON
    cache_ok = True

    def __init__(self, pydantic_type: type[_T], sa_column_type=None) -> None:
        super().__init__()
        self._pydantic_type = pydantic_type
        if sa_column_type is not None:
            self.impl = sa_column_type

    def process_bind_param(self, value, dialect) -> dict[str, Any] | None:
        if value is None:
            return None
        return self._pydantic_type.parse_obj(value).dict()

    def process_result_value(self, value, dialect) -> _T | None:
        if value:
            return self._pydantic_type.parse_obj(value)
        return None
