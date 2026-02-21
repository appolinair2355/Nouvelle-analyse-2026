import os
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import BOT_TOKEN, ADMIN_ID, CHANNEL_USERNAME, USER_PHONE
from storage import get_predictions, get_stats, clear_all
from scraper import scraper
from auth_manager import auth_manager
from pdf_generator import generate_pdf

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

class Handlers:
    def __init__(self):
        self.syncing = False
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            return
        
        connected = "✅ Connecté" if auth_manager.is_connected() else "❌ Non connecté"
        
        await update.message.reply_text(
            f"🎯 **Bot VIP KOUAMÉ & JOKER**\n\n"
            f"Status: {connected}\n"
            f"Votre numéro: `{USER_PHONE}`\n\n"
            f"Commandes:\n"
            f"/connect - Recevoir le code SMS\n"
            f"/code aaXXXXXX - Confirmer le code\n"
            f"/sync - Synchroniser récent\n"
            f"/fullsync - Tout l'historique\n"
            f"/report - Générer PDF\n"
            f"/stats - Statistiques",
            parse_mode='Markdown'
        )
    
    async def connect(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/connect - Envoie le code à votre numéro"""
        if not is_admin(update.effective_user.id):
            return
        
        if auth_manager.is_connected():
            await update.message.reply_text("✅ Déjà connecté !")
            return
        
        msg = await update.message.reply_text(f"📲 Envoi du code à {USER_PHONE}...")
        
        try:
            success, result = await auth_manager.send_code()
            await msg.edit_text(result)
        except Exception as e:
            await msg.edit_text(f"❌ Erreur: {str(e)}")
    
    async def code(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/code aaXXXXXX"""
        if not is_admin(update.effective_user.id):
            return
        
        if not context.args:
            await update.message.reply_text("Usage: `/code aa12345`", parse_mode='Markdown')
            return
        
        code = context.args[0]
        msg = await update.message.reply_text("🔐 Vérification...")
        
        try:
            success, result = await auth_manager.verify_code(code)
            await msg.edit_text(result)
        except Exception as e:
            await msg.edit_text(f"❌ Erreur: {str(e)}")
    
    async def sync(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            return
        
        if not auth_manager.is_connected():
            await update.message.reply_text("❌ Tapez /connect puis /code d'abord")
            return
        
        if self.syncing:
            await update.message.reply_text("⏳ Déjà en cours...")
            return
        
        self.syncing = True
        msg = await update.message.reply_text("🔄 Synchronisation...")
        
        try:
            async def progress(n):
                if n % 500 == 0:
                    await msg.edit_text(f"📥 {n} messages...")
            
            result = await scraper.sync(full=False, progress_callback=progress)
            await msg.edit_text(f"✅ **{result['new']}** nouvelles prédictions !")
        except Exception as e:
            await msg.edit_text(f"❌ Erreur: {str(e)[:300]}")
        finally:
            self.syncing = False
    
    async def fullsync(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            return
        
        if not auth_manager.is_connected():
            await update.message.reply_text("❌ Non connecté")
            return
        
        msg = await update.message.reply_text("🔄 Synchronisation complète...")
        
        try:
            result = await scraper.sync(full=True)
            await msg.edit_text(f"✅ **{result['new']}** prédictions récupérées !")
        except Exception as e:
            await msg.edit_text(f"❌ Erreur: {str(e)[:300]}")
    
    async def report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            return
        
        predictions = get_predictions(context.user_data.get('filters'))
        if not predictions:
            await update.message.reply_text("❌ Aucune donnée. Faites /fullsync d'abord")
            return
        
        msg = await update.message.reply_text("📄 Génération PDF...")
        
        try:
            pdf_path = generate_pdf(predictions, context.user_data.get('filters'))
            
            with open(pdf_path, 'rb') as f:
                await context.bot.send_document(
                    chat_id=ADMIN_ID,
                    document=f,
                    caption=f"✅ Rapport: {len(predictions)} prédictions"
                )
            
            os.remove(pdf_path)
            await msg.delete()
        except Exception as e:
            await msg.edit_text(f"❌ Erreur: {str(e)}")
    
    async def filter_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            return
        
        if not context.args:
            context.user_data['filters'] = {}
            await update.message.reply_text("✅ Filtres réinitialisés")
            return
        
        filters = {'couleur': context.args[0]}
        if len(context.args) > 1:
            filters['statut'] = ' '.join(context.args[1:])
        
        context.user_data['filters'] = filters
        await update.message.reply_text(f"✅ Filtre: {filters}")
    
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            return
        
        s = get_stats()
        preds = get_predictions()
        gagnes = sum(1 for p in preds if 'gagn' in p['statut'].lower())
        
        await update.message.reply_text(
            f"📊 Stats\n"
            f"• Total: {s['total']}\n"
            f"• Gagnés: {gagnes}\n"
            f"• Taux: {round(gagnes/s['total']*100,1)}%" if s['total'] else "N/A"
        )
    
    async def clear(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            return
        clear_all()
        await update.message.reply_text("🗑️ Effacé !")

handlers = Handlers()

def setup_bot():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(CommandHandler("connect", handlers.connect))
    app.add_handler(CommandHandler("code", handlers.code))
    app.add_handler(CommandHandler("sync", handlers.sync))
    app.add_handler(CommandHandler("fullsync", handlers.fullsync))
    app.add_handler(CommandHandler("report", handlers.report))
    app.add_handler(CommandHandler("filter", handlers.filter_cmd))
    app.add_handler(CommandHandler("stats", handlers.stats))
    app.add_handler(CommandHandler("clear", handlers.clear))
    
    return app
