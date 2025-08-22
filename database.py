import motor.motor_asyncio
from config import Config
from datetime import datetime

class Db:

    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.bot = self.db.bots
        self.userbot = self.db.userbot
        self.col = self.db.users
        self.nfy = self.db.notify
        self.chl = self.db.channels
        self.premium = self.db.premium_users

    def new_user(self, id, name):
        return dict(
            id = id,
            name = name,
            ban_status=dict(
                is_banned=False,
                ban_reason="",
            ),
        )

    async def add_user(self, id, name):
        user = self.new_user(id, name)
        await self.col.insert_one(user)

    async def is_user_exist(self, id):
        user = await self.col.find_one({'id':int(id)})
        return bool(user)

    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count

    async def total_users_bots_count(self):
        bcount = await self.bot.count_documents({})
        count = await self.col.count_documents({})
        return count, bcount

    async def remove_ban(self, id):
        ban_status = dict(
            is_banned=False,
            ban_reason=''
        )
        await self.col.update_one({'id': id}, {'$set': {'ban_status': ban_status}})

    async def ban_user(self, user_id, ban_reason="No Reason"):
        ban_status = dict(
            is_banned=True,
            ban_reason=ban_reason
        )
        await self.col.update_one({'id': user_id}, {'$set': {'ban_status': ban_status}})

    async def get_ban_status(self, id):
        default = dict(
            is_banned=False,
            ban_reason=''
        )
        user = await self.col.find_one({'id':int(id)})
        if not user:
            return default
        return user.get('ban_status', default)

    async def get_all_users(self):
        return self.col.find({})

    async def delete_user(self, user_id):
        await self.col.delete_many({'id': int(user_id)})

    async def get_banned(self):
        users = self.col.find({'ban_status.is_banned': True})
        b_users = [user['id'] async for user in users]
        return b_users

    async def update_configs(self, id, configs):
        await self.col.update_one({'id': int(id)}, {'$set': {'configs': configs}})

    async def get_configs(self, id):
        default = {
            'caption': None,
            'duplicate': True,
            'forward_tag': False,
            'min_size': 0,
            'max_size': 0,
            'extension': None,
            'keywords': None,
            'protect': None,
            'button': None,
            'db_uri': None,
            'filters': {
               'poll': True,
               'text': True,
               'audio': True,
               'voice': True,
               'video': True,
               'photo': True,
               'document': True,
               'animation': True,
               'sticker': True
            },
            'regex_filter': None,
            'persistent_deduplication': False,
            'message_replacements': None
        }
        user = await self.col.find_one({'id':int(id)})
        if user:
            user_configs = user.get('configs', {})
            # Ensure new keys exist
            for key, value in default.items():
                if key not in user_configs:
                    user_configs[key] = value
            return user_configs
        return default

    async def add_bot(self, datas):
        await self.bot.insert_one(datas)

    async def remove_bot(self, user_id, bot_id):
        await self.bot.delete_one({'user_id': int(user_id), 'id': int(bot_id)})

    async def get_bot(self, user_id: int, bot_id: int):
        bot = await self.bot.find_one({'user_id': user_id, 'id': bot_id})
        return bot if bot else None
    
    async def get_bots(self, user_id: int):
        bots = self.bot.find({'user_id': user_id})
        return [bot async for bot in bots]

    async def is_bot_exist(self, user_id, bot_id):
        bot = await self.bot.find_one({'user_id': user_id, 'id': bot_id})
        return bool(bot)

    async def add_userbot(self, datas):
        await self.userbot.insert_one(datas)

    async def remove_userbot(self, user_id, bot_id):
        await self.userbot.delete_one({'user_id': int(user_id), 'id': int(bot_id)})

    async def get_userbot(self, user_id: int, bot_id: int):
        bot = await self.userbot.find_one({'user_id': user_id, 'id': bot_id})
        return bot if bot else None
    
    async def get_userbots(self, user_id: int):
        bots = self.userbot.find({'user_id': user_id})
        return [bot async for bot in bots]

    async def is_userbot_exist(self, user_id, bot_id):
        bot = await self.userbot.find_one({'user_id': user_id, 'id': bot_id})
        return bool(bot)
    
    async def in_channel(self, user_id: int, chat_id: int) -> bool:
       channel = await self.chl.find_one({"user_id": int(user_id), "chat_id": int(chat_id)})
       return bool(channel)

    async def add_channel(self, user_id: int, chat_id: int, title, username):
       channel = await self.in_channel(user_id, chat_id)
       if channel:
         return False
       return await self.chl.insert_one({"user_id": user_id, "chat_id": chat_id, "title": title, "username": username})

    async def remove_channel(self, user_id: int, chat_id: int):
       channel = await self.in_channel(user_id, chat_id )
       if not channel:
         return False
       return await self.chl.delete_many({"user_id": int(user_id), "chat_id": int(chat_id)})

    async def get_channel_details(self, user_id: int, chat_id: int):
       return await self.chl.find_one({"user_id": int(user_id), "chat_id": int(chat_id)})

    async def get_user_channels(self, user_id: int):
       channels = self.chl.find({"user_id": int(user_id)})
       return [channel async for channel in channels]

    async def get_filters(self, user_id):
       filters = []
       filter_dict = (await self.get_configs(user_id))['filters']
       for k, v in filter_dict.items():
          if not v:
            filters.append(str(k))
       return filters

    async def add_frwd(self, user_id, bot_id):
       return await self.nfy.insert_one({'user_id': int(user_id), 'bot_id': int(bot_id)})

    async def rmve_frwd(self, user_id=0, bot_id=0, all=False):
        if all:
            data = {}
        elif bot_id:
            data = {'user_id': int(user_id), 'bot_id': int(bot_id)}
        else:
            data = {'user_id': int(user_id)}
        return await self.nfy.delete_many(data)

    async def get_all_frwd(self):
       return self.nfy.find({})
  
    async def forwad_count(self):
        c = await self.nfy.count_documents({})
        return c
        
    async def is_forwad_exit(self, user, bot_id=None):
        if bot_id:
            u = await self.nfy.find_one({'user_id': user, 'bot_id': bot_id})
        else:
            u = await self.nfy.find_one({'user_id': user})
        return bool(u)
        
    async def get_forward_details(self, user_id, bot_id=None):
        defult = {
            'chat_id': None,
            'forward_id': None,
            'toid': None,
            'last_id': None,
            'limit': None,
            'msg_id': None,
            'start_time': None,
            'fetched': 0,
            'offset': 0,
            'deleted': 0,
            'total': 0,
            'duplicate': 0,
            'skip': 0,
            'filtered' :0,
            'client_type': None
        }
        if bot_id:
            user = await self.nfy.find_one({'user_id': int(user_id), 'bot_id': int(bot_id)})
        else:
            user = await self.nfy.find_one({'user_id': int(user_id)})
        if user:
            return user.get('details', defult)
        return defult
   
    async def update_forward(self, user_id, bot_id, details):
        await self.nfy.update_one({'user_id': user_id, 'bot_id': bot_id}, {'$set': {'details': details}})
    
    async def add_premium_user(self, user_id, rank, expiry_time):
        await self.premium.update_one(
            {'user_id': user_id},
            {'$set': {'rank': rank, 'expiry_time': expiry_time}},
            upsert=True
        )

    async def remove_premium_user(self, user_id):
        await self.premium.delete_one({'user_id': user_id})

    async def get_premium_user(self, user_id):
        return await self.premium.find_one({'user_id': user_id})

    async def is_premium_user(self, user_id):
        user = await self.get_premium_user(user_id)
        if not user:
            return False
        # Check if expiry_time exists and if it's in the past
        if user.get('expiry_time') and user['expiry_time'] < datetime.now():
            return False
        return True

    async def get_premium_user_rank(self, user_id):
        if await self.is_premium_user(user_id):
            user = await self.get_premium_user(user_id)
            return user['rank']
        return "default"
        
    async def get_and_remove_expired_users(self):
        expired_users = []
        current_time = datetime.now()
        # Find users with an expiry_time that is not null and is in the past
        cursor = self.premium.find({"expiry_time": {"$ne": None, "$lt": current_time}})
        async for user in cursor:
            expired_users.append(user['user_id'])
        
        if expired_users:
            await self.premium.delete_many({"user_id": {"$in": expired_users}})
            
        return expired_users

db = Db(Config.DATABASE_URI, Config.DATABASE_NAME)