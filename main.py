import asyncio
import logging
from pyrogram import Client as VJ, idle, filters
from pyrogram.handlers import MessageHandler
from config import Config, temp
from database import db
from plugins.regix import restart_forwards
# Correctly import the handler function (not as a plugin)
from plugins.liveforward.handler import live_forward_handler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s ",
    force=True
)
pyro_log = logging.getLogger("pyrogram")
pyro_log.setLevel(logging.WARNING)

temp.LIVE_FORWARD_CLIENTS = {}

async def start_live_forwarder_for_user(user_id):
    if user_id in temp.LIVE_FORWARD_CLIENTS:
        logging.info(f"Live forwarder for user {user_id} is already running.")
        return
    userbots = await db.get_userbots(user_id)
    if not userbots:
        logging.error(f"Attempted to start live forwarder for {user_id} but no userbot found.")
        return
    userbot_session = userbots[0]['session']
    try:
        user_client = VJ(
            name=f"userbot_{user_id}",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            session_string=userbot_session
        )
        await user_client.start()
        
        # This is the key fix: Manually add the handler to the running userbot client.
        # It tells the userbot to execute `live_forward_handler` for every new channel message it sees.
        user_client.add_handler(MessageHandler(live_forward_handler, filters.channel & ~filters.me))
        
        temp.LIVE_FORWARD_CLIENTS[user_id] = user_client
        logging.info(f"Successfully started live forwarder listener for user {user_id}.")
    except Exception as e:
        logging.error(f"Failed to start live forwarder for user {user_id}: {e}", exc_info=True)

async def stop_live_forwarder_for_user(user_id):
    if user_id in temp.LIVE_FORWARD_CLIENTS:
        try:
            await temp.LIVE_FORWARD_CLIENTS[user_id].stop()
            logging.info(f"Successfully stopped live forwarder for user {user_id}.")
        except Exception as e:
            logging.error(f"Error stopping live forwarder for user {user_id}: {e}")
        finally:
            del temp.LIVE_FORWARD_CLIENTS[user_id]

async def load_all_live_forwards_on_startup():
    all_forwards = await db.get_all_live_forwards()
    unique_user_ids = set()
    async for forward in all_forwards:
        Config.LIVE_FORWARD_CONFIG[forward['from_chat_id']] = {
            "user_id": forward['user_id'],
            "to_chat_id": forward['to_chat_id'],
            "bot_id": forward['bot_id'],
            "client_type": forward['client_type']
        }
        unique_user_ids.add(forward['user_id'])
    logging.info(f"Found {len(unique_user_ids)} users with active live forwards. Starting listeners...")
    for user_id in unique_user_ids:
        await start_live_forwarder_for_user(user_id)

if __name__ == "__main__":
    VJBot = VJ(
        "VJ-Forward-Bot",
        bot_token=Config.BOT_TOKEN,
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        sleep_threshold=120,
        # Load all plugins from the 'plugins' directory, which now includes 'liveforward'
        plugins=dict(root="plugins")
    )

    VJBot.start_live_forwarder = start_live_forwarder_for_user
    VJBot.stop_live_forwarder = stop_live_forwarder_for_user
      
    async def main():
        await VJBot.start()
        logging.info("Main bot started.")
        await load_all_live_forwards_on_startup()
        await restart_forwards(VJBot)
        logging.info("Bot is now online.")
        await idle()
        logging.info("Stopping all live forwarder clients...")
        for user_id in list(temp.LIVE_FORWARD_CLIENTS.keys()):
            await stop_live_forwarder_for_user(user_id)

    asyncio.get_event_loop().run_until_complete(main())