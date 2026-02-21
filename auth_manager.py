import json
import os
from telethon import TelegramClient
from config import API_ID, API_HASH, SESSION_PATH, AUTH_STATE_FILE, USER_PHONE

class AuthManager:
    def __init__(self):
        self.client = None
        self._load_state()
    
    def _load_state(self):
        if os.path.exists(AUTH_STATE_FILE):
            with open(AUTH_STATE_FILE, 'r') as f:
                self.state = json.load(f)
        else:
            self.state = {'step': 'idle', 'code_sent': False}
    
    def _save_state(self):
        with open(AUTH_STATE_FILE, 'w') as f:
            json.dump(self.state, f)
    
    def is_connected(self):
        return os.path.exists(SESSION_PATH + ".session")
    
    async def send_code(self):
        """Envoie le code à votre numéro pré-configuré"""
        self.client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
        await self.client.connect()
        
        try:
            result = await self.client.send_code_request(USER_PHONE)
            
            self.state = {
                'step': 'waiting_code',
                'phone_code_hash': result.phone_code_hash
            }
            self._save_state()
            
            return True, f"📲 Code envoyé à {USER_PHONE}\nTapez: /code aaXXXXXX"
            
        except Exception as e:
            return False, f"Erreur: {str(e)}"
    
    async def verify_code(self, code: str):
        """Vérifie le code"""
        if self.state['step'] != 'waiting_code':
            return False, "Pas de code en attente. Tapez /connect d'abord"
        
        # Enlever le préfixe "aa"
        real_code = code[2:] if code.startswith('aa') else code
        
        try:
            await self.client.sign_in(
                phone=USER_PHONE,
                code=real_code,
                phone_code_hash=self.state['phone_code_hash']
            )
            
            self.state = {'step': 'connected'}
            self._save_state()
            
            await self.client.disconnect()
            return True, "✅ Connecté ! Utilisez /sync ou /fullsync"
            
        except Exception as e:
            return False, f"❌ Code invalide: {str(e)}"
    
    async def reset(self):
        """Déconnexion complète"""
        if self.client:
            await self.client.disconnect()
        self.state = {'step': 'idle'}
        self._save_state()
        if os.path.exists(SESSION_PATH + ".session"):
            os.remove(SESSION_PATH + ".session")

auth_manager = AuthManager()
