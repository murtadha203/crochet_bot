"""
Step Mode Handler - Step-by-step navigation and color editing

This is the heart of the interactive crochet assistant.
Provides row-by-row instructions with visual guides.
"""

from telegram import Update
from telegram.ext import ContextTypes
from PIL import Image
import config
from core.step_generator import StepGenerator
from core.composite_img import CompositeImageCreator
from core.session import SessionManager
from core.keyboards import (
    get_step_navigation_keyboard,
    get_color_picker_keyboard
)

session_mgr = SessionManager(config.DATABASE_PATH)


async def start_step_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start step-by-step mode"""
    query = update.callback_query
    await query.answer()
    
    # Get pattern data from context
    pattern_result = context.user_data.get('pattern_result')
    generator = context.user_data.get('generator')
    grid_path = context.user_data.get('grid_path')
    session_id = context.user_data.get('session_id')
    
    if not all([pattern_result, generator, grid_path, session_id]):
        await query.edit_message_text(config.ERROR_MESSAGES['no_session'])
        return
    
    # Get session for original image
    session = session_mgr.get_session(session_id)
    original_path = session['original_image_path']
    
    # Create step generator
    pattern_grid = pattern_result['pattern_data']
    colors = pattern_result['colors']
    
    step_gen = StepGenerator(pattern_grid, colors)
    total_steps = step_gen.get_total_steps()
    
    # Update session
    session_mgr.update_session(session_id, total_steps=total_steps, current_step=1)
    
    # Store images for composite creation
    grid_image = Image.open(grid_path)    
    # Reload grid and create new composite creator with updated pattern
    pattern_image = pattern_result.get('pattern_image')  # Get pattern image from result
    
    context.user_data['composite_creator'] = CompositeImageCreator(
        grid_image,
        Image.open(original_path),
        pattern_grid,
        pattern_image=pattern_image  # Pass pattern image!
    )
    context.user_data['step_generator'] = step_gen
    context.user_data['pattern_image'] = pattern_image  # Store for later use
    
    await query.edit_message_text(
        f"🎯 **الخطوات بالتسلسل**\n\n"
        f"هسه نمشي خطوه خطوه\n"
        f"عدد الخطوات: {total_steps}",
        parse_mode='Markdown'
    )
    
    # Show first step
    await _show_step(update.effective_message, context, 1)


async def step_navigation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle step navigation (next/prev/end) buttons"""
    query = update.callback_query
    await query.answer()
    
    session_id = context.user_data.get('session_id')
    step_gen = context.user_data.get('step_generator')
    
    if not step_gen or not session_id:
        # Send NEW message instead of trying to edit photo message
        await update.effective_message.reply_text(config.ERROR_MESSAGES['no_session'])
        return
    
    # Get current step
    current_step = session_mgr.get_current_step(session_id)
    total_steps = step_gen.get_total_steps()
    
    # Handle button action
    if query.data == "step_next":
        new_step = min(current_step + 1, total_steps)
    elif query.data == "step_prev":
        new_step = max(current_step - 1, 1)
    elif query.data == "step_end":
        await _end_step_mode(update, context)
        return
    else:
        return
    
    # Delete previous step message if it exists
    prev_msg_id = context.user_data.get('last_step_message_id')
    if prev_msg_id:
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=prev_msg_id
            )
        except:
            pass  # Message might be already deleted
    
    # Update session
    session_mgr.set_current_step(session_id, new_step)
    
    # Show new step
    await _show_step(update.effective_message, context, new_step)


