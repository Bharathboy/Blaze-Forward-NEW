# bharathboy/vj-forward-bot-new/VJ-Forward-Bot-NEW-084baf10231546bbbfc6225b6b9f609be14a7d31/plugins/public.py
import re
import asyncio 
from .utils import STS
from database import Db, db
from config import temp 
from script import Script
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait 
from pyrogram.errors.exceptions.not_acceptable_406 import ChannelPrivate as PrivateChat
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, ChatAdminRequired, UsernameInvalid, UsernameNotModified, ChannelPrivate
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

@Client.on_message(filters.private & filters.command(["forward"]))
async def run(bot, message):
    user_id = message.from_user.id
    
    bot_account = await db.get_bot(user_id)
    userbot_account = await db.get_userbot(user_id)
    _bot = None
    bot_type = None

    if not bot_account and not userbot_account:
        return await message.reply("<code>You didn't add any bot. Please add a bot using /settings !</code>")
    
    elif bot_account and not userbot_account:
        _bot = bot_account
        bot_type = 'bot'
    elif not bot_account and userbot_account:
        _bot = userbot_account
        bot_type = 'userbot'
    
    else:
        try:
            buttons = [
                # We use .get() to avoid errors if 'name' is not in the dictionary
                [KeyboardButton(f"🤖 Bot: {bot_account.get('name', 'N/A')}")],
                [KeyboardButton(f"👤 Userbot: {userbot_account.get('name', 'N/A')}")],
                [KeyboardButton("Cancel")]
            ]
            reply_markup = ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)
            
            choice_msg = await bot.ask(
                chat_id=message.chat.id,
                text="You have both a bot and a userbot configured.\n\n"
                     "**Which one would you like to use for this forward?**",
                reply_markup=reply_markup
            )

            if choice_msg.text.lower() == "cancel" or choice_msg.text.startswith('/'):
                return await message.reply("Operation cancelled.", reply_markup=ReplyKeyboardRemove())

            # Assign the chosen account to the `_bot` variable based on the reply
            if "🤖 Bot" in choice_msg.text:
                _bot = bot_account
                bot_type = 'bot'
            elif "👤 Userbot" in choice_msg.text:
                _bot = userbot_account
                bot_type = 'userbot'
            else:
                return await message.reply("Invalid choice. Operation cancelled.", reply_markup=ReplyKeyboardRemove())
        except Exception as e:
            return await message.reply(f"An error occurred: {e}. Operation cancelled.", reply_markup=ReplyKeyboardRemove())
    
    buttons = []
    btn_data = {}
    channels = await db.get_user_channels(user_id)
    if not channels:
       return await message.reply_text("please set a to channel in /settings before forwarding")
    
    if len(channels) > 1:
       for channel in channels:
         buttons.append([KeyboardButton(f"{channel['title']}")])
         btn_data[channel['title']] = channel['chat_id']
       buttons.append([KeyboardButton("cancel")]) 
       _toid = await bot.ask(message.chat.id, Script.TO_MSG.format(_bot['name'], _bot['username']), reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True))
       if _toid.text.startswith(('/', 'cancel')):
         return await message.reply_text(Script.CANCEL, reply_markup=ReplyKeyboardRemove())
       to_title = _toid.text
       toid = btn_data.get(to_title)
       if not toid:
         return await message.reply_text("wrong channel choosen !", reply_markup=ReplyKeyboardRemove())
    else:
       toid = channels[0]['chat_id']
       to_title = channels[0]['title']
    
    fromid = await bot.ask(message.chat.id, Script.FROM_MSG, reply_markup=ReplyKeyboardRemove())
    if fromid.text and fromid.text.startswith('/'):
       await message.reply(Script.CANCEL)
       return 
    
    if fromid.text and not fromid.forward_date:
       regex = re.compile("(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
       match = regex.match(fromid.text.replace("?single", ""))
       if not match:
           return await message.reply('Invalid link')
       chat_id = match.group(4)
       last_msg_id = int(match.group(5))
       if chat_id.isnumeric():
           chat_id  = int(("-100" + chat_id))
    elif fromid.forward_from_chat.type in [enums.ChatType.CHANNEL, 'supergroup']:
       last_msg_id = fromid.forward_from_message_id
       chat_id = fromid.forward_from_chat.username or fromid.forward_from_chat.id
       if last_msg_id == None:
           return await message.reply_text("**This may be a forwarded message from a group and sended by anonymous admin. instead of this please send last message link from group**")
    else:
       await message.reply_text("**invalid !**")
       return 
    
    try:
       title = (await bot.get_chat(chat_id)).title
    except (PrivateChat, ChannelPrivate, ChannelInvalid):
       title = "private" if fromid.text else fromid.forward_from_chat.title
    except (UsernameInvalid, UsernameNotModified):
       return await message.reply('Invalid Link specified.')
    except Exception as e:
       return await message.reply(f'Errors - {e}')
    
    skipno = await bot.ask(message.chat.id, Script.SKIP_MSG)
    if skipno.text.startswith('/'):
       await message.reply(Script.CANCEL)
       return
    
    forward_id = f"{user_id}-{skipno.id}"
    buttons = [[
        InlineKeyboardButton('Yes', callback_data=f"start_public_{forward_id}_{bot_type}"),
        InlineKeyboardButton('No', callback_data="close_btn")
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)
    await message.reply_text(
        text=Script.DOUBLE_CHECK.format(botname=_bot['name'], botuname=_bot['username'], from_chat=title, to_chat=to_title, skip=skipno.text),
        disable_web_page_preview=True,
        reply_markup=reply_markup
    )
    STS(forward_id).store(chat_id, toid, int(skipno.text), int(last_msg_id), bot_type)