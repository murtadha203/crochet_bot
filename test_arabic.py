#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Arabic Text Test Script
Tests if arabic_reshaper and python-bidi are working correctly
"""

import sys

def test_arabic_libraries():
    """Test if Arabic text processing libraries are working"""
    
    print("=" * 60)
    print("🧪 Arabic Text Processing Test")
    print("=" * 60)
    
    # Test 1: Check if libraries are installed
    print("\n📦 Test 1: Checking library installation...")
    
    try:
        import arabic_reshaper
        print("   ✅ arabic_reshaper is installed")
        print(f"      Version: {arabic_reshaper.__version__ if hasattr(arabic_reshaper, '__version__') else 'unknown'}")
    except ImportError as e:
        print(f"   ❌ arabic_reshaper NOT installed: {e}")
        return False
    
    try:
        from bidi.algorithm import get_display
        import bidi
        print("   ✅ python-bidi is installed")
        print(f"      Version: {bidi.VERSION if hasattr(bidi, 'VERSION') else 'unknown'}")
    except ImportError as e:
        print(f"   ❌ python-bidi NOT installed: {e}")
        return False
    
    # Test 2: Check Python version
    print(f"\n🐍 Test 2: Python version")
    print(f"   Version: {sys.version}")
    
    # Test 3: Test Arabic text processing
    print("\n📝 Test 3: Testing Arabic text processing...")
    
    test_texts = [
        "أبيض",
        "أحمر",
        "كروشيه",
        "الصف 1",
        "عدد الغرز: 225"
    ]
    
    for original_text in test_texts:
        try:
            # Process the text
            reshaped = arabic_reshaper.reshape(original_text)
            final = get_display(reshaped)
            
            print(f"\n   Original:  {original_text}")
            print(f"   Reshaped:  {reshaped}")
            print(f"   Final:     {final}")
            print(f"   Status: ✅ Processed successfully")
            
        except Exception as e:
            print(f"\n   Original:  {original_text}")
            print(f"   Status: ❌ Failed - {e}")
            return False
    
    # Test 4: Check font availability
    print("\n🔤 Test 4: Checking font availability...")
    
    import os
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/ttf-dejavu/DejaVuSans.ttf",  # Alternative DejaVu location
        "arial.ttf"
    ]
    
    found_fonts = []
    for font_path in font_paths:
        if os.path.exists(font_path):
            print(f"   ✅ Found: {font_path}")
            found_fonts.append(font_path)
        else:
            print(f"   ❌ Not found: {font_path}")
    
    if found_fonts:
        print(f"\n   ✅ {len(found_fonts)} Arabic-compatible font(s) available")
    else:
        print("\n   ⚠️  No fonts found - will use default (may not support Arabic)")
    
    # Test 5: Try to use Pillow with font
    print("\n🖼️ Test 5: Testing PIL/Pillow with Arabic text...")
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a test image
        img = Image.new('RGB', (300, 80), 'white')
        draw = ImageDraw.Draw(img)
        
        # Try to load a font
        font = None
        if found_fonts:
            try:
                font = ImageFont.truetype(found_fonts[0], 20)
                print(f"   ✅ Loaded font: {found_fonts[0]}")
            except Exception as e:
                print(f"   ⚠️  Font loading failed: {e}")
                font = ImageFont.load_default()
                print(f"   Using default font")
        else:
            font = ImageFont.load_default()
            print(f"   Using default font (no TrueType fonts found)")
        
        # Draw Arabic text
        test_text = "كروشيه"
        processed_text = get_display(arabic_reshaper.reshape(test_text))
        draw.text((10, 20), processed_text, fill='black', font=font)
        
        # Save test image
        output_path = "arabic_test.png"
        img.save(output_path)
        print(f"   ✅ Test image saved to: {output_path}")
        print(f"   Open this image to verify Arabic text displays correctly")
        
    except Exception as e:
        print(f"   ❌ Pillow test failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nIf Arabic text still appears wrong in your bot:")
    print("1. Make sure you uploaded ALL code files to PythonAnywhere")
    print("2. Restart your bot after updating requirements.txt")
    print("3. Check the bot logs for error messages")
    print("4. Open 'arabic_test.png' to verify the text looks correct")
    
    return True

if __name__ == "__main__":
    success = test_arabic_libraries()
    sys.exit(0 if success else 1)