async def step_color_edit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle color edit button and color selection"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    if callback_data == "step_color_edit":
        # Show color picker
        pattern_result = context.user_data.get('pattern_result')
        colors = pattern_result['colors'] if pattern_result else []
        
        session_id = context.user_data.get('session_id')
        current_step = session_mgr.get_current_step(session_id)
        step_gen = context.user_data.get('step_generator')
        step = step_gen.get_step(current_step)
        
        # Send NEW message (can't edit photo messages)
        await update.effective_message.reply_text(
            f"🎨 **تغيير اللون**\n\n"
            f"الخطوة {current_step}: {step['count']} غرز من {step['color_name']}\n\n"
            f"تغيير إلى:",
            parse_mode='Markdown',
            reply_markup=get_color_picker_keyboard(colors, show_all=False)
        )
        
        # Store step being edited
        context.user_data['editing_step'] = current_step
        
    elif callback_data == "color_show_all":
        # Show all colors
        from process import STANDARD_YARN_PALETTE
        all_colors = list(STANDARD_YARN_PALETTE.keys())
        
        await query.edit_message_reply_markup(
            reply_markup=get_color_picker_keyboard(all_colors, show_all=True)
        )
        
    elif callback_data == "color_cancel":
        # Cancel color edit - go back to current step
        session_id = context.user_data.get('session_id')
        current_step = session_mgr.get_current_step(session_id)
        await _show_step(update.effective_message, context, current_step)
        
    elif callback_data.startswith("color_"):
        # Color selected
        new_color = callback_data.replace("color_", "")
        editing_step = context.user_data.get('editing_step')
        
        if not editing_step:
            return
        
        # Apply color edit
        step_gen = context.user_data.get('step_generator')
        step_gen.apply_color_edit(editing_step, new_color)
        
        # Save edit to session
        session_id = context.user_data.get('session_id')
        color_edits = session_mgr.get_color_edits(session_id)
        color_edits[f'step_{editing_step}'] = {'new_color': new_color}
        session_mgr.save_color_edits(session_id, color_edits)
        
        await query.edit_message_text(
            f"{config.SUCCESS_MESSAGES['color_changed']}\n"
            f"تم تغيير اللون في الخطوة {editing_step} إلى {new_color}"
        )
        
        # Regenerate grid with edits
        await _regenerate_pattern_with_edits(context)
        
        # Show updated step
        await _show_step(update.effective_message, context, editing_step)


async def _show_step(message, context, step_number):
    """Show a specific step with composite image"""
    step_gen = context.user_data.get('step_generator')
    composite_creator = context.user_data.get('composite_creator')
    session_id = context.user_data.get('session_id')
    
    if not all([step_gen, composite_creator, session_id]):
        return
    
    step = step_gen.get_step(step_number)
    total_steps = step_gen.get_total_steps()
    
    # Create composite image
    composite = composite_creator.create_step_image(step)
    
    # Save temporarily
    import os
    composite_path = os.path.join(config.TEMP_DIR, f"{session_id}_step_{step_number}.png")
    composite.save(composite_path)
    
    # Send image with instruction
    with open(composite_path, 'rb') as img_file:
        result = await message.reply_photo(
            photo=img_file,
            caption=f"**الصف {step['row']} - الخطوة {step_number} من {total_steps}**\n\n"
                   f"{step['instruction_ar']}",
            reply_markup=get_step_navigation_keyboard(step_number, total_steps),
            parse_mode='Markdown'
        )
    
    # Store message ID for later deletion
    context.user_data['last_step_message_id'] = result.message_id


async def _regenerate_pattern_with_edits(context):
    """Regenerate pattern image with applied color edits"""
    step_gen = context.user_data.get('step_generator')
    grid_path = context.user_data.get('grid_path')
    session_id = context.user_data.get('session_id')
    
    if not all([step_gen, grid_path, session_id]):
        return
    
    # Get updated pattern grid
    from process import create_grid_pattern
    from PIL import Image
    
    
    updated_grid = step_gen.get_pattern_grid()
    pattern_result = context.user_data.get('pattern_result')
    colors = pattern_result['colors']
    pattern_image = context.user_data.get('pattern_image')  # Get stored pattern image
    original_path = context.user_data.get('original_path')
    
    # Update composite creator with pattern_image
    context.user_data['composite_creator'] = CompositeImageCreator(
        Image.open(grid_path),
        Image.open(original_path),
        updated_grid,
        pattern_image=pattern_image  # Pass pattern image!
    )


async def _end_step_mode(update, context):
    """End step-by-step mode"""
    query = update.callback_query
    await query.answer()  # Must answer callback
    
    session_id = context.user_data.get('session_id')
    grid_path = context.user_data.get('grid_path')
    palette_path = context.user_data.get('palette_path')
    
    await update.effective_message.reply_text(
        "🎉 **مبرووووك, خلصنا! صيحيني اشوفه**\n\n"
        "",
        parse_mode='Markdown'
    )
    
    # Send final pattern images
    if grid_path and palette_path:
        with open(grid_path, 'rb') as grid_file:
            await update.effective_message.reply_photo(
                photo=grid_file,
                caption="✅ المخطط النهائي"
            )
        
        with open(palette_path, 'rb') as palette_file:
            await update.effective_message.reply_photo(
                photo=palette_file,
                caption="🎨 لوحة الألوان النهائية"
            )
