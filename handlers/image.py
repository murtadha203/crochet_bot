"""
Image Handler - Processes uploaded images

Handles image upload, analysis, and initiates pattern generation workflow.
"""

from telegram import Update
from telegram.ext import ContextTypes
import os
import config
from core.image_analyzer import analyze_image_complexity
from core.session import SessionManager
from core.keyboards import get_size_selection_keyboard

session_mgr = SessionManager(config.DATABASE_PATH)


async def image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle image uploads"""
    user_id = update.effective_user.id
    
    # Ensure temp directory exists
    os.makedirs(config.TEMP_DIR, exist_ok=True)
    
    # Download image
    photo = update.message.photo[-1]  # Get largest size
    
    await update.message.reply_text("🔍 يتم تحليل الصورة...")
    
    # Download to temp
    file = await context.bot.get_file(photo.file_id)
    image_path = os.path.join(config.TEMP_DIR, f"{user_id}_{photo.file_id}.jpg")
    await file.download_to_drive(image_path)
    
    # Save original for later
    original_path = image_path
    
    # Analyze image complexity
    try:
        analysis = analyze_image_complexity(image_path)
    except Exception as e:
        config.logger.error(f"Analysis error: {e}")
        await update.message.reply_text(config.ERROR_MESSAGES['generic_error'])
        return
    
    # Create session
    session_id = session_mgr.create_session(user_id, image_path, original_path)
    
    # Save session ID in context
    context.user_data['session_id'] = session_id
    context.user_data['analysis'] = analysis
    # Bug #6: Store thresholds for the custom-size warning
    context.user_data['size_recommended'] = analysis['recommended_size']
    context.user_data['size_warning_threshold'] = analysis.get('warning_threshold', 0)
    
    # Build response message
    detail_text = {
        'low': 'قليلة',
        'medium': 'متوسطة',
        'high': 'عالية'
    }[analysis['detail_level']]
    
    message = (
        f"📊 **تحليل الصورة:**\n"
        f"  • الحجم الأصلي: {analysis['original_size'][0]}×{analysis['original_size'][1]} بكسل\n"
        f"  • التفاصيل: {detail_text}\n"
        f"  • الحجم الموصى به: {analysis['recommended_size']} غرزة\n\n"
        f"اختر الحجم:"
    )
    
    # Send keyboard
    keyboard = get_size_selection_keyboard(
        analysis['recommended_size'],
        analysis['min_size'],
        analysis['max_size']
    )
    
    await update.message.reply_text(
        message,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
