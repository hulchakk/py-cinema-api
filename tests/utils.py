from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.accounts import UserGroupModel, UserGroupEnum


async def get_default_user_group(db_session: AsyncSession) -> UserGroupModel:
    stmt = select(UserGroupModel).where(UserGroupModel.name == UserGroupEnum.USER)
    user_group = await db_session.scalar(stmt)

    assert user_group is not None

    return user_group
