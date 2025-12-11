import os
import subprocess
import sys

def build():
    print("Installing PyInstaller if missing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "ttkbootstrap", "psutil"])

    print("Building Executable...")
    # Clean previous
    if os.path.exists("build"):
        import shutil
        shutil.rmtree("build")
    if os.path.exists("dist"):
        import shutil
        shutil.rmtree("dist")

    # Command
    # We use --hidden-import to ensure ttkbootstrap themes are loaded
    # --noconsole: suppresses terminal
    # --onefile: single EXE
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "ThreadManagerPro",
        "--onefile",
        "--noconsole",
        "--clean",
        "--hidden-import", "ttkbootstrap",
        "--collect-all", "ttkbootstrap",
        "src/main.py"
    ]
    
    print(f"Running: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    
    print("\n[SUCCESS] Build complete! Check the 'dist' folder for 'ThreadManagerPro.exe'")

if __name__ == "__main__":
    build()
