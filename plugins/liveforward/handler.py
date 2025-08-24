import asyncio
import logging
import re
from pyrogram import Client, filters
from pyrogram.errors import FloodWait

from config import Config, temp
from database import db

from ..db import connect_user_db, connect_persistent_db
from ..regix import (
    custom_caption,
    extension_filter,
    keyword_filter,
    media,
    size_filter,
)
from ..test import get_client, parse_buttons

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

PROCESSING = set()

async def live_forward_handler(client, message):
    if message.chat.id not in Config.LIVE_FORWARD_CONFIG:
        return

    message_identifier = (message.chat.id, message.id)
    if message_identifier in PROCESSING:
        return
    PROCESSING.add(message_identifier)

    try:
        config = Config.LIVE_FORWARD_CONFIG[message.chat.id]
        user_id = config["user_id"]
        bot_id = config["bot_id"]
        to_chat_id = config["to_chat_id"]
        client_type = config["client_type"]
        
        
        listener_client = client
        
        
        forwarder_client = None
        if client_type == 'userbot':
            
            client_key = f"{user_id}_{bot_id}"
            forwarder_client = temp.USER_CLIENTS.get(client_key)
        else: 
            
            bot_details = await db.get_bot(user_id, bot_id)
            if bot_details:
                forwarder_client = await get_client(bot_details['token'], is_bot=True)

        if not forwarder_client:
            logging.error(f"Could not initialize or find forwarder client for user {user_id}, bot_id {bot_id}.")
            return

        async def perform_forward():
            configs = await db.get_configs(user_id)
            
            if (message.text and not configs.get('filters', {}).get('text', True)) or \
               (message.document and not configs.get('filters', {}).get('document', True)) or \
               (message.video and not configs.get('filters', {}).get('video', True)) or \
               (message.photo and not configs.get('filters', {}).get('photo', True)) or \
               (message.audio and not configs.get('filters', {}).get('audio', True)) or \
               (message.voice and not configs.get('filters', {}).get('voice', True)) or \
               (message.animation and not configs.get('filters', {}).get('animation', True)) or \
               (message.sticker and not configs.get('filters', {}).get('sticker', True)) or \
               (message.poll and not configs.get('filters', {}).get('poll', True)):
                return

            
            media_obj = fname = fsize = fuid = None
            if message.media:
                media_obj = getattr(message, message.media.value, None)
                if media_obj:
                    fname = getattr(media_obj, "file_name", None)
                    fsize = getattr(media_obj, "file_size", 0)
                    fuid = getattr(media_obj, "file_unique_id", None)

            
            user_rank = await db.get_premium_user_rank(user_id)
            message_replacements = None
            persistent_deduplication = False

            if user_rank != "default":
                regex_filter = configs.get('regex_filter')
                regex_filter_mode = configs.get('regex_filter_mode', 'exclude')
                message_replacements = configs.get('message_replacements')
                persistent_deduplication = configs.get('persistent_deduplication', False)
                
                if regex_filter and fname and (
                    (regex_filter_mode == 'exclude' and re.search(regex_filter, fname)) or
                    (regex_filter_mode == 'include' and not re.search(regex_filter, fname))
                ):
                    return

            keywords = "|".join(configs.get('keywords') or []) or None
            extensions = "|".join(configs.get('extensions') or []) or None
            
            if media_obj and fname and await extension_filter(extensions, fname):
                return
            if media_obj and fname and await keyword_filter(keywords, fname):
                return
            if media_obj and fsize and await size_filter(configs.get('max_size', 0), configs.get('min_size', 0), fsize):
                return

            
            if (configs.get('duplicate', True) or persistent_deduplication) and fuid:
                db_uri = configs.get('db_uri')
                if db_uri:
                    is_persistent = persistent_deduplication
                    db_connection = await (connect_persistent_db(user_id, db_uri) if is_persistent else connect_user_db(user_id, db_uri, config["to_chat_id"]))
                    
                    if db_connection[0]:
                        user_db = db_connection[1]
                        if await user_db.is_file_exit(fuid):
                            await user_db.close()
                            return
                        await user_db.add_file(fuid)
                        await user_db.close()

            
            if client_type == 'bot':
                
                
                if message.media:
                    file_id = getattr(message, message.media.value).file_id
                    new_caption = custom_caption(message, configs.get('caption'))
                    
                    
                    await forwarder_client.send_cached_media(
                        chat_id=to_chat_id,
                        file_id=file_id,
                        caption=new_caption if new_caption is not None else (message.caption or ""),
                        reply_markup=parse_buttons(configs.get('button') or ''),
                        protect_content=configs.get('protect', False)
                    )
                elif message.text:
                    await forwarder_client.send_message(
                        chat_id=to_chat_id,
                        text=message.text.html,
                        disable_web_page_preview=True,
                        reply_markup=parse_buttons(configs.get('button') or ''),
                        protect_content=configs.get('protect', False)
                    )
            else:
                
                if configs.get('forward_tag'):
                    await message.forward(to_chat_id)
                else:
                    await message.copy(
                        chat_id=to_chat_id,
                        caption=custom_caption(message, configs.get('caption')),
                        reply_markup=parse_buttons(configs.get('button') or ''),
                        protect_content=configs.get('protect', False)
                    )

        
        if client_type == 'bot':
             async with forwarder_client:
                 await perform_forward()
        else:
             await perform_forward()

    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        logging.error(f"Error in live forward handler for message {message.id} in chat {message.chat.id}: {e}", exc_info=True)
    finally:
        if message_identifier in PROCESSING:
            PROCESSING.remove(message_identifier)