import os
import re
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from database import init_db, get_predictions, get_stats, update_last_sync
from scraper import scraper
from pdf_generator import generate_predictions_pdf

# Configuration
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS', '').split(',') if x]
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME', '')

def is_admin(user_id: int) -> bool:
    return not ADMIN_IDS or user_id in ADMIN_IDS

class BotHandlers:
    def __init__(self):
        self.syncing = False
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        await update.message.reply_text(
            f"🎯 **Bot de Prédictions VIP**\n\n"
            f"Commandes:\n"
            f"/sync - Synchroniser les nouveaux messages\n"
            f"/fullsync - Synchronisation complète (1ère fois)\n"
            f"/report - Générer rapport PDF\n"
            f"/filter `couleur` `statut` - Filtrer (ex: /filter Trèfle GAGNÉ)\n"
            f"/stats - Statistiques\n\n"
            f"Canal: `{CHANNEL_USERNAME}`",
            parse_mode='Markdown'
        )
    
    async def sync(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Accès refusé")
            return
        
        if self.syncing:
            await update.message.reply_text("⏳ Synchronisation déjà en cours...")
            return
        
        self.syncing = True
        msg = await update.message.reply_text("🔄 Connexion à Telethon...")
        
        try:
            async def progress(count):
                await msg.edit_text(f"📥 {count} nouvelles prédictions trouvées...")
            
            result = await scraper.sync_history(CHANNEL_USERNAME, progress)
            
            await msg.edit_text(
                f"✅ **Synchronisation terminée!**\n"
                f"• Nouvelles prédictions: `{result['new_predictions']}`\n"
                f"• Dernier message ID: `{result['last_message_id']}`",
                parse_mode='Markdown'
            )
        except Exception as e:
            await msg.edit_text(f"❌ Erreur: {str(e)[:200]}")
        finally:
            self.syncing = False
    
    async def full_sync(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            return
        
        msg = await update.message.reply_text("🔄 Synchronisation complète en cours...")
        
        try:
            async def progress(count, msg_id):
                if count % 1000 == 0:
                    await msg.edit_text(f"📥 {count} prédictions... (ID: {msg_id})")
            
            result = await scraper.full_sync(CHANNEL_USERNAME, progress)
            
            await msg.edit_text(
                f"✅ **Synchronisation complète!**\n"
                f"• Total prédictions: `{result['total_predictions']}`",
                parse_mode='Markdown'
            )
        except Exception as e:
            await msg.edit_text(f"❌ Erreur: {str(e)[:200]}")
    
    async def report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            return
        
        msg = await update.message.reply_text("📊 Génération du rapport...")
        
        try:
            # Récupérer filtres stockés ou tous
            filters = context.user_data.get('filters', {})
            predictions = get_predictions(filters)
            
            if not predictions:
                await msg.edit_text("❌ Aucune prédiction dans la base.")
                return
            
            pdf_path = generate_predictions_pdf(predictions, filters)
            
            with open(pdf_path, 'rb') as f:
                await context.bot.send_document(
                    chat_id=update.effective_user.id,
                    document=f,
                    filename=f"rapport_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    caption=f"✅ **Rapport généré**\n"
                           f"• Prédictions: {len(predictions)}\n"
                           f"• Filtres: {filters if filters else 'Aucun'}",
                    parse_mode='Markdown'
                )
            
            os.remove(pdf_path)
            await msg.delete()
            
        except Exception as e:
            await msg.edit_text(f"❌ Erreur: {str(e)[:200]}")
    
    async def filter_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Définit les filtres pour le prochain rapport"""
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
        await update.message.reply_text(
            f"✅ Filtres définis:\n"
            f"• Couleur: {filters.get('couleur', 'Toutes')}\n"
            f"• Statut: {filters.get('statut', 'Tous')}\n\n"
            f"Utilisez /report pour générer le PDF filtré."
        )
    
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        stats = get_stats()
        predictions = get_predictions()
        
        # Calcul rapide
        gagnes = len([p for p in predictions if 'gagn' in p['statut'].lower()])
        
        await update.message.reply_text(
            f"📊 **Statistiques**\n"
            f"• Total prédictions: `{stats['total']}`\n"
            f"• Gagnés: `{gagnes}`\n"
            f"• Taux de réussite: `{round(gagnes/stats['total']*100, 1)}%`" if stats['total'] else "N/A",
            parse_mode='Markdown'
        )

handlers = BotHandlers()

def setup_bot():
    init_db()
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CommandHandler("sync", handlers.sync))
    application.add_handler(CommandHandler("fullsync", handlers.full_sync))
    application.add_handler(CommandHandler("report", handlers.report))
    application.add_handler(CommandHandler("filter", handlers.filter_cmd))
    application.add_handler(CommandHandler("stats", handlers.stats))
    
    return application
