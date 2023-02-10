from __future__ import annotations

import functools
from contextlib import asynccontextmanager
from typing import cast, Type

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from sqlaurum import ModelQueryManager


def get_dialect(
    obj: str | AsyncSession | AsyncEngine,
) -> type[sa.Dialect]:
    """
    Get the dialect of a session, engine, or connection url.
    """
    if isinstance(obj, AsyncSession):
        url = obj.bind.url  # type: ignore
    elif isinstance(obj, AsyncEngine):
        url = obj.url
    else:
        url = sa.engine.url.make_url(obj)

    return url.get_dialect()  # type: ignore


def get_query_manager_class(
    obj, base: type[object] | None = None
) -> type[ModelQueryManager]:
    dialect = get_dialect(obj)
    cls = ModelQueryManager

    if dialect.name == "postgres":
        from .dialects.postgres import PostgresQueryManager

        cls = PostgresQueryManager
    elif dialect.name == "sqlite":
        from .dialects.sqlite import SQLiteQueryManager

        cls = SQLiteQueryManager

    if base:
        return cast(Type[ModelQueryManager], type("", (base, cls), {}))

    return cls


def get_session_factory(engine: AsyncEngine, **kwargs):

    async_session = async_sessionmaker(engine, expire_on_commit=False, **kwargs)

    @asynccontextmanager
    async def get_session():
        async with async_session() as session:
            try:
                yield session
                await session.commit()
            except:  # noqa
                await session.rollback()
                raise

    return get_session


def inject_session(session_maker):
    def wrapper(func):
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            if "db" not in kwargs or kwargs["db"] is None:
                async with session_maker() as session:
                    kwargs["session"] = session
                    return await func(*args, **kwargs)

            return await func(*args, **kwargs)

        return wrapped

    return wrapper
