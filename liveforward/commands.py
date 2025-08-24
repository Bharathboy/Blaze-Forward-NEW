import re
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import ChannelPrivate

from config import Config, temp
from database import db
from script import Script
# We need to import the new controller functions from main
from main import start_live_forwarder_for_user, stop_live_forwarder_for_user

if not hasattr(Config, 'LIVE_FORWARD_CONFIG'):
    Config.LIVE_FORWARD_CONFIG = {}
if not hasattr(temp, 'LIVE_FORWARD_CONV'):
    temp.LIVE_FORWARD_CONV = {}

@Client.on_message(filters.private & filters.command("liveforward"))
async def live_forward_command(client, message):
    user_id = message.from_user.id
    
    if any(conf['user_id'] == user_id for conf in Config.LIVE_FORWARD_CONFIG.values()):
        await message.reply_text("You already have an active live forward session. Use /stoplive to stop it first.")
        return

    userbots = await db.get_userbots(user_id)
    if not userbots:
        await message.reply_text("A userbot is required for live forwarding. Please add one in /settings before proceeding.")
        return

    temp.LIVE_FORWARD_CONV[user_id] = {"userbots": userbots}
    
    channels = await db.get_user_channels(user_id)
    if not channels:
        await message.reply_text("Please add a destination (To) channel in /settings first.")
        temp.LIVE_FORWARD_CONV.pop(user_id, None)
        return
        
    buttons = [[InlineKeyboardButton(ch['title'], callback_data=f"live:to:{ch['chat_id']}")] for ch in channels]
    buttons.append([InlineKeyboardButton("Cancel", callback_data="live:cancel")])
    await message.reply_text("First, select the destination (To) channel for your live forward:", reply_markup=InlineKeyboardMarkup(buttons))

async def finalize_and_start_live_forward(message, user_id, conv):
    """A helper function to reduce code duplication."""
    from_chat_id = conv['from_chat_id']
    
    # Store config in memory and database
    Config.LIVE_FORWARD_CONFIG[from_chat_id] = {
        "user_id": user_id,
        "to_chat_id": conv['to_chat_id'],
        "bot_id": conv['bot_id'],
        "client_type": conv['client_type']
    }
    await db.add_live_forward(user_id, from_chat_id, conv['to_chat_id'], conv['bot_id'], conv['client_type'])
    
    # Start the user's specific listener client
    await start_live_forwarder_for_user(user_id)
    
    await message.edit_text(f"✅ Live forwarding activated!\n\nNew messages from `{from_chat_id}` will be forwarded to `{conv['to_chat_id']}`.\n\nUse /stoplive to stop.")
    temp.LIVE_FORWARD_CONV.pop(user_id, None)


@Client.on_callback_query(filters.regex(r"^live:"))
async def live_forward_callbacks(client, query):
    user_id = query.from_user.id
    parts = query.data.split(':')
    action = parts[1]

    conv = temp.LIVE_FORWARD_CONV.get(user_id)
    if not conv:
        await query.answer("This session has expired. Please start again.", show_alert=True)
        return

    if action == "cancel":
        temp.LIVE_FORWARD_CONV.pop(user_id, None)
        await query.message.edit_text("Live forwarding setup cancelled.")
        return

    if action == "to":
        to_chat_id = int(parts[2])
        conv['to_chat_id'] = to_chat_id
        conv['step'] = 'waiting_from'
        await query.message.edit_text("Great. Now, forward a message from the source (From) channel, or send me its link.")

    elif action == "client":
        client_type, bot_id = parts[2], int(parts[3])
        conv['client_type'] = client_type
        conv['bot_id'] = bot_id
        await finalize_and_start_live_forward(query.message, user_id, conv)


@Client.on_message(filters.private & (filters.text | filters.forwarded), group=-2)
async def live_forward_message_handler(client, message):
    user_id = message.from_user.id
    conv = temp.LIVE_FORWARD_CONV.get(user_id)

    if not conv or conv.get('step') != 'waiting_from':
        return

    if message.text and message.text.startswith('/'):
        if message.text == '/cancel':
            temp.LIVE_FORWARD_CONV.pop(user_id, None)
            await message.reply_text("Setup cancelled.")
        return

    from_chat_id = None
    is_private = False
    
    # Let the user know we're working on it
    processing_msg = await message.reply_text("`Checking channel...`")

    try:
        if message.forward_from_chat:
            from_chat_id = message.forward_from_chat.id
            if message.forward_from_chat.type == enums.ChatType.CHANNEL and not message.forward_from_chat.username:
                is_private = True
        elif message.text and "t.me" in message.text:
            chat_info = await client.get_chat(message.text.split('/')[-2] if "/c/" in message.text else message.text)
            from_chat_id = chat_info.id
            if chat_info.type == enums.ChatType.CHANNEL and not chat_info.username:
                is_private = True
        else:
            await processing_msg.edit_text("Invalid input. Please forward a message or send a channel link.")
            return

        conv['from_chat_id'] = from_chat_id

        if is_private:
            userbot = conv['userbots'][0]
            conv['client_type'] = 'userbot'
            conv['bot_id'] = userbot['id']
            await finalize_and_start_live_forward(processing_msg, user_id, conv)
        else:
            bots = await db.get_bots(user_id)
            userbots = conv['userbots']
            buttons = [[InlineKeyboardButton(f"🤖 BOT: {b.get('name', 'N/A')}", callback_data=f"live:client:bot:{b['id']}")] for b in bots]
            buttons.extend([[InlineKeyboardButton(f"👤 USERBOT: {u.get('name', 'N/A')}", callback_data=f"live:client:userbot:{u['id']}")] for u in userbots])
            buttons.append([InlineKeyboardButton("Cancel", callback_data="live:cancel")])
            await processing_msg.edit_text("Public channel detected. Please select which bot or userbot to use for forwarding:", reply_markup=InlineKeyboardMarkup(buttons))
            conv['step'] = 'waiting_client_choice'

    except ChannelPrivate:
        from_chat_id = message.forward_from_chat.id
        conv['from_chat_id'] = from_chat_id
        userbot = conv['userbots'][0]
        conv['client_type'] = 'userbot'
        conv['bot_id'] = userbot['id']
        await finalize_and_start_live_forward(processing_msg, user_id, conv)

    except Exception as e:
        await processing_msg.edit_text(f"An error occurred: `{e}`\nPlease try again.")
        temp.LIVE_FORWARD_CONV.pop(user_id, None)


@Client.on_message(filters.private & filters.command("stoplive"))
async def stop_live_forward(client, message):
    user_id = message.from_user.id
    
    keys_to_remove = [key for key, conf in Config.LIVE_FORWARD_CONFIG.items() if conf['user_id'] == user_id]
    
    if not keys_to_remove:
        await message.reply_text("You don't have any active live forward sessions.")
        return

    for key in keys_to_remove:
        del Config.LIVE_FORWARD_CONFIG[key]
        await db.remove_live_forward(user_id, key)
        
    # Stop the user's listener client
    await stop_live_forwarder_for_user(user_id)
        
    await message.reply_text("✅ All active live forward sessions have been stopped.")