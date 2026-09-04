#######################################################
#
#  Elvaerwyn_2026 texture_engine.py for maketexturqt
#  The engine V1.2
#
#######################################################

import os
import math
import numpy as np
from scipy.ndimage import sobel, laplace
from PIL import Image

# ==================================
# 1. CORE MATRIX ENGINE DATA FIELDS
# ==================================

class MultiColorPatternEngineNP:
    def __init__(self, size=1024):
        self.width = size
        self.height = size
        # Main mapping layout grid matrix
        self.pixel_matrix = np.zeros((self.height, self.width), dtype=np.uint8)
        # High-fidelity gradient rendering layers
        self.gradient_matrix = np.zeros((self.height, self.width), dtype=np.float32)

    def clear_canvas(self, color_id=0):
        """Resets the internal matrix layers fields instantly."""
        self.pixel_matrix.fill(color_id)
        self.gradient_matrix.fill(0.0)

    def create_image_object(self, hex_colors_list, use_gradients=False):
        """Transforms engine layer matrices into crisp RGB Pillow images safely."""

        while len(hex_colors_list) < 4:
            hex_colors_list.append("#ffffff")
        if len(hex_colors_list) > 4:
            hex_colors_list = hex_colors_list[:4]
        
        rgb_palette = np.array([[int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)] for h in hex_colors_list], dtype=np.uint8)

        clipped_matrix = np.clip(self.pixel_matrix, 0, 3)
        rgb_array = rgb_palette[clipped_matrix].astype(np.float32)
        
        if use_gradients:
            shading_mask = (self.pixel_matrix > 0)
            factor = np.expand_dims(self.gradient_matrix, axis=-1)
            rgb_array = np.where(shading_mask[..., None], rgb_array * (0.65 + 0.35 * factor), rgb_array)
            
        return Image.fromarray(np.clip(rgb_array, 0, 255).astype(np.uint8), 'RGB')

# ==================================
# 2. VECTORIZED COORDINATE SAMPLERS
# ==================================

def get_coordinates(width, height, angle_degrees=0):
    """Generates vectorized layout grids using mathematical coordinate pools."""
    y, x = np.ogrid[0:height, 0:width]
    if angle_degrees == 45:
        rx = (x + y) % width
        ry = (x - y) % height
    else:
        rx = np.broadcast_to(x, (height, width))
        ry = np.broadcast_to(y, (height, width))
    return rx, ry

# ========================================
# 3. NOISE & PROCEDURAL PATTERNS (SLIDER)
# ========================================

def generate_toroidal_noise_pattern(width, height, frequency=1.5, noise_threshold=0.35):
    """Generates a procedural seamless 2D wave texture via 4D toroidal sampling."""
    x_indices = np.linspace(0, 2 * np.pi, width, endpoint=False)
    y_indices = np.linspace(0, 2 * np.pi, height, endpoint=False)
    X, Y = np.meshgrid(x_indices, y_indices)
    
    x1, y1 = np.cos(X) * frequency, np.sin(X) * frequency
    x2, y2 = np.cos(Y) * frequency, np.sin(Y) * frequency
    
    raw_noise = (np.sin(x1 + x2) + np.cos(y1 - y2) + 
                 0.5 * np.sin(2 * x1 - 2 * y2) + 
                 0.25 * np.cos(4 * y1 + 4 * x2))
    
    normalized = (raw_noise - raw_noise.min()) / (raw_noise.max() - raw_noise.min() + 1e-5)
    pixel_matrix = np.zeros((height, width), dtype=np.uint8)
    step = (1.0 - noise_threshold) / 3.0
    
    pixel_matrix[normalized >= 0.00] = 0
    pixel_matrix[normalized >= noise_threshold] = 1
    pixel_matrix[normalized >= (noise_threshold + step)] = 2
    pixel_matrix[normalized >= (noise_threshold + 2 * step)] = 3
    return pixel_matrix, normalized

def generate_perlin_4d_pattern(width, height, scale=3.0, noise_threshold=0.30):
    """Fast deterministic pseudo-Perlin 4D simulation block."""
    x_indices = np.linspace(0, 2 * np.pi, width, endpoint=False)
    y_indices = np.linspace(0, 2 * np.pi, height, endpoint=False)
    X, Y = np.meshgrid(x_indices, y_indices)
    
    v1 = np.sin(np.cos(X) * scale) + np.cos(np.sin(Y) * scale)
    v2 = np.sin(np.sin(X) * scale * 2.0) * np.cos(np.cos(Y) * scale * 2.0)
    combined = (v1 + 0.4 * v2)
    
    normalized = (combined - combined.min()) / (combined.max() - combined.min() + 1e-5)
    pixel_matrix = np.zeros((height, width), dtype=np.uint8)
    step = (1.0 - noise_threshold) / 3.0
    
    pixel_matrix[normalized >= 0.00] = 0
    pixel_matrix[normalized >= noise_threshold] = 1
    pixel_matrix[normalized >= (noise_threshold + step)] = 2
    pixel_matrix[normalized >= (noise_threshold + 2 * step)] = 3
    return pixel_matrix, normalized

