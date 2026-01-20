"""
Start Handler - /start, /help, /new commands
"""

from telegram import Update
from telegram.ext import ContextTypes
import config
from core.session import SessionManager

session_mgr = SessionManager(config.DATABASE_PATH)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    
    # Register user
    session_mgr.register_user(
        user.id,
        username=user.username,
        first_name=user.first_name
    )
    
    await update.message.reply_text(
        config.SUCCESS_MESSAGES['welcome'],
        parse_mode='Markdown'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await update.message.reply_text(
        config.HELP_TEXT,
        parse_mode='Markdown'
    )


async def new_pattern_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /new command - start a new pattern"""
    # Clear user context
    context.user_data.clear()
    
    await update.message.reply_text(
        "✨ جاهزة لكروشية جديد؟ دزي الصورة"
    )
