import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from src.ui.tabs.system_monitor import SystemMonitorTab
from src.ui.tabs.hpc_engine import HPCEngineTab
from src.core.monitor import sys_monitor
import webbrowser

class AppWindow(ttk.Window):
    def __init__(self):
        super().__init__(title="Thread Management Library", themename="darkly")
        self.geometry("1100x800")
        self.place_window_center()
        
        # --- Header ---
        self.header = ttk.Frame(self, bootstyle="dark", padding=15)
        self.header.pack(fill=X)
        
        ttk.Label(self.header, text="Thread Management Library", font=("Roboto", 20, "bold"), bootstyle="inverse-dark").pack(side=LEFT)
        
        # Theme Toggle
        self.theme_var = tk.StringVar(value="Dark")
        self.theme_combo = ttk.Combobox(
            self.header, 
            textvariable=self.theme_var, 
            values=["Dark", "Light", "System"],
            state="readonly",
            bootstyle="secondary",
            width=12
        )
        self.theme_combo.pack(side=RIGHT)
        self.theme_combo.bind("<<ComboboxSelected>>", self.change_theme)
        ttk.Label(self.header, text="Theme:", bootstyle="inverse-dark").pack(side=RIGHT, padx=5)

        # --- Tabs ---
        self.notebook = ttk.Notebook(self, bootstyle="primary")
        self.notebook.pack(fill=BOTH, expand=YES, padx=10, pady=10)
        
        self.tab1 = SystemMonitorTab(self.notebook)
        self.tab2 = HPCEngineTab(self.notebook)
        
        self.notebook.add(self.tab1, text="System Dashboard")
        self.notebook.add(self.tab2, text="HPC Cluster Engine")
        
        # Status Bar
        self.status_bar = ttk.Label(self, text="Ready", bootstyle="secondary", padding=5, font=("Helvetica", 8))
        self.status_bar.pack(side=BOTTOM, fill=X)

        # Handle Close
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def change_theme(self, event):
        t = self.theme_var.get()
        style = ttk.Style()
        if t == "Light":
            style.theme_use("flatly") 
        elif t == "Dark":
            style.theme_use("darkly") 
        else:
            style.theme_use("superhero") # System/Default default

    def on_close(self):
        sys_monitor.stop()
        self.destroy()

