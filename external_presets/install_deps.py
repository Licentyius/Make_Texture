######################################################
#
# Install Dependencies for MaketexureQT by Elvaerwyn
#
######################################################

import sys
import subprocess

# 1. Define your full requirements for the standalone version
STANDALONE_REQS = [
    "numpy>=1.20.0",
    "scipy>=1.7.0",
    "pillow>=9.0.0",
    "matplotlib>=3.5.0",
    "PySide6>=6.2.0"
]

def check_and_install():
    # 2. Check if we are running inside MakeHuman 2
    # MH2 usually embeds its own python environment or has specific module signatures
    is_inside_makehuman = False
    
    try:
        # Check for a core MakeHuman module to see if we are in its environment
        import makehuman 
        is_inside_makehuman = True
        print("⚡ Detected MakeHuman 2 environment.")
    except ImportError:
        print("🖥️ Detected Standalone environment.")

    # 3. Determine what actually needs to be installed
    if is_inside_makehuman:
        # Inside MH2, we ONLY install Pillow if it's missing. 
        # (MH2 already ships with PySide6, numpy, scipy, and matplotlib)
        to_install = []
        try:
            import PIL # Test for Pillow
        except ImportError:
            to_install.append("pillow>=9.0.0")
    else:
        # Standalone users need everything
        to_install = STANDALONE_REQS

    # 4. Run the pip installer if there are missing packages
    if to_install:
        print(sys.executable)
        print(f"Installing missing requirements: {', '.join(to_install)}")
        try:
            # sys.executable ensures it installs directly to the active Python environment
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + to_install)
            print("✅ Installation completed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Installation failed: {e}")
    else:
        print("✅ All required packages are already available. Nothing to install.")

if __name__ == "__main__":
    check_and_install()
