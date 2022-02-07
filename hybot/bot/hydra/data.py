from typing import Optional

from aiocache import cached
from aiogram.types import Message
from attrdict import AttrDict

from hydra.rpc import BaseRPC
from hydb.api.client import HyDbClient, schemas

from . import HydraBot


class HydraBotData:
    __CREATING__ = []

    SERVER_INFO: schemas.ServerInfo
    STATS: schemas.Stats

    @cached(ttl=60)
    async def get_stats(self, bot: HydraBot) -> schemas.Stats:
        return await bot.db.asyncc.stats()

    @staticmethod
    def init(db: HyDbClient):
        HydraBotData.SERVER_INFO = db.server_info()

    @staticmethod
    async def update_at(db: HyDbClient, u: schemas.User, msg: Message) -> schemas.User:
        if u.info.get("at", "") != msg.from_user.username:
            u.info.at = msg.from_user.username

            await db.asyncc.user_info_put(u, u.info)

        return u

    @staticmethod
    async def user_load(bot: HydraBot, msg: Message, create: bool = True, requires_start: bool = True, dm_only: bool = True) -> Optional[schemas.User]:
        if msg.from_user.id in HydraBotData.__CREATING__:
            raise RuntimeError("Currently creating user account!")

        if msg.chat.id < 0 and dm_only:
            await msg.reply(f"Hi {msg.from_user.first_name}, that function is only available in a private chat.")
            return

        try:
            u: schemas.User = await bot.db.asyncc.user_get_tg(msg.from_user.id)

            if msg.chat.id < 0 and requires_start and "tz" not in u.info:
                bot_name = (await bot.get_me()).username
                await msg.reply(f"Hi {msg.from_user.first_name}!\nTo get started please send <pre>/start</pre> privately to me at @{bot_name}.")
                return

            return await HydraBotData.update_at(bot.db, u, msg)

        except BaseRPC.Exception as exc:
            if exc.response.status_code == 404:
                if msg.chat.id < 0 and requires_start:
                    bot_name = (await bot.get_me()).username
                    await msg.reply(f"Hi {msg.from_user.first_name}!\nTo get started please send <pre>/start</pre> privately to me at @{bot_name}.")
                    return

                if create:
                    if msg.from_user.id in HydraBotData.__CREATING__:
                        raise RuntimeError("Currently creating user account!")

                    HydraBotData.__CREATING__.append(msg.from_user.id)

                    try:
                        await msg.answer(
                            f"Welcome, <b>{msg.from_user.full_name}!</b>\n\n"
                            "One moment while I set things up..."
                        )

                        u: schemas.User = await bot.db.asyncc.user_add(msg.from_user.id)

                        return await HydraBotData.update_at(bot.db, u, msg)
                    finally:
                        HydraBotData.__CREATING__.remove(msg.from_user.id)
                else:
                    return None

            raise
