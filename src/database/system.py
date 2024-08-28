import os

from sqlalchemy import select, Integer, String, create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncAttrs, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped

from src.config import Config


class SystemDatabaseModel(AsyncAttrs, DeclarativeBase):
    pass


class SystemData(SystemDatabaseModel):
    """验证信息"""
    __tablename__ = 'telegram'
    id: Mapped[int] = mapped_column(autoincrement=True, index=True, primary_key=True)
    chat_id: Mapped[int] = mapped_column(Integer, index=True, )  # 群组id
    path: Mapped[str] = mapped_column(String, index=True, )  # 对应的gitHub仓库地址


os.makedirs(Config.DATABASES_DIR, exist_ok=True)
sync_engine = create_engine(f"sqlite:///{Config.DATABASES_DIR / 'system.db'}")
with sync_engine.begin() as connection:
    SystemDatabaseModel.metadata.create_all(sync_engine)
    connection.execute(text('PRAGMA journal_mode = WAL'))
ENGINE = create_async_engine(f'sqlite+aiosqlite:///{Config.DATABASES_DIR / "system.db"}', echo=False)
SystemFactory = async_sessionmaker(bind=ENGINE, expire_on_commit=False)


class SystemOperate:
    @staticmethod
    async def get_chat_verify_info(chat_id: int) -> SystemData | None:
        """
        获取验证信息
        :param chat_id: 群组ID
        """
        async with SystemFactory() as session:
            data = await session.execute(select(SystemData).filter_by(chat_id=chat_id).limit(1))
            return data.scalar_one_or_none()

    @staticmethod
    async def update_chat_verify_info(data: SystemData):
        """
        更新验证信息
        :param data: 验证的数据
        """
        async with SystemFactory() as session:
            async with session.begin():
                await session.merge(data)

    @staticmethod
    async def add_chat_verify_info(chat_id: int, rep_path: str) -> SystemData:
        """
        增加验证信息
        """
        async with SystemFactory() as session:
            async with session.begin():
                data = SystemData(chat_id=chat_id, path=rep_path)
                session.add(data)
            return data
