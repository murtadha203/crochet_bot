"""
Image Complexity Analyzer - Recommends optimal pattern size

This module analyzes uploaded images to determine:
- Detail level (high/medium/low)
- Optimal grid size
- Recommended size range
"""

from PIL import Image, ImageFilter
import numpy as np


def analyze_image_complexity(image_path):
    """
    Analyze image to recommend optimal grid size.
    
    Args:
        image_path (str): Path to the image file
    
    Returns:
        dict: {
            'recommended_size': int,
            'min_size': int,
            'max_size': int,
            'detail_level': 'low'|'medium'|'high',
            'original_size': (width, height),
            'stats': dict  # Additional statistics
        }
    """
    # Load image
    img = Image.open(image_path).convert('RGB')
    width, height = img.size
    
    # Calculate color complexity
    color_complexity = _calculate_color_complexity(img)
    
    # Calculate edge density
    edge_density = _calculate_edge_density(img)
    
    # Determine detail level and recommended size
    detail_level, recommended = _determine_size(
        width, height, color_complexity, edge_density
    )
    
    return {
        'recommended_size': recommended,
        'min_size': max(80, recommended - 50),
        'max_size': min(500, recommended + 100),
        'detail_level': detail_level,
        'original_size': (width, height),
        'stats': {
            'color_complexity': color_complexity,
            'edge_density': edge_density,
        }
    }


def _calculate_color_complexity(img):
    """Calculate number of distinct colors (complexity metric)"""
    # Resize for faster analysis
    img_small = img.copy()
    img_small.thumbnail((200, 200))
    
    # Count unique colors
    colors = img_small.getcolors(maxcolors=100000)
    
    if colors is None:
        # Too many colors
        return 1.0
    
    unique_count = len(colors)
    
    # Normalize to 0-1 range
    # 0-100 colors = simple (0.0-0.3)
    # 100-500 colors = medium (0.3-0.7)
    # 500+ colors = complex (0.7-1.0)
    if unique_count < 100:
        return unique_count / 300  # 0.0 - 0.33
    elif unique_count < 500:
        return 0.33 + (unique_count - 100) / 1000  # 0.33 - 0.73
    else:
        return min(0.73 + (unique_count - 500) / 2000, 1.0)  # 0.73 - 1.0


def _calculate_edge_density(img):
    """Calculate edge density using simple filter (complexity metric)"""
    # Convert to grayscale
    grey = img.convert('L')
    
    # Resize for faster processing
    grey.thumbnail((400, 400))
    
    # Apply edge detection filter
    edges = grey.filter(ImageFilter.FIND_EDGES)
    
    # Convert to numpy for analysis
    edge_array = np.array(edges)
    
    # Count edge pixels (bright pixels in edge image)
    edge_pixels = np.sum(edge_array > 30)  # Threshold
    total_pixels = edge_array.size
    
    density = edge_pixels / total_pixels
    
    # Normalize to 0-1
    # 0-0.05 = simple (few edges)
    # 0.05-0.15 = medium
    # 0.15+ = complex (many edges)
    return min(density / 0.2, 1.0)


def _determine_size(width, height, color_complexity, edge_density):
    """
    Determine detail level and recommended size.
    
    Logic:
    - High detail: Many colors OR many edges → Need larger grid
    - Medium detail: Moderate complexity → Medium grid
    - Low detail: Simple image → Smaller grid is fine
    """
    max_dimension = max(width, height)
    
    # Combined complexity score (0-1)
    complexity = (color_complexity * 0.4) + (edge_density * 0.6)
    # Edge density weighted more as it's better indicator of detail
    
    if complexity > 0.65:
        # High detail
        detail_level = 'high'
        # Use 30-40% of original dimension
        recommended = int(max_dimension * 0.35)
    elif complexity > 0.35:
        # Medium detail
        detail_level = 'medium'
        # Use 20-25% of original dimension
        recommended = int(max_dimension * 0.22)
    else:
        # Low detail
        detail_level = 'low'
        # Use 12-15% of original dimension
        recommended = int(max_dimension * 0.13)
    
    # Constrain to reasonable range (100-400 stitches)
    recommended = max(100, min(400, recommended))
    
    # Round to nearest 10 for cleaner numbers
    recommended = round(recommended / 10) * 10
    
    return detail_level, recommended


# Testing function
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = analyze_image_complexity(sys.argv[1])
        print(f"📊 Image Analysis:")
        print(f"  Original size: {result['original_size']}")
        print(f"  Detail level: {result['detail_level']}")
        print(f"  Recommended: {result['recommended_size']} stitches")
        print(f"  Range: {result['min_size']}-{result['max_size']}")
        print(f"  Color complexity: {result['stats']['color_complexity']:.2f}")
        print(f"  Edge density: {result['stats']['edge_density']:.2f}")
