## [Repository pattern](https://www.cosmicpython.com/book/chapter_02_repository.html)



## Implementing with sqlaurum

### Define your repository interface, preferably using `Protocol`

```python
from typing import Protocol, TypeVar, Optional

EntityT = TypeVar("EntityT")

class IRepository(Protocol[EntityT]):
    
    
    async def add(self, entity: EntityT) -> None: ...
    
    async def get_by_id(self, id) -> Optional[EntityT]: ...

UserT = TypeVar("UserT") # bound=DomainModel 

class IUserRepository(IRepository[UserT]):
    
    async def get_user_by_name(self, name: str) -> UserT: ...
```

### Create sql repository
```python
from sqlaurum import create_repository_class
from app.database.models import UserModel

SqlRepository = create_repository_class(...)


class SqlUserRepository(SqlRepository[UserModel]):
    
    async def get_by_id(self, id):
        return await self.one_or_none(id=id)

    async def get_user_by_name(self, name: str):
        return await self.one_or_none(name=name)

```
### That's it!

Your application can now expect the `IUserRepository` which can be used for type annotations.
Then you can pass/inject `SqlUserRepository` instance which conforms the interface protocol
thanks to python duck typing system.