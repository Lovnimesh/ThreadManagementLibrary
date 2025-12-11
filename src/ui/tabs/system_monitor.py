import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from src.core.monitor import sys_monitor

class SystemMonitorTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        self.pack(fill=BOTH, expand=YES)
        
        # --- Top Section: Statistics ---
        self.stats_frame = ttk.Frame(self)
        self.stats_frame.pack(fill=X, pady=(0, 10))
        
        # CPU Widget
        self.cpu_frame = ttk.Labelframe(self.stats_frame, text="CPU Usage", padding=10, bootstyle="info")
        self.cpu_frame.pack(side=LEFT, fill=BOTH, expand=YES, padx=5)
        self.cpu_bar = ttk.Meter(
            self.cpu_frame,
            metersize=120,
            amountused=0,
            metertype="semi",
            subtext="CPU %",
            interactive=False,
            bootstyle="info",
            stripethickness=10
        )
        self.cpu_bar.pack()

        # RAM Widget
        self.ram_frame = ttk.Labelframe(self.stats_frame, text="System RAM Usage", padding=10, bootstyle="warning")
        self.ram_frame.pack(side=LEFT, fill=BOTH, expand=YES, padx=5)
        self.ram_bar = ttk.Meter(
            self.ram_frame,
            metersize=120,
            amountused=0,
            metertype="semi",
            subtext="MEM %",
            interactive=False,
            bootstyle="warning",
            stripethickness=10
        )
        self.ram_bar.pack()
        
        # Threads Widget (Simple Text or Meter)
        self.thread_frame = ttk.Labelframe(self.stats_frame, text="Threads", padding=10, bootstyle="success")
        self.thread_frame.pack(side=LEFT, fill=BOTH, expand=YES, padx=5)
        self.thread_label = ttk.Label(self.thread_frame, text="0", font=("Helvetica", 24, "bold"), bootstyle="success")
        self.thread_label.pack(expand=True)
        self.thread_sub = ttk.Label(self.thread_frame, text="Total Active Threads")
        self.thread_sub.pack(side=BOTTOM)

        # --- Bottom Section: Process List ---
        self.proc_frame = ttk.Labelframe(self, text="Top Processes (Active)", padding=10)
        self.proc_frame.pack(fill=BOTH, expand=YES)

        # Columns
        cols = ("PID", "Name", "CPU %", "RAM (MB)", "Threads")
        self.tree = ttk.Treeview(self.proc_frame, columns=cols, show="headings", height=10, bootstyle="primary")
        
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor=CENTER)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.proc_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)

        # --- Start Update Loop ---
        self.start_monitoring()

    def start_monitoring(self):
        # Start the backend monitor
        sys_monitor.start()
        self.update_ui()

    def update_ui(self):
        # Fetch stats non-blocking
        stats = sys_monitor.get_stats()
        
        # Update Meters
        self.cpu_bar.configure(amountused=int(stats['cpu']))
        self.ram_bar.configure(amountused=int(stats['ram_percent']))
        self.thread_label.config(text=str(stats['total_threads']))
        
        # Update Tree
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Re-populate (Top 50)
        for p in stats['processes']:
            self.tree.insert("", END, values=(
                p['pid'],
                p['name'],
                f"{p['cpu_percent']:.1f}",
                f"{p['memory_mb']:.1f}",
                p.get('num_threads', 0)
            ))
            
        # Schedule next update
        self.after(1000, self.update_ui)
