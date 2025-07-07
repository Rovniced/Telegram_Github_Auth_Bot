from telegram import Update
from telegram.ext import ContextTypes


async def delete_service_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.delete()
