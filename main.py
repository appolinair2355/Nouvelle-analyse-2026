import os
import asyncio
import logging
from aiohttp import web
from bot_handler import setup_bot

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def health_check(request):
    from database import get_stats
    stats = get_stats()
    return web.json_response({
        'status': 'ok',
        'predictions': stats['total'],
        'timestamp': str(datetime.now())
    })

async def web_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv('PORT', 10000)))
    await site.start()
    logger.info("Serveur web démarré")

async def main():
    from datetime import datetime
    
    # Démarrer le serveur web (pour Render)
    await web_server()
    
    # Démarrer le bot
    application = setup_bot()
    await application.initialize()
    await application.start()
    
    logger.info("Bot démarré, démarrage du polling...")
    await application.updater.start_polling(allowed_updates=['message'])
    
    # Garder actif
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