def generate_cellular_voronoi_pattern(width, height, noise_scale=1.5, noise_threshold=0.15):
    """Ultra-fast seamless Voronoi engine using 2D grid unrolling"""
    num_cells = int(max(4, min(64, noise_scale * 8)))
    np.random.seed(42)
    points = np.random.rand(num_cells, 2) * [width, height]
    
    # Use open 2D grids to keep calculation memory allocations incredibly lightweight
    y, x = np.ogrid[0:height, 0:width]
    
    # Initialize the distance buffer container with infinity values
    min_dist_sq = np.full((height, width), float('inf'), dtype=np.float32)
    
    # Calculate cell distance profiles sequentially over compact 2D pixel coordinates
    for osx in [-width, 0, width]:
        for osy in [-height, 0, height]:
            shifted_points = points + [osx, osy]
            for p in shifted_points:
                # Optimized vector math pass executing directly inside hardware registers
                d_sq = (x - p[0])**2 + (y - p[1])**2
                min_dist_sq = np.minimum(min_dist_sq, d_sq)
                
    min_dist = np.sqrt(min_dist_sq)
    normalized = (min_dist - min_dist.min()) / (min_dist.max() - min_dist.min() + 1e-5)
    pixel_matrix = np.zeros((height, width), dtype=np.uint8)
    step = (1.0 - noise_threshold) / 3.0
    
    pixel_matrix[normalized >= 0.00] = 0
    pixel_matrix[normalized >= noise_threshold] = 1
    pixel_matrix[normalized >= (noise_threshold + step)] = 2
    pixel_matrix[normalized >= (noise_threshold + 2 * step)] = 3
    return pixel_matrix, normalized

def generate_reaction_diffusion_pattern(width, height, noise_scale=1.5, noise_threshold=0.25):
    """Simulates multi-pass turing reaction-diffusion cell structures with a randomized organic seed."""
    # Scale iterations dynamically with the slider metrics
    iterations = int(max(10, min(80, noise_scale * 15)))
    
    # Initialize standard Gray-Scott chemical matrices (A feed field, B seed field)
    np.random.seed(42)
    A = np.ones((height, width), dtype=np.float32)
    B = np.zeros((height, width), dtype=np.float32)
    
    # Scatter high-frequency seed drops across the canvas to give cells anchors to feed on
    noise_mask = np.random.rand(height, width) > 0.96
    B[noise_mask] = 1.0
    A[noise_mask] = 0.0
    
    # Define standard biological diffusion constants
    f, k = 0.0545, 0.0620 # Classic turing spot parameters
    
    for _ in range(iterations):
        # Calculate fast vectorized 9-point Laplacian convolution fields using matrix shifts
        lapA = (np.roll(A, 1, axis=0) + np.roll(A, -1, axis=0) +
                np.roll(A, 1, axis=1) + np.roll(A, -1, axis=1) - 4 * A)
        lapB = (np.roll(B, 1, axis=0) + np.roll(B, -1, axis=0) +
                np.roll(B, 1, axis=1) + np.roll(B, -1, axis=1) - 4 * B)
        
        # Execute Gray-Scott reaction-diffusion partial differential update loops
        reaction = A * (B**2)
        A += (0.2 * lapA - reaction + f * (1.0 - A))
        B += (0.1 * lapB + reaction - (f + k) * B)

    # Normalize chemical density B straight into the 4-color layout layer matrices
    normalized = (B - B.min()) / (B.max() - B.min() + 1e-5)
    pixel_matrix = np.zeros((height, width), dtype=np.uint8)
    step = (1.0 - noise_threshold) / 3.0
    
    pixel_matrix[normalized >= 0.00] = 0
    pixel_matrix[normalized >= noise_threshold] = 1
    pixel_matrix[normalized >= (noise_threshold + step)] = 2
    pixel_matrix[normalized >= (noise_threshold + 2 * step)] = 3
    return pixel_matrix, normalized

