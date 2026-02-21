import json
import os
from datetime import datetime

DATA_DIR = '/data' if os.path.exists('/data') else '/tmp'
os.makedirs(DATA_DIR, exist_ok=True)

PREDICTIONS_FILE = os.path.join(DATA_DIR, 'predictions.json')
LAST_SYNC_FILE = os.path.join(DATA_DIR, 'last_sync.json')

def load_json(filepath, default=None):
    """Charge un fichier JSON ou retourne la valeur par défaut"""
    if not os.path.exists(filepath):
        return default if default is not None else {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return default if default is not None else {}

def save_json(filepath, data):
    """Sauvegarde dans un fichier JSON"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

# =====================================================
# GESTION DES PRÉDICTIONS
# =====================================================

def add_prediction(message_id, numero, couleur, statut, raw_text):
    """Ajoute une prédiction"""
    predictions = load_json(PREDICTIONS_FILE, [])
    
    # Éviter les doublons
    if any(p['message_id'] == message_id for p in predictions):
        return False
    
    predictions.append({
        'message_id': message_id,
        'numero': numero,
        'couleur': couleur,
        'statut': statut,
        'raw_text': raw_text,
        'date': datetime.now().isoformat()
    })
    
    save_json(PREDICTIONS_FILE, predictions)
    return True

def get_predictions(filters=None):
    """Récupère les prédictions avec filtres optionnels"""
    predictions = load_json(PREDICTIONS_FILE, [])
    
    if not filters:
        return predictions
    
    result = []
    for p in predictions:
        match = True
        
        if filters.get('couleur'):
            if filters['couleur'].lower() not in p['couleur'].lower():
                match = False
        
        if filters.get('statut'):
            if filters['statut'].lower() not in p['statut'].lower():
                match = False
        
        if filters.get('numero'):
            if p['numero'] != filters['numero']:
                match = False
        
        if match:
            result.append(p)
    
    return result

def get_stats():
    """Statistiques rapides"""
    predictions = load_json(PREDICTIONS_FILE, [])
    return {
        'total': len(predictions),
        'last_update': datetime.now().isoformat()
    }

# =====================================================
# GESTION DE LA SYNCHRONISATION
# =====================================================

def get_last_sync():
    """Récupère le dernier message synchronisé"""
    return load_json(LAST_SYNC_FILE, {'last_message_id': 0})

def update_last_sync(message_id):
    """Met à jour le dernier message synchronisé"""
    save_json(LAST_SYNC_FILE, {
        'last_message_id': message_id,
        'sync_date': datetime.now().isoformat()
    })

def clear_all():
    """Vide toutes les données (pour tests)"""
    save_json(PREDICTIONS_FILE, [])
    save_json(LAST_SYNC_FILE, {'last_message_id': 0})
                   
