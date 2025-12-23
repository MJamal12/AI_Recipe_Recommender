# run_gui.py
"""
Launcher script for the Streamlit GUI
Just hit the play button to run the recipe recommender!
"""

import subprocess
import sys
import os

if __name__ == "__main__":
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    gui_path = os.path.join(script_dir, "gui.py")
    
    subprocess.run([sys.executable, "-m", "streamlit", "run", gui_path])