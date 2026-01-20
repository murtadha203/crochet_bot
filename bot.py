"""
Main Bot Application - Entry point for the Telegram bot

Run this file to start the bot.
"""

import config
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters
)

from handlers.start import start_command, help_command, new_pattern_command
from handlers.image import image_handler
from handlers.size_selection import (
    size_callback_handler,
    custom_size_handler,
    WAITING_CUSTOM_SIZE
)
from handlers.step_mode import (
    start_step_mode,
    step_navigation_handler,
    step_color_edit_handler
)


def main():
    """Start the bot"""
    # Validate configuration
    if config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Error: Please set your BOT_TOKEN in config.py")
        print("   Get a token from @BotFather on Telegram")
        return
    
    print("🤖 Starting Crochet Pattern Bot...")
    
    # Create application
    app = Application.builder().token(config.BOT_TOKEN).build()
    
    # === COMMAND HANDLERS ===
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("new", new_pattern_command))
    
    # === IMAGE HANDLER ===
    app.add_handler(MessageHandler(filters.PHOTO, image_handler))
    
    # === SIZE SELECTION WITH CONVERSATION (for custom size) ===
    size_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(size_callback_handler, pattern="^size_")],
        states={
            WAITING_CUSTOM_SIZE: [MessageHandler(filters.TEXT & ~filters.COMMAND, custom_size_handler)]
        },
        fallbacks=[],
        allow_reentry=True
    )
    app.add_handler(size_conv_handler)
    
    # === MAIN MENU CALLBACKS ===
    app.add_handler(CallbackQueryHandler(start_step_mode, pattern="^start_step_mode$"))
    # TODO: Add PDF export handler
    # app.add_handler(CallbackQueryHandler(export_pdf_handler, pattern="^export_pdf$"))
    app.add_handler(CallbackQueryHandler(new_pattern_command, pattern="^new_pattern$"))
    
    # === STEP MODE CALLBACKS ===
    app.add_handler(CallbackQueryHandler(step_navigation_handler, pattern="^step_(next|prev|end)$"))
    app.add_handler(CallbackQueryHandler(step_color_edit_handler, pattern="^(step_color_edit|color_)"))
    
    print("✅ Bot initialized successfully!")
    print(f"📊 Max pattern size: {config.MAX_PATTERN_SIZE}")
    print(f"🎨 Max colors: {config.MAX_COLORS}")
    print("\n🚀 Bot is running... Press Ctrl+C to stop")
    
    # Start polling
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
