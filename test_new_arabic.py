#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test the NEW Arabic rendering approach for PIL images
"""

from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
import os

def text_arabic_NEW(text):
    """New approach: reshape + reverse"""
    reshaped = arabic_reshaper.reshape(text)
    return reshaped[::-1]

# Create test image
img = Image.new('RGB', (400, 200), 'white')
draw = ImageDraw.Draw(img)

# Try to load font
try:
    if os.path.exists("fonts/Arial.ttf"):
        font = ImageFont.truetype("fonts/Arial.ttf", 30)
    else:
        font = ImageFont.load_default()
except:
    font = ImageFont.load_default()

# Test Arabic words
test_words = [
    "بيضاء",
    "برتقالي غامق", 
    "بني",
    "ذهبي",
    "عدد الغرز: 225"
]

y_pos = 20
for word in test_words:
    processed = text_arabic_NEW(word)
    
    # Show both
    draw.text((10, y_pos), f"Original: {word}", fill='black', font=font)
    draw.text((10, y_pos + 35), f"Fixed: {processed}", fill='blue', font=font)
    
    y_pos += 80

# Save
img.save("arabic_test_NEW.png")
print("✅ Saved: arabic_test_NEW.png")
print("\nCheck this image - the BLUE text should show correct Arabic!")
print("- Connected letters ✅")
print("- Right-to-left direction ✅")
