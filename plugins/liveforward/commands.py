import re
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import ChannelPrivate

from config import Config, temp
from database import db
from script import Script
from main import start_user_client, stop_user_client
from ..test import get_client

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
        await message.reply_text("A userbot is required for live forwarding. Please add one in /settings.")
        return

    temp.LIVE_FORWARD_CONV[user_id] = {"userbots": userbots}

    if len(userbots) == 1:
        # Auto-select if only one userbot exists
        conv = temp.LIVE_FORWARD_CONV[user_id]
        conv['listener_bot_id'] = userbots[0]['id']
        
        channels = await db.get_user_channels(user_id)
        if not channels:
            await message.reply_text("Please add a destination (To) channel in /settings.")
            temp.LIVE_FORWARD_CONV.pop(user_id, None)
            return
            
        buttons = [[InlineKeyboardButton(ch['title'], callback_data=f"live:to:{ch['chat_id']}")] for ch in channels]
        buttons.append([InlineKeyboardButton("Cancel", callback_data="live:cancel")])
        await message.reply_text("Using your only userbot for listening. Now, select the destination (To) channel:", reply_markup=InlineKeyboardMarkup(buttons))
    else:
        # Ask the user to choose a listener
        buttons = [[InlineKeyboardButton(f"👤 {ub.get('name', 'N/A')}", callback_data=f"live:listener:{ub['id']}")] for ub in userbots]
        buttons.append([InlineKeyboardButton("Cancel", callback_data="live:cancel")])
        await message.reply_text("Please select the userbot you want to use for both listening and forwarding:", reply_markup=InlineKeyboardMarkup(buttons))


async def finalize_and_start_live_forward(client, message, user_id, conv):
    from_chat_id = conv['from_chat_id']
    listener_bot_id = conv['listener_bot_id']
    
    listener_bot_details = next((ub for ub in conv['userbots'] if ub['id'] == listener_bot_id), {})
    userbot_username = listener_bot_details.get('username', 'your userbot')

    config_data = {
        "user_id": user_id,
        "from_chat_id": from_chat_id,
        "to_chat_id": conv['to_chat_id'],
        "bot_id": conv['bot_id'],
        "client_type": conv['client_type'],
        "listener_bot_id": listener_bot_id
    }
    Config.LIVE_FORWARD_CONFIG[from_chat_id] = config_data
    await db.add_live_forward(user_id, from_chat_id, conv['to_chat_id'], conv['bot_id'], conv['client_type'], listener_bot_id)
    
    await client.start_user_client(user_id, listener_bot_id)
    
    final_message = (
        f"✅ Live forwarding activated!\n\n"
        f"**Using Userbot:** `@{userbot_username}`\n"
        f"**IMPORTANT**: Please ensure this userbot has **JOINED** the source channel/group (`{from_chat_id}`) to detect new messages.\n\n"
        f"Use /stoplive to stop."
    )
    await message.edit_text(final_message)
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
        await query.message.edit_text("Setup cancelled.")
        return
        
    if action == "listener":
        conv['listener_bot_id'] = int(parts[2])
        channels = await db.get_user_channels(user_id)
        if not channels:
            await query.message.edit_text("Please add a destination (To) channel in /settings.")
            temp.LIVE_FORWARD_CONV.pop(user_id, None)
            return
        buttons = [[InlineKeyboardButton(ch['title'], callback_data=f"live:to:{ch['chat_id']}")] for ch in channels]
        buttons.append([InlineKeyboardButton("Cancel", callback_data="live:cancel")])
        await query.message.edit_text("Great. Now, select the destination (To) channel:", reply_markup=InlineKeyboardMarkup(buttons))

    elif action == "to":
        conv['to_chat_id'] = int(parts[2])
        conv['step'] = 'waiting_from'
        await query.message.edit_text("Excellent. Finally, forward a message from the source channel, or send its link.")
        
    elif action == "client":
        # This part is now effectively unused but kept for safety
        conv['client_type'] = parts[2]
        conv['bot_id'] = int(parts[3])
        await finalize_and_start_live_forward(client, query.message, user_id, conv)

@Client.on_message(filters.private & (filters.text | filters.forwarded), group=-2)
async def live_forward_message_handler(client, message):
    user_id = message.from_user.id
    conv = temp.LIVE_FORWARD_CONV.get(user_id)
    if not conv or conv.get('step') != 'waiting_from':
        return
    if message.text and message.text.startswith('/'):
        return
    
    processing_msg = await message.reply_text("`Checking channel...`")
    
    try:
        listener_bot_id = conv.get('listener_bot_id')
        userbot_session = next((ub['session'] for ub in conv['userbots'] if ub['id'] == listener_bot_id), None)

        if not userbot_session:
            await processing_msg.edit_text("Error: Could not find the selected listener userbot session.")
            return

        checker_client = await get_client(userbot_session, is_bot=False)
        async with checker_client:
            chat_info = await checker_client.get_chat(message.forward_from_chat.id if message.forward_from_chat else message.text)

        from_chat_id = chat_info.id
        conv['from_chat_id'] = from_chat_id

        # --- KEY FIX: Always use the listener userbot as the forwarder ---
        userbot = next((ub for ub in conv['userbots'] if ub['id'] == listener_bot_id), None)
        conv['client_type'] = 'userbot'
        conv['bot_id'] = userbot['id']
        await finalize_and_start_live_forward(client, processing_msg, user_id, conv)
            
    except Exception as e:
        await processing_msg.edit_text(f"An error occurred: `{e}`\nPlease ensure the link is correct or that your selected userbot has joined the channel.")
        temp.LIVE_FORWARD_CONV.pop(user_id, None)

@Client.on_message(filters.private & filters.command("stoplive"))
async def stop_live_forward(client, message):
    user_id = message.from_user.id
    configs_to_stop = [conf for conf in Config.LIVE_FORWARD_CONFIG.values() if conf['user_id'] == user_id]
    if not configs_to_stop:
        await message.reply_text("You don't have any active live forwards.")
        return
    
    listener_bot_id = None
    if configs_to_stop:
        listener_config = await db.get_live_forward_config(user_id, configs_to_stop[0]['from_chat_id'])
        if listener_config:
            listener_bot_id = listener_config.get('listener_bot_id')

    for config in configs_to_stop:
        del Config.LIVE_FORWARD_CONFIG[config['from_chat_id']]
        await db.remove_live_forward(user_id, config['from_chat_id'])
    
    if listener_bot_id:
        await client.stop_user_client(user_id, listener_bot_id)
    
    await message.reply_text("✅ All active live forward sessions have been stopped.")