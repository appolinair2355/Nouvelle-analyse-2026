import os
import asyncio
import logging
from aiohttp import web
from bot_handler import setup_bot
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def health(request):
    from storage import get_stats
    s = get_stats()
    return web.json_response({
        'status': 'ok',
        'predictions': s['total'],
        'time': str(datetime.now())
    })

async def web_server():
    app = web.Application()
    app.router.add_get('/', health)
    app.router.add_get('/health', health)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv('PORT', 10000)))
    await site.start()
    logger.info("Web server started")

async def main():
    await web_server()
    
    application = setup_bot()
    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=['message'])
    
    logger.info("Bot started!")
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
    
