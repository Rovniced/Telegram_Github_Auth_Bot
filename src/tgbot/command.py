import base64
import time
from asyncio import sleep

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus
from telegram.ext import ContextTypes, ConversationHandler

from src.config import Config
from src.database.system import SystemOperate
from src.database.user import UserOperate


class Command:
    @staticmethod
    async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
        await update.message.reply_text(
            "欢迎使用验证机器人！\n"
            "以下是可用的命令：\n"
            "/bind - 绑定当前群组的验证仓库\n"
            "/cancel - 取消当前操作\n"
            "请确保您是群组的管理员，并且已配置好验证仓库。"
            "(本bot仍在开发阶段，可能存在一些问题)\n"
        )

    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
        if context.args:
            if context.args[0].startswith("bind_"):
                group_id = int(context.args[0].split("_")[1])
                chat_id = update.effective_chat.id
                user_id = update.effective_user.id
                data = await context.bot.get_chat_administrators(group_id)
                if user_id in [i.user.id for i in data]:
                    chat_data = await SystemOperate.get_chat_verify_info(group_id)
                    context.user_data['bind'] = group_id
                    if chat_data:
                        await context.bot.send_message(chat_id=chat_id,
                                                       text=f"当前群组验证仓库为：https://github.com/{chat_data.path}\n"
                                                            f"您可以输入新的仓库地址，或者输入/cancel取消此过程")
                        return 0
                    else:
                        await context.bot.send_message(chat_id=chat_id, text=f"当前群组验证仓库未绑定，请输入仓库地址")
                        return 0
            else:
                await update.message.reply_text(f"您不是管理员，无法进行此操作")
                return ConversationHandler.END

    @staticmethod
    async def member_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        print("member update")
        chat_member_update = update.chat_member
        old = chat_member_update.old_chat_member.status
        new = chat_member_update.new_chat_member.status
        was_member = old == ChatMemberStatus.MEMBER
        is_member = new == ChatMemberStatus.MEMBER or new == ChatMemberStatus.RESTRICTED
        if not was_member and is_member:
            # 用户加入群组
            await Command.verify_update(update, context)

    @staticmethod
    async def join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        # 入群验证处理
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        await context.bot.approve_chat_join_request(chat_id=chat_id, user_id=user_id)
        await Command.verify_update(update, context)

    @staticmethod
    async def verify_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        chat_data = await SystemOperate.get_chat_verify_info(chat_id)
        if chat_data is None:
            await context.bot.send_message(chat_id=chat_id,
                                           text=f"您好,{update.effective_user.first_name}，欢迎加入本群！\n")
            return
        state = base64.b64encode(f"{user_id}#{chat_id}".encode()).decode()
        url = (
            f"https://github.com/login/oauth/authorize?client_id={Config.CLIENT_ID}&redirect_uri={Config.REDIRECT_URI}&scope=user"
            f"&state={state}")
        button = InlineKeyboardMarkup([[InlineKeyboardButton(text="点我进行验证", url=url)]])
        join_msg = await context.bot.send_message(chat_id=chat_id,
                                                  text=f"您好,{update.effective_user.first_name}，欢迎加入本群！\n"
                                                       f"为了保证群内环境，需要验证您的身份。\n"
                                                       f"您需要star此项目GitHub仓库,然后点击下面的按钮登录进行验证。"
                                                       f"仓库地址：https://github.com/{chat_data.path}\n"
                                                       f"请点击以下按钮跳转到网页进行验证,限时为3分钟",
                                                  reply_markup=button)
        # 对用户设置禁言
        await context.bot.restrict_chat_member(chat_id=chat_id, user_id=user_id,
                                               permissions={"can_send_messages": False,
                                                            "can_send_polls ": False,
                                                            "can_send_other_messages": False})
        await UserOperate.add_user_verify_info(user_id, chat_id)
        start_time = time.time()
        await sleep(2)
        while time.time() - start_time < 60 * 3:
            user_data = await UserOperate.get_user_info(user_id, chat_id)
            if user_data is None:
                await join_msg.delete()
                return
            await sleep(3)
        await join_msg.delete()
        user_data = await UserOperate.get_user_info(user_id, chat_id)
        if user_data is None:
            return
        user_data.failed_times += 1
        await UserOperate.update_user_info(user_data)
        if user_data.failed_times >= 5:
            await context.bot.banChatMember(chat_id=chat_id, user_id=user_id)
        await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)

    @staticmethod
    async def bind(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        if data := await context.bot.get_chat_administrators(chat_id):
            if user_id in [i.user.id for i in data]:
                chat_data = await SystemOperate.get_chat_verify_info(chat_id)
                if chat_data is None:
                    url = f"https://t.me/{context.bot.username}?start=bind_{chat_id}"
                    button = InlineKeyboardMarkup([[InlineKeyboardButton(text="点我进行验证", url=url)]])
                    await context.bot.send_message(chat_id=chat_id, text="请点击下面的按钮配置验证信息",
                                                   reply_markup=button)
                    return
                await context.bot.send_message(chat_id=chat_id, text=f"当前群组验证仓库为：{chat_data.path}")
                return
            else:
                await context.bot.send_message(chat_id=chat_id, text="您不是管理员，无法进行此操作")
                return
        else:
            await context.bot.send_message(chat_id=chat_id, text="获取用户信息失败，请联系开发者")
            return

    @staticmethod
    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text('操作已取消。')
        return ConversationHandler.END
