"""
Composite Image Creator - COMPLETE REWRITE
Simple, clear logic for step-by-step visual guides
"""

from PIL import Image, ImageDraw, ImageFont
import os

class CompositeImageCreator:
    """Creates visual guides for crochet steps"""
    
    COMPOSITE_SIZE = (800, 900)  # Width x Height
    REF_SIZE = (150, 150)  # Reference image size
    GRID_CELL_SIZE = 20  # Grid cells are 20x20 pixels
    
    def __init__(self, grid_image, original_image, pattern_grid, pattern_image=None):
        """
        Args:
            grid_image: PIL Image of the grid pattern (with colors and grid lines)  
            original_image: PIL Image of the original photo
            pattern_grid: 2D array of (r,g,b) tuples representing the pattern
            pattern_image: PIL Image of pattern WITHOUT grid lines (for zooming)
        """
        self.grid_image = grid_image
        self.original_image = original_image
        self.pattern_grid = pattern_grid
        
        # Use pattern_image for zooming if provided, otherwise fall back to grid
        self.pattern_image = pattern_image if pattern_image is not None else grid_image
        
        self.height = len(pattern_grid)  # Number of rows
        self.width = len(pattern_grid[0]) if pattern_grid else 0  # Number of columns
        
        # Load font
        try:
            from process import FONT_PATH
            if FONT_PATH and os.path.exists(FONT_PATH):
                self.font_large = ImageFont.truetype(FONT_PATH, 28)
                self.font_medium = ImageFont.truetype(FONT_PATH, 22)
            else:
                self.font_large = ImageFont.load_default()
                self.font_medium = ImageFont.load_default()
        except Exception as e:
            self.font_large = ImageFont.load_default()
            self.font_medium = ImageFont.load_default()
    
    def create_step_image(self, step):
        """
        Create composite image for a step.
        
        Layout:
        - Top: Reference image (150x150) with red box showing zoom area
        - Middle: Arabic text (step info)
        - Bottom: Zoomed grid section (large, fills most of space)
        
        Args:
            step: Dictionary with row, start_col, end_col, color_name, instruction_ar
        """
        # Create canvas
        canvas = Image.new('RGB', self.COMPOSITE_SIZE, (245, 245, 245))  # Light grey background
        draw = ImageDraw.Draw(canvas)
        
        # === 1. REFERENCE IMAGE WITH POSITION BOX ===
        ref_img = self._create_reference_with_box(step)
        canvas.paste(ref_img, (325, 20))  # Centered horizontally
        
        # === 2. STEP TEXT ===
        from process import text_arabic
        
        # Header text
        header = f"📍 الصف {step['row']} - الخطوة {step['step_number']}"
        header_ar = text_arabic(header)
        bbox = draw.textbbox((0, 0), header_ar, font=self.font_large)
        text_w = bbox[2] - bbox[0]
        draw.text((400 - text_w//2, 190), header_ar, fill='black', font=self.font_large)
        
        # Instruction text
        instr_ar = text_arabic(step['instruction_ar'])
        bbox = draw.textbbox((0, 0), instr_ar, font=self.font_medium)
        text_w = bbox[2] - bbox[0]
        draw.text((400 - text_w//2, 220), instr_ar, fill=(50, 50, 50), font=self.font_medium)
        
        # ===  3. ZOOMED GRID ===
        zoomed_grid = self._create_zoomed_grid_v2(step)
        
        # Center it horizontally, place at y=260
        paste_x = (800 - zoomed_grid.width) // 2
        canvas.paste(zoomed_grid, (paste_x, 260))
        
        return canvas
    
    def _create_reference_with_box(self, step):
        """
        Create reference image with red box showing which area is zoomed.
        
        The red box should match the exact rows being shown in the zoomed section.
        """
        # Resize original image to fit
        ref = self.original_image.copy()
        ref.thumbnail(self.REF_SIZE, Image.Resampling.LANCZOS)
        ref = ref.convert('RGB')
        
        draw = ImageDraw.Draw(ref)
        
        # Calculate which rows we'll show in zoom (we show ±25 rows around current)
        current_row = step['row'] - 1  # 0-indexed
        
        # Show 50 rows total centered on current row
        zoom_rows = 50
        half_zoom = zoom_rows // 2
        
        min_row = max(0, current_row - half_zoom)
        max_row = min(self.height, min_row + zoom_rows)
        
        # Adjust if we hit bottom
        if max_row == self.height:
            min_row = max(0, max_row - zoom_rows)
        
        # Draw red box showing these rows
        # Convert row positions to pixel positions on reference image
        box_top = int((min_row / self.height) * ref.height)
        box_bottom = int((max_row / self.height) * ref.height)
        
        draw.rectangle(
            [0, box_top, ref.width, box_bottom],
            outline='red',
            width=4
        )
        
        # Border around entire reference
        draw.rectangle(
            [0, 0, ref.width-1, ref.height-1],
            outline='black',
            width=2
        )
        
        return ref
    
    def _create_zoomed_grid_v2(self, step):
        """
        Create zoomed grid section - SIMPLE VERSION.
        
        Strategy:
        1. Show 50 rows × 40 columns centered on current step
        2. Crop that section from grid_image
        3. Scale up to fill 760x600 space
        4. Draw yellow box on current step cells
        """
        current_row = step['row'] - 1  # 0-indexed
        
        # CRITICAL: Convert reversed coordinates to original for LEFT direction
        step_start_col = step['start_col']
        step_end_col = step['end_col']
        
        if step.get('direction') == 'left':
            # These are reversed coordinates - convert to original
            step_start_col = self.width - step['end_col']
            step_end_col = self.width - step['start_col']
            print(f"DEBUG V2: LEFT zoom - converted {step['start_col']}-{step['end_col']} to {step_start_col}-{step_end_col}")
        
        mid_col = (step_start_col + step_end_col) // 2
        
        # Decide how much to show
        zoom_rows = min(50, self.height)
        zoom_cols = min(40, self.width)
        
        # Center on current position
        half_rows = zoom_rows // 2
        half_cols = zoom_cols // 2
        
        # Calculate bounds
        min_row = max(0, current_row - half_rows)
        max_row = min(self.height, min_row + zoom_rows)
        
        # Adjust if hit bottom
        if max_row == self.height:
            min_row = max(0, max_row - zoom_rows)
        
        min_col = max(0, mid_col - half_cols)
        max_col = min(self.width, min_col + zoom_cols)
        
        # Adjust if hit right edge
        if max_col == self.width:
            min_col = max(0, max_col - zoom_cols)
        
        print(f"DEBUG V2: Row {step['row']}, showing rows {min_row}-{max_row}, cols {min_col}-{max_col}")
        
        # ==== CROP FROM PATTERN IMAGE (no grid lines) ====
        # Pattern image is 1 pixel per cell
        crop_box = (
            min_col,  # Pattern is 1px per cell
            min_row,
            max_col,
            max_row
        )
        
        # Crop the pattern (color cells only, no grid)
        pattern_section = self.pattern_image.crop(crop_box)
        print(f"DEBUG V2: Cropped pattern size: {pattern_section.size}")
        
        # Scale up to make cells visible (20px per cell minimum)
        cell_size_scaled = 20  # Each cell becomes 20x20 pixels
        scaled_size = (
            pattern_section.width * cell_size_scaled,
            pattern_section.height * cell_size_scaled
        )
        
        zoomed = pattern_section.resize(scaled_size, Image.Resampling.NEAREST)
        print(f"DEBUG V2: Scaled to: {zoomed.size}")
        
        # Now add grid lines on the scaled image
        draw_grid = ImageDraw.Draw(zoomed)
        grid_color = (200, 200, 200)
        
        # Vertical lines
        for x in range(0, zoomed.width, cell_size_scaled):
            draw_grid.line([(x, 0), (x, zoomed.height)], fill=grid_color, width=1)
        
        # Horizontal lines  
        for y in range(0, zoomed.height, cell_size_scaled):
            draw_grid.line([(0, y), (zoomed.width, y)], fill=grid_color, width=1)
        
        # Draw yellow highlight on current step
        zoomed_rgba = zoomed.convert('RGBA')
        overlay = Image.new('RGBA', zoomed_rgba.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Calculate where current step is in the zoomed view
        local_row = current_row - min_row
        
        # Use the converted coordinates (already fixed for LEFT direction above)
        local_start_col = step_start_col - min_col
        local_end_col = step_end_col - min_col
        
        
        # Always draw yellow highlight (clamp to visible area)
        # Even if stitch extends beyond zoom, show the visible part
        
        # Calculate pixel positions (using cell_size_scaled, not scale!)
        y = local_row * cell_size_scaled
        
        # Clamp x coordinates to visible area
        x_start = max(0, local_start_col * cell_size_scaled)
        x_end = min(local_end_col * cell_size_scaled, (max_col - min_col) * cell_size_scaled)
        cell_h = cell_size_scaled
        
        # Only draw if there's something visible (row is visible and there's width)
        if (0 <= local_row < (max_row - min_row) and x_end > x_start):
            print(f"DEBUG V2: Yellow box at ({x_start:.0f}, {y:.0f}), size ({x_end-x_start:.0f}×{cell_h:.0f})")
            
            # Draw thick yellow outline
            draw.rectangle(
                [x_start, y, x_end, y + cell_h],
                outline='yellow',
                width=6  # Thick and visible!
            )
        else:
            print(f"DEBUG V2: Step not in zoomed view (row {local_row}, x_start {x_start}, x_end {x_end})")
        
        # Composite and return
        result = Image.alpha_composite(zoomed_rgba, overlay)
        return result.convert('RGB')
