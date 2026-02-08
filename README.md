# 🧶 Telegram Crochet Pattern Bot

محول الصور إلى باترون كروشيه - Telegram Bot

Convert any image into a step-by-step crochet pattern with intelligent color detection and interactive guidance.

## ✨ Features

- **Smart Image Analysis** - Automatically analyzes image complexity and recommends optimal pattern size
- **Intelligent Color Detection** - Uses Lab color space for perceptually accurate color matching
- **Step-by-Step Mode** - Interactive row-by-row instructions with visual guides
- **Localized Color Editing** - Change colors for specific stitches, not globally
- **Arabic Support** - Full Arabic interface and instructions

## 📁 Project Structure

```
croshet tg bot/
├── core/                    # Core image processing (independent of bot)
│   ├── image_analyzer.py    # Smart size recommendation
│   ├── pattern_gen.py       # Pattern generation wrapper
│   ├── step_generator.py    # Step-by-step instructions
│   ├── composite_img.py     # Visual step guides
│   ├── session.py           # Session management
│   └── keyboards.py         # Keyboard layouts
│
├── handlers/                # Bot interaction handlers
│   ├── start.py            # /start, /help commands
│   ├── image.py            # Image upload handling
│   ├── size_selection.py   # Size selection & pattern generation
│   └── step_mode.py        # Step-by-step navigation
│
├── data/                   # User data & sessions
│   ├── sessions.db         # SQLite database
│   └── temp/               # Temporary images
│
├── process.py              # Original pattern conversion logic
├── config.py               # Bot configuration
├── bot.py                  # Main bot application
└── requirements.txt        # Python dependencies
```

## 🚀 Setup Instructions

### 1. Prerequisites

- Python 3.10 or higher
- Telegram Bot Token (from @BotFather)

### 2. Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Edit `config.py` and set your bot token:

```python
BOT_TOKEN = "YOUR_ACTUAL_BOT_TOKEN_HERE"  # Get from @BotFather
```

### 4. Run the Bot

```bash
python bot.py
```

You should see:
```
🤖 Starting Crochet Pattern Bot...
✅ Bot initialized successfully!
🚀 Bot is running... Press Ctrl+C to stop
```

## 📖 User Guide

### Basic Usage

1. Start the bot: `/start`
2. Send any image
3. Bot analyzes and recommends size
4. Select pattern size
5. Get pattern grid + color palette

### Step-by-Step Mode

After pattern is generated:
1. Click "البدء بالخطوة بالخطوة"
2. Follow row-by-row instructions
3. Use ▶️ Next / ⏮️ Prev to navigate
4. Click 🎨 to change colors for current step
5. Click ⏹️ to end and get final pattern

## 🔧 Architecture

### Core Modules (Independent)

The `core/` directory contains all image processing logic, completely independent of Telegram:

- **image_analyzer.py** - Edge detection & color complexity analysis
- **pattern_gen.py** - Wraps `process.py` with clean interface
- **step_generator.py** - Converts grid to crochet instructions
- **composite_img.py** - Creates visual step guides
- **session.py** - SQL-based session persistence
- **keyboards.py** - Inline keyboard layouts

### Bot Handlers (Telegram-Specific)

The `handlers/` directory contains Telegram-specific code:

- **start.py** - Command handlers
- **image.py** - Image download & analysis trigger
- **size_selection.py** - Generates patterns
- **step_mode.py** - Interactive step-by-step guidance

### Design Philosophy

The core modules can be **reused** for:
- Web applications
- CLI tools
- Other messaging platforms

Only the `handlers/` and `bot.py` are Telegram-specific.

## 🧪 Testing Core Modules

You can test core modules independently:

```bash
# Test image analyzer
python core/image_analyzer.py test_images/tweety.jpg

# Test pattern generator
python core/pattern_gen.py test_images/tweety.jpg

# Test step generator
python core/step_generator.py

# Test composite creator
python core/composite_img.py test_images/tweety.jpg

# Test session manager
python core/session.py
```

## 🎨 How It Works

### 1. Smart Size Recommendation

```
Image → Edge Detection + Color Analysis → Complexity Score → Recommended Size
```

- **High complexity** (detailed, many colors): 30-40% of original
- **Medium complexity**: 20-25% of original
- **Low complexity**: 12-15% of original

### 2. Color Detection

```
Image → Quantize (32 colors) → Match to Yarn Palette → Top 10 colors
```

Uses **PIL quantization** to find actual dominant colors, then matches to standard yarn palette using **Lab color distance**.

### 3. Step-by-Step Instructions

```
Pattern Grid → Group Consecutive Colors → Generate Instructions
```

Example: `[red, red, red, blue, blue]` → Step 1: "3 red →", Step 2: "2 blue →"

### 4. Composite Images

```
Original Image (with position box) + Zoomed Grid (with highlight) → 800x900 composite
```

## 📊 Database Schema

```sql
users (
    user_id, username, first_name, language_code, created_at, last_active
)

sessions (
    session_id, user_id, image_path, pattern_size, colors_json,
    grid_path, palette_path, current_step, total_steps, color_edits_json
)
```

## 🔮 Future Enhancements

- [ ] PDF export with full instructions
- [ ] Multi-language support (English)
- [ ] Pattern library (save favorites)
- [ ] Yarn amount estimates
- [ ] Premium features (larger patterns, more colors)

## 🐛 Troubleshooting

### "No module named 'telegram'"
```bash
pip install python-telegram-bot==20.7
```

### "BOT_TOKEN not set"
Edit `config.py` and add your token from @BotFather

### Database errors
Delete `data/sessions.db` - it will be recreated

### Images not processing
Check that `data/temp/` directory exists and is writable

## 📝 License

This project is for educational purposes.

## 🙏 Credits

Built with:
- python-telegram-bot
- Pillow (PIL)
- SQLite

---

Made with ❤️ for crochet enthusiasts
