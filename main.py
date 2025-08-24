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

# Dictionaries to hold the running clients
temp.LISTENER_CLIENTS = {}
temp.FORWARDER_CLIENTS = {}

async def start_listener_client(user_id):
    """Starts and stores the userbot client responsible for listening to new messages."""
    if user_id in temp.LISTENER_CLIENTS:
        return
    userbots = await db.get_userbots(user_id)
    if not userbots:
        return
    session_string = userbots[0]['session']
    try:
        client = VJ(name=f"listener_{user_id}", api_id=Config.API_ID, api_hash=Config.API_HASH, session_string=session_string)
        await client.start()
        client.add_handler(MessageHandler(live_forward_handler, (filters.channel | filters.group) & ~filters.me))
        temp.LISTENER_CLIENTS[user_id] = client
        logging.info(f"Started listener for user_id: {user_id}")
    except Exception as e:
        logging.error(f"Failed to start listener for {user_id}: {e}", exc_info=True)

async def start_forwarder_client(user_id, bot_id, client_type):
    """Starts and stores the bot/userbot client responsible for sending messages."""
    client_key = f"{user_id}_{bot_id}"
    if client_key in temp.FORWARDER_CLIENTS:
        return
    try:
        if client_type == 'bot':
            account = await db.get_bot(user_id, bot_id)
            client = await get_client(account['token'], is_bot=True)
        else:
            account = await db.get_userbot(user_id, bot_id)
            client = await get_client(account['session'], is_bot=False)
        
        await client.start()
        temp.FORWARDER_CLIENTS[client_key] = client
        logging.info(f"Started forwarder client for user_id: {user_id}, bot_id: {bot_id}")
    except Exception as e:
        logging.error(f"Failed to start forwarder for {client_key}: {e}", exc_info=True)

async def stop_listener_client(user_id):
    """Stops the listening client for a user."""
    if user_id in temp.LISTENER_CLIENTS:
        try:
            await temp.LISTENER_CLIENTS[user_id].stop()
        finally:
            del temp.LISTENER_CLIENTS[user_id]
            logging.info(f"Stopped listener for user_id: {user_id}")

async def stop_forwarder_client(user_id, bot_id):
    """Stops the forwarding client for a user."""
    client_key = f"{user_id}_{bot_id}"
    if client_key in temp.FORWARDER_CLIENTS:
        try:
            await temp.FORWARDER_CLIENTS[client_key].stop()
        finally:
            del temp.FORWARDER_CLIENTS[client_key]
            logging.info(f"Stopped forwarder client for key: {client_key}")

async def load_all_live_forwards_on_startup():
    all_forwards = await db.get_all_live_forwards()
    unique_users = {}
    async for forward in all_forwards:
        Config.LIVE_FORWARD_CONFIG[forward['from_chat_id']] = forward
        user_id = forward['user_id']
        if user_id not in unique_users:
            unique_users[user_id] = []
        unique_users[user_id].append((forward['bot_id'], forward['client_type']))

    for user_id, clients in unique_users.items():
        await start_listener_client(user_id)
        for bot_id, client_type in clients:
            await start_forwarder_client(user_id, bot_id, client_type)

if __name__ == "__main__":
    VJBot = VJ(
        "VJ-Forward-Bot",
        bot_token=Config.BOT_TOKEN,
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        sleep_threshold=120,
        plugins=dict(root="plugins")
    )

    # Attach client management functions to the bot instance
    VJBot.start_listener = start_listener_client
    VJBot.start_forwarder = start_forwarder_client
    VJBot.stop_listener = stop_listener_client
    VJBot.stop_forwarder = stop_forwarder_client
      
    async def main():
        await VJBot.start()
        logging.info("Main bot started.")
        await load_all_live_forwards_on_startup()
        await restart_forwards(VJBot)
        logging.info("Bot is now online.")
        await idle()
        logging.info("Shutting down... Stopping all clients.")
        for user_id in list(temp.LISTENER_CLIENTS.keys()):
            await stop_listener_client(user_id)
        for client_key in list(temp.FORWARDER_CLIENTS.keys()):
            user_id, bot_id = map(int, client_key.split('_'))
            await stop_forwarder_client(user_id, bot_id)

    asyncio.get_event_loop().run_until_complete(main())