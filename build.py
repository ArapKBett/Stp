import sys
import os
from cx_Freeze import setup, Executable

# GUI applications require a different base on Windows
base = None
if sys.platform == "win32":
    base = "Win32GUI"

build_exe_options = {
    "packages": ["os", "PyQt5", "numpy"],
    "excludes": ["tkinter"],
    "include_files": []
}

setup(
    name="STEP Face Coloring",
    version="1.0",
    description="Application for coloring faces of STEP files",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", base=base, target_name="step_face_coloring")]
)
