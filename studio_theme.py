#######################################################
#
#  Elvaerwyn_2026 studio_theme.py for Maketextureqt v1.0
#  Template WIP
#
#######################################################

import tkinter as tk
from tkinter import ttk

def apply_studio_dark_theme():
    """
    Constructs a dark studio interface theme using Tcl/ttk Style styling nodes.
    Acts exactly like a QSS configuration block for easy downstream editing.
    """
    style = ttk.Style()
    style.theme_use('clam')

    # ==========================================
    # CORE COLOR DESIGN PALETTE (Devs shall EDIT HERE LATER)
    # ==========================================
    COLOR_BG_DARK      = "#18181c"  # Main window backing field
    COLOR_PANEL_BG     = "#1e1e24"  # Control panels and frame cards
    COLOR_ACCENT       = "#ffaa00"  # High-visibility triggers / Highlights
    COLOR_TEXT_MAIN    = "#f4f4f6"  # Primary labeling fields text
    COLOR_TEXT_MUTED   = "#a0a0aa"  # Sub-headings and structural markers
    COLOR_BORDER       = "#2d2d34"  # Field separators and split margins
    COLOR_FIELD_BG     = "#121214"  # Background element for entries/dropdowns
    COLOR_BUTTON_HOVER = "#e69900"  # Interactive cursor rollover shading

    # ===============================
    # STYLE COMPONENT CONFIGURATIONS
    # ===============================
    
    # 1. Root & Window Frame Styles
    style.configure('.',
        background=COLOR_BG_DARK,
        foreground=COLOR_TEXT_MAIN,
        troughcolor=COLOR_FIELD_BG,
        bordercolor=COLOR_BORDER,
        darkcolor=COLOR_BORDER,
        lightcolor=COLOR_BORDER,
        font=('Helvetica', 10)
    )

    style.configure('TFrame', background=COLOR_PANEL_BG)
    style.configure('TLabel', background=COLOR_PANEL_BG, foreground=COLOR_TEXT_MAIN)

    # 2. Advanced Section Header Typography Nodes
    style.configure('Heading.TLabel',
        background=COLOR_PANEL_BG,
        foreground=COLOR_ACCENT,
        font=('Helvetica', 10, 'bold')
    )
    style.configure('SubHeading.TLabel',
        background=COLOR_PANEL_BG,
        foreground=COLOR_TEXT_MUTED,
        font=('Helvetica', 9, 'bold')
    )

    # 3. Dropdown Menu Combobox Mappings
    style.configure('TCombobox',
        arrowcolor=COLOR_TEXT_MAIN,
        background=COLOR_PANEL_BG,
        fieldbackground=COLOR_FIELD_BG,
        foreground=COLOR_TEXT_MAIN,
        bordercolor=COLOR_BORDER,
        lightcolor=COLOR_BORDER,
        darkcolor=COLOR_BORDER,
        padding=4
    )
    style.map('TCombobox',
        fieldbackground=[('readonly', COLOR_FIELD_BG)],
        foreground=[('readonly', COLOR_TEXT_MAIN)]
    )

    # 4. Standard Input Entry Grids
    style.configure('TEntry',
        fieldbackground=COLOR_FIELD_BG,
        foreground=COLOR_TEXT_MAIN,
        bordercolor=COLOR_BORDER,
        lightcolor=COLOR_BORDER,
        darkcolor=COLOR_BORDER,
        padding=4
    )

    # 5. Checkbox Toggle Nodes
    style.configure('TCheckbutton',
        background=COLOR_PANEL_BG,
        foreground=COLOR_TEXT_MAIN,
        indicatorcolor=COLOR_FIELD_BG,
        indicatorbackground=COLOR_FIELD_BG
    )
    style.map('TCheckbutton',
        indicatorcolor=[('selected', COLOR_ACCENT)],
        background=[('active', COLOR_PANEL_BG)]
    )

    # 6. Master Studio Operational Triggers (Action.TButton)
    style.configure('Action.TButton',
        font=('Helvetica', 11, 'bold'),
        foreground='#101014',
        background=COLOR_ACCENT,
        bordercolor=COLOR_BORDER,
        focuscolor=COLOR_ACCENT,
        padding=6
    )
    style.map('Action.TButton',
        background=[('active', COLOR_BUTTON_HOVER)],
        foreground=[('active', '#000000')]
    )

    # 7. Standard Global Form Fields Utilities Buttons
    style.configure('TButton',
        font=('Helvetica', 9),
        foreground=COLOR_TEXT_MAIN,
        background=COLOR_BORDER,
        bordercolor=COLOR_BG_DARK,
        padding=4
    )
    style.map('TButton',
        background=[('active', COLOR_PANEL_BG)]
    )

    # 8. Main Framework Tab Navigator Configuration Nodes
    style.configure('TNotebook', background=COLOR_BG_DARK, bordercolor=COLOR_BORDER)
    style.configure('TNotebook.Tab',
        background=COLOR_PANEL_BG,
        foreground=COLOR_TEXT_MUTED,
        bordercolor=COLOR_BORDER,
        padding=5,  # FIXED: Restored clean numeric value
        font=('Helvetica', 9, 'bold')
    )
    style.map('TNotebook.Tab',
        background=[('selected', COLOR_BG_DARK)],
        foreground=[('selected', COLOR_ACCENT)]
    )

    # 9. Real-time Numerical Slider Configurations
    style.configure('Horizontal.TScale',
        background=COLOR_PANEL_BG,
        troughcolor=COLOR_FIELD_BG,
        sliderlength=16,
        sliderthickness=16,
        bordercolor=COLOR_BORDER
    )

