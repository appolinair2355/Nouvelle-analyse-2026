import re
from telethon import TelegramClient
from telethon.tl.types import Channel
from config import API_ID, API_HASH, SESSION_PATH, CHANNEL_USERNAME
from storage import add_prediction, get_last_sync, update_last_sync

PATTERN = re.compile(
    r'PRÉDICTION\s*#(\d+).*?'
    r'Couleur:\s*([^\n]+).*?'
    r'Statut:\s*([^\n]+)',
    re.IGNORECASE | re.DOTALL
)

class Scraper:
    def __init__(self):
        self.client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    
    async def sync(self, full=False, progress_callback=None):
        """Synchronise le canal VIP DE KOUAMÉ & JOKER"""
        await self.client.connect()
        
        if not await self.client.is_user_authorized():
            # Utilise le numéro fourni pour l'authentification
            await self.client.start(phone=lambda: input("Code reçu par SMS: "))
        
        try:
            # Recherche du canal par nom ou ID
            try:
                entity = await self.client.get_entity(CHANNEL_USERNAME)
            except:
                # Essayer avec le numéro de téléphone
                entity = await self.client.get_entity(CHANNEL_USERNAME.replace(" ", ""))
            
            if not isinstance(entity, Channel):
                raise ValueError(f"{CHANNEL_USERNAME} n'est pas un canal")
            
            total = 0
            last_id = 0
            min_id = 0 if full else get_last_sync().get('last_message_id', 0)
            
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
                
