# SQLAurum

![CI](https://github.com/performancemedia/sqlaurum/workflows/CI/badge.svg)
![Build](https://github.com/performancemedia/sqlaurum/workflows/Publish/badge.svg)
![License](https://img.shields.io/github/license/performancemedia/sqlaurum)
![Python](https://img.shields.io/pypi/pyversions/sqlaurum)
![Format](https://img.shields.io/pypi/format/sqlaurum)
![PyPi](https://img.shields.io/pypi/v/sqlaurum)
![Mypy](https://img.shields.io/badge/mypy-checked-blue)
![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)
[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)


*Wrapper around SQLAlchemy async session, core and Postgres native features*

## About

This library provides glue code to use sqlalchemy async sessions, core queries and orm models 
from one object which provides somewhat of repository pattern. This solution has few advantages:

- no need to pass `session` object to every function/method. It is stored (and optionally injected) in repository object
- write data access queries in one place
- no need to import `insert`,`update`, `delete`, `select` from sqlalchemy over and over again
- Implicit cast of results to `.scalars().all()` or `.one()`
- Your view model (e.g. FastAPI routes) does not need to know about the underlying storage. Repository class can be replaced at any moment any object providint similar interface.

## Usage

```python
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base
from sqlaurum import UUID, GenerateUUID, create_repository_class

Base = declarative_base()

class User(Base):
        __tablename__ = "user"
        id = sa.Column(
            UUID(), primary_key=True, server_default=GenerateUUID(), nullable=False
        )
        name = sa.Column(sa.Unicode(255))

Repository = create_repository_class("postgresql")

class UserRepository(Repository[User]):
    
    
    async def get_user_by_name(self, name: str):
        # custom user function
        return await self.select().filter_by(name=name).one()

user_repository = UserRepository(...)

# select
await user_repository.all()
await user_repository.select().where(User.name == "test")

# insert
user = await user_repository.insert({"name": "test"}).one()

await user_repository.commit()
# upsert
await user_repository.upsert({"name": "John"})

# delete
await user_repository.delete(name="John")

# custom sqlalchemy core functions

users = await user_repository.select().join(...).filter(
    User.name == "test"
).filter_by(...).order_by(User.created_at).limit(2).all()

```

## Sessions

Manager object needs `sqlalchemy.ext.asyncio.AsyncSession`, but it's possible
to provide the session object by yourself, by subclassing Manager class e.g.


```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine
from sqlaurum import create_session_factory, create_repository_class

engine = create_async_engine("sqlite+aiosqlite:///:memory:")
get_db = create_session_factory(engine)

AbstractRepository = create_repository_class(engine)


class Repository(AbstractRepository, abstract=True):
    """Base manager, which uses fastapi depends to get session object"""

    def __init__(self, session: AsyncSession = Depends(get_db)):
        super().__init__(session)

class UserRepository(Repository[User]):
    ...
        
# then in fastapi
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
async def get_users(user_repository: UserRepository = Depends(UserRepository)):
    return await user_repository.all()

```
