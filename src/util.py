from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler

from src.database.system import SystemOperate, SystemData


def generate_html(status: bool, text: str) -> str:
    if status:
        svg_content = f"""
            <svg class="checkmark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
                <circle class="checkmark__circle" cx="26" cy="26" r="25"/>
                <path class="checkmark__check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
            </svg>
            <div class="text">{text}</div>
        """
        color = "#4CAF50"
    else:
        svg_content = f"""
            <svg class="cross" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
                <circle class="cross__circle" cx="26" cy="26" r="25"/>
                <path class="cross__line1" fill="none" d="M16 16 36 36"/>
                <path class="cross__line2" fill="none" d="M36 16 16 36"/>
            </svg>
            <div class="text">{text}</div>
        """
        color = "#F44336"

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Telegram Github Auth Bot</title>
        <style>
            body {{
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background-color: #f0f0f0;
                font-family: Arial, sans-serif;
            }}
            .container {{
                display: flex;
                flex-direction: column;
                align-items: center;
                padding: 20px;
            }}
            .checkmark, .cross {{
                width: 56px;
                height: 56px;
                border-radius: 50%;
                display: block;
                stroke-width: 2;
                stroke: {color};
                stroke-miterlimit: 10;
                animation: scale .3s ease-in-out .9s both;
                position: relative;
                fill: white;
            }}
            .checkmark__circle, .cross__circle {{
                stroke-dasharray: 166;
                stroke-dashoffset: 166;
                stroke-width: 2;
                stroke-miterlimit: 10;
                stroke: {color};
                fill: none;
                animation: stroke 0.6s cubic-bezier(0.65, 0, 0.45, 1) forwards;
            }}
            .checkmark__check, .cross__line1, .cross__line2 {{
                transform-origin: 50% 50%;
                stroke-dasharray: 48;
                stroke-dashoffset: 48;
                stroke-width: 2;
                stroke: {color};
                animation: stroke 0.3s cubic-bezier(0.65, 0, 0.45, 1) 0.6s forwards;
            }}
            @keyframes stroke {{
                100% {{
                    stroke-dashoffset: 0;
                }}
            }}
            @keyframes scale {{
                0%, 100% {{
                    transform: none;
                }}
                50% {{
                    transform: scale3d(1.1, 1.1, 1);
                }}
            }}
            .text {{
                font-size: 24px;
                margin-top: 20px;
                color: {color};
                word-wrap: break-word;
                word-break: break-all;
                width: 90%;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            {svg_content}
        </div>
    </body>
    </html>
    """


async def bind_repo(update: Update, context: CallbackContext):
    chat_id = int(context.user_data.get('bind', ''))
    if chat_id == '':
        await update.message.reply_text("发生错误")
    repo_path = update.effective_message.text
    if "http" in repo_path:
        repo_path = repo_path.replace("https://github.com/", "")
    chat_data = await SystemOperate.get_chat_verify_info(chat_id)
    if chat_data:
        chat_data.path = repo_path
        await SystemOperate.update_chat_verify_info(chat_data)
        await update.effective_message.reply_text(f"当前群组验证仓库为：{chat_data.path}")
        return ConversationHandler.END
    else:
        chat_data = await SystemOperate.add_chat_verify_info(chat_id, repo_path)
        await update.effective_message.reply_text(f"当前群组验证仓库为：{chat_data.path}")
        return ConversationHandler.END
