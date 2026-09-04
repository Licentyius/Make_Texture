#######################################################
#
#  Main.py V1.2 
#  Elvaerwyn_2026 make_texture(qt)-mh2 plugin version py6 
#
#######################################################

import sys
import os
from PySide6 import QtWidgets, QtCore

TOOL_NAME = "MakeTexture Material & Core Tool"
_active_texture_window = None

def load_extension(app_reference, glob_reference=None):
    """
    Launches the structured multi-file texture package safely 
    inside the single-threaded layout tree window wrapper.
    """
    global _active_texture_window
    print("[Texture Package Bridge] Bootstrapping multi-file sub-modules...")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    # HYBRID STATE REUSE CHECK: 
    main_window = None
    for widget in QtWidgets.QApplication.topLevelWidgets():
        if isinstance(widget, QtWidgets.QMainWindow):
            main_window = widget
            break

    if main_window:
        existing_dock = main_window.findChild(QtWidgets.QDockWidget, "MH2_TextureGenerator_Dock")
        if existing_dock is not None:
            if existing_dock.isVisible():
                existing_dock.hide()
                print("[Texture Package Bridge] Left panel hidden. Workspace geometry collapsed.")
            else:
                existing_dock.show()
                existing_dock.raise_()
                print("[Texture Package Bridge] Pulled single left instance back into layout focus.")
            return _active_texture_window

    try:
        import maketexture_qt

        # Create the independent widget container canvas
        _active_texture_window = QtWidgets.QWidget()
        _active_texture_window.setWindowTitle(TOOL_NAME)
        _active_texture_window.setMinimumWidth(380)
        _active_texture_window.resize(380, 560)
        
        tool_layout = QtWidgets.QVBoxLayout(_active_story_window if '_active_story_window' in locals() else _active_texture_window)
        tool_layout.setContentsMargins(6, 6, 6, 6)

        # THE SMART HOOK HUNTER:
        target_func = None
        possible_hooks = ["init_ui", "initialize_ui", "register_tool", "build_panel", "setup_ui", "init_app", "main"]
        
        for hook_name in possible_hooks:
            if hasattr(maketexture_qt, hook_name):
                target_func = getattr(maketexture_qt, hook_name)
                print(f"[Texture Hunter] Successfully matched entry hook function: '{hook_name}'")
                break

        if not target_func:
            for attr_name in dir(maketexture_qt):
                attr_val = getattr(maketexture_qt, attr_name)
                if callable(attr_val) and not attr_name.startswith("__") and attr_name not in ["load_extension", "unload_extension"]:
                    target_func = attr_val
                    print(f"[Texture Hunter Smart Fallback] Locked onto active package function: '{attr_name}'")
                    break

        # Fire the function safely 
        if target_func:
            target_func(tool_layout, app_reference)
            print("[Texture Package Bridge] UI framework mounted completely.")
        else:
            print("[Texture Package Error] Found the files, but could not locate any layout initialization functions inside your package.")

        # ================================
        # HYBRID DOCKING SWITCH PIPELINE
        # ================================
        if main_window:
            # Inside MakeHuman 2: Wrap and dock it smoothly on the left sidebar
            dock = QtWidgets.QDockWidget("Texture Generator Console", main_window)
            dock.setObjectName("MH2_TextureGenerator_Dock")
            dock.setWidget(_active_texture_window)
            dock.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
            
            main_window.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock)
            dock.show()
            print("[Texture Engine] Natively docked inside MakeHuman 2 workspace left sidebar.")
        else:
            # Standalone Mode: Pop it open as its own independent window shell
            _active_texture_window.show()
            print("[Texture Engine] Running smoothly as a standalone environment window.")

        return _active_texture_window

    except Exception as e:
        import traceback
        print(f"[Texture Package Fatal] Failed to bootstrap package modules: {e}")
        traceback.print_exc()
        return None

def unload_extension():
    """Safely closes the texture widget workspace on layout unchecks."""
    global _active_texture_window
    print("[Texture Package Bridge] Cleaning workspace memory blocks...")
    
    for widget in QtWidgets.QApplication.topLevelWidgets():
        if isinstance(widget, QtWidgets.QMainWindow):
            dock = widget.findChild(QtWidgets.QDockWidget, "MH2_TextureGenerator_Dock")
            if dock:
                widget.removeDockWidget(dock)
                dock.deleteLater()
                break
                
    if _active_texture_window is not None:
        try:
            _active_texture_window.close()
        except Exception:
            pass
    _active_texture_window = None
