
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

SQLAlchemyRepository = create_repository_class("postgresql")

class UserRepository(SQLAlchemyRepository[User]):
    
    
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

Repository object needs `sqlalchemy.ext.asyncio.AsyncSession`, but it's possible
to provide the session object by yourself, by subclassing Repository class e.g.


```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlaurum import create_repository_class, create_session_factory

engine = create_async_engine("sqlite+aiosqlite:///:memory:")
get_db = create_session_factory(engine)


BaseSQLAlchemyRepository = create_repository_class(engine)


class SQLAlchemyRepository(BaseSQLAlchemyRepository, abstract=True):
    """Base manager, which uses fastapi depends to get session object"""

    def __init__(self, session: AsyncSession = Depends(get_db)):
        super().__init__(session)

class UserRepository(SQLAlchemyRepository[User]):
    ...
        
# then in fastapi
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
async def get_users(user_repo: UserRepository = Depends(UserRepository)):
    users = await user_repo.all()
    return users

```