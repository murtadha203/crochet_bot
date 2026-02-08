#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test THREE different approaches to see which works on PythonAnywhere
"""

from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
import os

def text_arabic_v1_RAW(text):
    """Version 1: NO processing at all - raw text"""
    return text

def text_arabic_v2_RESHAPE_ONLY(text):
    """Version 2: Only reshape, no BiDi"""
    return arabic_reshaper.reshape(text)

def text_arabic_v3_FULL(text):
    """Version 3: Reshape + BiDi (current approach)"""
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)

# Create test image
img = Image.new('RGB', (900, 300), 'white')
draw = ImageDraw.Draw(img)

# Load font
try:
    if os.path.exists("fonts/Arial.ttf"):
        font = ImageFont.truetype("fonts/Arial.ttf", 24)
    else:
        font = ImageFont.load_default()
except:
    font = ImageFont.load_default()

# Test with mixed content (Arabic + numbers)
test_text = "الصف 2 - الخطوة 73"

y = 20
draw.text((10, y), "TEST: الصف 2 - الخطوة 73", fill='black', font=font)
y += 40

# Test each version
v1 = text_arabic_v1_RAW(test_text)
draw.text((10, y), f"V1 (RAW): {v1}", fill='red', font=font)
y += 40

v2 = text_arabic_v2_RESHAPE_ONLY(test_text)
draw.text((10, y), f"V2 (RESHAPE): {v2}", fill='blue', font=font)
y += 40

v3 = text_arabic_v3_FULL(test_text)
draw.text((10, y), f"V3 (FULL): {v3}", fill='green', font=font)
y += 60

# Show what they are
print(f"Original:  {repr(test_text)}")
print(f"V1 (RAW):  {repr(v1)}")
print(f"V2 (RESHAPE): {repr(v2)}")
print(f"V3 (FULL): {repr(v3)}")

img.save("arabic_comparison_test.png")
print("\n✅ Saved: arabic_comparison_test.png")
print("\nCheck which version looks correct!")
print("- V1 (RED) = raw, no processing")
print("- V2 (BLUE) = reshaped only")  
print("- V3 (GREEN) = reshaped + BiDi")
