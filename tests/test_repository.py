from uuid import uuid4

import pytest
import sqlalchemy.exc

from sqlaurum.dialects.sqlite import SqliteModelRepository


def test_pytest_runs():
    assert 1 == 1


def test_user_repository_cls(user_repository):
    assert isinstance(user_repository, SqliteModelRepository)


async def test_user_repository(user_repository):
    res = await user_repository.select().all()
    assert res == []


async def test_user_repository_await(user_repository):
    res = await user_repository.select()
    assert res.scalars().all() == []


async def test_user_repository_await_one_or_none(user_repository):
    res = await user_repository.select().one_or_none()
    assert res is None


async def test_manager_insert(user_repository):
    result = await user_repository.insert({"name": "test"})
    result2 = await user_repository.select().all()
    assert len(result2) == 1
    if user_repository.supports_returning:
        result1 = result.scalars().one()
        assert result2 == [result1]
        assert result2[0].id == result1.id


async def test_manager_delete(user_repository):
    users = await user_repository.select().all()
    assert users == []
    await user_repository.insert({"name": "test"})
    users = await user_repository.select().all()
    assert len(users) == 1
    await user_repository.delete().execute()
    users = await user_repository.select().all()
    assert len(users) == 0


async def test_all_shortcut(user_repository):
    users = await user_repository.all()
    assert users == []

    not_user = await user_repository.one_or_none()
    assert not_user is None


async def test_one_not_found(user_repository):
    with pytest.raises(sqlalchemy.exc.NoResultFound):
        await user_repository.one()


async def test_default_upsert(user_repository):
    await user_repository.upsert({"name": "test"})


async def test_insert_no_conflict(user_repository):
    _id = uuid4()
    await user_repository.insert({"id": _id, "name": "test"}, ignore_conflicts=True)
    await user_repository.insert({"id": _id, "name": "test"}, ignore_conflicts=True)
    users = await user_repository.select().all()
    assert len(users) == 1
