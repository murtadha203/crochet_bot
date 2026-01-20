"""
Step Generator - Converts pattern grid into step-by-step crochet instructions

This is the heart of the step-by-step mode. It analyzes the pattern grid
and breaks it down into actionable instructions: "X stitches of color Y".
"""

from process import STANDARD_YARN_PALETTE


class StepGenerator:
    """Generates row-by-step crochet instructions from pattern grid"""
    
    def __init__(self, pattern_grid, color_names):
        """
        Initialize step generator.
        
        Args:
            pattern_grid (list of lists): 2D array pattern_grid[row][col] = color_name
            color_names (list): List of color names used in pattern
        """
        self.pattern_grid = pattern_grid
        self.color_names = color_names
        self.height = len(pattern_grid)
        self.width = len(pattern_grid[0]) if pattern_grid else 0
        
        self.steps = []
        self._generate_steps()
    
    def _generate_steps(self):
        """
        Convert pattern grid into step-by-step instructions.
        Groups consecutive cells of same color into single steps.
        """
        step_num = 1
        
        for row_idx, row in enumerate(self.pattern_grid):
            # Crochet alternates direction: odd rows go right, even rows go left
            # For simplicity in MVP, we'll always go right (user can reverse mentally)
            direction = 'right' if row_idx % 2 == 0 else 'left'
            
            # If going left, reverse the row for processing
            if direction == 'left':
                row = list(reversed(row))
            
            # Group consecutive same-color cells
            current_color = row[0]
            start_col = 0
            count = 1
            
            for col_idx in range(1, len(row)):
                if row[col_idx] == current_color:
                    count += 1
                else:
                    # Save current group as a step
                    self.steps.append(self._create_step(
                        step_num, row_idx, start_col, count, 
                        current_color, direction
                    ))
                    
                    # Start new group
                    current_color = row[col_idx]
                    start_col = col_idx
                    count = 1
                    step_num += 1
            
            # Don't forget last group in row
            self.steps.append(self._create_step(
                step_num, row_idx, start_col, count, 
                current_color, direction
            ))
            step_num += 1
    
    def _create_step(self, step_num, row_idx, start_col, count, color_name, direction):
        """Create a step dictionary"""
        # Get RGB for color
        color_rgb = STANDARD_YARN_PALETTE.get(color_name, (0, 0, 0))
        
        # Direction text
        arrow = 'الى اليمين' if direction == 'right' else 'الى اليسار'
        
        # Build instruction in Arabic
        # Add new row notification if this is the first stitch of a non-first row
        instruction = f"اشتغلي {count} غرز من اللون {color_name} {arrow}"
        
        # If this is the start of a new row (start_col == 0), add new row notification
        if start_col == 0 and row_idx > 0:
            instruction = f"سطر جديد : {instruction}"
        
        return {
            'step_number': step_num,
            'row': row_idx + 1,  # 1-indexed for user
            'start_col': start_col,
            'end_col': start_col + count,
            'color_name': color_name,
            'color_rgb': color_rgb,
            'count': count,
            'direction': direction,
            'instruction_ar': instruction,
        }
    
    def get_step(self, step_number):
        """
        Get a specific step by number.
        
        Args:
            step_number (int): 1-indexed step number
            
        Returns:
            dict or None: Step dictionary
        """
        if 1 <= step_number <= len(self.steps):
            return self.steps[step_number - 1]
        return None
    
    def get_total_steps(self):
        """Get total number of steps"""
        return len(self.steps)
    
    def get_steps_for_row(self, row_number):
        """
        Get all steps for a specific row.
        
        Args:
            row_number (int): 1-indexed row number
            
        Returns:
            list: List of step dictionaries for that row
        """
        return [s for s in self.steps if s['row'] == row_number]
    
    def apply_color_edit(self, step_number, new_color_name):
        """
        Change the color for a specific step.
        Updates the pattern grid for that step's cells.
        
        Args:
            step_number (int): Step to edit
            new_color_name (str): New color name
            
        Returns:
            dict: Updated step dictionary
        """
        step = self.get_step(step_number)
        if not step:
            return None
        
        # Update pattern grid
        row_idx = step['row'] - 1
        start_col = step['start_col']
        end_col = step['end_col']
        
        for col in range(start_col, end_col):
            self.pattern_grid[row_idx][col] = new_color_name
        
        # Update step data
        step['color_name'] = new_color_name
        step['color_rgb'] = STANDARD_YARN_PALETTE.get(new_color_name, (0, 0, 0))
        
        # Update instruction
        arrow = 'الى اليمين' if step['direction'] == 'right' else 'الى اليسار'
        step['instruction_ar'] = f"اشتغلي {step['count']} غرز من اللون {new_color_name} {arrow}"
        
        return step
    
    def get_pattern_grid(self):
        """Get current pattern grid (with any applied edits)"""
        return self.pattern_grid


# Testing
if __name__ == "__main__":
    # Create a simple test pattern
    test_grid = [
        ['أحمر', 'أحمر', 'أزرق', 'أزرق', 'أزرق'],
        ['أحمر', 'أبيض', 'أبيض', 'أزرق', 'أزرق'],
        ['أحمر', 'أحمر', 'أحمر', 'أزرق', 'أزرق'],
    ]
    colors = ['أحمر', 'أزرق', 'أبيض']
    
    print("🎯 Testing Step Generator...")
    gen = StepGenerator(test_grid, colors)
    
    print(f"\n📊 Pattern: 3 rows × 5 cols")
    print(f"   Total steps: {gen.get_total_steps()}")
    
    print("\n📝 First 5 steps:")
    for i in range(1, min(6, gen.get_total_steps() + 1)):
        step = gen.get_step(i)
        print(f"   Step {step['step_number']}: {step['instruction_ar']}")
    
    print("\n🎨 Testing color edit...")
    print(f"   Before: {gen.get_step(1)['color_name']}")
    gen.apply_color_edit(1, 'ذهبي')
    print(f"   After: {gen.get_step(1)['color_name']}")