def generate_procedural_wood(width, height, noise_scale=1.5, noise_threshold=0.32):
    """Calculates concentric sine ring elevations with random noise distortion grain."""
    y, x = np.ogrid[0:height, 0:width]
    cx, cy = width // 2, height // 2
    dx, dy = (x - cx) / width, (y - cy) / height
    
    x_indices = np.linspace(0, 2 * np.pi, width, endpoint=False)
    y_indices = np.linspace(0, 2 * np.pi, height, endpoint=False)
    X, Y = np.meshgrid(x_indices, y_indices)
    
    noise_wave = (np.sin(np.cos(X)*noise_scale) + np.cos(np.sin(Y)*noise_scale)) * 0.15
    dist = np.sqrt(dx**2 + dy**2) + noise_wave
    
    ring_frequency = int(24 * noise_scale)
    grain_sine = (np.sin(dist * np.pi * ring_frequency) + 1.0) / 2.0
    
    pixel_matrix = np.zeros((height, width), dtype=np.uint8)
    step = (1.0 - noise_threshold) / 3.0
    pixel_matrix[grain_sine >= 0.00] = 0
    pixel_matrix[grain_sine >= noise_threshold] = 1
    pixel_matrix[grain_sine >= (noise_threshold + step)] = 2
    pixel_matrix[grain_sine >= (noise_threshold + 2 * step)] = 3
    return pixel_matrix, grain_sine

