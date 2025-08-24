import re
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import ChannelPrivate, UserNotParticipant, ChannelInvalid, UsernameInvalid, PeerIdInvalid

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

    # Check for premium status and get task limit
    user_rank = await db.get_premium_user_rank(user_id)
    is_premium = user_rank != "default"
    source_limit = Config.TASK_LIMITS.get(user_rank, 1)

    temp.LIVE_FORWARD_CONV[user_id] = {
        "userbots": userbots, 
        "is_premium": is_premium,
        "source_limit": source_limit
    }

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
    listener_bot_id = conv['listener_bot_id']
    to_chat_id = conv['to_chat_id']
    
    listener_bot_details = next((ub for ub in conv['userbots'] if ub['id'] == listener_bot_id), {})
    userbot_username = listener_bot_details.get('username', 'your userbot')
    userbot_session = listener_bot_details.get('session')

    # Get chat IDs from the appropriate place
    if conv.get("is_premium", False):
        from_chat_ids = list(conv.get('from_chat_info', {}).keys())
    else:
        from_chat_ids = [conv.get('from_chat_id')]

    source_chats_text = ""
    for chat_id in from_chat_ids:
        if not chat_id: continue
        title = conv.get('from_chat_info', {}).get(chat_id, f"ID: {chat_id}")
        source_chats_text += f"- `{title}`\n"
    
    # Use the listener userbot to get the destination chat title
    to_chat_title = f"Private Chat ({to_chat_id})"
    if userbot_session:
        temp_userbot_client = await get_client(userbot_session, is_bot=False)
        async with temp_userbot_client:
            try:
                chat = await temp_userbot_client.get_chat(to_chat_id)
                to_chat_title = chat.title
            except Exception as e:
                print(f"Could not get 'to_chat' title with userbot: {e}")

    for from_chat_id in from_chat_ids:
        if not from_chat_id: continue
        config_data = {
            "user_id": user_id, "from_chat_id": from_chat_id, "to_chat_id": to_chat_id,
            "bot_id": conv['bot_id'], "client_type": conv['client_type'], "listener_bot_id": listener_bot_id
        }
        Config.LIVE_FORWARD_CONFIG[from_chat_id] = config_data
        await db.add_live_forward(user_id, from_chat_id, to_chat_id, conv['bot_id'], conv['client_type'], listener_bot_id)

    await client.start_user_client(user_id, listener_bot_id)

    final_message = (
        f"✅ Live forwarding activated!\n\n"
        f"**Using Userbot:** `@{userbot_username}`\n"
        f"**Forwarding from:**\n{source_chats_text}"
        f"**To:** `{to_chat_title}`\n\n"
        f"**IMPORTANT**: Please ensure this userbot has **JOINED** all source channels/groups to detect new messages.\n\n"
        f"Use /stoplive to stop."
    )
    await message.edit_text(final_message, reply_markup=None)
        
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
        is_premium = conv.get("is_premium", False)

        if is_premium:
            conv['from_chat_info'] = {} # Use a dict to store {id: title}
            await query.message.edit_text(
                "Excellent. As a premium user, you can add multiple source channels.\n\n"
                "Forward a message from the first source channel, or send its link.\n\n"
                "When you are finished adding sources, click the 'Done' button."
            )
        else:
            await query.message.edit_text("Excellent. Finally, forward a message from the source channel, or send its link.\n **Note:** Premium users can add multiple source channels, check /plans.")
            
    elif action == "done_adding_sources":
        if not conv.get('from_chat_info'):
            await query.answer("You haven't added any source channels yet.", show_alert=True)
            return

        userbot = next((ub for ub in conv['userbots'] if ub['id'] == conv['listener_bot_id']), None)
        conv['client_type'] = 'userbot'
        conv['bot_id'] = userbot['id']
        await finalize_and_start_live_forward(client, query.message, user_id, conv)


