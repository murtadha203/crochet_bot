"""Quick test to debug the image dimension issue"""
import sys
sys.path.insert(0, '.')
from core.pattern_gen import PatternGenerator

print("Testing image: IMG_20260121_100331_742.jpg")
gen = PatternGenerator('IMG_20260121_100331_742.jpg', size=150)

print('Analyzing colors...')
colors = gen.analyze_colors(max_colors=10)
print(f'Colors found: {len(colors)}')

print('Generating pattern...')
result = gen.generate_pattern(user_colors=colors)

print(f'Pattern size: {result["size"]}')
print(f'Grid image size: {result["grid_image"].size}')
print(f'Palette image size: {result["palette_image"].size}')

# Check if dimensions meet Telegram requirements
grid_w, grid_h = result["grid_image"].size
if grid_w < 100 or grid_h < 100:
    print(f"⚠️ WARNING: Grid image too small! {grid_w}x{grid_h}")
else:
    print(f"✅ Grid dimensions OK: {grid_w}x{grid_h}")

print('Saving test outputs...')
gen.save_outputs('test_grid_debug.png', 'test_palette_debug.png')
print('Done! Check test_grid_debug.png and test_palette_debug.png')
