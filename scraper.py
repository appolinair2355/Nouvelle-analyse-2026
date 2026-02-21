import re
import os
from telethon import TelegramClient
from telethon.tl.types import Channel
from storage import add_prediction, get_last_sync, update_last_sync

API_ID = int(os.getenv('API_ID', 0))
API_HASH = os.getenv('API_HASH', '')
SESSION_PATH = '/data/telethon_session' if os.path.exists('/data') else '/tmp/telethon_session'

# Pattern pour extraire les prédictions
PATTERN = re.compile(
    r'PRÉDICTION\s*#(\d+).*?'
    r'Couleur:\s*([^\n]+).*?'
    r'Statut:\s*([^\n]+)',
    re.IGNORECASE | re.DOTALL
)

class Scraper:
    def __init__(self):
        self.client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    
    async def sync(self, channel_username, full=False, progress_callback=None):
        """Synchronise les messages"""
        await self.client.connect()
        
        if not await self.client.is_user_authorized():
            await self.client.start(phone=os.getenv('USER_PHONE'))
        
        try:
            entity = await self.client.get_entity(channel_username)
            
            total = 0
            last_id = 0
            
            # Déterminer depuis où commencer
            if not full:
                last_sync = get_last_sync()
                min_id = last_sync.get('last_message_id', 0)
            else:
                min_id = 0
            
            async for message in self.client.iter_messages(entity, limit=50000, min_id=min_id):
                if not message.text:
                    continue
                
                match = PATTERN.search(message.text)
                if match:
                    added = add_prediction(
                        message_id=message.id,
                        numero=match.group(1),
                        couleur=match.group(2).strip(),
                        statut=match.group(3).strip(),
                        raw_text=message.text[:500]
                    )
                    if added:
                        total += 1
                
                if message.id > last_id:
                    last_id = message.id
                
                if total % 100 == 0 and progress_callback:
                    await progress_callback(total)
            
            if last_id > 0:
                update_last_sync(last_id)
            
            return {'new': total, 'last_id': last_id}
            
        finally:
            await self.client.disconnect()

scraper = Scraper()