@Client.on_message(filters.private & (filters.text | filters.forwarded), group=-2)
async def live_forward_message_handler(client, message):
    user_id = message.from_user.id
    conv = temp.LIVE_FORWARD_CONV.get(user_id)
    if not conv or conv.get('step') != 'waiting_from':
        return
    if message.text and message.text.startswith('/'):
        return
    
    status_message = conv.get('status_message')
    if not status_message:
        status_message = await message.reply_text("`Checking channel...`")
        conv['status_message'] = status_message
    else:
        await status_message.edit_text("`Checking channel...`")

    try:
        listener_bot_id = conv.get('listener_bot_id')
        userbot_session = next((ub['session'] for ub in conv['userbots'] if ub['id'] == listener_bot_id), None)

        if not userbot_session:
            await status_message.edit_text("Error: Could not find the selected listener userbot session.")
            return

        checker_client = await get_client(userbot_session, is_bot=False)
        async with checker_client:
            chat_id_str = message.forward_from_chat.id if message.forward_from_chat else message.text
            try:
                chat_info = await checker_client.get_chat(chat_id_str)
            except (UserNotParticipant, ChannelPrivate, ChannelInvalid, UsernameInvalid, PeerIdInvalid):
                await status_message.edit_text(
                    "**Error:** Your userbot is not a member of this channel. Please join the channel and try again.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Done Adding Sources", callback_data="live:done_adding_sources")]])
                )
                return

        from_chat_id = chat_info.id
        is_premium = conv.get("is_premium", False)

        if is_premium:
            source_limit = conv.get('source_limit', 1)
            if len(conv['from_chat_info']) >= source_limit:
                await status_message.edit_text(
                    f"You have reached your limit of **{source_limit}** source channels for your plan.\n\n"
                    "Click 'Done' to finalize.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Done Adding Sources", callback_data="live:done_adding_sources")]])
                )
                return

            if from_chat_id not in conv['from_chat_info']:
                conv['from_chat_info'][from_chat_id] = chat_info.title
                
                # Build the text with the list of added channel names
                added_sources_text = "\n".join(f"- `{title}`" for title in conv['from_chat_info'].values())
                
                await status_message.edit_text(
                    f"**Added Sources:**\n{added_sources_text}\n\n"
                    "Forward another message to add another source, or click 'Done'.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Done Adding Sources", callback_data="live:done_adding_sources")]])
                )
            else:
                await status_message.edit_text(
                    f"Source **{chat_info.title}** has already been added.\n\n"
                    "Forward another message to add another source, or click 'Done'.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Done Adding Sources", callback_data="live:done_adding_sources")]])
                )
        else:
            conv['from_chat_id'] = from_chat_id
            userbot = next((ub for ub in conv['userbots'] if ub['id'] == listener_bot_id), None)
            conv['client_type'] = 'userbot'
            conv['bot_id'] = userbot['id']
            await finalize_and_start_live_forward(client, status_message, user_id, conv)
            
    except Exception as e:
        await status_message.edit_text(f"An error occurred: `{e}`\nPlease ensure the link is correct or that your selected userbot has joined the channel.")
        temp.LIVE_FORWARD_CONV.pop(user_id, None)

@Client.on_message(filters.private & filters.command("stoplive"))
async def stop_live_forward(client, message):
    user_id = message.from_user.id
    configs_to_stop = [conf for conf in Config.LIVE_FORWARD_CONFIG.values() if conf['user_id'] == user_id]
    if not configs_to_stop:
        await message.reply_text("You don't have any active live forwards.")
        return
    
    listeners_to_stop = set()
    for config in configs_to_stop:
        from_chat_id = config['from_chat_id']
        listener_bot_id = config.get('listener_bot_id')
        if from_chat_id in Config.LIVE_FORWARD_CONFIG:
            del Config.LIVE_FORWARD_CONFIG[from_chat_id]
        await db.remove_live_forward(user_id, from_chat_id)
        if listener_bot_id:
            listeners_to_stop.add(listener_bot_id)

    for listener_bot_id in listeners_to_stop:
        # Check if this listener is still in use by another live forward for the same user
        is_listener_in_use = any(
            conf['user_id'] == user_id and conf.get('listener_bot_id') == listener_bot_id
            for conf in Config.LIVE_FORWARD_CONFIG.values()
        )
        if not is_listener_in_use:
            await client.stop_user_client(user_id, listener_bot_id)
    
    await message.reply_text("✅ All active live forward sessions have been stopped.")