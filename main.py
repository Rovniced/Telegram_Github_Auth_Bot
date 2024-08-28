import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from telegram import Update
from telegram.ext import CommandHandler, Application, MessageHandler, ChatJoinRequestHandler

from src.api import oauth_router
from src.config import Config
from src.tgbot.command import Command

app = FastAPI()

app.include_router(oauth_router)


@app.exception_handler(HTTPException)
async def http_exception_handler(__request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content=exc.detail)


def run_bot():
    application = Application.builder().token("TOKEN").build()
    application.add_handler(CommandHandler("start", Command.start))
    application.add_handler(ChatJoinRequestHandler(Command.join))
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    uvicorn.run(app='main:app', host=Config.HOST, port=Config.PORT, workers=Config.WORKERS)
    run_bot()
