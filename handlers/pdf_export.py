
"""
PDF Export Handler - Generates and sends pattern PDF
"""

from telegram import Update
from telegram.ext import ContextTypes
import os
import config
from core.session import SessionManager
from core.step_generator import StepGenerator
from core.pdf_generator import PDFGenerator

session_mgr = SessionManager(config.DATABASE_PATH)

async def export_pdf_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle PDF export callback"""
    query = update.callback_query
    await query.message.reply_text("جاري إنشاء الملف... ⏳")
    
    session_id = context.user_data.get('session_id')
    
    if not session_id:
        await query.message.reply_text(config.ERROR_MESSAGES['no_session'])
        return

    # Get pattern data
    pattern_result = context.user_data.get('pattern_result')
    if not pattern_result:
        await query.message.reply_text("عفواً، لازم تسوين (باترون جديد) اول")
        return
        
    try:
        # Generate steps
        pattern_grid = pattern_result['pattern_data']
        colors = pattern_result['colors']
        step_gen = StepGenerator(pattern_grid, colors)
        steps = []
        for i in range(1, step_gen.get_total_steps() + 1):
            steps.append(step_gen.get_step(i))
            
        # Basic Info
        basic_info = {
            'width': pattern_result['size'][0],
            'height': pattern_result['size'][1],
            'color_count': len(colors)
        }
        
        # Generate PDF
        pdf_gen = PDFGenerator()
        output_path = os.path.join(config.TEMP_DIR, f"{session_id}_pattern.pdf")
        
        # Ensure temp dir exists
        os.makedirs(config.TEMP_DIR, exist_ok=True)
        
        pdf_gen.generate_steps_pdf(steps, basic_info, output_path)
        
        # Send PDF
        with open(output_path, 'rb') as pdf_file:
            await query.message.reply_document(
                document=pdf_file,
                filename="pattern.pdf",
                caption="📄 تفضلي هذا مخطط الكروشيه كامل"
            )
            
    except Exception as e:
        config.logger.error(f"PDF generation error: {e}")
        await query.message.reply_text(config.ERROR_MESSAGES['generic_error'])
