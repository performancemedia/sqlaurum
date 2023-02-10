from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Generic, Sequence, TypeVar, Type

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from sqlaurum.types import OnConflict

M = TypeVar("M", bound=Type[DeclarativeBase])


class BaseQueryManager:
    supports_returning: bool = False

    _insert = staticmethod(sa.insert)
    _update = staticmethod(sa.update)
    _delete = staticmethod(sa.delete)
    _select = staticmethod(sa.select)

    def __init__(self, session: AsyncSession | None = None):
        self._session = session
        self._stmt: Any = None

    def __str__(self) -> str:
        if self._stmt is not None:
            return f"<{type(self).__name__}> [{self._stmt}]"
        return type(self).__name__

    def __repr__(self) -> str:
        return type(self).__name__

    def __aiter__(self):
        return self.session.stream_scalars(self._stmt)

    def __getattr__(self, item):
        self._stmt = getattr(self._stmt, item)
        return self

    def __call__(self, *args, **kwargs):
        self._stmt = self._stmt(*args, **kwargs)
        return self

    def __await__(self):
        return self.session.execute(self._stmt).__await__()

    @property
    def session(self) -> AsyncSession:
        assert self._session, "Session not set"
        return self._session

    async def flush(self, objects=None) -> None:
        await self.session.flush(objects)

    async def commit(self, raise_on_exception: bool = True) -> None:
        try:
            await self.session.commit()
        except:  # noqa
            await self.session.rollback()
            if raise_on_exception:
                raise

    @asynccontextmanager
    async def transaction(self):
        async with self.session.begin():
            yield

    def add(self, instance) -> None:
        self.session.add(instance)

    def add_all(self, instances) -> None:
        self.session.add_all(instances)

    async def execute(self, *args, **kwargs):
        if len(args) == 0:
            args = (self._stmt,)
        return await self.session.execute(*args, **kwargs)

    async def scalars(self, *args, **kwargs):
        return (await self.session.execute(self._stmt, *args, **kwargs)).scalars()

    async def all(self, *args, **kwargs) -> Sequence[M]:
        return (await self.scalars(*args, **kwargs)).all()

    async def one(self, *args, **kwargs) -> M:
        return (await self.scalars(*args, **kwargs)).one()

    get = one

    async def one_or_none(self, *args, **kwargs) -> M | None:
        return (await self.scalars(*args, **kwargs)).one_or_none()

    async def mappings(self, *args, **kwargs):
        return (await self.session.execute(*args, **kwargs)).mappings()

    def update(self, table, values: Any | None = None, **kwargs):
        query = self._update(table)
        if values:
            query = query.values(values, **kwargs)
        self._stmt = query
        return self

    def insert(
        self,
        table=None,
        values: Any | None = None,
        return_results: bool = True,
        **kwargs,
    ):
        query = self._insert(table)
        if values:
            query = query.values(values)
        if self.supports_returning and return_results:
            query = query.returning(table)
        self._stmt = query
        return self

    def delete(self, table, *args, **kwargs):
        query = self._delete(table)
        if args:
            query = query.filter(*args)
        if kwargs:
            query = query.filter_by(**kwargs)
        self._stmt = query
        return self

    def select(self, *args, **kwargs):
        self._stmt = self._select(*args, **kwargs)
        return self


class ModelQueryManager(BaseQueryManager, Generic[M]):
    """Base class which provides both SQLAlchemy core (with bound model) and session interfaces"""

    supports_on_conflict: bool = False

    model: M
    order_by: Any | None = None

    def __init_subclass__(cls, **kwargs):
        if "abstract" not in kwargs:
            cls.model = cls.__orig_bases__[0].__args__[0]
            assert cls.model

    @property
    def on_conflict(self) -> OnConflict:
        pk_columns = {c.name for c in self.model.__table__.primary_key.columns}  # type: ignore
        return {
            "index_elements": list(pk_columns),
            "set_": {
                c.name for c in self.model.__table__.columns if c.name not in pk_columns
            },
        }

    async def execute(self, *args, **kwargs):
        if self._stmt is not None:
            args = (self._stmt, *args)
        return await super().execute(*args, **kwargs)

    async def scalars(self, *args, **kwargs):
        if self._stmt is None:
            query = self._select(self.model)
            if self.order_by is not None:
                query = query.order_by(self.order_by)
            self._stmt = query
        return await super().scalars(*args, **kwargs)

    def update(self, values: Any | None = None, **kwargs):  # type: ignore
        return super().update(self.model, values, **kwargs)

    def insert(self, values: Any | None = None, return_results: bool = True, **kwargs):  # type: ignore
        super().insert(self.model, values, return_results=return_results)

        if self.supports_on_conflict:
            ignore_conflicts = kwargs.pop("ignore_conflicts", False)
            if ignore_conflicts:
                on_conflict = {k: self.on_conflict[k] for k in ("constraint", "index_elements") if k in self.on_conflict}  # type: ignore
                index_where = kwargs.pop("index_where", None)
                if index_where:
                    on_conflict["index_where"] = index_where
                self._stmt = self._stmt.on_conflict_do_nothing(**on_conflict)
        return self

    def delete(self, *args, **kwargs):
        return super().delete(self.model, *args, **kwargs)

    def select(self, *args, **kwargs):
        if len(args) == 0:
            args = (self.model,)
        self._stmt = self._select(*args, **kwargs)
        return self

    def upsert(self, values: Any | None = None, return_result: bool = True, **kwargs):
        assert (
            self.supports_on_conflict
        ), f"{type(self).__name__} does not support upsert"
        self.insert(values, return_result=return_result)
        kwargs.update(self.on_conflict)
        set_ = kwargs.pop("set_", None)
        if set_:
            kwargs["set_"] = {k: getattr(self._stmt.excluded, k) for k in set_}
        self._stmt = self._stmt.on_conflict_do_update(**kwargs)
        return self
