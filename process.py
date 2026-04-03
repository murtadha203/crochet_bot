#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Image to Knitting/Crochet Pattern Converter
Converts cartoon images into pixel-perfect patterns with Arabic instructions
"""

import os
import re
import math
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

FONT_PATH = "fonts/Arial.ttf" #this path do exist
CELL_SIZE = 20  # Scale factor for grid visualization

# ===== Standard Yarn Palette (35 curated colors) =====
# Based on common DMC/Bernat/Red Heart yarn colors
# Each entry: "Arabic Name": (R, G, B)
STANDARD_YARN_PALETTE = {
    # Neutrals (9) — Bug #3C: added two missing grey shades to close Lab-space gap
    "أسود": (0, 0, 0),
    "أبيض": (255, 255, 255),
    "رمادي داكن جداً": (40, 40, 40),   # very dark gray — fills gap near black
    "رمادي غامق": (80, 80, 80),
    "رمادي متوسط": (160, 160, 160),    # mid gray — fills gap between light/dark
    "رمادي": (128, 128, 128),
    "رمادي فاتح": (192, 192, 192),
    "كريمي": (255, 253, 208),
    "بيجي": (245, 222, 179),

    # Skin tones (3) - for cartoon faces
    "بشرة": (255, 224, 189),
    "بشرة فاتحة": (255, 239, 219),
    "بشرة داكنة": (210, 180, 140),

    # Reds/Pinks (5)
    "أحمر غامق": (128, 0, 0),
    "أحمر": (220, 20, 60),
    "وردي غامق": (199, 21, 133),
    "وردي": (255, 192, 203),
    "وردي فاتح": (255, 228, 225),

    # Oranges/Browns (6)
    "بني غامق": (101, 67, 33),
    "بني": (165, 42, 42),
    "برتقالي محمر": (183, 65, 14),
    "برتقالي": (255, 140, 0),
    "برتقالي فاتح": (255, 218, 185),
    "جملي": (210, 180, 140),

    # Yellows/Golds (3)
    "ذهبي غامق": (184, 134, 11),
    "ذهبي": (255, 215, 0),
    "أصفر": (255, 255, 0),

    # Greens (5)
    "أخضر غامق": (0, 100, 0),
    "أخضر": (0, 180, 0),
    "زيتي": (128, 128, 0),
    "أخضر فاتح": (144, 238, 144),
    "نعناعي": (152, 255, 152),

    # Blues (5)
    "كحلي": (0, 0, 128),
    "أزرق غامق": (0, 0, 205),
    "أزرق": (0, 0, 255),
    "سماوي": (135, 206, 235),
    "تركواز": (64, 224, 208),

    # Purples (4)
    "بنفسجي غامق": (75, 0, 130),
    "بنفسجي": (128, 0, 128),
    "ليلكي": (200, 162, 200),
    "لافندر": (230, 230, 250),
}

# ===== Lab Color Space Functions =====
def rgb_to_lab(rgb):
    """Convert RGB to Lab color space for perceptually accurate color comparison"""
    r, g, b = rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0

    # RGB to XYZ
    r = ((r + 0.055) / 1.055) ** 2.4 if r > 0.04045 else r / 12.92
    g = ((g + 0.055) / 1.055) ** 2.4 if g > 0.04045 else g / 12.92
    b = ((b + 0.055) / 1.055) ** 2.4 if b > 0.04045 else b / 12.92

    x = r * 0.4124 + g * 0.3576 + b * 0.1805
    y = r * 0.2126 + g * 0.7152 + b * 0.0722
    z = r * 0.0193 + g * 0.1192 + b * 0.9505

    # XYZ to Lab (D65 illuminant)
    x, y, z = x / 0.95047, y / 1.00000, z / 1.08883

    x = x ** (1/3) if x > 0.008856 else (7.787 * x) + (16/116)
    y = y ** (1/3) if y > 0.008856 else (7.787 * y) + (16/116)
    z = z ** (1/3) if z > 0.008856 else (7.787 * z) + (16/116)

    L = (116 * y) - 16
    a = 500 * (x - y)
    b_lab = 200 * (y - z)

    return (L, a, b_lab)

def color_distance_lab(rgb1, rgb2):
    """Calculate perceptual color distance using Lab color space (Delta E)"""
    lab1 = rgb_to_lab(rgb1)
    lab2 = rgb_to_lab(rgb2)

    # Delta E (CIE76 formula)
    return math.sqrt(
        (lab1[0] - lab2[0])**2 +
        (lab1[1] - lab2[1])**2 +
        (lab1[2] - lab2[2])**2
    )

# ===== Arabic Text Helper =====
def text_arabic(text):
    """
    Convert Arabic text for proper RTL display with connected letters.
    
    CRITICAL: For MIXED content (Arabic + numbers + Latin), we MUST use BiDi algorithm!
    Simple reversal breaks when text contains numbers, spaces, punctuation.
    
    Example: "الصف 2" reversed becomes "2 فصلا" which is WRONG!
    
    Solution:
    1. arabic_reshaper: Connects the letters (ا ل ع ر ب ي ة → العربية)
    2. get_display: Applies BiDi algorithm (handles Arabic + numbers correctly)
    """
    try:
        # Step 1: Reshape to connect letters
        reshaped_text = arabic_reshaper.reshape(text)
        
        # Step 2: Apply BiDi algorithm for proper mixed-content handling
        bidi_text = get_display(reshaped_text)
        
        return bidi_text
    except Exception as e:
        print(f"⚠️ WARNING: Arabic text processing failed: {e}")
        print(f"  Text: {text}")
        print(f"  Returning original text")
        return text

# ===== Color Name Mapping =====
def get_closest_color_name(rgb):
    """Map RGB values to Arabic color name using HSV color space for better accuracy"""
    if isinstance(rgb, int):
        return f"مفهرس {rgb}"

    r, g, b = rgb

    # Convert RGB to HSV for perceptually accurate color naming
    r_norm, g_norm, b_norm = r/255.0, g/255.0, b/255.0
    max_val = max(r_norm, g_norm, b_norm)
    min_val = min(r_norm, g_norm, b_norm)
    diff = max_val - min_val

    # Calculate HSV
    # Hue (0-360)
    if diff == 0:
        hue = 0
    elif max_val == r_norm:
        hue = (60 * ((g_norm - b_norm) / diff) + 360) % 360
    elif max_val == g_norm:
        hue = (60 * ((b_norm - r_norm) / diff) + 120) % 360
    else:
        hue = (60 * ((r_norm - g_norm) / diff) + 240) % 360

    # Saturation (0-1)
    saturation = 0 if max_val == 0 else diff / max_val

    # Value/Brightness (0-1)
    value = max_val

    # === Decision Tree for Color Naming ===

    # 1. Check for black/white first
    if value < 0.15:  # Very dark
        return "أسود"
    if value > 0.9 and saturation < 0.1:  # Very bright and unsaturated
        return "أبيض"

    # 2. Low saturation = Grey/Beige tones
    if saturation < 0.15:  # Nearly grey
        if value > 0.75:
            return "رمادي فاتح"
        elif value > 0.45:
            return "رمادي"
        else:
            return "رمادي غامق"

    # 3. Low saturation + warm = Beige/Cream
    if saturation < 0.30:
        if hue < 60 or hue > 300:  # Warm tones
            if value > 0.75:
                return "كريمي"
            else:
                return "بيجي"
        else:
            # Cool greys
            if value > 0.65:
                return "رمادي فاتح"
            else:
                return "رمادي"

    # 4. High saturation = Pure colors (based on hue)
    # Red: 0-15, 345-360
    if (hue >= 345 or hue < 15):
        if value < 0.5:
            return "أحمر غامق"
        elif saturation > 0.6:
            return "أحمر"
        else:
            return "وردي"

    # Orange/Brown: 15-45
    elif hue < 45:
        if value < 0.4:
            return "بني غامق"
        elif value < 0.6 or saturation < 0.5:
            return "بني"
        else:
            return "برتقالي"

    # Yellow/Gold: 45-70
    elif hue < 70:
        if saturation < 0.5:
            return "بيج"
        elif value > 0.7:
            return "أصفر"
        else:
            return "ذهبي"

    # Green: 70-160
    elif hue < 160:
        if value < 0.4:
            return "أخضر غامق"
        elif saturation > 0.5:
            return "أخضر"
        else:
            return "زيتي"

    # Cyan/Turquoise: 160-200
    elif hue < 200:
        return "تركواز"

    # Blue: 200-260
    elif hue < 260:
        if value < 0.4:
            return "كحلي"
        elif value > 0.7:
            return "سماوي"
        else:
            return "أزرق"

    # Purple/Violet: 260-330
    elif hue < 330:
        if saturation > 0.5:
            return "بنفسجي"
        else:
            return "وردي"

    # Pink: 330-345
    else:
        return "وردي"


# ===== Color Similarity Merger =====
def merge_similar_colors(image, threshold=10):
    """
    Merge colors that are too similar (e.g., RGB(0,0,0) and RGB(1,0,1))

    Args:
        image: PIL Image in RGB mode
        threshold: Maximum Euclidean distance to consider colors as "the same"

    Returns:
        PIL Image with merged colors
    """
    width, height = image.size
    pixels = image.load()

    # Get all unique colors
    colors = image.getcolors(width * height)
    if not colors:
        return image

    # Sort by frequency (most common first)
    colors.sort(key=lambda x: x[0], reverse=True)

    # Build color mapping: similar_color -> dominant_color
    color_map = {}

    for i, (count_i, rgb_i) in enumerate(colors):
        if rgb_i in color_map:
            continue  # Already mapped

        # This color is dominant (not yet mapped)
        color_map[rgb_i] = rgb_i

        # Find all similar colors and map them to this dominant one
        for j, (count_j, rgb_j) in enumerate(colors):
            if i == j or rgb_j in color_map:
                continue

            # Calculate Euclidean distance
            distance = math.sqrt(
                (rgb_i[0] - rgb_j[0])**2 +
                (rgb_i[1] - rgb_j[1])**2 +
                (rgb_i[2] - rgb_j[2])**2
            )

            # If similar enough, map to dominant color
            if distance <= threshold:
                color_map[rgb_j] = rgb_i

    # Apply color mapping to entire image
    new_image = Image.new("RGB", (width, height))
    new_pixels = new_image.load()

    for y in range(height):
        for x in range(width):
            old_color = pixels[x, y]
            new_color = color_map.get(old_color, old_color)
            new_pixels[x, y] = new_color

    return new_image

# ===== Perceptual Color Merger (by Name) =====
def merge_colors_by_name(image):
    """
    Merge colors that have the same perceptual name.
    If two colors are both called "سماوي", they should be ONE color in the pattern.

    Args:
        image: PIL Image in RGB mode

    Returns:
        PIL Image with name-duplicates merged
    """
    width, height = image.size
    pixels = image.load()

    # Get all unique colors
    colors = image.getcolors(width * height)
    if not colors:
        return image

    # Sort by frequency (most common first)
    colors.sort(key=lambda x: x[0], reverse=True)

    # Group colors by their Arabic name
    name_groups = {}
    for count, rgb in colors:
        name = get_closest_color_name(rgb)
        if name not in name_groups:
            name_groups[name] = []
        name_groups[name].append((count, rgb))

    # Build color mapping: for each name group, map all to the most frequent one
    color_map = {}
    for name, group in name_groups.items():
        # Sort by frequency within group
        group.sort(key=lambda x: x[0], reverse=True)
        dominant_color = group[0][1]  # Most frequent color with this name

        # Map all colors in this group to the dominant one
        for count, rgb in group:
            color_map[rgb] = dominant_color


    # Apply color mapping to entire image
    new_image = Image.new("RGB", (width, height))
    new_pixels = new_image.load()

    for y in range(height):
        for x in range(width):
            old_color = pixels[x, y]
            new_color = color_map.get(old_color, old_color)
            new_pixels[x, y] = new_color

    return new_image

# ===== Map Image to User's Yarn Palette =====
def map_to_user_palette(image, user_colors):
    """
    Map every pixel in the image to the closest color from user's available yarn colors.
    Uses Lab color space for perceptually accurate matching.

    Args:
        image: PIL Image in RGB mode
        user_colors: List of color names that the user has (e.g., ["أحمر", "أزرق", "بني"])

    Returns:
        PIL Image with all pixels mapped to user's palette
    """
    width, height = image.size
    pixels = image.load()

    # Build user's palette from selected colors
    user_palette = {}
    for color_name in user_colors:
        if color_name in STANDARD_YARN_PALETTE:
            user_palette[color_name] = STANDARD_YARN_PALETTE[color_name]

    if not user_palette:
        print("❌ خطأ: لم يتم اختيار ألوان صحيحة")
        return image

    print(f"✅ الألوان المتاحة: {len(user_palette)} لون")

    # Create new image
    new_image = Image.new("RGB", (width, height))
    new_pixels = new_image.load()

    # Map each pixel to closest user color (using Lab distance)
    for y in range(height):
        for x in range(width):
            pixel_rgb = pixels[x, y]

            # Find closest color from user's palette
            min_distance = float('inf')
            closest_color = list(user_palette.values())[0]

            for color_rgb in user_palette.values():
                distance = color_distance_lab(pixel_rgb, color_rgb)
                if distance < min_distance:
                    min_distance = distance
                    closest_color = color_rgb

            new_pixels[x, y] = closest_color

    return new_image

# ===== Auto-Suggest Colors from Image =====
def suggest_colors_from_image(image_path, max_suggested=10):
    """
    NEW APPROACH: Analyze ACTUAL colors in image, then match to palette.

    Old approach (WRONG):
        pixel → closest palette color → count frequencies
        Problem: Orange becomes gold, white gets filtered, "invents" colors

    New approach (CORRECT):
        image → extract actual dominant colors → match each to palette
        Result: Orange stays orange, white is detected, real colors used

    Args:
        image_path: Path to the image file
        max_suggested: Maximum number of colors to suggest

    Returns:
        List of suggested color names sorted by importance
    """
    # Load image
    img = Image.open(image_path).convert("RGB")

    # Resize for analysis (keep details, not too small)
    img.thumbnail((400, 400), Image.Resampling.LANCZOS)

    # === STEP 1: Extract ACTUAL dominant colors from image ===
    # Use PIL quantization to find the most common colors
    # This finds what colors ACTUALLY exist, not what we think should exist

    # Extract MANY colors to capture small but visible regions (eyes, highlights)
    # Then we'll match to palette and filter
    num_extract = 32  # Extract many colors to get small details like eyes

    try:
        # Quantize to find dominant colors
        quantized = img.quantize(colors=num_extract, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)

        # Get the palette (list of RGB values)
        palette_data = quantized.getpalette()

        # Count pixels per color index
        color_counts = quantized.getcolors(num_extract * 2)

        if not color_counts:
            # Fallback: just sample pixels
            color_counts = [(1, i) for i in range(num_extract)]

        # Build list of actual colors with their counts
        actual_colors = []
        for count, color_index in color_counts:
            r = palette_data[color_index * 3]
            g = palette_data[color_index * 3 + 1]
            b = palette_data[color_index * 3 + 2]
            actual_colors.append(((r, g, b), count))

    except Exception as e:
        print(f"⚠️ Quantization failed, using fallback: {e}")
        # Fallback: sample pixels directly
        pixels = list(img.getdata())
        from collections import Counter
        pixel_counts = Counter(pixels).most_common(num_extract)
        actual_colors = [(rgb, count) for rgb, count in pixel_counts]

    # === STEP 2: Match each actual color to closest palette color ===
    # This is the KEY difference: we're matching ACTUAL colors, not every pixel

    palette_matches = {}  # palette_name -> (total_count, actual_rgb_that_matched)

    for actual_rgb, count in actual_colors:
        # Find closest palette color for this ACTUAL color
        min_distance = float('inf')
        closest_name = None

        for name, palette_rgb in STANDARD_YARN_PALETTE.items():
            distance = color_distance_lab(actual_rgb, palette_rgb)
            if distance < min_distance:
                min_distance = distance
                closest_name = name

        if closest_name:
            if closest_name in palette_matches:
                # Add count to existing match
                old_count, _ = palette_matches[closest_name]
                palette_matches[closest_name] = (old_count + count, actual_rgb)
            else:
                palette_matches[closest_name] = (count, actual_rgb)

    # === STEP 3: Sort by count and return ===
    sorted_colors = sorted(palette_matches.items(), key=lambda x: x[1][0], reverse=True)

    # Return top colors (limit to max_suggested)
    return [name for name, (count, rgb) in sorted_colors[:max_suggested]]

# ===== Input Parser =====
def parse_input():
    """Parse the 4-line input format"""
    print("=== محول الصور إلى باترون كروشيه/حياكة ===\n")

    # Line 1: type
    line1 = "type 2"
    match = re.search(r'\d+', line1)
    pattern_type = int(match.group()) if match else 2
    is_knitting = (pattern_type == 1)

    # Line 2: image path
    line2 = r"test_images\HD-wallpaper-tweety-bird-cartoon-character.jpg"
    # Remove "image path" prefix and any quotes
    img_path = re.sub(r'^image path\s+', '', line2, flags=re.IGNORECASE).strip(' "\'')

    # Line 3: length
    line3 = "300"
    match = re.search(r'\d+', line3)
    longest_side = int(match.group()) if match else 250

    # === AUTO-SUGGEST COLORS ===
    print("🔍 تحليل الصورة...")
    suggested_colors = suggest_colors_from_image(img_path, max_suggested=12)

    print(f"\n✨ الألوان المقترحة ({len(suggested_colors)} لون):")
    print("   " + ", ".join(suggested_colors))

    # Line 4: User confirmation or reduction
    # Format: "yes" or a number (e.g., "8" to use only 8 colors)
    line4 = "yes"  # Hardcoded for now - can be input("هل لديك جميع هذه الألوان؟ (yes أو عدد الألوان): ")

    if line4.strip().lower() in ["yes", "نعم", "y"]:
        # User has all suggested colors
        user_colors = suggested_colors
        print(f"✅ استخدام جميع الألوان المقترحة ({len(user_colors)} لون)")
    else:
        # User wants to reduce color count
        try:
            requested_count = int(re.search(r'\d+', line4).group())
            user_colors = suggested_colors[:requested_count]
            print(f"✅ استخدام أول {requested_count} لون: {', '.join(user_colors)}")
        except:
            # Default to all if parsing fails
            user_colors = suggested_colors
            print(f"⚠️  استخدام جميع الألوان الافتراضية ({len(user_colors)} لون)")

    return img_path, is_knitting, longest_side, user_colors


# ===== Bug-Fix Helper Functions =====

def get_resize_filter(img, target_w, target_h):
    """
    Bug #1 Fix: Choose resizing filter based on image characteristics.
    - Pixel art / cartoon with few colors: NEAREST (hard edges, no blending)
    - Photography / natural illustration: LANCZOS (smooth gradients)
    """
    # Sample at small size to count unique colors quickly
    small = img.copy()
    small.thumbnail((200, 200), Image.Resampling.NEAREST)
    unique_colors = len(set(small.getdata()))

    # Pixel art heuristic: very few distinct colors
    if unique_colors < 64:
        return Image.Resampling.NEAREST

    # Severe downscaling with limited colors also benefits from NEAREST
    scale_factor = max(img.width / target_w, img.height / target_h)
    if scale_factor > 4 and unique_colors < 200:
        return Image.Resampling.NEAREST

    return Image.Resampling.LANCZOS


def sharpen_for_palette(img):
    """
    Bug #3B Fix: Boost contrast before palette mapping.
    Polarises ambiguous intermediate pixels toward black or white,
    preventing them from drifting to wrong palette colors (e.g. purple).
    """
    from PIL import ImageEnhance
    enhancer = ImageEnhance.Contrast(img)
    return enhancer.enhance(1.4)


def enhance_for_small_output(img, target_size):
    """
    Bug #4 Fix: Pre-process non-pixel-art images that will be heavily downscaled.
    Thickens outlines so fine features survive the size reduction.
    """
    from PIL import ImageFilter, ImageEnhance
    source_size = max(img.width, img.height)
    scale_factor = source_size / target_size

    if scale_factor < 3:
        return img  # mild downscale — no enhancement needed

    # Step 1: Edge enhancement — thickens outlines
    enhanced = img.filter(ImageFilter.EDGE_ENHANCE_MORE)

    # Step 2: Sharpen — recovers clarity lost by edge enhancement
    sharpener = ImageEnhance.Sharpness(enhanced)
    enhanced = sharpener.enhance(1.8)

    # Step 3: Contrast boost — pushes mid-tones toward black or white
    contraster = ImageEnhance.Contrast(enhanced)
    enhanced = contraster.enhance(1.3)

    return enhanced


def get_background_color(img, sample_size=3):
    """
    Bug #5 Fix: Detect background color by sampling image corners.
    Returns the most common colour found at the 8 border sample points.
    """
    from collections import Counter
    pixels = img.load()
    w, h = img.size
    corners = []
    for cx, cy in [
        (0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
        (w // 2, 0), (0, h // 2), (w - 1, h // 2), (w // 2, h - 1)
    ]:
        corners.append(pixels[cx, cy])
    return Counter(corners).most_common(1)[0][0]


def create_background_mask(img, bg_color, tolerance=15):
    """
    Bug #5 Fix: Create a boolean mask — True where pixel IS background.
    Uses Euclidean RGB distance to tolerate slight JPEG noise.
    """
    pixels = img.load()
    w, h = img.size
    br, bg_c, bb = bg_color
    mask = {}
    for y in range(h):
        for x in range(w):
            r, g, b = pixels[x, y]
            dist = math.sqrt((r - br) ** 2 + (g - bg_c) ** 2 + (b - bb) ** 2)
            mask[(x, y)] = dist < tolerance
    return mask


# ===== Main Processing Function =====
def process_image():
    """Main image processing pipeline"""

    # Parse input
    img_path, is_knitting, longest_side, user_colors = parse_input()

    # Validate file exists
    if not os.path.exists(img_path):
        print(f"❌ خطأ: الملف غير موجود - {img_path}")
        return

    print(f"\n📥 معالجة الصورة: {os.path.basename(img_path)}")
    print(f"🧶 النوع: {'حياكة' if is_knitting else 'كروشيه'}")
    print(f"📏 الحجم: {longest_side} غرزة")
    print(f"🎨 الألوان: {', '.join(user_colors)}\n")

    # Load image
    original_image = Image.open(img_path).convert("RGB")
    orig_width, orig_height = original_image.size

    # Calculate target dimensions
    if orig_width >= orig_height:
        new_width = longest_side
        new_height = int((orig_height / orig_width) * longest_side)
    else:
        new_height = longest_side
        new_width = int((orig_width / orig_height) * longest_side)

    # Apply knitting stretch if needed
    if is_knitting:
        new_height = int(new_height * 1.35)

    print(f"🔧 أبعاد الباترون: {new_width} × {new_height}")

    # === STEP 1: Resize the image ===
    # Bug #1: Use adaptive filter — NEAREST for cartoon/pixel-art, LANCZOS for photos
    from PIL import ImageFilter, ImageEnhance
    resize_filter = get_resize_filter(original_image, new_width, new_height)
    filter_name = "NEAREST" if resize_filter == Image.Resampling.NEAREST else "LANCZOS"
    print(f"⚙️  تصغير الصورة بفلتر {filter_name}...")

    # Bug #4: Edge enhancement for non-pixel-art before downscaling
    is_pixel_art = (resize_filter == Image.Resampling.NEAREST)
    if not is_pixel_art:
        original_image = enhance_for_small_output(original_image, longest_side)

    resized_image = original_image.resize((new_width, new_height), resize_filter)

    # === STEP 2: Smooth out JPEG artifacts and anti-aliasing ===
    # Bug #2: Size-adaptive smoothing — skip median filter at small output sizes
    MIN_SIZE_FOR_SMOOTHING = 120  # stitches
    if min(new_width, new_height) >= MIN_SIZE_FOR_SMOOTHING:
        print("🧹 تنعيم الصورة...")
        smoothed_image = resized_image.filter(ImageFilter.MedianFilter(size=3))
    else:
        print(f"⚠️ Smoothing skipped: output {new_width}×{new_height} too small — details preserved")
        smoothed_image = resized_image

    # === STEP 2.5: Background separation (Bug #5) ===
    import math as _math
    bg_color = get_background_color(smoothed_image)
    bg_mask = create_background_mask(smoothed_image, bg_color)

    # === STEP 3: Contrast boost before palette mapping (Bug #3B) ===
    contrast_image = sharpen_for_palette(smoothed_image)

    # === STEP 4: Map to user's yarn palette ===
    print("🎨 تطبيق الألوان المتاحة...")
    final_image = map_to_user_palette(contrast_image, user_colors)

    # === STEP 4.5: Restore background pixels to white (Bug #5) ===
    final_pixels = final_image.load()
    white_rgb = STANDARD_YARN_PALETTE.get("أبيض", (255, 255, 255))
    for (x, y), is_bg in bg_mask.items():
        if is_bg:
            final_pixels[x, y] = white_rgb

    # === Extract color palette ===
    colors = final_image.getcolors(new_width * new_height)
    if not colors:
        print("❌ خطأ: لم يتم العثور على ألوان")
        return

    # Sort by frequency (most common first)
    colors.sort(key=lambda x: x[0], reverse=True)

    # Create color map: RGB -> (color_id, color_name, count)
    color_map = {}
    print("\n🎨 الألوان المستخدمة:")

    # Build reverse lookup from STANDARD_YARN_PALETTE
    rgb_to_name = {rgb: name for name, rgb in STANDARD_YARN_PALETTE.items()}

    for i, (count, rgb) in enumerate(colors):
        color_id = i + 1
        # Direct lookup from standard palette (exact match!)
        color_name = rgb_to_name.get(rgb, f"لون مخصص RGB{rgb}")
        color_map[rgb] = (color_id, color_name, count)
        print(f"  {color_id}. {color_name} - {count} غرزة - RGB{rgb}")

    # === Generate Grid Image ===
    print("\n📐 رسم الشبكة...")
    grid_width = new_width * CELL_SIZE
    grid_height = new_height * CELL_SIZE

    grid_image = final_image.resize((grid_width, grid_height), Image.Resampling.NEAREST)
    draw = ImageDraw.Draw(grid_image)

    # Draw grid lines
    grid_color = (200, 200, 200)
    for x in range(0, grid_width, CELL_SIZE):
        draw.line([(x, 0), (x, grid_height)], fill=grid_color, width=1)
    for y in range(0, grid_height, CELL_SIZE):
        draw.line([(0, y), (grid_width, y)], fill=grid_color, width=1)

    # Draw border
    draw.rectangle([(0, 0), (grid_width - 1, grid_height - 1)], outline="black", width=3)

    grid_image.save("pattern_grid.png")
    print("✅ تم حفظ: pattern_grid.png")

    # === Generate Color Palette Image ===
    print("🎨 إنشاء جدول الألوان...")
    num_colors = len(colors)
    palette_rows = math.ceil(math.sqrt(num_colors))
    palette_cols = math.ceil(num_colors / palette_rows)

    cell_width = 300
    cell_height = 80

    palette_image = Image.new("RGB", (palette_cols * cell_width, palette_rows * cell_height), "white")
    palette_draw = ImageDraw.Draw(palette_image)


    try:
        if FONT_PATH and os.path.exists(FONT_PATH):
            font = ImageFont.truetype(FONT_PATH, 20)
            print(f"✅ Using font: {FONT_PATH}")
        else:
            print(f"⚠️ Arabic font not found, using default (Arabic may not display correctly)")
            font = ImageFont.load_default()
    except Exception as e:
        print(f"⚠️ Font loading error: {e}, using default")
        font = ImageFont.load_default()

    for i, (count, rgb) in enumerate(colors):
        color_id, color_name, _ = color_map[rgb]

        row = i // palette_cols
        col = i % palette_cols
        x_base = col * cell_width
        y_base = row * cell_height

        # Draw color swatch
        palette_draw.rectangle(
            [x_base + 10, y_base + 10, x_base + 50, y_base + 50],
            fill=rgb,
            outline="black",
            width=2
        )

        # Draw label
        label = f"رقم {color_id} | {color_name}\nعدد الغرز: {count}"
        label_arabic = text_arabic(label)
        palette_draw.text((x_base + 60, y_base + 20), label_arabic, fill="black", font=font)

    palette_image.save("pattern_colors.png")
    print("✅ تم حفظ: pattern_colors.png")

    # === Generate Row-by-Row Text Instructions ===
    print("\n📝 تعليمات الصفوف:\n")

    pixels = final_image.load()

    for row in range(new_height):
        row_num = row + 1
        row_data = []

        # Read pixels for this row
        for col in range(new_width):
            rgb = pixels[col, row]
            row_data.append(rgb)

        # Reverse even rows (zig-zag pattern for knitting/crochet)
        if row_num % 2 == 0:
            row_data = row_data[::-1]

        # Build instruction string
        instructions = []
        current_color = None
        current_count = 0

        for rgb in row_data:
            if rgb == current_color:
                current_count += 1
            else:
                if current_color is not None:
                    color_id, color_name, _ = color_map[current_color]
                    instructions.append(f"{current_count}×{color_name}")
                current_color = rgb
                current_count = 1

        # Add last segment
        if current_color is not None:
            color_id, color_name, _ = color_map[current_color]
            instructions.append(f"{current_count}×{color_name}")

        # Print row instruction
        instruction_text = f"صف {row_num}: " + " + ".join(instructions)
        print(text_arabic(instruction_text))

    print("\n✅ اكتمل التحويل!")
    print(f"📊 إجمالي: {new_height} صف × {new_width} غرزة = {new_width * new_height} غرزة")

# ===== Entry Point =====
if __name__ == "__main__":
    try:
        process_image()
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        import traceback

        traceback.print_exc()
