from __future__ import annotations

import functools
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from .repository import SQLAlchemyModelRepository


def create_repository_class(obj: str | AsyncEngine) -> type[SQLAlchemyModelRepository]:
    if isinstance(obj, str):
        dialect = obj
    elif isinstance(obj, AsyncEngine):
        dialect = obj.url.get_dialect().name
    else:
        raise TypeError(f"str or AsyncEngine expected, got {type(obj)}")

    if dialect == "postgres":
        from .dialects.postgres import PostgresModelRepository

        return PostgresModelRepository

    elif dialect == "sqlite":
        from .dialects.sqlite import SqliteModelRepository

        return SqliteModelRepository

    return SQLAlchemyModelRepository


def create_session_factory(engine: AsyncEngine, **kwargs):

    async_session = async_sessionmaker(bind=engine, expire_on_commit=False, **kwargs)

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
