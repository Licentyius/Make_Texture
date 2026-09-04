############################################
# 
#  Elvaerwyn_2026 lut generator standalone 
#
############################################

import os
import numpy as np
from PIL import Image

def generate_squares_hald(level):
    cube_size = level ** 2
    img_size = cube_size * level
    hald = np.zeros((img_size, img_size, 3), dtype=np.uint8)
    
    for r in range(cube_size):
        for g in range(cube_size):
            for b in range(cube_size):
                block_x = r % level
                block_y = r // level
                
                x = block_x * cube_size + b
                y = block_y * cube_size + g
                
                hald[y, x, 0] = np.uint8(r * 255 / (cube_size - 1))
                hald[y, x, 1] = np.uint8(g * 255 / (cube_size - 1))
                hald[y, x, 2] = np.uint8(b * 255 / (cube_size - 1))
    return hald

def generate_lines_hald(level):
    cube_size = level ** 2
    img_size = cube_size * level
    hald = np.zeros((img_size, img_size, 3), dtype=np.uint8)
    
    for y in range(img_size):
        for x in range(img_size):
            r_val = int(y * (cube_size - 1) / (img_size - 1))
            g_val = x % cube_size
            b_val = int((x // cube_size) * (cube_size - 1) / (level - 1))
            
            hald[y, x, 0] = np.uint8(r_val * 255 / (cube_size - 1))
            hald[y, x, 1] = np.uint8(g_val * 255 / (cube_size - 1))
            hald[y, x, 2] = np.uint8(b_val * 255 / (cube_size - 1))
    return hald

# --- EXPOSE DRIVERS FOR THE USER INTERFACE ---
LUT_TYPES = {
    "Standard Squares (Hald Grid)": generate_squares_hald,
    "Vertical Lines (3D LUT Style)": generate_lines_hald
}

def generate_single_lut(style_name, level):
    """Bakes out a specific color LUT format on demand."""
    if style_name not in LUT_TYPES:
        raise ValueError(f"Unknown format pattern: {style_name}")
        
    matrix_func = LUT_TYPES[style_name]
    matrix_data = matrix_func(level)
    
    return Image.fromarray(matrix_data, 'RGB')
