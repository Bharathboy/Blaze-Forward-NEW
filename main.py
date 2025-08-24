import asyncio
import logging
from pyrogram import Client as VJ, idle, filters
from pyrogram.handlers import MessageHandler
from config import Config, temp
from database import db
from plugins.regix import restart_forwards
from plugins.liveforward.handler import live_forward_handler
from plugins.test import get_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s ",
    force=True
)
pyro_log = logging.getLogger("pyrogram")
pyro_log.setLevel(logging.WARNING)

temp.USER_CLIENTS = {}

async def start_user_client(user_id, listener_bot_id):
    client_key = f"{user_id}_{listener_bot_id}"
    if client_key in temp.USER_CLIENTS:
        logging.info(f"User client for {client_key} is already running.")
        return
    
    userbot = await db.get_userbot(user_id, listener_bot_id)
    if not userbot:
        logging.error(f"Cannot start client for {client_key}: No userbot found in settings.")
        return
        
    session_string = userbot['session']
    try:
        client = VJ(
            name=f"user_session_{client_key}",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            session_string=session_string
        )
        await client.start()
        client.add_handler(MessageHandler(live_forward_handler, (filters.channel | filters.group) & ~filters.me))
        temp.USER_CLIENTS[client_key] = client
        logging.info(f"Successfully started and registered listener for client key: {client_key}")
    except Exception as e:
        logging.error(f"Failed to start user client for {client_key}: {e}", exc_info=True)

async def stop_user_client(user_id, listener_bot_id):
    client_key = f"{user_id}_{listener_bot_id}"
    if client_key in temp.USER_CLIENTS:
        try:
            await temp.USER_CLIENTS[client_key].stop()
            logging.info(f"Stopped user client for client key: {client_key}")
        except Exception as e:
            logging.error(f"Error stopping user client for {client_key}: {e}")
        finally:
            del temp.USER_CLIENTS[client_key]

async def load_all_live_forwards_on_startup():
    all_forwards = await db.get_all_live_forwards()
    unique_listeners = {}
    async for forward in all_forwards:
        Config.LIVE_FORWARD_CONFIG[forward['from_chat_id']] = forward
        user_id = forward['user_id']
        listener_id = forward.get('listener_bot_id')
        if user_id and listener_id:
            unique_listeners[user_id] = listener_id
    
    logging.info(f"Found {len(unique_listeners)} unique users with live forwards. Starting clients...")
    for user_id, listener_id in unique_listeners.items():
        await start_user_client(user_id, listener_id)

if __name__ == "__main__":
    VJBot = VJ(
        "VJ-Forward-Bot",
        bot_token=Config.BOT_TOKEN,
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        sleep_threshold=120,
        plugins=dict(root="plugins")
    )

    VJBot.start_user_client = start_user_client
    VJBot.stop_user_client = stop_user_client
      
    async def main():
        await VJBot.start()
        logging.info("Main bot started.")
        await load_all_live_forwards_on_startup()
        await restart_forwards(VJBot)
        logging.info("Bot is now online and ready.")
        await idle()
        logging.info("Shutting down... Stopping all user clients.")
        for client_key in list(temp.USER_CLIENTS.keys()):
            user_id, listener_id = map(int, client_key.split('_'))
            await stop_user_client(user_id, listener_id)

    asyncio.get_event_loop().run_until_complete(main())