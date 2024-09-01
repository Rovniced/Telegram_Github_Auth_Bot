import base64
from asyncio import sleep

from telegram import Update, InlineKeyboardButton
from telegram.ext import ContextTypes

from src.config import Config
from src.database.system import SystemOperate
from src.database.user import UserOperate


class Command:
    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        pass

    @staticmethod
    async def join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        # 入群验证处理
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        await context.bot.approve_chat_join_request(chat_id=chat_id, user_id=user_id)
        chat_data = await SystemOperate.get_chat_verify_info(chat_id)
        if chat_data is None:
            await context.bot.send_message(chat_id=chat_id, text=f"您好,{update.effective_user.first_name}，欢迎加入本群！\n"
                                                                 f"本群暂未配置验证功能。")
            return
        state = base64.b64encode(f"{user_id}#{chat_id}".encode()).decode()
        url = (f"https://github.com/login/oauth/authorize?client_id={Config.CLIENT_ID}&redirect_uri={Config.REDIRECT_URI}&scope=user"
               f"&state={state}")
        button = [[InlineKeyboardButton(text="点我进行验证", url=url)]]
        await context.bot.send_message(chat_id=chat_id, text=f"您好,{update.effective_user.first_name}，欢迎加入本群！\n"
                                                             f"为了保证群内环境，需要验证您的身份。\n"
                                                             f"您需要star此项目GitHub仓库,然后点击下面的按钮登录进行验证。"
                                                             f"仓库地址：https://github.com/{chat_data.path}\n"
                                                             f"请点击以下按钮跳转到网页进行验证,限时为5分钟", reply_markup=button)
        # 对用户设置禁言
        await context.bot.restrict_chat_member(chat_id=chat_id, user_id=user_id, can_send_messages=False)
        await UserOperate.add_user_verify_info(user_id, chat_id)
        # 设置定时任务，5分钟后未通过直接踢出
        await sleep(60 * 5)
        user_data = await UserOperate.get_user_info(user_id, chat_id)
        if user_data is None:
            return
        await context.bot.kick_chat_member(chat_id=chat_id, user_id=user_id)
