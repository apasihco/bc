"""
MIT License

Copyright (c) 2023 TheHamkerCat

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import re
from datetime import datetime, timedelta

from pyrogram import filters
from pyrogram.types import ChatPermissions

from wbb import SUDOERS, app
from wbb.core.decorators.errors import capture_err
from wbb.core.decorators.permissions import adminsOnly
from wbb.modules.admin import list_admins
from wbb.utils.dbfunctions import (
    delete_bl_filter,
    get_bll_words,
    save_bl_filter,
)
from wbb.utils.filter_groups import bl_filters_group

__MODULE__ = "bl"
__HELP__ = """
/bll - Get All The bll Words In The Chat.
/bl [WORD|SENTENCE] - bl A Word Or A Sentence.
/wl [WORD|SENTENCE] - wl A Word Or A Sentence.
"""


@app.on_message(filters.command("bl") & ~filters.private)
@adminsOnly("can_restrict_members")
async def save_filters(_, message):
    if len(message.command) < 2:
        return await message.reply_text("Usage:\n/bl [WORD|SENTENCE]")
    word = message.text.split(None, 1)[1].strip()
    if not word:
        return await message.reply_text(
            "**Usage**\n__/bl [WORD|SENTENCE]__"
        )
    chat_id = message.chat.id
    await save_bl_filter(chat_id, word)
    await message.reply_text(f"__**bll {word}.**__")


@app.on_message(filters.command("bll") & ~filters.private)
@capture_err
async def get_filterss(_, message):
    data = await get_bll_words(message.chat.id)
    if not data:
        await message.reply_text("**No bll words in this chat.**")
    else:
        msg = f"List of bll words in {message.chat.title} :\n"
        for word in data:
            msg += f"**-** `{word}`\n"
        await message.reply_text(msg)


@app.on_message(filters.command("wl") & ~filters.private)
@adminsOnly("can_restrict_members")
async def del_filter(_, message):
    if len(message.command) < 2:
        return await message.reply_text("Usage:\n/wl [WORD|SENTENCE]")
    word = message.text.split(None, 1)[1].strip()
    if not word:
        return await message.reply_text("Usage:\n/wl [WORD|SENTENCE]")
    chat_id = message.chat.id
    deleted = await delete_bl_filter(chat_id, word)
    if deleted:
        return await message.reply_text(f"**wll {word}.**")
    await message.reply_text("**No such bl filter.**")


@app.on_message(filters.text & ~filters.private, group=bl_filters_group)
@capture_err
async def bl_filters_re(_, message):
    text = message.text.lower().strip()
    if not text:
        return
    chat_id = message.chat.id
    user = message.from_user
    if not user:
        return
    if user.id in SUDOERS:
        return
    list_of_filters = await get_bll_words(chat_id)
    for word in list_of_filters:
        pattern = r"( |^|[^\w])" + re.escape(word) + r"( |$|[^\w])"
        if re.search(pattern, text, flags=re.IGNORECASE):
            if user.id in await list_admins(chat_id):
                return
            try:
                await message.delete()
                await message.chat.restrict_member(
                    user.id,
                    ChatPermissions(),
                    until_date=datetime.now() + timedelta(minutes=60),
                )
            except Exception:
                return
            return await app.send_message(
                chat_id,
                f"Muted {user.mention} [`{user.id}`] for 1 hour "
                + f"due to a bl match on {word}.",
            )
