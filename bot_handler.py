import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from storage import get_predictions, get_stats, clear_all
from scraper import scraper
from pdf_generator import generate_pdf

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHANNEL = os.getenv('CHANNEL_USERNAME', '')

class Handlers:
    def __init__(self):
        self.syncing = False
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🎯 **Bot Prédictions VIP**\n\n"
            "/sync - Synchroniser nouveaux messages\n"
            "/fullsync - Tout l'historique\n"
            "/report - Générer PDF\n"
            "/filter `couleur` `statut` - Filtrer\n"
            "/stats - Statistiques\n"
            "/clear - Vider les données",
            parse_mode='Markdown'
        )
    
    async def sync(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self.syncing:
            await update.message.reply_text("⏳ Déjà en cours...")
            return
        
        self.syncing = True
        msg = await update.message.reply_text("🔄 Synchronisation...")
        
        try:
            async def progress(n):
                await msg.edit_text(f"📥 {n} nouvelles prédictions...")
            
            result = await scraper.sync(CHANNEL, full=False, progress_callback=progress)
            
            await msg.edit_text(
                f"✅ **Synchronisé!**\n"
                f"• Nouvelles: `{result['new']}`\n"
                f"• Dernier ID: `{result['last_id']}`",
                parse_mode='Markdown'
            )
        except Exception as e:
            await msg.edit_text(f"❌ Erreur: {str(e)[:200]}")
        finally:
            self.syncing = False
    
    async def fullsync(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = await update.message.reply_text("🔄 Synchronisation complète...")
        
        try:
            result = await scraper.sync(CHANNEL, full=True)
            await msg.edit_text(f"✅ **Terminé!**\nTotal: `{result['new']}`", parse_mode='Markdown')
        except Exception as e:
            await msg.edit_text(f"❌ Erreur: {str(e)[:200]}")
    
    async def report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = await update.message.reply_text("📊 Génération PDF...")
        
        try:
            filters = context.user_data.get('filters', {})
            predictions = get_predictions(filters)
            
            if not predictions:
                await msg.edit_text("❌ Aucune prédiction trouvée.")
                return
            
            pdf_path = generate_pdf(predictions, filters)
            
            with open(pdf_path, 'rb') as f:
                await context.bot.send_document(
                    chat_id=update.effective_user.id,
                    document=f,
                    filename=f"rapport_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    caption=f"✅ **Rapport généré**\nPrédictions: {len(predictions)}",
                    parse_mode='Markdown'
                )
            
            os.remove(pdf_path)
            await msg.delete()
            
        except Exception as e:
            await msg.edit_text(f"❌ Erreur: {str(e)[:200]}")
    
    async def filter_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            context.user_data['filters'] = {}
            await update.message.reply_text("✅ Filtres réinitialisés")
            return
        
        filters = {}
        if len(context.args) >= 1:
            filters['couleur'] = context.args[0]
        if len(context.args) >= 2:
            filters['statut'] = ' '.join(context.args[1:])
        
        context.user_data['filters'] = filters
        await update.message.reply_text(f"✅ Filtres: {filters}")
    
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        s = get_stats()
        predictions = get_predictions()
        gagnes = len([p for p in predictions if 'gagn' in p['statut'].lower()])
        
        await update.message.reply_text(
            f"📊 **Statistiques**\n"
            f"• Total: `{s['total']}`\n"
            f"• Gagnés: `{gagnes}`\n"
            f"• Taux: `{round(gagnes/s['total']*100,1)}%`" if s['total'] else "N/A",
            parse_mode='Markdown'
        )
    
    async def clear(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        clear_all()
        await update.message.reply_text("🗑️ Données effacées!")

handlers = Handlers()

def setup_bot():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(CommandHandler("sync", handlers.sync))
    app.add_handler(CommandHandler("fullsync", handlers.fullsync))
    app.add_handler(CommandHandler("report", handlers.report))
    app.add_handler(CommandHandler("filter", handlers.filter_cmd))
    app.add_handler(CommandHandler("stats", handlers.stats))
    app.add_handler(CommandHandler("clear", handlers.clear))
    
    return app
