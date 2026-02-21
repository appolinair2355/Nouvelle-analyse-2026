import re
import os
import asyncio
from telethon import TelegramClient
from telethon.tl.types import Channel
from database import save_prediction, get_last_sync, update_last_sync

API_ID = int(os.getenv('API_ID', 0))
API_HASH = os.getenv('API_HASH', '')
SESSION_PATH = '/data/telethon_session'

# Pattern pour extraire les prédictions
PREDICTION_PATTERN = re.compile(
    r'PRÉDICTION\s*#(\d+).*?'
    r'Couleur:\s*([^\n]+).*?'
    r'Statut:\s*([^\n]+)',
    re.IGNORECASE | re.DOTALL
)

class PredictionScraper:
    def __init__(self):
        self.client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    
    async def sync_history(self, channel_username, progress_callback=None):
        """Synchronise tout l'historique ou uniquement les nouveaux messages"""
        await self.client.connect()
        
        if not await self.client.is_user_authorized():
            await self.client.start(phone=os.getenv('USER_PHONE'))
        
        try:
            entity = await self.client.get_entity(channel_username)
            if not isinstance(entity, Channel):
                raise ValueError("Ce n'est pas un canal")
            
            last_sync = get_last_sync()
            last_id = last_sync['last_message_id']
            
            total_new = 0
            max_id = last_id
            
            # Récupère depuis le dernier message connu
            async for message in self.client.iter_messages(
                entity, 
                min_id=last_id,
                limit=10000
            ):
                if not message.text:
                    continue
                
                match = PREDICTION_PATTERN.search(message.text)
                if match:
                    save_prediction(
                        message_id=message.id,
                        numero=match.group(1),
                        couleur=match.group(2).strip(),
                        statut=match.group(3).strip(),
                        raw_text=message.text[:500]
                    )
                    total_new += 1
                
                if message.id > max_id:
                    max_id = message.id
                
                if total_new % 100 == 0 and progress_callback:
                    await progress_callback(total_new)
            
            if max_id > last_id:
                update_last_sync(max_id)
            
            return {
                'new_predictions': total_new,
                'last_message_id': max_id
            }
            
        finally:
            await self.client.disconnect()
    
    async def full_sync(self, channel_username, progress_callback=None):
        """Première synchronisation complète"""
        await self.client.connect()
        
        if not await self.client.is_user_authorized():
            await self.client.start(phone=os.getenv('USER_PHONE'))
        
        try:
            entity = await self.client.get_entity(channel_username)
            total = 0
            
            async for message in self.client.iter_messages(entity, limit=50000):
                if not message.text:
                    continue
                
                match = PREDICTION_PATTERN.search(message.text)
                if match:
                    save_prediction(
                        message_id=message.id,
                        numero=match.group(1),
                        couleur=match.group(2).strip(),
                        statut=match.group(3).strip(),
                        raw_text=message.text[:500]
                    )
                    total += 1
                
                if total % 500 == 0 and progress_callback:
                    await progress_callback(total, message.id)
            
            update_last_sync(message.id if message else 0)
            return {'total_predictions': total}
            
        finally:
            await self.client.disconnect()

scraper = PredictionScraper()
