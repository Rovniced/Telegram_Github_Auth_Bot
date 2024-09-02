import os
from datetime import datetime

from sqlalchemy import select, Integer, create_engine, text, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncAttrs, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped

from src.config import Config


class UserDatabaseModel(AsyncAttrs, DeclarativeBase):
    pass


class UserData(UserDatabaseModel):
    """用户验证信息"""
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(autoincrement=True, index=True, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True, )  # 用户id
    chat_id: Mapped[int] = mapped_column(Integer, index=True, )  # 群组id
    verify_time: Mapped[int] = mapped_column(Integer, )  # 验证开始时间戳
    failed_times: Mapped[int] = mapped_column(Integer, )  # 验证失败次数


os.makedirs(Config.DATABASES_DIR, exist_ok=True)
sync_engine = create_engine(f"sqlite:///{Config.DATABASES_DIR / 'user.db'}")
with sync_engine.begin() as connection:
    UserDatabaseModel.metadata.create_all(sync_engine)
    connection.execute(text('PRAGMA journal_mode = WAL'))
ENGINE = create_async_engine(f'sqlite+aiosqlite:///{Config.DATABASES_DIR / "user.db"}', echo=False)
UserFactory = async_sessionmaker(bind=ENGINE, expire_on_commit=False)


class UserOperate:
    @staticmethod
    async def get_user_info(user_id: int, chat_id: int) -> UserData | None:
        """
        获取对应账户的验证状态
        :param user_id: 用户id
        :param chat_id: 群组id
        """
        async with UserFactory() as session:
            data = await session.execute(select(UserData).filter_by(user_id=user_id, chat_id=chat_id).limit(1))
            return data.scalar_one_or_none()

    @staticmethod
    async def update_user_info(data: UserData):
        """
        更新用户验证状态
        :param data: 用户信息
        """
        async with UserFactory() as session:
            async with session.begin():
                await session.merge(data)

    @staticmethod
    async def add_user_verify_info(user_id: int, chat_id: int) -> UserData:
        """
        增加用户的验证信息
        """
        async with UserFactory() as session:
            async with session.begin():
                data = UserData(user_id=user_id, chat_id=chat_id, failed_times=1, verify_time=int(datetime.now().timestamp()))
            session.add(data)
            return data

    @staticmethod
    async def delete_user_info(user_id: int, chat_id: int) -> bool:
        """
        删除用户的验证信息
        """
        async with UserFactory() as session:
            async with session.begin():
                await session.execute(delete(UserData).filter_by(user_id=user_id, chat_id=chat_id))
            return True
