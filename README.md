# Thread Management Library (Rebuilt & Optimized)

This project has been rebuilt from scratch for maximum performance, minimal size, and modern UI using `ttkbootstrap`.

## Features
- **System Monitor**: Real-time CPU/RAM/Thread stats + Active Process List (Top 50).
- **HPC Engine**: ThreadPool simulation with visual worker states (Green=Idle, Red=Busy).
- **Optimized**: 
    - Zero UI Lag (Background monitoring thread).
    - Custom Canvas Rendering (No heavy matplotlib dependency).
    - Efficient `psutil` usage.
- **Theme**: Dark/Light/System support.

## How to Run locally
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the app:
   ```bash
   python src/main.py
   ```

## How to Build EXE
1. Run the included build script:
   ```bash
   python build_exe.py
   ```
2. The standalone executable will be in the `dist/` folder.

## Optimization Notes
- **UI Framework**: `ttkbootstrap` was chosen over PySide6 (100MB+ vs ~30MB) and Tkinter (Ugly).
- **Graphing**: Custom `tk.Canvas` drawing used instead of `matplotlib` to save ~50MB in EXE size and improve start-up time.
- **Threading**: `SystemMonitor` runs in a daemon thread. `HPCEngine` uses `concurrent.futures`. Main UI thread is never blocked.
