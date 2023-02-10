# Welcome to SQLAurum

## Version 0.1.0

## Description

*Wrapper around SQLAlchemy async session, core and Postgres native features*

## About

This library provides glue code to use sqlalchemy async sessions, core queries and orm models 
from one object which provides somewhat of repository pattern. This solution has few advantages:

- no need to pass `session` object to every function/method. It is stored (and optionally injected) in manager object
- write data access queries in one place
- no need to import `insert`,`update`, `delete`, `select` from sqlalchemy over and over again
- Implicit cast of results to `.scalars().all()` or `.one()`
- Your view model (e.g. FastAPI routes) does not need to know about the underlying storage. Manager class can be replaced at any moment any object providint similar interface.


## Usage

```python
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base
from sqlaurum import UUID, GenerateUUID, get_query_manager_class

Base = declarative_base()

class User(Base):
        __tablename__ = "user"
        id = sa.Column(
            UUID(), primary_key=True, server_default=GenerateUUID(), nullable=False
        )
        name = sa.Column(sa.Unicode(255))

Manager = get_query_manager_class("postgresql")

class UserManager(Manager[User]):
    
    
    async def get_user_by_name(self, name: str):
        # custom user function
        return await self.select().filter_by(name=name).one()

user_manager = UserManager(...)

# select
await user_manager.all()
await user_manager.select().where(User.name == "test")

# insert
user = await user_manager.insert({"name": "test"}).one()

await user_manager.commit()
# upsert
await user_manager.upsert({"name": "John"})

# delete
await user_manager.delete(name="John")

# custom sqlalchemy core functions

users = await user_manager.select().join(...).filter(
    User.name == "test"
).filter_by(...).order_by(User.created_at).limit(2).all()

```

## Sessions

Manager object needs `sqlalchemy.ext.asyncio.AsyncSession`, but it's possible
to provide the session object by yourself, by subclassing Manager class e.g.


```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlaurum import get_query_manager_class

engine = create_async_engine("sqlite+aiosqlite:///:memory:")
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    async with async_session() as db_session:
        try:
            yield db_session
            await db_session.commit()
        except: # noqa
            await db_session.rollback()
            raise
        finally:
            await db_session.close()

AbstractManager = get_query_manager_class(engine)



class BaseManager(AbstractManager, abstract=True):
    """Base manager, which uses fastapi depends to get session object"""

    def __init__(self, session: AsyncSession = Depends(get_db)):
        super().__init__(session)

class UserManager(BaseManager[User]):
    ...
        
# then in fastapi
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
async def get_users(m: UserManager = Depends(UserManager)):
    return await m.all()

```
