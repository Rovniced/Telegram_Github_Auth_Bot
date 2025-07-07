from telegram import Update
from telegram.ext import ContextTypes

from src.tgbot.command import Command


async def delete_service_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("msg del")
    await update.message.delete()
    if update.message.left_chat_member:
        pass
    elif update.message.new_chat_members:
        for member in update.message.new_chat_members:
            print(f"User joined the chat. {str(member.id)}")
            await Command.verify_update(update, context)

