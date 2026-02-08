"""
Keyboard Layouts - Inline keyboards for bot interactions

Defines all button layouts used in the bot.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_size_selection_keyboard(recommended_size, min_size, max_size):
    """
    Get keyboard for size selection based on image analysis.
    
    Args:
        recommended_size (int): Recommended pattern size
        min_size (int): Minimum recommended size
        max_size (int): Maximum recommended size
    """
    small = min_size
    large = max_size
    
    keyboard = [
        [
            InlineKeyboardButton(
                f"⭐ موصى به: {recommended_size}",
                callback_data=f"size_{recommended_size}"
            ),
        ],
        [
            InlineKeyboardButton(f"صغير: {small}", callback_data=f"size_{small}"),
            InlineKeyboardButton(f"كبير: {large}", callback_data=f"size_{large}"),
        ],
        [
            InlineKeyboardButton("مخصص ⚙️", callback_data="size_custom"),
        ],
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_main_menu_keyboard():
    """Main menu after pattern is generated"""
    keyboard = [
        [InlineKeyboardButton("🎯 الخطوات بالتسلسل", callback_data="start_step_mode")],
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_step_navigation_keyboard(current_step, total_steps):
    """Keyboard for step-by-step navigation"""
    keyboard = []
    
    # Navigation row
    nav_row = []
    if current_step > 1:
        nav_row.append(InlineKeyboardButton("⏮️ السابق", callback_data=f"step_prev"))
    if current_step < total_steps:
        nav_row.append(InlineKeyboardButton("▶️ التالي", callback_data=f"step_next"))
    
    # Add Jump button only on first step
    if current_step == 1:
        nav_row.append(InlineKeyboardButton("تنقل 🔢", callback_data="step_jump"))
    
    if nav_row:
        keyboard.append(nav_row)
    
    # Action buttons
    keyboard.append([
        InlineKeyboardButton("⏹️ إنهاء", callback_data="step_end"),
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_color_picker_keyboard(available_colors, show_all=False):
    """
    Keyboard for color selection.
    
    Args:
        available_colors (list): List of color names
        show_all (bool): If True, show all colors from palette
    """
    from process import STANDARD_YARN_PALETTE
    
    if show_all:
        # Show all colors from standard palette
        colors_to_show = list(STANDARD_YARN_PALETTE.keys())
    else:
        # Show only colors used in this pattern
        colors_to_show = available_colors
    
    # Create keyboard with 3 colors per row
    keyboard = []
    row = []
    
    for i, color_name in enumerate(colors_to_show):
        row.append(InlineKeyboardButton(
            color_name, 
            callback_data=f"color_{color_name}"
        ))
        
        if len(row) == 3:
            keyboard.append(row)
            row = []
    
    # Add remaining colors
    if row:
        keyboard.append(row)
    
    # Add "Show More" or "Cancel" button
    if not show_all and len(available_colors) < 10:
        keyboard.append([InlineKeyboardButton("عرض المزيد 📋", callback_data="color_show_all")])
    
    keyboard.append([InlineKeyboardButton("إلغاء ❌", callback_data="color_cancel")])
    
    return InlineKeyboardMarkup(keyboard)


def get_confirm_keyboard():
    """Simple yes/no confirmation"""
    keyboard = [
        [
            InlineKeyboardButton("نعم ✅", callback_data="confirm_yes"),
            InlineKeyboardButton("لا ❌", callback_data="confirm_no"),
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)


# Testing
if __name__ == "__main__":
    print("🎹 Testing keyboard layouts...")
    
    # Test size selection
    size_kb = get_size_selection_keyboard(150, 100, 200)
    print(f"✅ Size keyboard: {len(size_kb.inline_keyboard)} rows")
    
    # Test main menu
    main_kb = get_main_menu_keyboard()
    print(f"✅ Main menu: {len(main_kb.inline_keyboard)} rows")
    
    # Test step navigation
    step_kb = get_step_navigation_keyboard(5, 100)
    print(f"✅ Step navigation: {len(step_kb.inline_keyboard)} rows")
    
    # Test color picker
    colors = ['أحمر', 'أزرق', 'أخضر', 'أصفر']
    color_kb = get_color_picker_keyboard(colors)
    print(f"✅ Color picker: {len(color_kb.inline_keyboard)} rows")
    
    print("\n🎉 All keyboards created successfully!")
