from __future__ import annotations

import functools
from contextlib import asynccontextmanager

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from sqlaurum.repository import SQLAlchemyModelRepository


def get_dialect_name(
    obj: str | AsyncSession | AsyncEngine,
) -> str:
    """
    Get the dialect of a session, engine, or connection url.
    """
    if isinstance(obj, str):
        return obj
    if isinstance(obj, AsyncSession):
        url = obj.bind.url  # type: ignore
    elif isinstance(obj, AsyncEngine):
        url = obj.url
    else:
        url = sa.engine.url.make_url(obj)

    return url.get_dialect()  # type: ignore


def create_repository_class(obj) -> type[SQLAlchemyModelRepository]:
    dialect = get_dialect_name(obj)

    if dialect == "postgres":
        from .dialects.postgres import PostgresModelRepository

        return PostgresModelRepository

    elif dialect == "sqlite":
        from .dialects.sqlite import SqliteModelRepository

        return SqliteModelRepository

    return SQLAlchemyModelRepository


def create_session_factory(engine: AsyncEngine, **kwargs):

    async_session = async_sessionmaker(engine, expire_on_commit=False, **kwargs)

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
    session_scope = asynccontextmanager(session_maker)

    def wrapper(func):
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            if "db" not in kwargs or kwargs["db"] is None:
                async with session_scope() as session:
                    kwargs["session"] = session
                    return await func(*args, **kwargs)

            return await func(*args, **kwargs)

        return wrapped

    return wrapper
