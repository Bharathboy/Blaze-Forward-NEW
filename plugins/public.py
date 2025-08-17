# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

import re
import asyncio
from .utils import STS
from database import Db, db
from config import temp
from script import Script
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.errors.exceptions.not_acceptable_406 import ChannelPrivate as PrivateChat
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, ChatAdminRequired, UsernameInvalid, UsernameNotModified, ChannelPrivate
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

# temp dictionary to hold conversation state for each user
if not hasattr(temp, 'FORWARD_CONV'):
    temp.FORWARD_CONV = {}

# --- HELPER FUNCTIONS ---

async def msg_edit(msg, text, reply_markup=None, wait=True):
    """A wrapper for editing messages to handle common exceptions."""
    try:
        return await msg.edit(text, reply_markup=reply_markup)
    except MessageNotModified:
        pass
    except FloodWait as e:
        if wait:
            await asyncio.sleep(e.value)
            return await msg_edit(msg, text, reply_markup, wait)

async def send_confirmation(bot, user_id, message):
    """Prepares and sends the final confirmation message to the user."""
    conv_data = temp.FORWARD_CONV[user_id]
    toid = conv_data['to_id']
    to_title = conv_data['to_title']
    client_type = conv_data['client_type']
    account = conv_data['bot_account'] if client_type == 'bot' else conv_data['userbot_account']
    fromid = conv_data['from_id']
    last_msg_id = conv_data['last_msg_id']
    skipno = conv_data['skipno']

    try:
        title = (await bot.get_chat(fromid)).title
    except (PrivateChat, ChannelPrivate, ChannelInvalid, UsernameInvalid, UsernameNotModified):
        title = "a private chat"
    except Exception as e:
        await message.reply(f'An error occurred while fetching chat title: {e}')
        del temp.FORWARD_CONV[user_id]
        return

    forward_id = f"{user_id}-{message.id}"
    buttons = [
        [InlineKeyboardButton('Yes, Start Forwarding', callback_data=f"start_public_{forward_id}")],
        [InlineKeyboardButton('No, Cancel', callback_data="close_btn")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    await message.reply_text(
        text=Script.DOUBLE_CHECK.format(
            botname=account.get('name', 'N/A'),
            botuname=account.get('username', 'N/A'),
            from_chat=title,
            to_chat=to_title,
            skip=skipno
        ),
        disable_web_page_preview=True,
        reply_markup=reply_markup
    )

    STS(forward_id).store(fromid, toid, skipno, last_msg_id, client_type)
    del temp.FORWARD_CONV[user_id]

async def ask_for_to_channel(bot, user_id, chat_id, message=None):
    """Asks the user to select a destination channel."""
    channels = await db.get_user_channels(user_id)
    if not channels:
        await bot.send_message(chat_id, "Please set a 'To' channel in /settings before forwarding.")
        if user_id in temp.FORWARD_CONV:
            del temp.FORWARD_CONV[user_id]
        return

    conv_data = temp.FORWARD_CONV[user_id]
    client_type = conv_data['client_type']
    account = conv_data['bot_account'] if client_type == 'bot' else conv_data['userbot_account']
    text = Script.TO_MSG.format(account.get('name', 'N/A'), account.get('username', 'N/A'))

    if len(channels) > 1:
        buttons = [
            [InlineKeyboardButton(f"{channel['title']}", callback_data=f"fwd:channel:{channel['chat_id']}:{channel['title']}")]
            for channel in channels
        ]
        buttons.append([InlineKeyboardButton("Cancel", callback_data="fwd:cancel")])
        reply_markup = InlineKeyboardMarkup(buttons)

        if message:
            await msg_edit(message, text, reply_markup=reply_markup)
        else:
            await bot.send_message(chat_id, text, reply_markup=reply_markup)
    else:
        # Auto-select if only one channel exists
        channel = channels[0]
        conv_data['to_id'] = channel['chat_id']
        conv_data['to_title'] = channel['title']
        conv_data['step'] = "waiting_from"

        prompt_message = Script.FROM_MSG
        if message:
            await msg_edit(message, prompt_message)
        else:
            await bot.send_message(chat_id, prompt_message)

# --- HANDLERS ---

@Client.on_message(filters.private & filters.command(["forward"]) )
async def forward_command(bot, message):
    """Entry point for the /forward command."""
    user_id = message.from_user.id
    if user_id in temp.FORWARD_CONV:
        del temp.FORWARD_CONV[user_id]

    bot_account = await db.get_bot(user_id)
    userbot_account = await db.get_userbot(user_id)

    if not bot_account and not userbot_account:
        return await message.reply("<code>You didn't add any bot. Please add a bot using /settings !</code>")

    temp.FORWARD_CONV[user_id] = {'bot_account': bot_account, 'userbot_account': userbot_account}

    if bot_account and not userbot_account:
        temp.FORWARD_CONV[user_id]['client_type'] = 'bot'
        await ask_for_to_channel(bot, user_id, message.chat.id)
    elif not bot_account and userbot_account:
        temp.FORWARD_CONV[user_id]['client_type'] = 'userbot'
        await ask_for_to_channel(bot, user_id, message.chat.id)
    else:
        buttons = [
            [InlineKeyboardButton(f"､Bot: {bot_account.get('name', 'N/A')}", callback_data="fwd:client:bot")],
            [InlineKeyboardButton(f"側 Userbot: {userbot_account.get('name', 'N/A')}", callback_data="fwd:client:userbot")],
            [InlineKeyboardButton("Cancel", callback_data="fwd:cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply(
            "You have both a bot and a userbot configured.\n\n"
            "**Which one would you like to use for this forward?**",
            reply_markup=reply_markup
        )

@Client.on_callback_query(filters.regex(r"^fwd:"))
async def forward_callback_handler(bot, query):
    """Handles all callback queries for the forward conversation."""
    user_id = query.from_user.id
    if user_id not in temp.FORWARD_CONV:
        return await query.answer("This is an old message. Please start the process again with /forward.", show_alert=True)

    data = query.data.split(':', 3)
    action = data[1]

    if action == "cancel":
        del temp.FORWARD_CONV[user_id]
        await query.answer("Operation cancelled.")
        await msg_edit(query.message, "Operation cancelled.")
        return

    if action == "client":
        client_type = data[2]
        temp.FORWARD_CONV[user_id]['client_type'] = client_type
        await query.answer(f"Selected {client_type}.")
        await ask_for_to_channel(bot, user_id, query.message.chat.id, message=query.message)

    elif action == "channel":
        to_id = int(data[2])
        to_title = data[3]
        temp.FORWARD_CONV[user_id].update({'to_id': to_id, 'to_title': to_title, 'step': "waiting_from"})
        await query.answer(f"Destination set to: {to_title}")
        await msg_edit(query.message, Script.FROM_MSG)

    elif action == "skip":
        choice = data[2]
        if choice == "yes":
            temp.FORWARD_CONV[user_id]['step'] = "waiting_skip"
            await query.answer("Please provide the number of messages to skip.")
            await msg_edit(query.message, Script.SKIP_MSG)
        else: # "no"
            temp.FORWARD_CONV[user_id]['skipno'] = 0
            await query.answer("Will not skip any messages.")
            await msg_edit(query.message, "Generating final confirmation...")
            await send_confirmation(bot, user_id, query.message)

@Client.on_message(filters.private & ~filters.command(["forward", "cancel", "help", "start", "restart", "settings"]) & filters.text)
async def forward_message_handler(bot, message):
    """Handles text message inputs during the forward conversation."""
    user_id = message.from_user.id
    if user_id not in temp.FORWARD_CONV or 'step' not in temp.FORWARD_CONV[user_id]:
        return

    conv_data = temp.FORWARD_CONV[user_id]
    step = conv_data.get('step')

    if message.text.startswith('/'):
        del temp.FORWARD_CONV[user_id]
        await message.reply(Script.CANCEL)
        return

    if step == "waiting_from":
        if message.text and not message.forward_date:
            regex = re.compile("(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
            match = regex.match(message.text.replace("?single", ""))
            if not match:
                return await message.reply('Invalid link. Please send a valid public message link.')
            chat_id = match.group(4)
            last_msg_id = int(match.group(5))
            if chat_id.isnumeric():
                chat_id = int("-100" + chat_id)
        elif message.forward_from_chat and message.forward_from_chat.type in [enums.ChatType.CHANNEL, enums.ChatType.SUPERGROUP]:
            last_msg_id = message.forward_from_message_id
            chat_id = message.forward_from_chat.username or message.forward_from_chat.id
            if last_msg_id is None:
                return await message.reply_text("This looks like a message from an anonymous admin. Please provide the last message link from the channel instead.")
        else:
            return await message.reply_text("Invalid input. Please forward a message or send a message link.")

        conv_data.update({'from_id': chat_id, 'last_msg_id': last_msg_id, 'step': 'confirm_skip'})
        
        buttons = [
            [InlineKeyboardButton("Yes", callback_data="fwd:skip:yes"),
             InlineKeyboardButton("No", callback_data="fwd:skip:no")]
        ]
        await message.reply("Do you want to skip any messages?", reply_markup=InlineKeyboardMarkup(buttons))

    elif step == "waiting_skip":
        if not message.text.isdigit():
            return await message.reply("Invalid number. Please enter only the number of messages to skip.")
        
        conv_data['skipno'] = int(message.text)
        await send_confirmation(bot, user_id, message)