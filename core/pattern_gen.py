"""
Pattern Generator - Wrapper around process.py

This module provides a clean interface to the existing pattern generation logic.
Keeps the core pattern algorithm separate from bot-specific code.
"""

import sys
import os
from PIL import Image

# Import from parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from process import (
    suggest_colors_from_image,
    map_to_user_palette,
    STANDARD_YARN_PALETTE,
    CELL_SIZE
)


class PatternGenerator:
    """Manages pattern generation workflow"""
    
    def __init__(self, image_path, size, is_knitting=False):
        """
        Initialize pattern generator.
        
        Args:
            image_path (str): Path to the input image
            size (int): Longest side in stitches
            is_knitting (bool): Always False for crochet
        """
        self.image_path = image_path
        self.size = size
        self.is_knitting = is_knitting
        
        self.suggested_colors = []
        self.pattern_grid = None
        self.pattern_image = None
        self.palette_image = None
        self.actual_size = None  # (width, height) in stitches
        
    def analyze_colors(self, max_colors=10):
        """
        Analyze image and suggest colors from standard palette.
        
        Args:
            max_colors (int): Maximum colors to suggest
            
        Returns:
            list: Color names from STANDARD_YARN_PALETTE
        """
        self.suggested_colors = suggest_colors_from_image(
            self.image_path,
            max_suggested=max_colors
        )
        return self.suggested_colors
    
    def generate_pattern(self, user_colors=None):
        """
        Generate the pattern grid and images.
        
        Args:
            user_colors (list): Optional list of color names to use.
                               If None, uses suggested colors.
        
        Returns:
            dict: {
                'grid_image': PIL.Image,
                'palette_image': PIL.Image,
                'size': (width, height),
                'colors': list of color names,
                'total_stitches': int
            }
        """
        if user_colors is None:
            user_colors = self.suggested_colors
        
        if not user_colors:
            raise ValueError("No colors specified. Run analyze_colors() first or provide user_colors.")
        
        # Load and resize image
        img = Image.open(self.image_path).convert("RGB")
        
        # Calculate dimensions maintaining aspect ratio
        width, height = img.size
        if width > height:
            new_width = self.size
            new_height = int((height / width) * self.size)
        else:
            new_height = self.size
            new_width = int((width / height) * self.size)
        
        # Enforce minimum dimensions to prevent Telegram's Photo_invalid_dimensions error
        # Telegram requires at least 10 pixels on each side
        MIN_DIMENSION = 10
        if new_width < MIN_DIMENSION:
            new_width = MIN_DIMENSION
        if new_height < MIN_DIMENSION:
            new_height = MIN_DIMENSION
        
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.actual_size = (new_width, new_height)
        
        # Apply median filter for smoothing
        from PIL import ImageFilter
        img = img.filter(ImageFilter.MedianFilter(size=3))
        
        # Map to user's color palette
        self.pattern_image = map_to_user_palette(img, user_colors)
        
        # Create grid visualization
        self.grid_image = self._create_grid_pattern(user_colors)
        
        # Create color palette image
        self.palette_image = self._create_color_palette_image(user_colors)
        
        # Extract pattern data as 2D array
        self.pattern_grid = self._extract_pattern_data()
        
        total_stitches = new_width * new_height
        
        return {
            'grid_image': self.grid_image,
            'palette_image': self.palette_image,
            'pattern_image': self.pattern_image,  # Add this!
            'size': self.actual_size,
            'colors': user_colors,
            'total_stitches': total_stitches,
            'pattern_data': self.pattern_grid
        }
    
    def _create_grid_pattern(self, colors):
        """Create grid visualization"""
        from PIL import ImageDraw
        
        width, height = self.pattern_image.size
        grid_width = width * CELL_SIZE
        grid_height = height * CELL_SIZE
        
        # Ensure minimum dimensions for Telegram (at least 100x100)
        grid_width = max(grid_width, 100)
        grid_height = max(grid_height, 100)
        
        # CRITICAL: Telegram requires width + height < 10000 pixels
        # If the grid is too large, scale it down proportionally
        MAX_TELEGRAM_SUM = 9900  # Leave some margin
        if grid_width + grid_height > MAX_TELEGRAM_SUM:
            scale_factor = MAX_TELEGRAM_SUM / (grid_width + grid_height)
            grid_width = int(grid_width * scale_factor)
            grid_height = int(grid_height * scale_factor)
        
        grid_image = self.pattern_image.resize((grid_width, grid_height), Image.Resampling.NEAREST)
        draw = ImageDraw.Draw(grid_image)
        
        # Draw grid lines
        grid_color = (200, 200, 200)
        for x in range(0, grid_width, CELL_SIZE):
            draw.line([(x, 0), (x, grid_height)], fill=grid_color, width=1)
        for y in range(0, grid_height, CELL_SIZE):
            draw.line([(0, y), (grid_width, y)], fill=grid_color, width=1)
        
        # Draw border
        draw.rectangle([(0, 0), (grid_width - 1, grid_height - 1)], outline="black", width=3)
        
        return grid_image
    
    def _create_color_palette_image(self, colors):
        """Create color palette visualization"""
        from PIL import ImageDraw, ImageFont
        import math
        
        width, height = self.pattern_image.size
        
        # Get color counts
        color_counts = self.pattern_image.getcolors(width * height)
        if not color_counts:
            # Return minimum size palette (Telegram requirement)
            return Image.new('RGB', (300, 80), 'white')
        
        color_counts.sort(key=lambda x: x[0], reverse=True)
        
        # Create color map
        rgb_to_name = {rgb: name for name, rgb in STANDARD_YARN_PALETTE.items()}
        color_data = []
        for count, rgb in color_counts:
            color_name = rgb_to_name.get(rgb, f"RGB{rgb}")
            color_data.append((rgb, color_name, count))
        
        # Layout
        num_colors = len(color_data)
        palette_rows = math.ceil(math.sqrt(num_colors))
        palette_cols = math.ceil(num_colors / palette_rows)
        
        cell_width = 300
        cell_height = 80
        
        # Calculate dimensions
        img_width = palette_cols * cell_width
        img_height = palette_rows * cell_height
        
        # Ensure minimum dimensions for Telegram (at least 10x10, but we use 300x80 minimum)
        img_width = max(img_width, 300)
        img_height = max(img_height, 80)
        
        palette_image = Image.new("RGB", (img_width, img_height), "white")
        draw = ImageDraw.Draw(palette_image)
        
        
        try:
            from process import FONT_PATH
            if FONT_PATH and os.path.exists(FONT_PATH):
                font = ImageFont.truetype(FONT_PATH, 20)
            else:
                font = ImageFont.load_default()
        except Exception as e:
            font = ImageFont.load_default()
        
        for i, (rgb, name, count) in enumerate(color_data):
            row = i // palette_cols
            col = i % palette_cols
            x_base = col * cell_width
            y_base = row * cell_height
            
            # Draw color swatch
            draw.rectangle(
                [x_base + 10, y_base + 10, x_base + 50, y_base + 50],
                fill=rgb,
                outline="black",
                width=2
            )
            
            # Draw label
            label = f"{name}\nعدد الغرز: {count}"
            from process import text_arabic
            label_arabic = text_arabic(label)
            draw.text((x_base + 60, y_base + 20), label_arabic, fill="black", font=font)
        
        return palette_image
    
    def _extract_pattern_data(self):
        """
        Extract 2D array of color names from pattern image.
        
        Returns:
            list of lists: pattern_grid[row][col] = color_name
        """
        if self.pattern_image is None:
            return None
        
        width, height = self.pattern_image.size
        pixels = self.pattern_image.load()
        
        # Build reverse lookup: RGB -> color name
        rgb_to_name = {}
        for name, rgb in STANDARD_YARN_PALETTE.items():
            rgb_to_name[rgb] = name
        
        # Extract grid
        grid = []
        for y in range(height):
            row = []
            for x in range(width):
                pixel_rgb = pixels[x, y]
                color_name = rgb_to_name.get(pixel_rgb, "أسود")  # Default to black
                row.append(color_name)
            grid.append(row)
        
        return grid
    
    def save_outputs(self, grid_path, palette_path):
        """
        Save generated images to files.
        
        Args:
            grid_path (str): Path to save grid pattern
            palette_path (str): Path to save color palette
        """
        if self.grid_image is None or self.palette_image is None:
            raise ValueError("No pattern generated yet. Run generate_pattern() first.")
        
        self.grid_image.save(grid_path)
        self.palette_image.save(palette_path)
        
        return grid_path, palette_path


# Testing
if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_image = sys.argv[1]
        
        print("🎨 Creating pattern generator...")
        gen = PatternGenerator(test_image, size=150)
        
        print("🔍 Analyzing colors...")
        colors = gen.analyze_colors()
        print(f"  Found {len(colors)} colors: {', '.join(colors)}")
        
        print("⏳ Generating pattern...")
        result = gen.generate_pattern()
        
        print(f"✅ Pattern ready!")
        print(f"  Size: {result['size'][0]}×{result['size'][1]} = {result['total_stitches']} stitches")
        print(f"  Colors: {len(result['colors'])}")
        
        gen.save_outputs("test_grid.png", "test_palette.png")
        print("  Saved: test_grid.png, test_palette.png")
