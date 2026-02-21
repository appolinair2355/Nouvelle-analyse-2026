import os

# =====================================================
# CONFIGURATION PRÉ-DÉFINIE
# =====================================================

BOT_TOKEN = "8359623168:AAHno00lno02QOw5OvGukP0TIgn4sDFB158"
ADMIN_ID = 1190237801
API_ID = 29177661
API_HASH = "a8639172fa8d35dbfd8ea46286d349ab"

# Canal cible
CHANNEL_ID = -1003329818758
CHANNEL_USERNAME = "VIP DE KOUAMÉ & JOKER"

# VOTRE NUMÉRO PRÉ-CONFIGURÉ
USER_PHONE = "+22995501564"

# Render
PORT = int(os.getenv('PORT', 10000))

# Chemins
DATA_DIR = '/data' if os.path.exists('/data') else '/tmp'
PREDICTIONS_FILE = f"{DATA_DIR}/predictions.json"
LAST_SYNC_FILE = f"{DATA_DIR}/last_sync.json"
SESSION_PATH = f"{DATA_DIR}/telethon_session"
AUTH_STATE_FILE = f"{DATA_DIR}/auth_state.json"

def ensure_data_dir():
    import os
    os.makedirs(DATA_DIR, exist_ok=True)
