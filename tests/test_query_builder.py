import pytest
import sqlalchemy.exc


def test_pytest_runs():
    assert 1 == 1


async def test_user_manager(user_manager):
    res = await user_manager.select().all()
    assert res == []


async def test_user_manager_await(user_manager):
    res = await user_manager.select()
    assert res.scalars().all() == []


async def test_user_manager_await_one_or_none(user_manager):
    res = await user_manager.select().one_or_none()
    assert res is None


async def test_manager_insert(user_manager):
    result = await user_manager.insert({"name": "test"})
    result2 = await user_manager.select().all()
    assert len(result2) == 1
    if user_manager.supports_returning:
        result1 = result.scalars().one()
        assert result2 == [result1]
        assert result2[0].id == result1.id


async def test_manager_delete(user_manager):
    users = await user_manager.select().all()
    assert users == []
    await user_manager.insert({"name": "test"})
    users = await user_manager.select().all()
    assert len(users) == 1
    await user_manager.delete().execute()
    users = await user_manager.select().all()
    assert len(users) == 0


async def test_all_shortcut(user_manager):
    users = await user_manager.all()
    assert users == []

    not_user = await user_manager.one_or_none()
    assert not_user is None


async def test_one_not_found(user_manager):
    with pytest.raises(sqlalchemy.exc.NoResultFound):
        await user_manager.one()


async def test_default_upsert(user_manager):
    await user_manager.upsert({"name": "test"})


async def test_insert_no_conflict(user_manager):
    await user_manager.insert({"name": "test"}, ignore_conflicts=True)
    await user_manager.insert({"name": "test"}, ignore_conflicts=True)
    users = await user_manager.select().all()
    assert len(users) == 1
