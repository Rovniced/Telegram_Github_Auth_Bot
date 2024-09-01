import asyncio
import logging
import multiprocessing
import sys

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from hypercorn.asyncio import serve
from hypercorn.config import Config as HypercornConfig
from telegram import Update
from telegram.ext import CommandHandler, Application, ChatJoinRequestHandler

from src.api import oauth_router
from src.config import Config
from src.tgbot.command import Command

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        },
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'app.log',
            'formatter': 'default',
            'maxBytes': 10485760,
            'backupCount': 5,
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'stream': sys.stdout,
        }
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': Config.LOG_LEVEL,
    },
}


def run_bot():
    asyncio.set_event_loop(asyncio.new_event_loop())
    # noinspection PyUnresolvedReferences
    logging.config.dictConfig(LOGGING_CONFIG)
    logging.info("Bot process starting...")

    application = Application.builder().token(Config.BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", Command.start))
    application.add_handler(ChatJoinRequestHandler(Command.join))
    application.run_polling(allowed_updates=Update.ALL_TYPES)


def run_api():
    # noinspection PyUnresolvedReferences
    logging.config.dictConfig(LOGGING_CONFIG)
    logging.info("API process starting...")

    app = FastAPI()

    app.include_router(oauth_router)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(__request: Request, exc: HTTPException):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)

    hypercorn_config = HypercornConfig()
    hypercorn_config.bind = [f"{Config.HOST}:{Config.PORT}"]
    hypercorn_config.accesslog = '-'

    import asyncio
    # noinspection PyTypeChecker
    asyncio.run(serve(app, hypercorn_config))


if __name__ == "__main__":
    # noinspection PyUnresolvedReferences
    logging.config.dictConfig(LOGGING_CONFIG)

    bot_process = multiprocessing.Process(target=run_bot)
    api_process = multiprocessing.Process(target=run_api)

    bot_process.start()
    api_process.start()

    bot_process.join()
    api_process.join()
