from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession
from .repository import BaseSQLAlchemyRepository


class UoWContextManager(ABC):
    @abstractmethod
    async def __aenter__(self):
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        raise NotImplementedError

    async def commit(self):
        raise NotImplementedError


class SQLAlchemyUnitOfWork(UoWContextManager):
    repositories: dict[str, BaseSQLAlchemyRepository] = {}

    def __init__(self, session: AsyncSession, raise_on_exception: bool = True):
        self.session = session
        self._raise_on_exception = raise_on_exception
        self._repositories = {}
        self._transaction = None
        for name, repo_class in self.repositories.values():
            self._repositories[name] = repo_class(session=session)

    def __getattr__(self, item):
        return self._repositories.get(item)

    async def commit(self):
        await self.session.commit()

    async def __aenter__(self):
        self._transaction = self.session.begin()
        await self._transaction.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        try:
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            if self._raise_on_exception:
                raise e from exc
        finally:
            await self._transaction.__aexit__(exc_type, exc, tb)
