import base64

import httpx
from fastapi import APIRouter, Response, Request, HTTPException

__all__ = ["oauth_router"]

from starlette.responses import HTMLResponse

from telegram import Bot

from src.config import Config
from src.database.system import SystemOperate
from src.database.user import UserOperate
from src.util import generate_html

oauth_router = APIRouter(prefix='/oauth', tags=["Github验证"])


class AuthException(Exception):
    pass


tg_bot = Bot(token=Config.BOT_TOKEN)


@oauth_router.get("/code", summary='code', description='code')
async def get_file(request: Request) -> Response:
    query_params = request.query_params
    code = query_params.get('code')
    state = query_params.get('state')
    try:
        if access_token := await get_access_token(code, state):
            user_id, chat_id = map(int, base64.b64decode(state).decode('utf-8').split("#"))
            chat_data = await SystemOperate.get_chat_verify_info(chat_id)
            if chat_data is None:
                return HTMLResponse(content=generate_html(False, "校验失败，群组未配置验证功能"), status_code=400)
            if await user_is_star(access_token, chat_data.path):
                await UserOperate.delete_user_info(user_id, chat_id)
                await tg_bot.restrict_chat_member(chat_id=chat_id, user_id=user_id, permissions={"can_send_messages": False,
                                                                                                 "can_send_polls ": False,
                                                                                                 "can_send_other_messages": False})
                return HTMLResponse(content=generate_html(True, "校验成功，您可以退出此页面并返回群组了"), status_code=200)
            else:
                return HTMLResponse(
                    content=generate_html(False, f"校验失败，您未给https://github.com/{chat_data.path}项目点star，请给该项目点击star后验证"),
                    status_code=300)
        else:
            return HTMLResponse(content=generate_html(False, "校验失败，access_token获取失败，请联系开发者"), status_code=401)
    except AuthException as e:
        return HTMLResponse(content=generate_html(False, "校验发生错误，请联系开发者 {e}"), status_code=500)


async def get_access_token(code: str, state: str) -> str:
    """
    获取access_token
    :param code:
    :param state:
    :return:
    """
    params = {
        "client_id": Config.CLIENT_ID,
        "client_secret": Config.CLIENT_SECRET,
        "code": code,
        "state": state
    }
    headers = {
        "Accept": "application/json"
    }
    url = "https://github.com/login/oauth/access_token"
    async with httpx.AsyncClient() as client:
        response = await client.post(url, params=params, headers=headers)
        access_token = response.json().get("access_token")
        return access_token


async def user_is_star(access_token: str, rep_path: str) -> bool:
    """
    判断指定仓库是否被star
    :param access_token:
    :param rep_path:
    :return:
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        url = "https://api.github.com/user/starred/" + rep_path
        response = await client.get(url, headers=headers)
        return response.status_code == 204
