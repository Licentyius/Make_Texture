"""
Elvaerwyn_2026 q3paintroom.py for make_texture-mh2 plugin version py6 v1.0
Dedicated 3D Paint Room Module - Completely Isolated Tab Environment-WIP
"""

import os
import numpy as np
from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
                             QPushButton, QSlider, QColorDialog, QMessageBox, QFileDialog)

from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

class PaintRoom3DQtTab(QWidget):
    def __init__(self, ui_app_reference=None):
        super().__init__()
        self.ui_app = ui_app_reference
        
        self.obj_vertices = None
        self.obj_faces = None
        self.obj_uvs = None
        self.obj_face_uv_indices = None
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        controls_panel = QWidget()
        controls_layout = QVBoxLayout(controls_panel)
        main_layout.addWidget(controls_panel, 1)
        
        render_panel = QWidget()
        render_layout = QVBoxLayout(render_panel)
        main_layout.addWidget(render_panel, 3)
        
        title = QLabel("Dedicated 3D Paint Room")
        title.setStyleSheet("font-size: 11pt; font-weight: bold; color: #ffaa00;")
        controls_layout.addWidget(title)
        
        btn_load = QPushButton("📦 Load Object Mesh (.obj)")
        btn_load.setStyleSheet("background-color: #2b3b4c; font-weight: bold; padding: 5px;")
        btn_load.clicked.connect(self.browse_for_mesh)
        controls_layout.addWidget(btn_load)
        
        self.lbl_status = QLabel("No mesh loaded. Use standalone browser.")
        self.lbl_status.setStyleSheet("color: #a0a0aa; font-size: 9pt;")
        controls_layout.addWidget(self.lbl_status)
        controls_layout.addStretch()
        
        self.fig = Figure(figsize=(5, 5), dpi=100, facecolor='#18181c')
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_facecolor('#18181c')
        
        self.canvas = FigureCanvasQTAgg(self.fig)
        render_layout.addWidget(self.canvas)
        
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.toolbar.setStyleSheet("background-color: #1e1e24; border: none;")
        render_layout.addWidget(self.toolbar)
        
        self.canvas.mpl_connect('button_press_event', self.on_mesh_click)
        self.clear_viewport()

    def clear_viewport(self):
        self.ax.clear()
        self.ax.set_facecolor('#18181c')
        self.ax.axis('off')
        self.canvas.draw()

    def browse_for_mesh(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Wavefront Mesh", "", "Wavefront Files (*.obj)")
        if file_path:
            self.parse_obj_file(file_path)

    def parse_obj_file(self, path):
        verts, faces, uvs, face_uvs = [], [], [], []
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    stripped = line.strip()
                    if not stripped or stripped.startswith('#'): 
                        continue
                    parts = stripped.split()
                    if not parts: 
                        continue
                        
                    # Safe token extractor that avoids editor clipping bugs
                    line_tag = parts.pop(0)
                    
                    if line_tag == 'v':
                        verts.append([float(parts[ 0 ]), float(parts[ 1 ]), float(parts[ 2 ])])
                    elif line_tag == 'vt':
                        uvs.append([float(parts[ 0 ]), float(parts[ 1 ])])
                    elif line_tag == 'f':
                        f_idx, f_uv = [], []
                        for p in parts:
                            chks = p.split('/')
                            f_idx.append(int(chks[ 0 ]) - 1)
                            if len(chks) > 1 and chks[ 1 ]:
                                f_uv.append(int(chks[ 1 ]) - 1)
                            else:
                                f_uv.append(0)
                        
                        for i in range(1, len(f_idx) - 1):
                            faces.append([f_idx[ 0 ], f_idx[ i ], f_idx[ i + 1 ]])
                            face_uvs.append([f_uv[ 0 ], f_uv[ i ], f_uv[ i + 1 ]])

            self.obj_vertices = np.array(verts, dtype=np.float32)
            self.obj_faces = np.array(faces, dtype=np.int32)
            self.obj_uvs = np.array(uvs, dtype=np.float32) if uvs else np.zeros((len(verts), 2), dtype=np.float32)
            self.obj_face_uv_indices = np.array(face_uvs, dtype=np.int32) if face_uvs else np.zeros((len(faces), 3), dtype=np.int32)
            
            self.lbl_status.setText(f"Loaded: {len(self.obj_vertices)} Vertices")
            self.render_mesh()
            
            QMessageBox.information(self, "Mesh Loaded!", f"Successfully parsed standalone mesh:\n{len(self.obj_vertices)} Vertices\n{len(self.obj_faces)} Polygons")
            
        except Exception as e:
            QMessageBox.critical(self, "OBJ Load Error", f"Could not parse file data parameters: {e}")

    def render_mesh(self):
        self.ax.clear()
        self.ax.set_facecolor('#18181c')
        self.ax.axis('off')
        
        try:
            polys = [self.obj_vertices[face] for face in self.obj_faces]
            collection = Poly3DCollection(polys, alpha=0.9)
            collection.set_facecolor('#4f5059')
            collection.set_edgecolor('#2d2d34')
            collection.set_linewidth(0.1)
            self.ax.add_collection3d(collection)
            
            flat = self.obj_vertices.flatten()
            self.ax.auto_scale_xyz(flat, flat, flat)
            self.ax.set_box_aspect((1, 1, 1))
            self.canvas.draw()
        except Exception as e:
            print(f"Render engine warning: {e}")

    def load_unstructured_obj_file_geometry(self, path):
        """Parses standalone file text strings into the memory vectors safely."""
        verts, faces, uvs, face_uvs = [], [], [], []
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    stripped = line.strip()
                    if not stripped or stripped.startswith('#'): 
                        continue
                    parts = stripped.split()
                    if not parts: 
                        continue

                    line_tag = parts.pop(0)
                    
                    if line_tag == 'v':
                        # Unpack the 3 remaining string values safely into x, y, and z variables
                        x_str, y_str, z_str = parts[0], parts[1], parts[2]
                        verts.append([float(x_str), float(y_str), float(z_str)])
                        
                    elif line_tag == 'vt':
                        u_str, v_str = parts[0], parts[1]
                        uvs.append([float(u_str), float(v_str)])
                        
                    elif line_tag == 'f':
                        f_idx, f_uv = [], []
                        for p in parts:
                            chks = p.split('/')
                            f_idx.append(int(chks[0]) - 1)
                            if len(chks) > 1 and chks[1]:
                                f_uv.append(int(chks[1]) - 1)
                            else:
                                f_uv.append(0)
                        
                        # Apply Triangle Fan processing sequence loops to split models topology geometry
                        for i in range(1, len(f_idx) - 1):
                            faces.append([f_idx[0], f_idx[i], f_idx[i + 1]])
                            face_uvs.append([f_uv[0], f_uv[i], f_uv[i + 1]])

            # Mount processed vectors variables over the hidden paint workspace objects properties
            self.obj_vertices = np.array(verts, dtype=np.float32)
            self.obj_faces = np.array(faces, dtype=np.int32)
            self.obj_uvs = np.array(uvs, dtype=np.float32) if uvs else np.zeros((len(verts), 2), dtype=np.float32)
            self.obj_face_uv_indices = np.array(face_uvs, dtype=np.int32) if face_uvs else np.zeros((len(faces), 3), dtype=np.int32)
            
            self.lbl_status.setText(f"Loaded: {len(self.obj_vertices)} Vertices")
            self.render_mesh()
            
            QMessageBox.information(self, "Mesh Loaded!", f"Successfully parsed standalone mesh:\n{len(self.obj_vertices)} Vertices\n{len(self.obj_faces)} Polygons")
            
        except Exception as e:
            QMessageBox.critical(self, "OBJ Load Error", f"Could not parse file layout arrays coordinates: {e}")


    def on_mesh_click(self, event):
        if event.xdata is None or event.ydata is None or self.obj_vertices is None:
            return
        print(f"🎯 3D Canvas Click Intercepted at Screen Point: X={event.xdata:.2f}, Y={event.ydata:.2f}")
