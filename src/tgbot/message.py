from telegram import Update
from telegram.ext import ContextTypes


async def delete_service_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("msg del")
    await update.message.delete()
