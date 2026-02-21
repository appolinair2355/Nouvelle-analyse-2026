import os
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import BOT_TOKEN, ADMIN_ID, CHANNEL_USERNAME, CHANNEL_PHONE
from storage import get_predictions, get_stats, clear_all
from scraper import scraper
from pdf_generator import generate_pdf

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

class Handlers:
    def __init__(self):
        self.syncing = False
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Accès réservé à l'administrateur.")
            return
            
        await update.message.reply_text(
            f"🎯 **Bot Prédictions VIP**\n\n"
            f"Canal: `{CHANNEL_USERNAME}`\n"
            f"Contact: `{CHANNEL_PHONE}`\n\n"
            f"Commandes:\n"
            f"/sync - Synchroniser nouveaux messages\n"
            f"/fullsync - Tout l'historique\n"
            f"/report - Générer PDF\n"
            f"/filter `couleur` `statut` - Filtrer\n"
            f"/stats - Statistiques\n"
            f"/clear - Vider les données",
            parse_mode='Markdown'
        )
    
    async def sync(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            return
        
        if self.syncing:
            await update.message.reply_text("⏳ Déjà en cours...")
            return
        
        self.syncing = True
        msg = await update.message.reply_text("🔄 Connexion au canal VIP...")
        
        try:
            async def progress(n):
                await msg.edit_text(f"📥 {n} nouvelles prédictions...")
            
            result = await scraper.sync(full=False, progress_callback=progress)
            
            await msg.edit_text(
                f"✅ **Synchronisé!**\n"
                f"• Nouvelles: `{result['new']}`\n"
                f"• Dernier ID: `{result['last_id']}`",
                parse_mode='Markdown'
            )
        except Exception as e:
            await msg.edit_text(f"❌ Erreur: {str(e)[:300]}")
        finally:
            self.syncing = False
    
    async def fullsync(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            return
        
        msg = await update.message.reply_text("🔄 Synchronisation complète du canal...")
        
        try:
            result = await scraper.sync(full=True)
            await msg.edit_text(
                f"✅ **Terminé!**\n"
                f"• Total récupéré: `{result['new']}`",
                parse_mode='Markdown'
            )
        except Exception as e:
            await msg.edit_text(f"❌ Erreur: {str(e)[:300]}")
    
    async def report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            return
        
        msg = await update.message.reply_text("📊 Génération du rapport PDF...")
        
        try:
            filters = context.user_data.get('filters', {})
            predictions = get_predictions(filters)
            
            if not predictions:
                await msg.edit_text("❌ Aucune prédiction trouvée. Faites /sync d'abord.")
                return
            
            pdf_path = generate_pdf(predictions, filters)
            
            with open(pdf_path, 'rb') as f:
                await context.bot.send_document(
                    chat_id=ADMIN_ID,
                    document=f,
                    filename=f"rapport_vip_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    caption=f"✅ **Rapport VIP**\n"
                           f"• Canal: {CHANNEL_USERNAME}\n"
                           f"• Prédictions: {len(predictions)}\n"
                           f"• Filtres: {filters if filters else 'Aucun'}",
                    parse_mode='Markdown'
                )
            
            os.remove(pdf_path)
            await msg.delete()
            
        except Exception as e:
            await msg.edit_text(f"❌ Erreur: {str(e)[:300]}")
    
    async def filter_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            return
            
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
        if not is_admin(update.effective_user.id):
            return
            
        s = get_stats()
        predictions = get_predictions()
        gagnes = len([p for p in predictions if 'gagn' in p['statut'].lower()])
        perdus = len([p for p in predictions if 'perd' in p['statut'].lower()])
        
        await update.message.reply_text(
            f"📊 **Statistiques VIP**\n"
            f"• Total: `{s['total']}`\n"
            f"• Gagnés: `{gagnes}`\n"
            f"• Perdus: `{perdus}`\n"
            f"• Taux: `{round(gagnes/s['total']*100,1)}%`" if s['total'] else "N/A",
            parse_mode='Markdown'
        )
    
    async def clear(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            return
            
        clear_all()
        await update.message.reply_text("🗑️ Données effacées!")

handlers = Handlers()

def setup_bot():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(CommandHandler("sync", handlers.sync))
    app.add_handler(CommandHandler("fullsync", handlers.fullsync))
    app.add_handler(CommandHandler("report", handlers.report))
    app.add_handler(CommandHandler("filter", handlers.filter_cmd))
    app.add_handler(CommandHandler("stats", handlers.stats))
    app.add_handler(CommandHandler("clear", handlers.clear))
    
    return app
                    
