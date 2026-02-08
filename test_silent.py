"""Silent test to debug the image dimension issue - no print statements with emojis"""
import sys
import os

# Suppress stdout to avoid encoding issues
class SilentWriter:
    def write(self, x): pass
    def flush(self): pass

# Temporarily redirect stdout to capture the issue
old_stdout = sys.stdout
sys.stdout = SilentWriter()

try:
    sys.path.insert(0, '.')
    from core.pattern_gen import PatternGenerator
    from PIL import Image
    
    # Test the image
    img_path = 'IMG_20260121_100331_742.jpg'
    
    # Open and check original dimensions
    original = Image.open(img_path)
    orig_size = original.size
    orig_mode = original.mode
    
    # Test pattern generation
    gen = PatternGenerator(img_path, size=150)
    colors = gen.analyze_colors(max_colors=10)
    result = gen.generate_pattern(user_colors=colors)
    
    grid_size = result["grid_image"].size
    palette_size = result["palette_image"].size
    pattern_size = result["size"]
    
    # Save outputs
    gen.save_outputs('test_grid_debug.png', 'test_palette_debug.png')
    
    success = True
    error_msg = None
    
except Exception as e:
    success = False
    error_msg = str(e)
    import traceback
    error_trace = traceback.format_exc()
    
finally:
    sys.stdout = old_stdout

# Now print results (simple ASCII only)
print("=" * 50)
print("IMAGE DIMENSION DEBUG REPORT")
print("=" * 50)

if success:
    print(f"Original image: {orig_size[0]}x{orig_size[1]} ({orig_mode})")
    print(f"Pattern size: {pattern_size[0]}x{pattern_size[1]} stitches")
    print(f"Grid image: {grid_size[0]}x{grid_size[1]} pixels")
    print(f"Palette image: {palette_size[0]}x{palette_size[1]} pixels")
    print(f"Colors found: {len(colors)}")
    print()
    
    # Check Telegram limits
    print("Telegram API Checks:")
    if grid_size[0] < 100 or grid_size[1] < 100:
        print(f"  WARNING: Grid too small! Min is 100x100")
    else:
        print(f"  Grid dimensions OK")
    
    if grid_size[0] > 10000 or grid_size[1] > 10000:
        print(f"  WARNING: Grid too large! Max is 10000x10000")
    else:
        print(f"  Grid size within limits")
        
    if grid_size[0] + grid_size[1] > 10000:
        print(f"  WARNING: Sum of dimensions > 10000!")
    
    print()
    print("Test files saved: test_grid_debug.png, test_palette_debug.png")
else:
    print(f"ERROR: {error_msg}")
    print()
    print("Full traceback:")
    print(error_trace)
