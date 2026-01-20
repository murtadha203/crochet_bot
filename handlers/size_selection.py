"""
Size Selection Handler - Handles size button callbacks and custom size input
"""

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
import os
import config
from core.pattern_gen import PatternGenerator
from core.session import SessionManager
from core.keyboards import get_main_menu_keyboard

session_mgr = SessionManager(config.DATABASE_PATH)

# Conversation state
WAITING_CUSTOM_SIZE = 1


async def size_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle size selection button callbacks"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    if callback_data == "size_custom":
        # Ask for custom size
        await query.edit_message_text(
            "📏 **شكد تريدين طول المخطط **\n\n"
            "اكتبي عدد الغرز للضلع الأطول (مثال: 250)\n\n"
            f"💡 الحد الأدنى: {config.MIN_PATTERN_SIZE}\n"
            f"   الحد الأقصى: {config.MAX_PATTERN_SIZE}",
            parse_mode='Markdown'
        )
        return WAITING_CUSTOM_SIZE
    
    # Extract size from callback_data (e.g., "size_150")
    size = int(callback_data.split('_')[1])
    
    await _generate_pattern(update, context, size)


async def custom_size_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom size text input"""
    try:
        size = int(update.message.text.strip())
        
        if size < config.MIN_PATTERN_SIZE or size > config.MAX_PATTERN_SIZE:
            await update.message.reply_text(
                f"❌ الحجم لازم يكون بين {config.MIN_PATTERN_SIZE} و {config.MAX_PATTERN_SIZE}"
            )
            return WAITING_CUSTOM_SIZE
        
        await _generate_pattern(update, context, size)
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text("❌ اكتب رقم صحيح")
        return WAITING_CUSTOM_SIZE


async def _generate_pattern(update, context, size):
    """Generate the pattern with specified size"""
    # Get session
    session_id = context.user_data.get('session_id')
    if not session_id:
        await update.effective_message.reply_text(config.ERROR_MESSAGES['no_session'])
        return
    
    session = session_mgr.get_session(session_id)
    if not session:
        await update.effective_message.reply_text(config.ERROR_MESSAGES['no_session'])
        return
    
    image_path = session['image_path']
    original_path = session['original_image_path']
    
    # Send processing message
    processing_msg = await update.effective_message.reply_text("⏳ جاري إنشاء المـخطط...")
    
    try:
        # Generate pattern
        generator = PatternGenerator(image_path, size, is_knitting=False)
        
        # Analyze colors
        colors = generator.analyze_colors(max_colors=config. MAX_COLORS)
        
        # Generate pattern
        result = generator.generate_pattern(user_colors=colors)
        
        # Save outputs
        grid_path = os.path.join(config.TEMP_DIR, f"{session_id}_grid.png")
        palette_path = os.path.join(config.TEMP_DIR, f"{session_id}_palette.png")
        
        generator.save_outputs(grid_path, palette_path)
        
        # Update session
        session_mgr.update_session(
            session_id,
            pattern_size=size,
            colors_json=str(colors),
            grid_path=grid_path,
            palette_path=palette_path
        )
        
        # Store in context for step mode
        context.user_data['generator'] = generator
        context.user_data['pattern_result'] = result
        context.user_data['grid_path'] = grid_path
        context.user_data['palette_path'] = palette_path
        
        # Delete processing message
        await processing_msg.delete()
        
        # Send pattern images FIRST
        with open(grid_path, 'rb') as grid_file:
            await update.effective_message.reply_photo(
                photo=grid_file,
                caption="🎨 مخطط الكروشية"
            )
        
        with open(palette_path, 'rb') as palette_file:
            await update.effective_message.reply_photo(
                photo=palette_file,
                caption="🎨 لوحة الألوان"
            )
        
        # THEN send success message with menu
        await update.effective_message.reply_text(
            f"{config.SUCCESS_MESSAGES['pattern_ready']}\n\n"
            f"📊 **الحجم:** {result['size'][0]}×{result['size'][1]} غرزة "
            f"({result['total_stitches']:,} غرزة)\n"
            f"🎨 **الألوان:** {len(result['colors'])} لون\n\n"
            "هل تريد:",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )
        
    except Exception as e:
        config.logger.error(f"Pattern generation error: {e}")
        await processing_msg.edit_text(config.ERROR_MESSAGES['generic_error'])
