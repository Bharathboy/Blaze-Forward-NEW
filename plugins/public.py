import re
import asyncio
from typing import Optional

from .utils import STS
from database import db
from config import temp
from script import Script
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.errors.exceptions.not_acceptable_406 import ChannelPrivate as PrivateChat
from pyrogram.errors.exceptions.bad_request_400 import (
    ChannelInvalid, UsernameInvalid, UsernameNotModified, ChannelPrivate
)
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# ensure conversation state dict exists
temp.FORWARD_CONV = getattr(temp, 'FORWARD_CONV', {})

COMMANDS = ["forward"]


async def msg_edit(msg, text, reply_markup=None, retry=True):
    """Safe edit: ignore 'not modified' and handle FloodWait by sleeping.
    Returns the edited message or None on failure.
    """
    try:
        return await msg.edit(text, reply_markup=reply_markup)
    except MessageNotModified:
        return None
    except FloodWait as e:
        if retry:
            await asyncio.sleep(e.value)
            return await msg_edit(msg, text, reply_markup, retry=False)


async def send_confirmation(bot: Client, user_id: int, message):
    """Prepare and send final confirmation, store forwarding state in STS.
    Pops conv state when done.
    """
    conv = temp.FORWARD_CONV.pop(user_id, None)
    if not conv:
        return await message.reply_text("Session expired. Start again with /forward.")

    toid = conv['to_id']
    to_title = conv['to_title']
    client_type = conv['client_type']
    account = conv['bot_account'] if client_type == 'bot' else conv['userbot_account']
    fromid = conv['from_id']
    last_msg_id = conv['last_msg_id']
    skipno = conv.get('skipno', 0)

    # try to get a readable source title
    try:
        title = (await bot.get_chat(fromid)).title
    except (PrivateChat, ChannelPrivate, ChannelInvalid, UsernameInvalid, UsernameNotModified):
        title = "a private chat"
    except Exception as e:
        await message.reply_text(f"An error occurred while fetching chat title: {e}")
        return

    forward_id = f"{user_id}-{message.id}"
    buttons = [
        [InlineKeyboardButton('Yes, Start Forwarding',
                              callback_data=f"start_public_{forward_id}")],
        [InlineKeyboardButton('No, Cancel', callback_data='close_btn')]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    await message.reply_text(
        Script.DOUBLE_CHECK.format(
            botname=account.get('name', 'N/A'),
            botuname=account.get('username', 'N/A'),
            from_chat=title,
            to_chat=to_title,
            skip=skipno
        ),
        disable_web_page_preview=True,
        reply_markup=reply_markup
    )

    # persist the forwarding config in STS
    STS(forward_id).store(fromid, toid, skipno, last_msg_id, client_type, account.get('id'))


async def ask_for_to_channel(bot: Client, user_id: int, chat_id: int, message=None):
    """Show channel choices or auto-select when only one exists."""
    channels = await db.get_user_channels(user_id)
    if not channels:
        await bot.send_message(chat_id, "Please set a 'To' channel in /settings before forwarding.")
        temp.FORWARD_CONV.pop(user_id, None)
        return

    conv = temp.FORWARD_CONV.setdefault(user_id, {})
    client_type = conv.get('client_type')
    account = conv.get('bot_account') if client_type == 'bot' else conv.get(
        'userbot_account')
    text = Script.TO_MSG.format(account.get(
        'name', 'N/A'), account.get('username', 'N/A'))

    if len(channels) > 1:
        buttons = [[InlineKeyboardButton(
            ch['title'], callback_data=f"fwd:channel:{ch['chat_id']}:{ch['title']}")] for ch in channels]
        buttons.append([InlineKeyboardButton(
            "Cancel", callback_data="fwd:cancel")])
        markup = InlineKeyboardMarkup(buttons)
        if message:
            await msg_edit(message, text, reply_markup=markup)
        else:
            await bot.send_message(chat_id, text, reply_markup=markup)
        return

    # only one channel -> auto-select
    ch = channels[0]
    conv.update({'to_id': ch['chat_id'],
                'to_title': ch['title'], 'step': 'waiting_from'})
    prompt_message = Script.FROM_MSG
    if message:
        await msg_edit(message, prompt_message)
    else:
        await bot.send_message(chat_id, prompt_message)


@Client.on_message(filters.private & filters.command(COMMANDS))
async def forward_command(bot: Client, message):
    user_id = message.from_user.id
    # reset any previous session
    temp.FORWARD_CONV.pop(user_id, None)

    bots = await db.get_bots(user_id)
    userbots = await db.get_userbots(user_id)
    
    if not bots and not userbots:
        return await message.reply_text("<code>You didn't add any bot. Please add a bot using /settings !</code>")

    temp.FORWARD_CONV[user_id] = {}
    
    buttons = []
    for _bot in bots:
        if _bot['id'] not in temp.lock.get(user_id, []):
            buttons.append([InlineKeyboardButton(
                f"Bot: {_bot.get('name', 'N/A')}", callback_data=f"fwd:client:bot:{_bot['id']}")])
    for usr_bot in userbots:
        if usr_bot['id'] not in temp.lock.get(user_id, []):
            buttons.append([InlineKeyboardButton(
                f"Userbot: {usr_bot.get('name', 'N/A')}", callback_data=f"fwd:client:userbot:{usr_bot['id']}")])
    
    if not buttons:
        return await message.reply_text("All your bots are currently busy. Please wait for a job to complete.")

    buttons.append([InlineKeyboardButton("Cancel", callback_data="fwd:cancel")])
    await message.reply_text(
        "You have multiple bots available.\n\nWhich one would you like to use for this forward?",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


@Client.on_callback_query(filters.regex(r"^fwd:"))
async def forward_callback_handler(bot: Client, query):
    user_id = query.from_user.id
    if user_id not in temp.FORWARD_CONV:
        return await query.answer("This is an old message. Please start again with /forward.", show_alert=True)

    # allow title to contain ':' by limiting splits
    parts = query.data.split(':', 4)
    action = parts[1]

    if action == 'cancel':
        temp.FORWARD_CONV.pop(user_id, None)
        await query.answer('Operation cancelled.')
        await msg_edit(query.message, 'Operation cancelled.')
        return

    if action == 'client':
        client_type = parts[2]
        bot_id = int(parts[3])
        
        if client_type == 'bot':
            account = await db.get_bot(user_id, bot_id)
            temp.FORWARD_CONV[user_id]['bot_account'] = account
        else:
            account = await db.get_userbot(user_id, bot_id)
            temp.FORWARD_CONV[user_id]['userbot_account'] = account
            
        temp.FORWARD_CONV[user_id]['client_type'] = client_type
        await query.answer(f"Selected {account.get('name', 'N/A')}.")
        await ask_for_to_channel(bot, user_id, query.message.chat.id, message=query.message)
        return

    if action == 'channel':
        to_id = int(parts[2])
        to_title = parts[3]
        temp.FORWARD_CONV[user_id].update(
            {'to_id': to_id, 'to_title': to_title, 'step': 'waiting_from'})
        await query.answer(f"Destination set to: {to_title}")
        await msg_edit(query.message, Script.FROM_MSG)
        return

    if action == 'skip':
        choice = parts[2]
        if choice == 'yes':
            temp.FORWARD_CONV[user_id]['step'] = 'waiting_skip'
            await query.answer('Please provide the number of messages to skip.')
            await msg_edit(query.message, Script.SKIP_MSG)
        else:
            temp.FORWARD_CONV[user_id]['skipno'] = 0
            await query.answer('Will not skip any messages.')
            await msg_edit(query.message, 'Generating final confirmation...')
            await send_confirmation(bot, user_id, query.message)


@Client.on_message(filters.private & filters.text, group=-1)
async def forward_message_handler(bot: Client, message):
    user_id = message.from_user.id
    conv = temp.FORWARD_CONV.get(user_id)
    if not conv or 'step' not in conv:
        return

    step = conv['step']
    try:
        # treat slash commands as cancellation
        if message.text.startswith('/'):
            temp.FORWARD_CONV.pop(user_id, None)
            return await message.reply_text(Script.CANCEL)
    except Exception as e:
        print(e)
        return

    # waiting for the source message (link or forwarded message)
    if step == 'waiting_from':
        # link-based public message
        if message.text and not getattr(message, 'forward_date', None):
            regex = re.compile(
                r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[A-Za-z_0-9]+)/(?P<msg>\d+)$")
            txt = message.text.replace('?single', '')
            m = regex.search(txt)
            if not m:
                return await message.reply_text('Invalid link. Please send a valid public message link.')

            chat_id = m.group(4)
            last_msg_id = int(m.group('msg'))
            if chat_id.isnumeric():
                chat_id = int(f"-100{chat_id}")

        # forwarded message from a channel/supergroup
        elif getattr(message, 'forward_from_chat', None) and message.forward_from_chat.type in [enums.ChatType.CHANNEL, enums.ChatType.SUPERGROUP]:
            last_msg_id = message.forward_from_message_id
            chat_id = message.forward_from_chat.username or message.forward_from_chat.id
            if last_msg_id is None:
                return await message.reply_text("This looks like a message from an anonymous admin. Please provide the last message link from the channel instead.")
        else:
            return await message.reply_text("Invalid input. Please forward a message or send a message link.")

        conv.update(
            {'from_id': chat_id, 'last_msg_id': last_msg_id, 'step': 'confirm_skip'})
        buttons = [[
            InlineKeyboardButton('Yes', callback_data='fwd:skip:yes'),
            InlineKeyboardButton('No', callback_data='fwd:skip:no')
        ]]
        await message.reply_text('Do you want to skip any messages?', reply_markup=InlineKeyboardMarkup(buttons))
        return

    # waiting for skip number
    if step == 'waiting_skip':
        if not message.text.isdigit():
            return await message.reply_text('Invalid number. Please enter only the number of messages to skip.')
        conv['skipno'] = int(message.text)
        await send_confirmation(bot, user_id, message)
        return