"""
Elvaerwyn_2026 make_texture(qt)-mh2 plugin version py6 v1.1
Integrated Multi-Tab Procedural Material Studio & More 
Dual-Purpose: Runs Standalone or Embedded as an MH2 Plugin.
"""

import os
import sys
import numpy as np
from scipy.ndimage import sobel
from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                             QLabel, QGroupBox, QPushButton, QSlider, QColorDialog, 
                             QMessageBox, QApplication, QMainWindow)
from PySide6.QtGui import QPixmap, QImage, QPainter, QPen, QColor

import matplotlib
matplotlib.use('QtAgg')

# =============================================
# DEEP OPERATING SYSTEM FILE DESCRIPTOR FILTER 
# =============================================
try:
    null_fd = os.open(os.devnull, os.O_WRONLY)
    real_stderr_fd = os.dup(2)
    os.dup2(null_fd, 2)
    os.close(null_fd)
    sys.stderr = os.fdopen(real_stderr_fd, 'w')
except Exception:
    pass

# ==========================================
# PERSISTENT LIVE IMAGE PAINT CANVAS ENGINE
# ==========================================
class MH2LivePaintCanvas(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 400)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMouseTracking(True)
        self.setStyleSheet("border: 2px solid #2d2d34; background-color: #121214;")
        
        self.brush_color = QColor(255, 170, 0)
        self.brush_size = 12
        self.last_point = QPoint()
        self.image_path = None
        
        self.canvas_image = QImage(1024, 1024, QImage.Format.Format_ARGB32)
        self.canvas_image.fill(QColor("#141418"))
        self.refresh_display()

    def initialize_canvas_bitmap(self):
        """Loads the active character diffuse texture or initializes an empty one safely."""
        if self.image_path and os.path.isfile(self.image_path):
            try:
                self.canvas_image = QImage(self.image_path)
                print(f"[Painter IO] Loaded texture map: {self.image_path}")
            except Exception:
                self.canvas_image = QImage(1024, 1024, QImage.Format.Format_ARGB32)
                self.canvas_image.fill(QColor("#141418"))
        else:
            self.canvas_image = QImage(1024, 1024, QImage.Format.Format_ARGB32)
            self.canvas_image.fill(QColor("#141418"))
        self.refresh_display()

    def refresh_display(self):
        if self.width() > 0 and self.height() > 0:
            pixmap = QPixmap.fromImage(self.canvas_image).scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.setPixmap(pixmap)
            self.repaint() # Force immediate interface redraw

    def paintEvent(self, event):
        """Native Qt Event Override"""
        super().paintEvent(event)
        ui_painter = QPainter(self)
        ui_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pixmap = self.pixmap()
        if pixmap and not pixmap.isNull():
            offset_x = (self.width() - pixmap.width()) // 2
            offset_y = (self.height() - pixmap.height()) // 2
            ui_painter.drawPixmap(offset_x, offset_y, pixmap)
        ui_painter.end()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.refresh_display()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.last_point = self.map_coordinates(event.position().toPoint())
            self.draw_stroke(self.last_point, is_click=True)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            current_point = self.map_coordinates(event.position().toPoint())
            if not self.last_point.isNull():
                self.draw_stroke(current_point, is_click=False)
            self.last_point = current_point

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.last_point = QPoint()

    def map_coordinates(self, pt):
        pixmap = self.pixmap()
        if not pixmap or pixmap.isNull(): return QPoint()
        
        offset_x = (self.width() - pixmap.width()) // 2
        offset_y = (self.height() - pixmap.height()) // 2
        
        img_x = int((pt.x() - offset_x) * (1024 / pixmap.width()))
        img_y = int((pt.y() - offset_y) * (1024 / pixmap.height()))
        return QPoint(np.clip(img_x, 0, 1023), np.clip(img_y, 0, 1023))

    def draw_stroke(self, pt, is_click):
        if pt.isNull(): 
            return
            
        painter = QPainter(self.canvas_image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(self.brush_color, self.brush_size, Qt.PenStyle.SolidLine,  Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        if is_click: 
            painter.drawPoint(pt)
        else: 
            painter.drawLine(self.last_point, pt)
            
        painter.end()
        self.refresh_display()

        # TRIGGER PASS: 
        parent_tab = self.parentWidget()
        if parent_tab and hasattr(parent_tab, 'compute_live_texture_rebuild'):
            parent_tab.compute_live_texture_rebuild()

class LivePaintTabWidget(QWidget):
    def __init__(self, app_reference=None):
        super().__init__()
        self.app = app_reference
        self.body_texture_path = None
        self.init_ui()
        # Run discovery loop dynamically inside the manager thread container
        self.discover_active_body_texture_map()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        left_container = QVBoxLayout()
        
        self.paint_viewport = MH2LivePaintCanvas()
        left_container.addWidget(QLabel("<b>Interactive Master Paint Layer (Click & Drag):</b>"))
        left_container.addWidget(self.paint_viewport, 1)

        controls_group = QGroupBox("Texture Studio Modifiers")
        controls_layout = QVBoxLayout(controls_group)

        controls_layout.addWidget(QLabel("Brush Drawing Diameter Size:"))
        slider_brush = QSlider(Qt.Orientation.Horizontal)
        slider_brush.setRange(2, 60)
        slider_brush.setValue(12)
        slider_brush.valueChanged.connect(lambda val: setattr(self.paint_viewport, 'brush_size', val))
        controls_layout.addWidget(slider_brush)

        controls_layout.addWidget(QLabel("Normal Map Bump Intensity Elevation:"))
        self.slider_strength = QSlider(Qt.Orientation.Horizontal)
        self.slider_strength.setRange(1, 40)
        self.slider_strength.setValue(12)
        self.slider_strength.valueChanged.connect(lambda val: self.compute_live_texture_rebuild())
        controls_layout.addWidget(self.slider_strength)

        palette_layout = QHBoxLayout()
        btn_brush_color = QPushButton("🎨 Brush Shading Color")
        btn_brush_color.setStyleSheet("background-color: #ffaa00; color: #101014; font-weight: bold;")
        btn_brush_color.clicked.connect(self.pick_brush_tint)
        palette_layout.addWidget(btn_brush_color)

        btn_clear = QPushButton("🔄 Reset Brush Canvas")
        btn_clear.clicked.connect(self.clear_canvas_action)
        palette_layout.addWidget(btn_clear)
        controls_layout.addLayout(palette_layout)
        
        left_container.addWidget(controls_group)

        btn_save_maps = QPushButton("💾 Export Painted Channel Texture Maps")
        btn_save_maps.setStyleSheet("font-weight: bold; background-color: #2D5A27; color: #FFFFFF; min-height: 28px;")
        btn_save_maps.clicked.connect(self.execute_texture_disk_flush)
        left_container.addWidget(btn_save_maps)

        right_container = QVBoxLayout()
        self.normal_viewport = QLabel()
        self.normal_viewport.setMinimumSize(400, 400)
        self.normal_viewport.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.normal_viewport.setStyleSheet("border: 2px solid #2d2d34; background-color: #121214;")
        
        right_container.addWidget(QLabel("<b>Live Procedural Normal Map Channel Output Viewport:</b>"))
        right_container.addWidget(self.normal_viewport, 1)
        
        btn_generate_normal = QPushButton("⚡ Bake Live Convolutions Matrix")
        btn_generate_normal.setStyleSheet("font-weight: bold; min-height: 28px;")
        btn_generate_normal.clicked.connect(self.compute_live_texture_rebuild)
        right_container.addWidget(btn_generate_normal)

        main_layout.addLayout(left_container, 1)
        main_layout.addLayout(right_container, 1)

    def discover_active_body_texture_map(self):
        """
        WIP Dynamically extracts the currently equipped character skin map path
        straight from the engine's memory registers. Safely defaults if standalone.
        """
        import os
        self.body_texture_path = None

        # SAFETY GUARD: Only interrogate self.app if it actually exists!
        if self.app is not None:
            try:
                # Check common MakeHuman 2 API paths for the active character model
                if hasattr(self.app, 'selected_character') and self.app.selected_character:
                    char_obj = self.app.selected_character
                    if hasattr(char_obj, 'skin_texture') and char_obj.skin_texture:
                        self.body_texture_path = os.path.normpath(char_obj.skin_texture).replace("\\", "/")
                
                # Secondary fallback: Extract straight from the active clothing/skin layer matrix
                elif hasattr(self.app, 'equipment'):
                    for slot in getattr(self.app, 'equipment', []):
                        if isinstance(slot, dict) and slot.get('name') == 'skin':
                            image_selector = slot.get('func')
                            if image_selector and hasattr(image_selector, 'picwidget'):
                                selected_asset = image_selector.picwidget.getSelected()
                                if selected_asset and getattr(selected_asset, 'filename', None):
                                    self.body_texture_path = os.path.normpath(selected_asset.filename).replace("\\", "/")
                                    break
            except Exception as api_err:
                print(f"⚠️ [Painter API Fallback] Memory scan pass slipped: {api_err}")

        # STANDALONE FALLBACK: If self.app is None, use local working directory paths cleanly
        if not self.body_texture_path:
            env_obj = getattr(self.app, 'env', None) if self.app else None
            root_dir = env_obj.stdUserPath() if env_obj else os.getcwd()
            self.body_texture_path = os.path.normpath(os.path.join(root_dir, "textures", "active_paint_layer.png")).replace("\\", "/")

        print(f"🎯 [Dynamic Painter] Connected brush to active skin tracking map: {self.body_texture_path}")
        self.paint_viewport.image_path = self.body_texture_path
        self.paint_viewport.initialize_canvas_bitmap()

    def pick_brush_tint(self):
        color = QColorDialog.getColor(self.paint_viewport.brush_color, self, "Choose Stroke Color")
        if color.isValid(): 
            self.paint_viewport.brush_color = color

    def clear_canvas_action(self):
        """Forces the raster canvas image to fill with a solid, opaque background tone."""
        self.paint_viewport.canvas_image.fill(QColor("#141418"))
        self.paint_viewport.refresh_display()
        self.compute_live_texture_rebuild()

    def compute_live_texture_rebuild(self):
        width = self.paint_viewport.canvas_image.width()
        height = self.paint_viewport.canvas_image.height()
        
        ptr = self.paint_viewport.canvas_image.bits()
        rgba_array = np.frombuffer(ptr, dtype=np.uint8).reshape((height, width, 4))
        
        grayscale_height = 0.299 * rgba_array[..., 2] + 0.587 * rgba_array[..., 1] + 0.114 * rgba_array[..., 0]
        normalized_height = (grayscale_height - grayscale_height.min()) / (grayscale_height.max() - grayscale_height.min() + 1e-5)
        
        dx = sobel(normalized_height, axis=1, mode='wrap') * float(self.slider_strength.value())
        dy = sobel(normalized_height, axis=0, mode='wrap') * float(self.slider_strength.value())
        dz = np.ones_like(normalized_height)
        
        norm_factor = np.sqrt(dx**2 + dy**2 + dz**2 + 1e-5)
        
        r = (((-dx / norm_factor) + 1.0) * 127.5).astype(np.uint8)
        g = (((-dy / norm_factor) + 1.0) * 127.5).astype(np.uint8)
        b = (((dz / norm_factor) + 1.0) * 127.5).astype(np.uint8)
        
        normal_rgb = np.stack((r, g, b), axis=-1)
        processed_img = QImage(normal_rgb.data, width, height, width * 3, QImage.Format.Format_RGB888)
        
        scaled_pixmap = QPixmap.fromImage(processed_img).scaled(
            self.normal_viewport.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.normal_viewport.setPixmap(scaled_pixmap)

    def execute_texture_disk_flush(self):
        if not self.body_texture_path: 
            return
            
        parent_dir = os.path.dirname(self.body_texture_path)
        if parent_dir and not os.path.exists(parent_dir):
            try: 
                os.makedirs(parent_dir)
            except Exception: 
                pass
                
        success = self.paint_viewport.canvas_image.save(self.body_texture_path, "PNG")
        if success:
            QMessageBox.information(self, "Maps Exported Successfully!", f"Saved PBR texture channels down to folder:\n{self.body_texture_path}")
            if hasattr(self.app, 'glob') and hasattr(self.app.glob, 'openGLWindow'):
                self.app.glob.openGLWindow.Tweak()

# ========================================================
# STANDALONE DESKTOP EXECUTION INTERFACE CONTAINER GATING 
# ========================================================
class MakeTextureQtStandaloneApp(QMainWindow):
    """Standard Shell Window that opens exclusively when running outside the engine environment."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MakeTexture Studio Workbook (Standalone Execution Mode)")
        self.resize(1200, 800)
        
        self.tabs_container = QTabWidget()
        self.setCentralWidget(self.tabs_container)
        
        try:
            import qtexturewindow
            import qmaterialviewer
            import q3dpaintroom  # Local file lookup for standalone mode
            
            self.makepattern_tab = qtexturewindow.MakePatternQtTab()
            self.tabs_container.addTab(self.makepattern_tab, "makepattern")
            
            self.material_viewer_tab = qmaterialviewer.MaterialShader3DQtTab(ui_app_reference=self.makepattern_tab)
            self.tabs_container.addTab(self.material_viewer_tab, "3D Material Viewer")
            
            self.live_paint_tab = LivePaintTabWidget(app_reference=None)
            self.tabs_container.addTab(self.live_paint_tab, "Realtime Texture Painter")

            # Mount the 3D Paint Sandbox
            self.paint3d_room_tab = q3dpaintroom.PaintRoom3DQtTab(ui_app_reference=self.makepattern_tab)
            self.tabs_container.addTab(self.paint3d_room_tab, "Interactive 3D Skin Painter")
            
        except Exception as err:
            QMessageBox.critical(self, "Import Error", f"Could not load sibling workspace tab modules:\n{err}")

# ========================================================
# NATIVE SCROLLER INTERFACE ENTRY HOOK FOR PLUGIN SCANNER
# ========================================================
def register_tool(tool_layout, app_reference):
    """
    Automated initialization entry hook targeted explicitly by file main.py.
    Compiles and mounts all workspace room tabs directly inside the live engine frame layout.
    """
    import sys
    import os
    
    # DYNAMIC ABSOLUTE PATH NAMESPACE HOOK FOR MAKEHUMAN 2
    current_plugin_dir = os.path.dirname(os.path.abspath(__file__))
    if current_plugin_dir not in sys.path:
        sys.path.insert(0, current_plugin_dir)
        
    import qtexturewindow
    import qmaterialviewer
    
    # Safely import Room 4 using dynamic fallback layers
    try:
        import q3dpaintroom
    except ImportError:
        try:
            from . import q3dpaintroom
        except ImportError as e:
            print(f"⚠️ [Critical Room 4 Path Failure]: {e}")
            q3dpaintroom = None
    
    tabs_container = QTabWidget()
    tool_layout.addWidget(tabs_container)
    
    try:
        # Room 1 Setup
        makepattern_tab = qtexturewindow.MakePatternQtTab()
        tabs_container.addTab(makepattern_tab, "makepattern")
        
        # Room 2 Setup
        material_viewer_tab = qmaterialviewer.MaterialShader3DQtTab(ui_app_reference=makepattern_tab)
        tabs_container.addTab(material_viewer_tab, "3D Material Viewer")
        
        # Room 3 Setup (Flat drawing canvas)
        live_paint_tab = LivePaintTabWidget(app_reference=app_reference)
        tabs_container.addTab(live_paint_tab, "Realtime Texture Painter")

        # =============================================================
        # 🎨 MOUNT ROOM 4 DIRECTLY INTO THE LIVE ENGINE TABS HIERARCHY
        # =============================================================
        if q3dpaintroom is not None:
            paint3d_room_tab = q3dpaintroom.PaintRoom3DQtTab(ui_app_reference=makepattern_tab)
            tabs_container.addTab(paint3d_room_tab, "Interactive 3D Skin Painter")
            print("[Texture Studio Bridge] SUCCESS: All 4 tabs matched and mounted cleanly via explicit relative hooks.")
        else:
            print("⚠️ [Room 4 Skip] Discovered 3 tabs because q3dpaintroom file structure path dropped.")
        
    except Exception as hook_err:
        print(f"⚠️ [Room 4 Integration Fault]: {hook_err}")


if __name__ == "__main__":
    standalone_app = QApplication(sys.argv)
    standalone_app.setStyle('Fusion')
    
    dark_stylesheet = """
        QMainWindow { background-color: #18181c; }
        QWidget { background-color: #1e1e24; color: #f4f4f6; font-family: 'Helvetica'; font-size: 10pt; }
        QLabel { background-color: transparent; }
        QTabWidget::pane { border: 1px solid #2d2d34; background: #18181c; }
        QTabBar::tab { background: #1e1e24; color: #a0a0aa; border: 1px solid #2d2d34; padding: 6px 12px; font-weight: bold; }
        QTabBar::tab:selected { background: #18181c; color: #ffaa00; border-bottom-color: #18181c; }
        QPushButton { background-color: #2d2d34; border: 1px solid #121214; padding: 5px; border-radius: 4px; }
        QPushButton:hover { background-color: #ffaa00; color: #101014; }
        QComboBox, QLineEdit, QListWidget { background-color: #121214; border: 1px solid #2d2d34; padding: 4px; color: #f4f4f6; }
    """
    standalone_app.setStyleSheet(dark_stylesheet)
    
    window_frame = MakeTextureQtStandaloneApp()
    window_frame.show()
    sys.exit(standalone_app.exec())



