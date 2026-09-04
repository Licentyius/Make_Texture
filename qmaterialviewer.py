#######################################################
#
#  Elvaerwyn_2026 qmaterialviewer.py for make_texture
#  mh2 plugin version py6 v1.1 WIP
#
#######################################################

import numpy as np
from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QComboBox, QPushButton, QCheckBox

from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT

class MaterialShader3DQtTab(QWidget):
    def __init__(self, ui_app_reference):
        super().__init__()
        self.ui_app = ui_app_reference
        
        # 1. Main Horizontal Layout Split
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        controls_panel = QWidget()
        controls_layout = QVBoxLayout(controls_panel)
        main_layout.addWidget(controls_panel, 1) # Weight 1
        
        render_panel = QWidget()
        render_layout = QVBoxLayout(render_panel)
        main_layout.addWidget(render_panel, 3) # Weight 3
        
        # --- CONTROL DASHBOARD ---
        title_label = QLabel("3D Shader Mesh Engine")
        title_label.setStyleSheet("font-size: 11pt; font-weight: bold; color: #ffaa00;")
        controls_layout.addWidget(title_label)
        
        controls_layout.addWidget(QLabel("Mesh Geometry Primitive:"))
        self.mesh_combo = QComboBox()
        self.mesh_combo.addItems(["Cylinder Column", "Sphere", "Cube Box", "Torus Donut", "Plane Face Flat"])
        self.mesh_combo.currentTextChanged.connect(self.render_mesh_viewport)
        controls_layout.addWidget(self.mesh_combo)

        # MH2 HYBRID LAYER: Dynamic Scene Mesh Picker Dropdown
        controls_layout.addWidget(QLabel("Active MakeHuman 2 Target Mesh Layer:"))
        self.mh2_mesh_target_combo = QComboBox()
        self.mh2_mesh_target_combo.addItems(["[Scraping Engine Scene Layer Matrix...]"])
        self.mh2_mesh_target_combo.currentTextChanged.connect(self.extract_native_mh2_helper_mesh_by_name)
        controls_layout.addWidget(self.mh2_mesh_target_combo)
        
        self.btn_refresh_mh2_scene = QPushButton("🔄 Scan Active Model Helpers")
        self.btn_refresh_mh2_scene.setStyleSheet("background-color: #2d2d34; padding: 4px;")
        self.btn_refresh_mh2_scene.clicked.connect(self.populate_mh2_scene_mesh_dropdown)
        controls_layout.addWidget(self.btn_refresh_mh2_scene)

        
        self.chk_lighting = QCheckBox("Enable Realistic 3D Shading/Lighting")
        self.chk_lighting.setChecked(True)
        self.chk_lighting.stateChanged.connect(self.render_mesh_viewport)
        controls_layout.addWidget(self.chk_lighting)
        
        self.btn_update = QPushButton("🔄 Render Active Texture to 3D")
        self.btn_update.setStyleSheet("background-color: #ffaa00; font-weight: bold; color: #101014; padding: 6px;")
        self.btn_update.clicked.connect(self.render_mesh_viewport)
        controls_layout.addWidget(self.btn_update)
        
        tips_label = QLabel("💡 Navigation Tips:\n• Left-Click + Drag to rotate\n• Right-Click + Drag to zoom\n• Toggle sliders on tab 1 to alter layout shapes.")
        tips_label.setStyleSheet("color: #a0a0aa; font-size: 9pt;")
        tips_label.setWordWrap(True)
        controls_layout.addWidget(tips_label)
        controls_layout.addStretch()

        # --- MATPLOTLIB 3D AXES CANVAS MOUNT ---
        self.fig = Figure(figsize=(5, 5), dpi=100, facecolor='#18181c')
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_facecolor('#18181c')
        
        self.canvas = FigureCanvasQTAgg(self.fig)
        render_layout.addWidget(self.canvas)
        
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.toolbar.setStyleSheet("background-color: #1e1e24; border: none;")
        render_layout.addWidget(self.toolbar)

        self.render_mesh_viewport()

    def render_mesh_viewport(self):
        """Generates 3D spatial grids and map-wraps active textures onto displaced primitive faces."""
        self.ax.clear()
        self.ax.set_facecolor('#18181c')
        self.ax.axis('off')
        
        try:
            engine = self.ui_app.execute_generation_pipeline(target_size=256)
            hex_list = self.ui_app.get_validated_colors()
            pil_img = engine.create_image_object(hex_list, use_gradients=self.ui_app.chk_grad.isChecked())
            height_source = engine.gradient_matrix if (self.ui_app.chk_grad.isChecked() and np.any(engine.gradient_matrix > 0)) else engine.pixel_matrix
        except Exception:
            pil_img = Image.new('RGB', (256, 256), '#dfb443')
            height_source = np.zeros((256, 256), dtype=np.float32)

        import texture_engine
        chosen_mesh = self.mesh_combo.currentText()
        is_lit = self.chk_lighting.isChecked()

        if chosen_mesh == "Plane Face Flat":
            # Builds a rock-solid, perfectly flat 100x100 matrix pane with zero vertical height depth.
            x_range = np.linspace(-1, 1, 100)
            y_range = np.linspace(-1, 1, 100)
            X, Y = np.meshgrid(x_range, y_range)
            Z = np.zeros_like(X) # Pure flat zero plane. Absolute zero spikes!
        else:
            X, Y, Z = texture_engine.generate_3d_mesh_coordinates(chosen_mesh, resolution=64)
            if chosen_mesh == "Cylinder Column":
                X, Y, Z = texture_engine.apply_3d_displacement_height(X, Y, Z, height_source.astype(np.float32), displacement_scale=0.18)

        mesh_resolution = 100 if chosen_mesh == "Plane Face Flat" else 64
        img_res = pil_img.resize((mesh_resolution, mesh_resolution), Image.Resampling.BILINEAR)
        tex_resized = np.array(img_res).astype(np.float32) / 255.0

        self.ax.plot_surface(
            X, Y, Z, 
            rcount=mesh_resolution, 
            ccount=mesh_resolution, 
            facecolors=tex_resized, 
            shade=is_lit, 
            antialiased=True
        )
        self.ax.set_box_aspect((1, 1, 1))
        self.canvas.draw()

    def populate_mh2_scene_mesh_dropdown(self):
        """Scrapes the live 3D character mesh hierarchy layers inside MakeHuman 2 memory layout arrays."""
        self.mh2_mesh_target_combo.clear()
        
        # Standalone protection gate fallback
        if not hasattr(self, 'mh2_app') or self.mh2_app is None:
            self.mh2_mesh_target_combo.addItems(["Standalone Mode: No MH2 Engine Active"])
            return

        human_instance = None
        if hasattr(self.mh2_app, 'human'): human_instance = self.mh2_app.human
        elif hasattr(self.mh2_app, 'glob') and hasattr(self.mh2_app.glob, 'human'): human_instance = self.mh2_app.glob.human

        if not human_instance:
            self.mh2_mesh_target_combo.addItems(["Could not locate active human instance"])
            return

        available_layers = ["Base Body Skin Mesh"] # The core target skin layer is always present
        
        # Scrape active proxies tracking structures (clothes, helper objects, topology layers)
        if hasattr(human_instance, 'proxies') and human_instance.proxies:
            for proxy_name in human_instance.proxies.keys():
                available_layers.append(f"Proxy: {proxy_name}")
                
        # Scrape alternative attached asset records mapping configurations
        if hasattr(human_instance, 'attached_assets') and human_instance.attached_assets:
            for asset_key in human_instance.attached_assets.keys():
                available_layers.append(f"Asset: {asset_key}")
                
        self.mh2_mesh_target_combo.addItems(available_layers)
        print(f"[Texture Studio] Discovered {len(available_layers)} interactive 3D target geometry surfaces in scene context.")

    def extract_native_mh2_helper_mesh_by_name(self, selected_layer_text):
        """
        Extracts raw vector coordinates and UV assignment mappings straight 
        out of MakeHuman 2's compiled graphic vertex structures.
        """
        if not selected_layer_text or "Standalone" in selected_layer_text or "Could not" in selected_layer_text:
            return

        human_instance = None
        if hasattr(self, 'mh2_app') and self.mh2_app:
            if hasattr(self.mh2_app, 'human'): human_instance = self.mh2_app.human
            elif hasattr(self.mh2_app, 'glob') and hasattr(self.mh2_app.glob, 'human'): human_instance = self.mh2_app.glob.human

        if not human_instance:
            return

        try:
            verts, faces, uvs, face_uvs = [], [], [], []
            target_mesh_obj = None

            # Route A: Target the Base Human Skin Mesh coordinates
            if selected_layer_text == "Base Body Skin Mesh":
                target_mesh_obj = human_instance # The human object itself holds the base mesh configuration
            
            # Route B: Extract data out of active proxy items
            elif selected_layer_text.startswith("Proxy: "):
                proxy_key = selected_layer_text.replace("Proxy: ", "")
                target_mesh_obj = human_instance.proxies.get(proxy_key)
                
            # Route C: Extract data out of alternative asset arrays
            elif selected_layer_text.startswith("Asset: "):
                asset_key = selected_layer_text.replace("Asset: ", "")
                target_mesh_obj = human_instance.attached_assets.get(asset_key)

            if target_mesh_obj:
                # THE ENGINE DEEP DIVE: Extract raw data pools out of MakeHuman's mesh objects
                # MakeHuman 2 standard mesh property fields mappings
                if hasattr(target_mesh_obj, 'coord') and target_mesh_obj.coord is not None:
                    # Convert internal vector point pools directly into high-velocity NumPy structural layouts
                    self.obj_vertices = np.array(target_mesh_obj.coord, dtype=np.float32)
                elif hasattr(target_mesh_obj, 'vertices') and target_mesh_obj.vertices is not None:
                    self.obj_vertices = np.array([v.co for v in target_mesh_obj.vertices], dtype=np.float32)

                if hasattr(target_mesh_obj, 'fcoord') and target_mesh_obj.fcoord is not None:
                    self.obj_faces = np.array(target_mesh_obj.fcoord, dtype=np.int32)
                elif hasattr(target_mesh_obj, 'faces') and target_mesh_obj.faces is not None:
                    self.obj_faces = np.array([f.v for f in target_mesh_obj.faces], dtype=np.int32)

                # Capture accompanying texturing layout indices to enable 3D brush calculations
                if hasattr(target_mesh_obj, 'uv') and target_mesh_obj.uv is not None:
                    self.obj_uvs = np.array(target_mesh_obj.uv, dtype=np.float32)
                if hasattr(target_mesh_obj, 'fuv') and target_mesh_obj.fuv is not None:
                    self.obj_face_uv_indices = np.array(target_mesh_obj.fuv, dtype=np.int32)

                # Set dropdown toggle state value configuration rules
                self.mesh_combo.setCurrentText("Custom Loaded OBJ Model")
                print(f"[MH2 Mesh Sync] Extracted {len(self.obj_vertices)} vectors from active scene item: {selected_layer_text}")
                self.render_mesh_viewport()
                
        except Exception as sync_fault:
            print(f"⚠️ [MH2 Mesh Extraction Failure] Could not index target object variables: {sync_fault}")


