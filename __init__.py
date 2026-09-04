"""
Elvaerwyn_2026 Init- Integrated Texture Package Bridge Loader
Upgraded: Docking for MH2
"""

import os
import sys
from PySide6 import QtWidgets

TOOL_NAME = "Make Texture (PySide6 Edition)"

def register_tool(layout, app):
    """
    The Official Entry Hook. Instantiates the multi-tab layout interface
    and appends it directly into MakeHuman 2's primary container panel.
    """

    addon_dir = os.path.dirname(os.path.abspath(__file__))

    if addon_dir not in sys.path:
        sys.path.insert(0, addon_dir)
        
    try:
        import qtexturewindow
        import qmaterialviewer
        
        from .maketexture_qt import LivePaintTabWidget  

        try:
            from . import q3dpaintroom
        except ImportError:
            import q3dpaintroom

        tabs_container = QtWidgets.QTabWidget()
        
        makepattern_tab = qtexturewindow.MakePatternQtTab()
        tabs_container.addTab(makepattern_tab, "makepattern")
        
        material_viewer_tab = qmaterialviewer.MaterialShader3DQtTab(ui_app_reference=makepattern_tab)
        tabs_container.addTab(material_viewer_tab, "3D Material Viewer")

        live_paint_tab = LivePaintTabWidget(app_reference=app)
        tabs_container.addTab(live_paint_tab, "Realtime Texture Painter")
        
        # =======================================================================
        # 🎨 STEP 3: MOUNT ROOM 4 DIRECTLY INTO THE INTERFACE TABS CONTAINER
        # =======================================================================
        if q3dpaintroom is not None:
            paint3d_room_tab = q3dpaintroom.PaintRoom3DQtTab(ui_app_reference=makepattern_tab)
            tabs_container.addTab(paint3d_room_tab, "Interactive 3D Skin Painter")
            print("[Texture Studio Bridge] SUCCESS: All 4 tabs matched and mounted cleanly via explicit relative hooks.")
        else:
            print("⚠️ [Room 4 Hook Error] Could not add the 4th tab because q3dpaintroom failed to import.")
        
        # 3. Inject the multi-tab interface smoothly into the system layout
        layout.addWidget(tabs_container)
        
        # Save a core reference back to MakeHuman 2's main application hook 
        makepattern_tab.mh2_app = app
        material_viewer_tab.mh2_app = app
        if q3dpaintroom is not None and hasattr(paint3d_room_tab, 'mh2_app'):
            paint3d_room_tab.mh2_app = app
        
        # TRIGGER RUNTIME SCENE EXTRACTOR: 
        # Instantly pulls the active character base body mesh, helpers, or clothing proxies right on startup!
        try:
            material_viewer_tab.populate_mh2_scene_mesh_dropdown()
        except Exception as scan_err:
            print(f"[Texture Studio Startup Error] Scene helper pre-scan skipped: {scan_err}")
        
    except Exception as err:
        import traceback
        traceback.print_exc()
        error_label = QtWidgets.QLabel(f"<font color='red'><b>Failed to mount components:</b><br>{str(err)}</font>")
        layout.addWidget(error_label)
        print(f"[MH2 Addon Error] Fault loading 'Elvaerwyn_make_texture': {err}")
