from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

# from sqlaurum import ...


async def get_db() -> AsyncSession:
    ...


class DependableManager(abstract=True):
    def __init__(self, session: AsyncSession = Depends(get_db)):
        super().__init__(session)
