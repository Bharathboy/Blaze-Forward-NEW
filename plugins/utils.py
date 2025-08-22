import time as tm
from database import Db, db
from .test import parse_buttons

STATUS = {}

def progress_bar_tuple(pct, width=16, empty='□', half='◧', full='■', usehalf=False):
    try:
        if isinstance(pct, str):
            pct = float(pct.strip('%').strip())
        p = float(pct)
    except Exception:
        p = 0.0

    p = max(0.0, min(100.0, p))

    if usehalf:
        total_half = width * 2
        filled_half = int(round((p / 100.0) * total_half))
        full_blocks, half_blocks = divmod(filled_half, 2)
    else:
        full_blocks = int(round((p / 100.0) * width))
        half_blocks = 0

    empty_blocks = width - full_blocks - half_blocks
    bar = (full * full_blocks) + (half * half_blocks) + (empty * empty_blocks)
    return bar, p

class STS:
    def __init__(self, id):
        self.id = id
        self.data = STATUS

    def verify(self):
        return self.data.get(self.id)

    def store(self, From, to,  skip, limit, client_type, bot_id):
        self.data[self.id] = {"FROM": From, 'TO': to, 'total_files': 0, 'skip': skip, 'limit': limit,
                  'fetched': skip, 'filtered': 0, 'deleted': 0, 'duplicate': 0, 'total': limit, 'start': 0, 'client_type': client_type, 'bot_id': bot_id}

    def get(self, value=None, full=False):
        values = self.data.get(self.id)
        if not full:
           return values.get(value)
        for k, v in values.items():
            setattr(self, k, v)
        return self

    def add(self, key=None, value=1, time=False, start_time=None):
        if time:
          return self.data[self.id].update({'start': tm.time() if start_time is None else start_time})
        self.data[self.id].update({key: self.get(key) + value}) 

    def divide(self, no, by):
       by = 1 if int(by) == 0 else by 
       return int(no) / by 

    async def get_data(self, user_id):
        client_type = self.get('client_type')
        bot_id = self.get('bot_id')

        if client_type == 'bot':
            bot = await db.get_bot(user_id, bot_id)
        elif client_type == 'userbot':
            bot = await db.get_userbot(user_id, bot_id)
        else:
            # Fallback to check both types if client_type is not specified
            bot = await db.get_bot(user_id, bot_id)
            if bot is None:
                bot = await db.get_userbot(user_id, bot_id)

        configs = await db.get_configs(user_id)
        filters = await db.get_filters(user_id)

        # Prepare the button from the configuration
        button = parse_buttons(configs.get('button') or '')

        # Consolidate all settings into a single dictionary for clarity
        forwarding_data = {
            'filters': filters,
            'skip_duplicate': configs.get('duplicate', True),
            'db_uri': configs.get('db_uri'),
            'min_size': configs.get('min_size', 0),
            'max_size': configs.get('max_size', 0),
            'keywords': configs.get('keywords'),
            'extensions': configs.get('extension'),
            # Premium features
            'persistent_deduplication': configs.get('persistent_deduplication', False),
            'regex_filter': configs.get('regex_filter'),
            'regex_filter_mode': configs.get('regex_filter_mode', 'exclude'),
            'message_replacements': configs.get('message_replacements')
        }

        return bot, configs.get('caption'), configs.get('forward_tag', False), forwarding_data, configs.get('protect'), button