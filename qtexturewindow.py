######################################################
#
#  Elvaerwyn_2026 qtexturewindow.py for make_texture
#  mh2 texture window py6 plugin version v1.0-WIP
#
######################################################

import os
import numpy as np
from PIL import Image, ImageQt
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
                             QComboBox, QCheckBox, QPushButton, QLineEdit, 
                             QSlider, QListWidget, QListWidgetItem, QColorDialog, 
                             QMessageBox, QScrollArea, QFrame, QSplitter, QSizePolicy)


class ZoomableTextureLabel(QLabel):
    """
    An advanced interactive Qt Label component that intercepts mouse inputs
    to allow dynamic zooming, scaling, and canvas panning configurations.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #1a1a1a; border: 1px solid #333333;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setMinimumSize(256, 256)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        
        # Core transformation state trackers
        self.base_pixmap = QPixmap()
        self.zoom_factor = 1.0
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        
        # Mouse movement tracking coordinates pivots
        self.is_panning = False
        self.mouse_start_x = 0
        self.mouse_start_y = 0

    def set_texture_pixmap(self, pixmap):
        """Loads incoming calculated texture layers while retaining current zoom parameters."""
        self.base_pixmap = pixmap
        self.update_viewport_display()

    def wheelEvent(self, event):
        """Intercepts mouse scroll wheel ticks to calculate dynamic zooming steps."""
        delta = event.angleDelta().y()
        zoom_step = 1.1 if delta > 0 else 0.9
        new_zoom = self.zoom_factor * zoom_step
        if 0.5 <= new_zoom <= 8.0:
            self.zoom_factor = new_zoom
            self.update_viewport_display()
        event.accept()

    def mousePressEvent(self, event):
        """Activates layout panning rules when clicking onto the design canvas."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_panning = True
            self.mouse_start_x = event.position().x()
            self.mouse_start_y = event.position().y()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        event.accept()

    def mouseMoveEvent(self, event):
        """Calculates structural drag offsets relative to your mouse cursor coordinates."""
        if self.is_panning and not self.base_pixmap.isNull():
            curr_x = event.position().x()
            curr_y = event.position().y()
            self.pan_offset_x += (curr_x - self.mouse_start_x)
            self.pan_offset_y += (curr_y - self.mouse_start_y)
            self.mouse_start_x = curr_x
            self.mouse_start_y = curr_y
            self.update_viewport_display()
        event.accept()

    def mouseReleaseEvent(self, event):
        """Releases the canvas translation locks cleanly on mouse clip drop."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        event.accept()

    def update_viewport_display(self):
        """Transforms and maps image arrays smoothly based on zoom translations."""
        if self.base_pixmap.isNull():
            return
            
        w = int(self.base_pixmap.width() * self.zoom_factor)
        h = int(self.base_pixmap.height() * self.zoom_factor)
        
        scaled_pix = self.base_pixmap.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        container_w = max(100, self.width())
        container_h = max(100, self.height())
        canvas_composite = QPixmap(container_w, container_h)
        canvas_composite.fill(QColor("#1a1a1a"))
        
        from PySide6.QtGui import QPainter
        painter = QPainter(canvas_composite)
        
        pos_x = (container_w - w) // 2 + self.pan_offset_x
        pos_y = (container_h - h) // 2 + self.pan_offset_y
        
        painter.drawPixmap(pos_x, pos_y, scaled_pix)
        painter.end()
        super().setPixmap(canvas_composite)

    def reset_transform_matrices(self):
        """Resets layout tracking offsets back to center frame values."""
        self.zoom_factor = 1.0
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        self.update_viewport_display()

class MakePatternQtTab(QWidget):
    def __init__(self):
        super().__init__()
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        self.horizontal_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.horizontal_splitter)
        
        # Left Scrollable Control Panel Area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        control_panel = QWidget()
        self.control_layout = QVBoxLayout(control_panel)
        self.control_layout.setContentsMargins(10, 10, 10, 10)
        scroll_area.setWidget(control_panel)
        self.horizontal_splitter.addWidget(scroll_area)
        
        # Right Viewport Preview Panel Area
        preview_panel = QWidget()
        preview_layout = QVBoxLayout(preview_panel)
        preview_layout.setContentsMargins(10, 10, 10, 10)
        self.horizontal_splitter.addWidget(preview_panel)

        # --- LIVE PBR MAP PREVIEW SELECTOR ---
        preview_layout.addWidget(QLabel("Active Viewport Render Map Channel:"))
        self.preview_mode_combo = QComboBox()
        self.preview_mode_combo.addItems([
            "Color Diffuse Texture Preview", 
            "PBR RGB Normal Map Preview", 
            "PBR Grayscale Roughness Preview",
            "PBR Ambient Occlusion (AO) Preview"
        ])
        preview_layout.addWidget(self.preview_mode_combo)
        
        # Enforce exact coordinate array parameters to freeze layout widths
        self.horizontal_splitter.setSizes([550, 550])
        
        # --- PREVIEW CANVAS VIEWPORT ---
        preview_layout.addWidget(QLabel("Engine Viewport Preview (Scroll to Zoom / Drag to Pan):"))
        self.viewport_canvas = ZoomableTextureLabel()
        preview_layout.addWidget(self.viewport_canvas, 1) 
        
        self.btn_reset_zoom = QPushButton("🔍 Reset Preview Viewport Zoom")
        self.btn_reset_zoom.clicked.connect(self.viewport_canvas.reset_transform_matrices)
        preview_layout.addWidget(self.btn_reset_zoom)
        
        # --- REPEAT PATTERN SELECTOR (BASE LAYER) ---
        self.control_layout.addWidget(QLabel("Base Layout Pattern Style:"))
        self.pattern_combo = QComboBox()
        self.pattern_combo.addItems([
            "Woven Plaid", "Polka Dots", "Hearts", "Diamonds", "Chevron", "Star_Field",
            "True Polka Dots", "Fish Scales", "Linear Stripes", "Herringbone", "Teardrops", "Paisley Fractal", "Floral Weave",
            "Toroidal Organic Noise", "Perlin/Simplex 4D", "Cellular/Voronoi Loop", "Reaction-Diffusion", "Procedural Wood", "Stacked Bricks"
        ])
        self.pattern_combo.currentTextChanged.connect(self.trigger_live_render)
        self.preview_mode_combo.currentTextChanged.connect(self.trigger_live_render)
        self.control_layout.addWidget(self.pattern_combo)

        # --- SECONDARY LAYER MANAGER ENGINE ---
        self.control_layout.addWidget(QLabel("Composite Overlay Pattern Style (Layer 2):"))
        self.layer2_combo = QComboBox()
        self.layer2_combo.addItems(["None - Disabled", "Woven Plaid", "True Polka Dots", "Linear Stripes", "Herringbone", "Teardrops", "Floral Weave"])
        self.layer2_combo.currentTextChanged.connect(self.trigger_live_render)
        self.control_layout.addWidget(self.layer2_combo)

        self.control_layout.addWidget(QLabel("Layer Blend Composite Mode:"))
        self.blend_mode_combo = QComboBox()
        self.blend_mode_combo.addItems(["Additive Blend (+)", "Multiplicative Mask (*)", "Subtractive Carve (-)"])
        self.blend_mode_combo.currentTextChanged.connect(self.trigger_live_render)
        self.control_layout.addWidget(self.blend_mode_combo)

        # --- PBR GRAPHICS CONTROLS SLIDERS ---
        self.control_layout.addWidget(QLabel("PBR Texture Maps Parameters Customization:"))
        
        normal_row = QHBoxLayout()
        normal_row.addWidget(QLabel("Normal Intensity Strength:"), 0)
        self.normal_strength_slider = QSlider(Qt.Orientation.Horizontal)
        self.normal_strength_slider.setRange(100, 3000) # Maps 1.0 to 30.0
        self.normal_strength_slider.setValue(1200)     # Default 12.0
        self.normal_strength_slider.valueChanged.connect(self.trigger_live_render)
        normal_row.addWidget(self.normal_strength_slider, 1)
        self.control_layout.addLayout(normal_row)

        rough_row = QHBoxLayout()
        rough_row.addWidget(QLabel("Base Roughness / Gloss Scale:"), 0)
        self.rough_slider = QSlider(Qt.Orientation.Horizontal)
        self.rough_slider.setRange(0, 100) # Maps 0.0 to 1.0
        self.rough_slider.setValue(50)     # Default 0.5
        self.rough_slider.valueChanged.connect(self.trigger_live_render)
        rough_row.addWidget(self.rough_slider, 1)
        self.control_layout.addLayout(rough_row)

        # --- AO SHADOW INTENSITY SLIDER ---
        ao_row = QHBoxLayout()
        ao_row.addWidget(QLabel("AO Crevice Shadow Intensity:") , 0)
        self.ao_intensity_slider = QSlider(Qt.Orientation.Horizontal)
        self.ao_intensity_slider.setRange(5, 50) # Maps 0.5 to 5.0 thickness power
        self.ao_intensity_slider.setValue(25)     # Default 2.5
        ao_row.addWidget(self.ao_intensity_slider, 1)
        self.control_layout.addLayout(ao_row)

        # --- NORMAL MAP VECTOR ORIENTATION TOGGLE ---
        self.chk_invert_y = QCheckBox("Invert Normal Y-Axis (DirectX / Flip-Green standard)")
        
        # --- ALIGNMENT MODE LAYOUT ---
        self.control_layout.addWidget(QLabel("Pattern Layout Mode (Geometric Only):"))
        self.layout_combo = QComboBox()
        self.layout_combo.addItems(["Standard Linear Columns", "Staggered Diagonal (50% Offset)", "Micro Shift Grid (25% Offset)"])
        self.layout_combo.currentTextChanged.connect(self.trigger_live_render)
        self.control_layout.addWidget(self.layout_combo)
        
        self.control_layout.addWidget(QLabel("Angular Rotation Incline (Geometric Only):"))
        self.angle_combo = QComboBox()
        self.angle_combo.addItems(["Standard Vertical Alignment", "45-Degree Diagonal Lanes"])
        self.angle_combo.currentTextChanged.connect(self.trigger_live_render)
        self.control_layout.addWidget(self.angle_combo)
        
        # --- ADVANCED FX MODIFIER FLAGS ---
        self.control_layout.addWidget(QLabel("Advanced Engine Modifiers:"))
        self.chk_mirror = QCheckBox("Flip Pattern Upside-Down (Invert)")
        self.chk_mirror.stateChanged.connect(self.trigger_live_render)
        self.control_layout.addWidget(self.chk_mirror)
        
        self.chk_grad = QCheckBox("Enable Smooth Shading Gradients")
        self.chk_grad.stateChanged.connect(self.trigger_live_render)
        self.control_layout.addWidget(self.chk_grad)
        
        self.chk_tile = QCheckBox("Preview 2x2 Seamless Repeating Grid")
        self.chk_tile.stateChanged.connect(self.trigger_live_render)
        self.control_layout.addWidget(self.chk_tile)

        # Declares and physically mounts the missing Y-Axis flip toggle into the control panel
        self.chk_invert_y = QCheckBox("Invert Normal Y-Axis (DirectX / Flip-Green standard)")
        self.chk_invert_y.stateChanged.connect(self.trigger_live_render)
        self.control_layout.addWidget(self.chk_invert_y)
        
        # --- REAL-TIME SUNLIGHT SHADING DIRECTION CONTROLS ---
        self.control_layout.addWidget(QLabel("Sunlight Shading Direction Vector:"))
        self.chk_sun_shading = QCheckBox("Enable Real-Time 2D Viewport Shadows")
        self.chk_sun_shading.stateChanged.connect(self.trigger_live_render)
        self.control_layout.addWidget(self.chk_sun_shading)
        
        sun_angle_row = QHBoxLayout()
        sun_angle_row.addWidget(QLabel("Sun Angle (Orbit):"), 0)
        self.sun_angle_slider = QSlider(Qt.Orientation.Horizontal)
        self.sun_angle_slider.setRange(0, 360)
        self.sun_angle_slider.setValue(45)
        self.sun_angle_slider.valueChanged.connect(self.trigger_live_render)
        sun_angle_row.addWidget(self.sun_angle_slider, 1)
        self.control_layout.addLayout(sun_angle_row)
        
        sun_elev_row = QHBoxLayout()
        sun_elev_row.addWidget(QLabel("Sun Elevation (Height):"), 0)
        self.sun_elev_slider = QSlider(Qt.Orientation.Horizontal)
        self.sun_elev_slider.setRange(10, 90)
        self.sun_elev_slider.setValue(45)
        self.sun_elev_slider.valueChanged.connect(self.trigger_live_render)
        sun_elev_row.addWidget(self.sun_elev_slider, 1)
        self.control_layout.addLayout(sun_elev_row)
        
        # --- PROCEDURAL NOISE PROPERTIES CONTROLS ---
        self.control_layout.addWidget(QLabel("Procedural Noise Tuners:"))
        freq_row = QHBoxLayout()
        freq_row.addWidget(QLabel("Scale / Frequency:"), 0)
        self.freq_slider = QSlider(Qt.Orientation.Horizontal)
        self.freq_slider.setRange(20, 1000)
        self.freq_slider.setValue(150)
        self.freq_slider.valueChanged.connect(self.trigger_live_render)
        freq_row.addWidget(self.freq_slider, 1)
        self.control_layout.addLayout(freq_row)
        
        thresh_row = QHBoxLayout()
        thresh_row.addWidget(QLabel("Density Threshold:"), 0)
        self.thresh_slider = QSlider(Qt.Orientation.Horizontal)
        self.thresh_slider.setRange(1, 85)
        self.thresh_slider.setValue(32)
        self.thresh_slider.valueChanged.connect(self.trigger_live_render)
        thresh_row.addWidget(self.thresh_slider, 1)
        self.control_layout.addLayout(thresh_row)
      
        # =========================================
        # FILE FORMATS & SEAMLESS TILING DROPDOWNS
        # =========================================
        self.control_layout.addWidget(QLabel("Texture Export Target Resolution:"))
        self.size_combo = QComboBox()
        self.size_combo.addItems(["1024 x 1024 (1K)", "2048 x 2048 (2K)"])
        self.control_layout.addWidget(self.size_combo)
        
        # Upgraded the hardcoded combo box to a dynamic numeric layout input string field
        self.control_layout.addWidget(QLabel("Custom Seamless Tiling Repeat Count (e.g., 1, 4, 8, 12):"))
        self.tile_repeat_entry = QLineEdit("1")
        self.tile_repeat_entry.textChanged.connect(self.trigger_live_render)
        self.control_layout.addWidget(self.tile_repeat_entry)
        
        self.control_layout.addWidget(QLabel("Target Output Texture Extension Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "PNG Texture Asset (.png) [Lossless/Alpha]", 
            "TGA Truevision Uncompressed Asset (.tga) [Game Pipeline Standard]", 
            "TIFF Production Master File (.tiff) [High-Fidelity VFX]", 
            "BMP Windows Bitmap (.bmp) [Uncompressed Legacy Support]", 
            "JPEG Compressed File (.jpg) [Lightweight Preview Distribution]", 
            "WebP Modern Web Vector (.webp) [Optimized Web Deployment Master]"
        ])
        self.control_layout.addWidget(self.format_combo)

        # --- HARMONIOUS COLOR SUGGESTER PANEL ---
        self.control_layout.addWidget(QLabel("Automatic Palette Harmony Suggester:"))
        harmony_row = QHBoxLayout()
        self.harmony_type_combo = QComboBox()
        self.harmony_type_combo.addItems(["Complementary", "Split-Complementary", "Triadic", "Analogous"])
        harmony_row.addWidget(self.harmony_type_combo)
        
        btn_generate_scheme = QPushButton("🪄 Harmonize")
        btn_generate_scheme.clicked.connect(self.trigger_palette_harmony)
        harmony_row.addWidget(btn_generate_scheme)
        self.control_layout.addLayout(harmony_row)

        # ================================
        # FOUR-COLOR VISUAL PICKER SYSTEM 
        # ================================
        self.control_layout.addWidget(QLabel("Layer Color Palette Management:"))

        # --- ROW A SETUP ---
        row_a = QWidget()
        layout_a = QHBoxLayout(row_a)
        layout_a.setContentsMargins(0, 2, 0, 2)
        layout_a.addWidget(QLabel("Layer A (Base Field):"))
        self.entry_a = QLineEdit("#111625")
        self.entry_a.setMaximumWidth(80)
        self.entry_a.textChanged.connect(self.trigger_live_render)
        layout_a.addWidget(self.entry_a)
        btn_pick_a = QPushButton("🎨")
        btn_pick_a.setMaximumWidth(35)
        btn_pick_a.clicked.connect(lambda: self.open_qt_color_dialog(self.entry_a, "Layer A"))
        layout_a.addWidget(btn_pick_a)
        self.control_layout.addWidget(row_a)

        # --- ROW B SETUP ---
        row_b = QWidget()
        layout_b = QHBoxLayout(row_b)
        layout_b.setContentsMargins(0, 2, 0, 2)
        layout_b.addWidget(QLabel("Layer B (Primary):"))
        self.entry_b = QLineEdit("#dfb443")
        self.entry_b.setMaximumWidth(80)
        self.entry_b.textChanged.connect(self.trigger_live_render)
        layout_b.addWidget(self.entry_b)
        btn_pick_b = QPushButton("🎨")
        btn_pick_b.setMaximumWidth(35)
        btn_pick_b.clicked.connect(lambda: self.open_qt_color_dialog(self.entry_b, "Layer B"))
        layout_b.addWidget(btn_pick_b)
        self.control_layout.addWidget(row_b)

        # --- ROW C SETUP ---
        row_c = QWidget()
        layout_c = QHBoxLayout(row_c)
        layout_c.setContentsMargins(0, 2, 0, 2)
        layout_c.addWidget(QLabel("Layer C (Secondary):"))
        self.entry_c = QLineEdit("#a31c1c")
        self.entry_c.setMaximumWidth(80)
        self.entry_c.textChanged.connect(self.trigger_live_render)
        layout_c.addWidget(self.entry_c)
        btn_pick_c = QPushButton("🎨")
        btn_pick_c.setMaximumWidth(35)
        btn_pick_c.clicked.connect(lambda: self.open_qt_color_dialog(self.entry_c, "Layer C"))
        layout_c.addWidget(btn_pick_c)
        self.control_layout.addWidget(row_c)

        # --- ROW D SETUP ---
        row_d = QWidget()
        layout_d = QHBoxLayout(row_d)
        layout_d.setContentsMargins(0, 2, 0, 2)
        layout_d.addWidget(QLabel("Layer D (Pins):"))
        self.entry_d = QLineEdit("#f4f3ef")
        self.entry_d.setMaximumWidth(80)
        self.entry_d.textChanged.connect(self.trigger_live_render)
        layout_d.addWidget(self.entry_d)
        btn_pick_d = QPushButton("🎨")
        btn_pick_d.setMaximumWidth(35)
        btn_pick_d.clicked.connect(lambda: self.open_qt_color_dialog(self.entry_d, "Layer D"))
        layout_d.addWidget(btn_pick_d)
        self.control_layout.addWidget(row_d)

        # --- SAVED PALETTE LIBRARY MANAGER UI PANEL ---
        self.control_layout.addWidget(QLabel("Saved Color Palette Library:"))
        palette_tool_row = QHBoxLayout()
        self.palette_name_entry = QLineEdit("Custom_Palette_1")
        palette_tool_row.addWidget(self.palette_name_entry)
        
        btn_save_pal = QPushButton("💾 Save")
        btn_save_pal.clicked.connect(self.save_current_palette)
        palette_tool_row.addWidget(btn_save_pal)
        
        btn_del_pal = QPushButton("❌ Del")
        btn_del_pal.clicked.connect(self.delete_selected_palette)
        palette_tool_row.addWidget(btn_del_pal)
        self.control_layout.addLayout(palette_tool_row)
        
        self.palette_listbox = QListWidget()
        self.palette_listbox.setMinimumHeight(320)
        self.palette_listbox.setMaximumHeight(800)
        self.palette_listbox.currentRowChanged.connect(self.load_selected_palette_by_index)
        self.control_layout.addWidget(self.palette_listbox)
        
        # Enforce dynamic absolute directory discovery relative to the script module location WIP.
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
        except Exception:
            script_dir = os.getcwd()
            
        self.palette_db_path = os.path.join(script_dir, "saved_palettes.txt")

        self.refresh_palette_listbox_view()
        
        # --- BOTTOM ACTION PANEL ---
        self.control_layout.addWidget(QLabel("Export File Name Prefix:"))
        self.prefix_entry = QLineEdit("multicolor_pattern")
        self.control_layout.addWidget(self.prefix_entry)
        
        self.chk_textures = QCheckBox("Export Full PBR Suite (Diffuse, Normal, AO, Rough, Spec)")
        self.chk_textures.setStyleSheet("font-weight: bold; color: #f4f4f6;")
        self.control_layout.addWidget(self.chk_textures)
        
        self.btn_export = QPushButton("⚡ Save Full Resolution Asset")
        self.btn_export.setStyleSheet("background-color: #ffaa00; font-weight: bold; color: black; padding: 6px;")
        self.btn_export.clicked.connect(self.trigger_export)
        self.control_layout.addWidget(self.btn_export)
        
        # Change
        self.normal_strength_slider.valueChanged.connect(self.trigger_live_render)
        self.rough_slider.valueChanged.connect(self.trigger_live_render)
        self.btn_export.clicked.connect(self.trigger_export)

        # FIXED: Place the new channel selector connection hook right here!
        self.preview_mode_combo.currentTextChanged.connect(self.trigger_live_render)

        self.ao_intensity_slider.valueChanged.connect(self.trigger_live_render)
        self.chk_invert_y.stateChanged.connect(self.trigger_live_render)

        # Safely execute your unified startup rendering preview pass
        self.trigger_live_render()

    # ==============================
    # MEMORY-SAFE COMPONENT METHODS
    # ==============================
    def open_qt_color_dialog(self, target_entry, label_name):
        """Bypasses local variable scopes to process colors memory-safely."""
        color = QColorDialog.getColor(QColor(target_entry.text()), self, f"Select {label_name}")
        if color.isValid():
            target_entry.setText(color.name())
            self.trigger_live_render()

    def get_validated_colors(self):
        """Extracts text inputs and normalizes hexadecimal strings for processing."""
        hex_list = [
            self.entry_a.text().strip(),
            self.entry_b.text().strip(),
            self.entry_c.text().strip(),
            self.entry_d.text().strip()
        ]
        for i in range(len(hex_list)):
            if not hex_list[i].startswith("#"): 
                hex_list[i] = "#" + hex_list[i]
            if len(hex_list[i]) != 7: 
                hex_list[i] = "#000000"
        return hex_list

    def refresh_palette_listbox_view(self):
        """Refreshes the saved palette manager, painting inline visual color swatches for every entry."""
        self.palette_listbox.clear()
        if not os.path.exists(self.palette_db_path): 
            return
            
        try:
            with open(self.palette_db_path, "r") as f:
                for line in f:
                    parts = line.strip().split(",")
                    if len(parts) != 5:
                        continue
                        
                    palette_name = parts[0]
                    colors = parts[1:] # Extracts the 4 hex strings (#111625, etc.)
                    
                    # 1. Create a blank base list widget row container object
                    list_item = QListWidgetItem(self.palette_listbox)
                    list_item.setSizeHint(QSize(100, 36)) # Allocate vertical spacing for swatches
                    
                    # 2. Build a custom interface widget layer to embed inside the row grid
                    row_widget = QWidget()
                    row_layout = QHBoxLayout(row_widget)
                    row_layout.setContentsMargins(6, 2, 6, 2)
                    row_layout.setSpacing(8)
                    
                    # Add your custom palette text name label on the left margin
                    name_label = QLabel(palette_name)
                    name_label.setStyleSheet("font-weight: bold; color: #f4f4f6;")
                    row_layout.addWidget(name_label, 1) # Set weight to 1 to push circles to the right
                    
                    # 3. Generate a grouped layout loop for your four color swatches circles
                    swatch_container = QWidget()
                    swatch_layout = QHBoxLayout(swatch_container)
                    swatch_layout.setContentsMargins(0, 0, 0, 0)
                    swatch_layout.setSpacing(4) # Keep circles tight together
                    
                    for hex_color in colors:
                        circle_frame = QFrame()
                        circle_frame.setFixedSize(16, 16) # Build square aspect canvas bounds
                        
                        # Apply CSS styling sheets to round the frame corners into smooth circle swatches
                        circle_frame.setStyleSheet(f"""
                            background-color: {hex_color};
                            border: 1px solid #4a4a52;
                            border-radius: 8px;
                        """)
                        swatch_layout.addWidget(circle_frame)
                        
                    row_layout.addWidget(swatch_container, 0) # Lock size constraints
                    
                    # 4. Inject the custom visual container layer straight back into the list row framework
                    self.palette_listbox.addItem(list_item)
                    self.palette_listbox.setItemWidget(list_item, row_widget)
                    
        except Exception as e: 
            print(f"Error reading palette records: {str(e)}")


    def save_current_palette(self):
        name = self.palette_name_entry.text().strip().replace(" ", "_").replace(",", "")
        if not name: return
        palettes = {}
        if os.path.exists(self.palette_db_path):
            with open(self.palette_db_path, "r") as f:
                for line in f:
                    parts = line.strip().split(",")
                    if len(parts) == 5: palettes[parts[0]] = parts[1:]
        palettes[name] = [self.entry_a.text().strip(), self.entry_b.text().strip(), self.entry_c.text().strip(), self.entry_d.text().strip()]
        with open(self.palette_db_path, "w") as f:
            for k, v in palettes.items(): f.write(f"{k},{v[0]},{v[1]},{v[2]},{v[3]}\n")
        self.refresh_palette_listbox_view()

    def load_selected_palette_by_index(self, row_index):
        """Looks up the text file database by index row to feed the palette slots cleanly."""
        if row_index < 0 or not os.path.exists(self.palette_db_path): 
            return
            
        try:
            with open(self.palette_db_path, "r") as f:
                lines = f.readlines()
                
            if row_index < len(lines):
                target_line = lines[row_index].strip()
                parts = target_line.split(",")
                
                # Verify the record matches the 4-color pattern engine pipeline configuration
                if len(parts) == 5:
                    colors = parts[1:]
                    for entry, val in zip([self.entry_a, self.entry_b, self.entry_c, self.entry_d], colors):
                        entry.setText(val)
                        
                    # Re-paint the 2D workspace viewport immediately with the updated values
                    self.trigger_live_render()
        except Exception as e:
            print(f"Error executing palette indexing stream pass: {str(e)}")

    def delete_selected_palette(self):
        current_row = self.palette_listbox.currentRow()
        if current_row < 0 or not os.path.exists(self.palette_db_path): 
            return
            
        try:
            with open(self.palette_db_path, "r") as f:
                lines = f.readlines()
                
            if current_row < len(lines):
                del lines[current_row]
                with open(self.palette_db_path, "w") as f:
                    f.writelines(lines)
                    
                self.refresh_palette_listbox_view()
        except Exception as e:
            print(f"Error handling file deletion block sequence: {str(e)}")

    def trigger_palette_harmony(self):
        """Generates matching color palettes from the Layer A base string color value."""
        import texture_engine
        base_color = self.entry_a.text().strip()
        if not base_color.startswith("#") or len(base_color) != 7: base_color = "#111625"
        selected_mode = self.harmony_type_combo.currentText()
        new_colors = texture_engine.generate_color_harmonies(base_color, selected_mode)
        for entry, color_val in zip([self.entry_a, self.entry_b, self.entry_c, self.entry_d], new_colors):
            entry.setText(color_val)
        self.trigger_live_render()

    def get_pattern_arrays(self, style_name, target_size, scalar, current_freq, current_thresh):
        """Helper to route string calls straight into background calculation functions with slider variables."""
        import texture_engine

        use_grads = self.chk_grad.isChecked()
        
        # Noise Routing Modes
        if style_name == "Toroidal Organic Noise": return texture_engine.generate_toroidal_noise_pattern(target_size, target_size, current_freq, current_thresh)
        elif style_name == "Perlin/Simplex 4D": return texture_engine.generate_perlin_4d_pattern(target_size, target_size, current_freq, current_thresh)
        elif style_name == "Cellular/Voronoi Loop": return texture_engine.generate_cellular_voronoi_pattern(target_size, target_size, current_freq, current_thresh)
        elif style_name == "Reaction-Diffusion": return texture_engine.generate_reaction_diffusion_pattern(target_size, target_size, current_freq, current_thresh)
        elif style_name == "Procedural Wood": return texture_engine.generate_procedural_wood(target_size, target_size, current_freq, current_thresh)
        elif style_name == "Stacked Bricks": return texture_engine.generate_stacked_bricks(target_size, target_size, current_freq)
        
        # Live 'use_grads' checkbox variable!
        elif style_name == "Woven Plaid": return texture_engine.generate_plaid_pattern(target_size, target_size, int(32 * current_thresh), int(128 / current_freq), 0, use_grads)
        elif style_name == "Polka Dots": return texture_engine.generate_polka_dots(target_size, target_size, int(32 * current_thresh), int(128 / current_freq), 0.0, 0, use_grads)
        elif style_name == "Hearts": return texture_engine.generate_hearts_pattern(target_size, target_size, int(128 / current_freq), False, 0.0, 0, use_grads)
        elif style_name == "Diamonds": return texture_engine.generate_diamonds_pattern(target_size, target_size, int(128 / current_freq), 0.0, 0, use_grads)
        elif style_name == "Chevron": return texture_engine.generate_chevrons_pattern(target_size, target_size, int(128 / current_freq), 0, use_grads)
        elif style_name == "Star_Field": return texture_engine.generate_star_field(target_size, target_size, int(128 / current_freq), 0.0, 0, use_grads)
        
        # Premium Textile Routing Modes
        elif style_name == "True Polka Dots": return texture_engine.generate_true_polka_dots(target_size, target_size, current_freq, current_thresh)
        elif style_name == "Fish Scales": return texture_engine.generate_fish_scales(target_size, target_size, current_freq, current_thresh)
        elif style_name == "Linear Stripes": return texture_engine.generate_linear_stripes(target_size, target_size, current_freq, current_thresh)
        elif style_name == "Herringbone": return texture_engine.generate_herringbone(target_size, target_size, current_freq, current_thresh)
        elif style_name == "Teardrops": return texture_engine.generate_teardrops(target_size, target_size, current_freq, current_thresh)
        elif style_name == "Paisley Fractal": return texture_engine.generate_paisley_fractal(target_size, target_size, current_freq, current_thresh)
        elif style_name == "Floral Weave": return texture_engine.generate_floral_weave(target_size, target_size, current_freq, current_thresh)
        
        return np.zeros((target_size, target_size), dtype=np.uint8), np.zeros((target_size, target_size), dtype=np.float32)

    def execute_generation_pipeline(self, target_size):
        """Generates texture layer combinations and synchronizes slope data safely across all PBR buffers."""
        import texture_engine
        engine = texture_engine.MultiColorPatternEngineNP(size=target_size)
        scalar = target_size / 1024.0

        # Capture all active slider tuning states cleanly out of UI layout objects
        current_freq = self.freq_slider.value() / 100.0
        current_thresh = self.thresh_slider.value() / 100.0

        current_height = self.normal_strength_slider.value() / 1200.0  # Normalize around your default 12.0 value
 
        current_variation = 0.0
        current_seed = 42
        
        # Pass variables dynamically to Layer 1

        p1, g1 = self.get_pattern_arrays(
            self.pattern_combo.currentText(), target_size, scalar, 
            current_freq, current_thresh
        )
        l2_choice = self.layer2_combo.currentText()
        
        if l2_choice != "None - Disabled":

            p2, g2 = self.get_pattern_arrays(
                l2_choice, target_size, scalar, 
                1.5, 0.32
            )
            blend_mode = self.blend_mode_combo.currentText()
            p2_safe = np.broadcast_to(p2, (target_size, target_size)).astype(np.uint8)
            g2_safe = np.broadcast_to(g2, (target_size, target_size)).astype(np.float32)

     
            if "Additive" in blend_mode:
                engine.pixel_matrix = np.clip(p1 + p2_safe, 0, 3).astype(np.uint8)
                engine.gradient_matrix = np.clip(g1 + g2_safe, 0.0, 1.0)
            elif "Multiplicative" in blend_mode:
                engine.pixel_matrix = np.clip(p1 * p2_safe, 0, 3).astype(np.uint8)
                engine.gradient_matrix = np.clip(g1 * g2_safe, 0.0, 1.0)
            else:
                engine.pixel_matrix = np.clip(p1.astype(np.int16) - p2_safe.astype(np.int16), 0, 3).astype(np.uint8)
                engine.gradient_matrix = np.clip(g1 - g2_safe, 0.0, 1.0)
        else:
            engine.pixel_matrix = p1
            engine.gradient_matrix = g1
            
        return engine

    def trigger_live_render(self):
        """Updates the interactive primary preview viewport canvas on slider ticks."""
        try:
            import texture_engine
            v_width = max(128, self.viewport_canvas.width())
            v_height = max(128, self.viewport_canvas.height())
            preview_dim = min(v_width, v_height, 350)
            
            engine = self.execute_generation_pipeline(target_size=preview_dim)
            render_channel = self.preview_mode_combo.currentText()
            
            # Extract height data safely to feed the PBR generation sub-loops
            base_height = engine.gradient_matrix if (self.chk_grad.isChecked() and np.any(engine.gradient_matrix > 0)) else engine.pixel_matrix
            base_height = base_height.astype(np.float32)
            
            # --- CALCULATE CHOSEN MAP SELECTION ON THE FLY ---
            if "Normal" in render_channel:
                strength_val = float(self.normal_strength_slider.value() / 100.0)
                norm_rgb = texture_engine.compute_normal_map(
                    base_height, 
                    strength=strength_val, 
                    invert_y=self.chk_invert_y.isChecked()
                )
                pil_img = Image.fromarray(norm_rgb, 'RGB')

                
            elif "Roughness" in render_channel:
                rough_val = self.rough_slider.value() / 100.0
                rough_gray = texture_engine.compute_roughness_map(base_height, base_roughness=rough_val)
                pil_img = Image.fromarray(rough_gray, 'L')
                
            elif "AO" in render_channel:
                # Tracks your dynamic AO crevice slider intensity smoothly
                ao_val = float(self.ao_intensity_slider.value() / 10.0) if hasattr(self, 'ao_intensity_slider') else 2.5
                ao_gray = texture_engine.compute_ao_map(base_height, intensity=ao_val)
                pil_img = Image.fromarray(ao_gray, 'L')
                
            else: # Color Diffuse Texture Preview Channel
                hex_list = self.get_validated_colors()
                pil_img = engine.create_image_object(hex_list, use_gradients=self.chk_grad.isChecked())

                if self.chk_sun_shading.isChecked():
                    sun_mask = texture_engine.compute_sun_shading(
                        base_height, 
                        angle_degrees=self.sun_angle_slider.value(), 
                        elevation_degrees=self.sun_elev_slider.value()
                    )
                    rgb_array = np.array(pil_img).astype(np.float32)
                    shaded_rgb = np.clip(rgb_array * np.expand_dims(sun_mask, axis=-1), 0, 255).astype(np.uint8)
                    pil_img = Image.fromarray(shaded_rgb, 'RGB')

            # Apply 2x2 tiling repeat views if checked
            # --- APPLY DYNAMIC VIEWPORT TILING ---
            if self.chk_tile.isChecked():
                try:
                    # Parse the custom input entry text into a safe math integer
                    rep_count = max(1, int(self.tile_repeat_entry.text().strip()))
                except ValueError:
                    rep_count = 1  # Fallback gracefully if the user types letters
                
                if rep_count > 1:
                    sub_sz = preview_dim // rep_count
                    if sub_sz >= 2:  # Stop matrix drops if cells get micro-pixel thin
                        resized_cell = pil_img.resize((sub_sz, sub_sz), Image.Resampling.BILINEAR)
                        tiled_canvas = Image.new(pil_img.mode, (preview_dim, preview_dim))
                        
                        # Loop rows and columns dynamically to fill the screen canvas grid sheet
                        for col in range(rep_count):
                            for row in range(rep_count):
                                tiled_canvas.paste(resized_cell, (col * sub_sz, row * sub_sz))
                        pil_img = tiled_canvas

                
            q_img = ImageQt.ImageQt(pil_img)
            pixmap = QPixmap.fromImage(q_img)
            self.viewport_canvas.set_texture_pixmap(pixmap)
        except Exception as e: 
            print(f"Render exception caught: {str(e)}")

    def trigger_export(self):
        """Bakes production texture maps dynamically into local directories across multi-formats."""
        import os
        import numpy as np
        
        try:
            chosen_size_str = self.size_combo.currentText()
            canvas_size = 2048 if "2048" in chosen_size_str else 1024
            prefix = self.prefix_entry.text().strip().replace(" ", "") or "multicolor_asset"
            
            script_dir = os.path.dirname(os.path.abspath(__file__))
            resolution_folder = "1k" if canvas_size == 1024 else "2k"
            target_directory = os.path.join(script_dir, "textures", "patterns", resolution_folder)
            os.makedirs(target_directory, exist_ok=True)
            
            engine = self.execute_generation_pipeline(target_size=canvas_size)
            hex_list = self.get_validated_colors()
            final_image = engine.create_image_object(hex_list, use_gradients=self.chk_grad.isChecked())
            
            # FIXED: Wiped out all legacy combo references. Uses the new numeric entry box safely.
            try:
                rep_count = max(1, int(self.tile_repeat_entry.text().strip()))
            except (ValueError, AttributeError):
                rep_count = 1
                
            if rep_count > 1:
                tiled_export = Image.new('RGB', (canvas_size, canvas_size))
                cell_sz = canvas_size // rep_count
                resized_export_cell = final_image.resize((cell_sz, cell_sz), Image.Resampling.BILINEAR)
                
                for col in range(rep_count):
                    for row in range(rep_count):
                        tiled_export.paste(resized_export_cell, (col * cell_sz, row * cell_sz))
                final_image = tiled_export
                
            format_text = self.format_combo.currentText()
            if "TGA" in format_text: ext_choice, format_tag = ".tga", "TGA"
            elif "TIFF" in format_text: ext_choice, format_tag = ".tiff", "TIFF"
            elif "BMP" in format_text: ext_choice, format_tag = ".bmp", "BMP"
            elif "JPEG" in format_text: ext_choice, format_tag = ".jpg", "JPEG"
            elif "WebP" in format_text: ext_choice, format_tag = ".webp", "WEBP"
            else: ext_choice, format_tag = ".png", "PNG"
            
            filename = f"{prefix}_{self.pattern_combo.currentText().lower().replace(' ', '').replace('/', '_')}{ext_choice}"
            full_path = os.path.join(target_directory, filename)
            final_image.save(full_path, format=format_tag)
            
            success_msg = f"Pattern asset exported dynamically to:\n{full_path}"
            
            if self.chk_textures.isChecked():
                import texture_engine
                if self.chk_grad.isChecked() and hasattr(engine, 'gradient_matrix') and engine.gradient_matrix is not None:
                    base_height = engine.gradient_matrix if np.any(engine.gradient_matrix > 0) else engine.pixel_matrix
                else:
                    base_height = engine.pixel_matrix
                
                normal_power = float(self.normal_strength_slider.value() / 10.0)
                rough_base = float(self.rough_slider.value() / 100.0)
                
                texture_engine.export_texture_maps(
                    base_height.astype(np.float32), 
                    target_directory, 
                    filename,
                    normal_strength=normal_power,
                    rough_base=rough_base
                )
                success_msg += f"\n\nGenerated customized 5-map production PBR bundle wrapped in [{format_tag}] containers!"
                
            QMessageBox.information(self, "Export Success", success_msg)
            
        except Exception as e: 
            QMessageBox.critical(self, "Engine Error", f"Export collapsed:\n{str(e)}")
