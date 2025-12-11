import sys
import os

# Ensure src is in path if run mainly
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from src.ui.app_window import AppWindow

def main():
    app = AppWindow()
    app.mainloop()

if __name__ == "__main__":
    main()