def generate_stacked_bricks(width, height, scalar=1.0):
    """Builds a pixel- brick layout utilizing alternating staggered offsets."""
    brick_w, brick_h = int(128 * scalar), int(64 * scalar)
    mortar_thickness = max(2, int(4 * scalar))
    y, x = np.ogrid[0:height, 0:width]
    
    row_id = y // brick_h
    stagger_shift = (row_id % 2 * (brick_w // 2)).astype(np.int32)
    shifted_x = (x + stagger_shift) % width
    
    horizontal_mortar = (y % brick_h) < mortar_thickness
    vertical_mortar = (shifted_x % brick_w) < mortar_thickness
    
    pixel_matrix = np.zeros((height, width), dtype=np.uint8)
    pixel_matrix[vertical_mortar | horizontal_mortar] = 2
    brick_edges = ((y % brick_h) == mortar_thickness) | ((shifted_x % brick_w) == mortar_thickness)
    pixel_matrix[brick_edges & (pixel_matrix != 2)] = 1
    
    local_x = ((shifted_x % brick_w) - (brick_w // 2)) / (brick_w // 2)
    local_y = ((y % brick_h) - (brick_h // 2)) / (brick_h // 2)
    brick_gradient = np.clip(1.0 - (local_x**4 + local_y**4), 0, 1)
    return pixel_matrix, brick_gradient

def generate_hearts_pattern(width, height, cell_size, flip_orientation, row_offset, angle_degrees, use_gradients):
    """Generates a matrix of mathematical hearts layered with shadow offsets."""
    rx, ry = get_coordinates(width, height, angle_degrees)
    pixel_matrix = np.zeros((height, width), dtype=np.uint8)
    gradient_matrix = np.zeros((height, width), dtype=np.float32)
    
    row_tier = ry // cell_size
    x_shift = np.floor(row_tier % 2 * (float(row_offset) * cell_size)).astype(np.int32)

    shifted_x = (rx + x_shift) % width
    lx = (shifted_x % cell_size) / cell_size - 0.5
    ly = (ry % cell_size) / cell_size - 0.5
    y_mult = 1.4 if flip_orientation else -1.4
    ny = ly * y_mult + 0.1
    nx = lx * 1.5
    
    shadow_x, shadow_y = nx - 0.04, ny - 0.04
    shadow_val = (shadow_x**2 + shadow_y**2 - 0.18)**3 - (shadow_x**2) * (shadow_y**3)
    heart_val = (nx**2 + ny**2 - 0.18)**3 - (nx**2) * (ny**3)
    
    pixel_matrix[shadow_val <= 0.0] = 2
    pixel_matrix[heart_val <= 0.0] = 1
    if use_gradients:
        gradient_matrix = np.clip((ly + 0.5), 0, 1).astype(np.float32)
    return pixel_matrix, gradient_matrix

def generate_plaid_pattern(width, height, thickness, grid_spacing, angle_degrees, use_gradients):
    rx, ry = get_coordinates(width, height, angle_degrees)
    pixel_matrix = np.zeros((height, width), dtype=np.uint8)
    gradient_matrix = np.zeros((height, width), dtype=np.float32)
    
    m1 = ((ry % grid_spacing) < thickness) | ((rx % grid_spacing) < thickness)
    m2 = ((ry % (grid_spacing // 2)) < (thickness // 2)) | ((rx % (grid_spacing // 2)) < (thickness // 2))
    m3 = ((ry % (grid_spacing // 4)) < (thickness // 4)) | ((rx % (grid_spacing // 4)) < (thickness // 4))
    pixel_matrix[m1] = 1
    pixel_matrix[m2] = 2
    pixel_matrix[m3] = 3
    if use_gradients:
        gradient_matrix = ((ry % grid_spacing) / grid_spacing).astype(np.float32)
    return pixel_matrix, gradient_matrix

def generate_polka_dots(width, height, radius, cell_size, row_offset, angle_degrees, use_gradients):
    rx, ry = get_coordinates(width, height, angle_degrees)
    pixel_matrix = np.zeros((height, width), dtype=np.uint8)
    gradient_matrix = np.zeros((height, width), dtype=np.float32)
    
    row_tier = ry // cell_size
    x_shift = (row_tier % 2 * (row_offset * cell_size)).astype(np.int32)
    shifted_x = (rx + x_shift) % width
    cx = (shifted_x // cell_size) * cell_size + (cell_size // 2)
    cy = (ry // cell_size) * cell_size + (cell_size // 2)
    dist = np.hypot(shifted_x - cx, ry - cy)
    pixel_matrix[dist <= radius] = 1
    pixel_matrix[dist <= (radius // 3)] = 2
    if use_gradients:
        gradient_matrix = np.clip(1.0 - (dist / (radius + 1e-5)), 0, 1).astype(np.float32)
    return pixel_matrix, gradient_matrix

def generate_star_field(width, height, frequency, row_offset, angle_degrees, use_gradients):
    rad = math.radians(angle_degrees)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    y, x = np.ogrid[0:height, 0:width]
    rx = x * cos_a + y * sin_a
    ry = -x * sin_a + y * cos_a
    pixel_matrix = np.zeros((height, width), dtype=np.uint8)
    gradient_matrix = np.zeros((height, width), dtype=np.float32)
    
    row_tier = (ry // frequency).astype(np.int32)
    x_shift = row_tier % 2 * (row_offset * frequency)
    shifted_x = rx + x_shift
    local_x = np.abs(shifted_x) % frequency
    local_y = np.abs(ry) % frequency
    mid = frequency // 2
    dist_sum = np.abs(local_x - mid) + np.abs(local_y - mid)
    pixel_matrix[dist_sum < (frequency // 5)] = 1
    if use_gradients:
        gradient_matrix = np.clip(1.0 - (dist_sum / (frequency // 5 + 1e-5)), 0, 1).astype(np.float32)
    return pixel_matrix, gradient_matrix

def generate_diamonds_pattern(width, height, cell_size, row_offset, angle_degrees, use_gradients):
    rad = math.radians(angle_degrees)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    y, x = np.ogrid[0:height, 0:width]
    rx = x * cos_a + y * sin_a
    ry = -x * sin_a + y * cos_a
    pixel_matrix = np.zeros((height, width), dtype=np.uint8)
    gradient_matrix = np.zeros((height, width), dtype=np.float32)
    
    row_tier = (ry // cell_size).astype(np.int32)
    x_shift = row_tier % 2 * (row_offset * cell_size)
    shifted_x = rx + x_shift
    lx = np.abs((shifted_x % cell_size) - (cell_size // 2))
    ly = np.abs((ry % cell_size) - (cell_size // 2))
    dist_sum = lx + ly
    pixel_matrix[dist_sum < (cell_size // 3)] = 1
    if use_gradients:
        gradient_matrix = np.clip(1.0 - (dist_sum / (cell_size // 3 + 1e-5)), 0, 1).astype(np.float32)
    return pixel_matrix, gradient_matrix

def generate_chevrons_pattern(width, height, cell_size, angle_degrees, use_gradients):
    rad = math.radians(angle_degrees)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    y, x = np.ogrid[0:height, 0:width]
    rx = x * cos_a + y * sin_a
    ry = -x * sin_a + y * cos_a
    pixel_matrix = np.zeros((height, width), dtype=np.uint8)
    gradient_matrix = np.zeros((height, width), dtype=np.float32)
    
    lx = np.abs((rx % cell_size) - (cell_size // 2))
    ly = np.abs(ry) % (cell_size // 2)
    pixel_matrix[np.abs(lx - ly) < (cell_size // 12)] = 1
    if use_gradients:
        gradient_matrix = np.clip((ly / (cell_size // 2 + 1e-5)), 0, 1).astype(np.float32)
    return pixel_matrix, gradient_matrix

# ===========================================
# 5. 3D RENDER MAP EXPORTERS (SEAMLESS WRAP)
# ===========================================

def compute_normal_map(h_map, strength=12.0, invert_y=False):
    """Calculates surface gradients to generate an RGB Normal Map with dynamic Y-axis flipping."""
    normal_strength = float(strength)
    
    dx = sobel(h_map, axis=1, mode='wrap') * normal_strength
    dy = sobel(h_map, axis=0, mode='wrap') * normal_strength
    
    # Accepts the incoming keyword argument and flips the green channel safely
    if invert_y:
        dy = -dy
        
    dz = np.ones_like(h_map)
    norm = np.sqrt(dx**2 + dy**2 + dz**2 + 1e-5)
    
    r = (((-dx / norm) + 1.0) * 127.5).astype(np.uint8)
    g = (((-dy / norm) + 1.0) * 127.5).astype(np.uint8)
    b = (((dz / norm) + 1.0) * 127.5).astype(np.uint8)
    return np.stack((r, g, b), axis=-1)

def compute_ao_map(h_map, intensity=2.5):
    """Simulates Ambient Occlusion by computing negative surface curvature scaled by the slider."""
    crevices = laplace(h_map, mode='wrap')

    ao = 1.0 - (crevices * float(intensity))
    return (np.clip(ao, 0.0, 1.0) * 255).astype(np.uint8)

def compute_roughness_map(h_map, base_roughness=0.5):
    """Generates a PBR Roughness grayscale map based on surface curvature."""
    dx = sobel(h_map, axis=1, mode='wrap')
    dy = sobel(h_map, axis=0, mode='wrap')
    slope = np.sqrt(dx**2 + dy**2)
    if slope.max() - slope.min() > 1e-5:
        slope_norm = (slope - slope.min()) / (slope.max() - slope.min())
    else:
        slope_norm = np.zeros_like(slope)
    roughness = float(base_roughness) + (slope_norm * 0.4)
    return (np.clip(roughness, 0.0, 1.0) * 255).astype(np.uint8)

def compute_specular_map(h_map, invert_for_metal=False):
    """Generates a PBR Specular map (dielectric micro-reflectivity)."""
    specular = 0.5 * (h_map + 0.5)
    if invert_for_metal:
        specular = 1.0 - specular
    return (np.clip(specular, 0.0, 1.0) * 255).astype(np.uint8)

def generate_3d_mesh_coordinates(mesh_type="Cylinder Column", resolution=64):
    """Generates 3D structural grids for Cylinder, Sphere, Cube, and Torus primitive shapes needs work."""
    if mesh_type == "Cylinder Column":
        theta = np.linspace(0, 2 * np.pi, resolution)
        z = np.linspace(0, 1, resolution)
        Theta, Z = np.meshgrid(theta, z)
        X = np.cos(Theta)
        Y = np.sin(Theta)
        return X, Y, Z
        
    elif mesh_type == "Sphere":
        u = np.linspace(0, 2 * np.pi, resolution)
        v = np.linspace(0, np.pi, resolution)
        U, V = np.meshgrid(u, v)
        X = np.cos(U) * np.sin(V)
        Y = np.sin(U) * np.sin(V)
        Z = np.cos(V)
        return X, Y, Z
        
    elif mesh_type == "Cube Box":
        # Create a cube by mapping a grid across 6 face directions smoothly
        # To maintain uniform plot_surface matrix sizing, we map a spherical grid cube projection
        u = np.linspace(0, 2 * np.pi, resolution)
        v = np.linspace(0, np.pi, resolution)
        U, V = np.meshgrid(u, v)
        x = np.cos(U) * np.sin(V)
        y = np.sin(U) * np.sin(V)
        z = np.cos(V)
        # Inflate the sphere outward into flat bounding planes
        max_val = np.maximum(np.abs(x), np.maximum(np.abs(y), np.abs(z))) + 1e-5
        return x / max_val, y / max_val, z / max_val
        
    else:  # Torus Donut
        u = np.linspace(0, 2 * np.pi, resolution)
        v = np.linspace(0, 2 * np.pi, resolution)
        U, V = np.meshgrid(u, v)
        R, r = 1.0, 0.4  # Major and minor radius sizes
        X = (R + r * np.cos(V)) * np.cos(U)
        Y = (R + r * np.cos(V)) * np.sin(U)
        Z = r * np.sin(V)
        return X, Y, Z

def export_texture_maps(base_height, target_directory, filename, normal_strength=12.0, rough_base=0.5):
    """Calculates heightmaps, normal buffers, soft shadow fields, roughness, and specular maps in matching target formats."""
    h_min, h_max = base_height.min(), base_height.max()
    if h_max - h_min > 1e-5:
        base_height = (base_height - h_min) / (h_max - h_min)
    else:
        base_height = np.zeros_like(base_height)

    normal_rgb   = compute_normal_map(base_height, strength=normal_strength)
    ao_gray      = compute_ao_map(base_height)
    diffuse_gray = (base_height * 255).astype(np.uint8)
    rough_gray   = compute_roughness_map(base_height, base_roughness=rough_base)
    spec_gray    = compute_specular_map(base_height)


    # Extract the chosen format extension dynamically from the incoming filename to align sub-maps
    name_part, ext_part = os.path.splitext(filename)
    format_tag = ext_part.lstrip('.').upper()
    if format_tag == "JPG": format_tag = "JPEG" # Normalize extension aliases for Pillow matching
    
    # Save the complete 5-map production bundle utilizing matching compression formats
    Image.fromarray(diffuse_gray, mode='L').save(os.path.join(target_directory, f"{name_part}_diffuse{ext_part}"), format=format_tag)
    Image.fromarray(normal_rgb, mode='RGB').save(os.path.join(target_directory, f"{name_part}_normal{ext_part}"), format=format_tag)
    Image.fromarray(ao_gray, mode='L').save(os.path.join(target_directory, f"{name_part}_ao{ext_part}"), format=format_tag)
    Image.fromarray(rough_gray, mode='L').save(os.path.join(target_directory, f"{name_part}_roughness{ext_part}"), format=format_tag)
    Image.fromarray(spec_gray, mode='L').save(os.path.join(target_directory, f"{name_part}_specular{ext_part}"), format=format_tag)

def generate_color_harmonies(base_hex, harmony_type="Complementary"):
    """
    Generates balanced mathematical color palettes from a single base color.
    Returns a list of 4 hex color strings matching the layout system rules.
    """
    # Parse hex string to normalized RGB floats
    hex_clean = base_hex.lstrip('#')
    r, g, b = [int(hex_clean[i:i+2], 16) / 255.0 for i in (0, 2, 4)]
    
    # Convert to Hue-Saturation-Value space for clean rotational angles
    import colorsys
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    
    harmonies = []
    if harmony_type == "Complementary":
        offsets = [0.0, 0.5, 0.0, 0.5]
        s_mult  = [1.0, 0.8, 0.5, 0.4]
    elif harmony_type == "Split-Complementary":
        offsets = [0.0, 0.41, 0.59, 0.0]
        s_mult  = [1.0, 0.9, 0.9, 0.5]
    elif harmony_type == "Triadic":
        offsets = [0.0, 0.33, 0.66, 0.0]
        s_mult  = [1.0, 0.9, 0.9, 0.4]
    else:  # Analogous
        offsets = [0.0, 0.08, 0.92, 0.16]
        s_mult  = [1.0, 0.95, 0.95, 0.8]
        
    for ho, so in zip(offsets, s_mult):
        nh = (h + ho) % 1.0
        ns = max(0.1, min(1.0, s * so))
        nr, ng, nb = colorsys.hsv_to_rgb(nh, ns, v)
        harmonies.append(f"#{int(nr*255):02x}{int(ng*255):02x}{int(nb*255):02x}")
        
    return harmonies

def apply_3d_displacement_height(X, Y, Z, height_matrix, displacement_scale=0.15):
    """
    Physically displaces surface coordinate grids along vertex normal vectors
    utilizing high-precision grayscale elevation arrays.
    """
    from scipy.ndimage import zoom
    h_min, h_max = height_matrix.min(), height_matrix.max()
    if h_max - h_min > 1e-5:
        h_norm = (height_matrix - h_min) / (h_max - h_min)
    else:
        h_norm = np.zeros_like(height_matrix)

    h_resized = zoom(h_norm, (X.shape[0] / float(h_norm.shape[0]), X.shape[1] / float(h_norm.shape[1])), order=1)
    
    mag = np.sqrt(X**2 + Y**2 + 1e-5)
    nX = X / mag
    nY = Y / mag
    
    disp_X = X + (nX * h_resized * displacement_scale)
    disp_Y = Y + (nY * h_resized * displacement_scale)
    disp_Z = Z  
    return disp_X, disp_Y, disp_Z

def compute_sun_shading(height_matrix, angle_degrees=45, elevation_degrees=45):
    """Calculates 2D Lambertian light shading fields across pixel arrays."""
    rad_azimuth = math.radians(angle_degrees)
    rad_elevation = math.radians(elevation_degrees)
    
    lx = math.cos(rad_elevation) * math.cos(rad_azimuth)
    ly = math.cos(rad_elevation) * math.sin(rad_azimuth)
    lz = math.sin(rad_elevation)
    
    dx = sobel(height_matrix, axis=1, mode='wrap') * 4.0
    dy = sobel(height_matrix, axis=0, mode='wrap') * 4.0
    dz = np.ones_like(height_matrix)
    
    norm = np.sqrt(dx**2 + dy**2 + dz**2 + 1e-5)
    nx, ny, nz = -dx / norm, -dy / norm, dz / norm
    
    dot_product = nx * lx + ny * ly + nz * lz
    shading_mask = np.clip(dot_product, 0.0, 1.0)
    return 0.4 + 0.6 * shading_mask

# =========================================================
# VECTORIZED GEOMETRIC GENERATORS DRIVEN DYNAMICALLY - WIP
# =========================================================

def generate_linear_stripes(width, height, current_freq=1.5, current_thresh=0.32):
    """Generates parallel lanes with beautifully curved cylindrical surface profiles."""
    X, Y = np.meshgrid(np.arange(width), np.arange(height))
    pixel_matrix = np.zeros((height, width), dtype=np.uint8)
    
    grid_spacing = max(4, int(256 / float(current_freq)))
    stripe_w = max(1, int(grid_spacing * float(current_thresh)))
    
    mask = (X % grid_spacing) < stripe_w
    pixel_matrix[mask] = 1

    local_coord = (X % stripe_w) / float(stripe_w + 1e-5)
    curved_profile = 4.0 * local_coord * (1.0 - local_coord)
    gradient_matrix = np.where(mask, np.clip(curved_profile, 0, 1), 0.0).astype(np.float32)
    
    return pixel_matrix, gradient_matrix

def generate_true_polka_dots(width, height, current_freq=1.5, current_thresh=0.32):
    """Generates dot grids with smooth spherical dome surface profiles."""
    X, Y = np.meshgrid(np.arange(width), np.arange(height))
    pixel_matrix = np.zeros((height, width), dtype=np.uint8)
    
    cell_size = max(8, int(256 / float(current_freq)))
    radius = max(2, int((cell_size // 2) * float(current_thresh)))
    
    row_tier = Y // cell_size
    col_tier = X // cell_size
    offset = (row_tier % 2) * (cell_size // 2)
    
    cx = col_tier * cell_size + (cell_size // 2) + offset
    cy = row_tier * cell_size + (cell_size // 2)
    
    dist = np.hypot((X - cx) % width, (Y - cy) % height)
    mask = dist <= radius
    pixel_matrix[mask] = 1

    domed_profile = np.sqrt(np.clip(1.0 - (dist / (radius + 1e-5))**2, 0, 1))
    gradient_matrix = np.where(mask, domed_profile, 0.0).astype(np.float32)
    
    return pixel_matrix, gradient_matrix

def generate_fish_scales(width, height, current_freq=1.5, current_thresh=0.32):
    """Generates overlapping fish scales with curved, scooping armor surfaces."""
    X, Y = np.meshgrid(np.arange(width), np.arange(height))
    pixel_matrix = np.zeros((height, width), dtype=np.uint8)
    
    cell_w = max(16, int(256 / float(current_freq)))
    cell_h = cell_w // 2  
    
    lx = (X % cell_w) / float(cell_w) - 0.5
    ly = (Y % cell_h) / float(cell_h) - 0.5
    row_tier = Y // cell_h
    lx_staggered = np.where(row_tier % 2 == 0, lx, (lx + 0.5) % 1.0 - 0.5)
    
    radius = float(current_thresh) * 0.85 + 0.15
    dist_primary = np.sqrt(lx_staggered**2 + (ly - 0.2)**2)
    primary_scallop = dist_primary <= radius
    
    lx_neighbor = np.where((row_tier + 1) % 2 == 0, lx, (lx + 0.5) % 1.0 - 0.5)
    dist_neighbor_left = np.sqrt((lx_neighbor - 0.5)**2 + (ly + 0.8)**2)
    dist_neighbor_right = np.sqrt((lx_neighbor + 0.5)**2 + (ly + 0.8)**2)
    
    mask = primary_scallop & (dist_neighbor_left > radius) & (dist_neighbor_right > radius)
    pixel_matrix[mask] = 1

    scooped_profile = np.clip(1.0 - (dist_primary / (radius + 1e-5)), 0, 1)
    gradient_matrix = np.where(mask, scooped_profile**0.75, 0.0).astype(np.float32)
    
    return pixel_matrix, gradient_matrix

def generate_herringbone(width, height, current_freq=1.5, current_thresh=0.32):
    y, x = np.ogrid[0:height, 0:width]
    pixel_matrix = np.zeros((height, width), dtype=np.uint8)
    block_w = max(8, int(256 / float(current_freq)))
    block_h = block_w // 2
    row, col = y // block_h, (x + (y // block_h % 2) * block_h) // block_w
    lx, ly = x % block_w, y % block_h
    split = float(current_thresh) * 2.0
    mask = np.where((row + col) % 2 == 0, lx > ly * split, lx < (block_h - ly) * split)
    pixel_matrix[mask] = 1
    return pixel_matrix, mask.astype(np.float32)

def generate_teardrops(width, height, current_freq=1.5, current_thresh=0.32):
    y, x = np.ogrid[0:height, 0:width]
    pixel_matrix = np.zeros((height, width), dtype=np.uint8)
    size = max(16, int(384 / float(current_freq)))
    lx, ly = (x % size) / float(size) - 0.5, (y % size) / float(size) - 0.5
    w_boundary = float(current_thresh) * ((np.clip(0.5 - ly, 0.01, 1.0))**1.5) * (1.0 + ly)
    mask = (np.abs(lx) <= w_boundary) & (ly < 0.4) & (ly > -0.4)
    pixel_matrix[mask] = 1
    return pixel_matrix, mask.astype(np.float32)

def generate_paisley_fractal(width, height, current_freq=1.5, current_thresh=0.32):
    y, x = np.ogrid[0:height, 0:width]
    size = max(16, int(384 / float(current_freq)))
    lx, ly = (x % size) / float(size) - 0.5, (y % size) / float(size) - 0.5
    theta, r = np.arctan2(ly, lx), np.hypot(lx, ly)
    swirl = np.sin(theta * 3.0 + r * 5.0) * 0.1
    mask = (r <= (float(current_thresh) + swirl)) & (lx + ly < 0.4)
    pixel_matrix = np.zeros((height, width), dtype=np.uint8)
    pixel_matrix[mask] = 1
    return pixel_matrix, np.clip(1.0 - r, 0, 1).astype(np.float32)

def generate_floral_weave(width, height, current_freq=1.5, current_thresh=0.32):
    y, x = np.ogrid[0:height, 0:width]
    size = max(16, int(384 / float(current_freq)))
    lx, ly = (x % size) / float(size) - 0.5, (y % size) / float(size) - 0.5
    theta, r = np.arctan2(ly, lx), np.hypot(lx, ly)
    petal_wave = np.abs(np.cos(4 * theta)) * float(current_thresh) + 0.05
    mask = r <= petal_wave
    pixel_matrix = np.zeros((height, width), dtype=np.uint8)
    pixel_matrix[mask] = 1
    return pixel_matrix, np.clip(petal_wave - r, 0, 1).astype(np.float32)

def route_dynamic_pattern(style_name, size, scalar, freq, thresh, height_scale, variation, seed):
    """Centralized math router that injects micro-variation coordinates, height adjustments, and random seeds."""
    y, x = np.mgrid[0:size, 0:size]
    
    # 1. Inject Micro-Variation and Asymmetry coordinate distortion
    if variation > 0:
        np.random.seed(int(seed))
        wave_x = np.sin(y * 0.05 + int(seed)) * (float(variation) * (size * 0.08))
        wave_y = np.cos(x * 0.05 + int(seed)) * (float(variation) * (size * 0.08))
        x = np.clip(x + wave_x, 0, size - 1).astype(np.int32)
        y = np.clip(y + wave_y, 0, size - 1).astype(np.int32)

    # 2. Establish uniform bounding cells scales metrics
    cell_w = max(8, int((128 * scalar) / float(freq)))
    cell_h = cell_w // 2
    radius = max(2, int((cell_w // 2) * float(thresh)))
    stripe_w = max(1, int(cell_w * float(thresh)))

    np.random.seed(int(seed))
    
    # 3. Route specific procedural string names to matching geometry stencils
    if style_name == "Linear Stripes": p, g = generate_linear_stripes(size, size, freq, thresh)
    elif style_name == "True Polka Dots": p, g = generate_true_polka_dots(size, size, freq, thresh)
    elif style_name == "Fish Scales": p, g = generate_fish_scales(size, size, freq, thresh)
    elif style_name == "Herringbone": p, g = generate_herringbone(size, size, freq, thresh)
    elif style_name == "Teardrops": p, g = generate_teardrops(size, size, freq, thresh)
    elif style_name == "Paisley Fractal": p, g = generate_paisley_fractal(size, size, freq, thresh)
    elif style_name == "Floral Weave": p, g = generate_floral_weave(size, size, freq, thresh)
    elif style_name == "Toroidal Organic Noise": p, g = generate_toroidal_noise_pattern(size, size, freq, thresh)
    elif style_name == "Perlin/Simplex 4D": p, g = generate_perlin_4d_pattern(size, size, freq, thresh)
    elif style_name == "Cellular/Voronoi Loop": p, g = generate_cellular_voronoi_pattern(size, size, freq, thresh)
    elif style_name == "Reaction-Diffusion": p, g = generate_reaction_diffusion_pattern(size, size, freq, thresh)
    elif style_name == "Procedural Wood": p, g = generate_procedural_wood(size, size, freq, thresh)
    elif style_name == "Stacked Bricks": p, g = generate_stacked_bricks(size, size, freq)
    else: p, g = generate_plaid_pattern(size, size, stripe_w, cell_w, 0, False)
 
    h_min, h_max = g.min(), g.max()
    if h_max - h_min > 1e-5:
        g_normalized = (g - h_min) / (h_max - h_min)
    else:
        g_normalized = np.zeros_like(g)
        
    return p, g_normalized.astype(np.float32)
