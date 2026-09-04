############################################
# 
#  Elvaerwyn_2026 gobo generator standalone 
#
############################################

from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QVBoxLayout, QComboBox, QPushButton, QLabel, QMessageBox, QTabWidget, QSpinBox
import traceback
import os

def setup_preset_engines_ui(self):
    """Call this inside your QTextureWindow layout initialization method."""
    
    self.preset_super_box = QGroupBox("Procedural Texture Generators")
    super_layout = QVBoxLayout()
    
    self.preset_tabs = QTabWidget()
    
    # ------------------ TAB 1: GOBO MASK GENERATOR ------------------
    gobo_tab = QWidget()
    gobo_layout = QVBoxLayout(gobo_tab)
    gobo_layout.addWidget(QLabel("Procedural Lighting Masks (Gobos):"))
    
    gobo_ctrl_layout = QHBoxLayout()
    self.gobo_selector = QComboBox()
    
    # Safely look up your original Gobo scripts
    try:
        from presets.gobo_generator import GOBO_REGISTRY
        self.gobo_selector.addItems(list(GOBO_REGISTRY.keys()))
    except Exception:
        self.gobo_selector.addItem("Gobo engine unavailable")
        
    self.bake_gobo_btn = QPushButton("Bake & Apply Gobo")
    self.bake_gobo_btn.clicked.connect(self.on_bake_gobo_clicked)
    
    gobo_ctrl_layout.addWidget(self.gobo_selector)
    gobo_ctrl_layout.addWidget(self.bake_gobo_btn)
    gobo_layout.addLayout(gobo_ctrl_layout)
    self.preset_tabs.addTab(gobo_tab, "Gobo Projectors")
    
    # ------------------ TAB 2: COLOR LUT GENERATOR ------------------
    lut_tab = QWidget()
    lut_layout = QVBoxLayout(lut_tab)
    lut_layout.addWidget(QLabel("Color Look-Up Table (CLUT) Identity Textures:"))
    
    lut_ctrl_layout = QHBoxLayout()
    self.lut_selector = QComboBox()
    
    try:
        from presets.lut_generator import LUT_TYPES
        self.lut_selector.addItems(list(LUT_TYPES.keys()))
    except Exception:
        self.lut_selector.addItem("LUT engine unavailable")
        
    # Add control for LUT Level (Size) to match your array config [4, 5, 8, 12, 16]
    lut_ctrl_layout.addWidget(QLabel("Level:"))
    self.lut_level_box = QSpinBox()
    self.lut_level_box.setRange(4, 16)
    self.lut_level_box.setValue(8) # Standard sweet-spot resolution
    
    self.bake_lut_btn = QPushButton("Bake & Apply LUT")
    self.bake_lut_btn.clicked.connect(self.on_bake_lut_clicked)
    
    lut_ctrl_layout.addWidget(self.lut_selector)
    lut_ctrl_layout.addWidget(self.lut_level_box)
    lut_ctrl_layout.addWidget(self.bake_lut_btn)
    lut_layout.addLayout(lut_ctrl_layout)
    self.preset_tabs.addTab(lut_tab, "Color LUTs")
    
    # Assemble and append to the main extension layout
    super_layout.addWidget(self.preset_tabs)
    self.preset_super_box.setLayout(super_layout)
    self.main_layout.addWidget(self.preset_super_box)

# --- ACTION LOGIC FOR THE SLOTS ---

def on_bake_gobo_clicked(self):
    pattern = self.gobo_selector.currentText()
    if "unavailable" in pattern: return
    try:
        from presets.gobo_generator import generate_single_gobo
        pil_img = generate_single_gobo(pattern, resolution=2048)
        self.apply_preset_texture_to_engine(pil_img, f"gobo_{pattern}")
    except Exception as e:
        QMessageBox.critical(self, "Bake Error", f"Gobo Generation failed:\n{e}")

def on_bake_lut_clicked(self):
    style = self.lut_selector.currentText()
    level = self.lut_level_box.value()
    if "unavailable" in style: return
    try:
        from presets.lut_generator import generate_single_lut
        pil_img = generate_single_lut(style, level)
        self.apply_preset_texture_to_engine(pil_img, f"identity_lut_lvl{level}")
    except Exception as e:
        QMessageBox.critical(self, "Bake Error", f"LUT Generation failed:\n{e}")
