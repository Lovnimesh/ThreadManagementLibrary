
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import time
import queue
import psutil
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import sys
import os

# Ensure we can import from the parent directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import monitor
from threadlib import ThreadPool, ThreadPoolStats

ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class ThreadManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Threads Management - Professional")
        self.geometry("1100x800")

        # Data & State
        self.thread_pool = None
        self.monitor_thread = None
        self.monitor_running = True
        self.monitor_queue = queue.Queue()
        
        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._init_sidebar()
        self._init_main_area()
        
        # Start background monitor
        self.start_monitoring()
        
        # Start UI updater for monitor
        self.after(100, self.check_monitor_queue)

    def _init_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="ThreadManager\nPro", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.sidebar_button_1 = ctk.CTkButton(self.sidebar_frame, text="Dashboard", command=self.show_dashboard)
        self.sidebar_button_1.grid(row=1, column=0, padx=20, pady=10)

        self.sidebar_button_2 = ctk.CTkButton(self.sidebar_frame, text="HPC Engine", command=self.show_hpc)
        self.sidebar_button_2.grid(row=2, column=0, padx=20, pady=10)

        # Appearance Mode
        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 20))
        self.appearance_mode_optionemenu.set("Dark")

    def _init_main_area(self):
        self.tabview = ctk.CTkTabview(self, width=800)
        self.tabview.grid(row=0, column=1, padx=(10, 10), pady=(10, 10), sticky="nsew")
        self.tabview.add("System Monitor")
        self.tabview.add("HPC Engine")
        
        # We start with System Monitor
        self.setup_system_tab()
        self.setup_hpc_tab()

    def show_dashboard(self):
        self.tabview.set("System Monitor")

    def show_hpc(self):
        self.tabview.set("HPC Engine")

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

    # ---------------- SYSTEM MONITOR ----------------
    def setup_system_tab(self):
        self.tab_sys = self.tabview.tab("System Monitor")
        self.tab_sys.grid_columnconfigure(0, weight=1)
        
        # Metrics Frame
        self.metrics_frame = ctk.CTkFrame(self.tab_sys)
        self.metrics_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        self.lbl_cpu = ctk.CTkLabel(self.metrics_frame, text="CPU: -%", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_cpu.pack(side="left", padx=20, pady=15)
        
        self.lbl_mem = ctk.CTkLabel(self.metrics_frame, text="RAM: -%", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_mem.pack(side="left", padx=20, pady=15)
        
        self.lbl_threads = ctk.CTkLabel(self.metrics_frame, text="Threads: -", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_threads.pack(side="left", padx=20, pady=15)

        # Filter
        self.filter_frame = ctk.CTkFrame(self.tab_sys)
        self.filter_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(self.filter_frame, text="Filter Process:").pack(side="left", padx=10)
        self.entry_filter = ctk.CTkEntry(self.filter_frame, placeholder_text="e.g. python")
        self.entry_filter.pack(side="left", padx=10, fill="x", expand=True)
        ctk.CTkButton(self.filter_frame, text="Force Refresh", command=self.trigger_refresh).pack(side="right", padx=10)

        # Process List (Scrollable Frame imitating a list)
        self.proc_list_frame = ctk.CTkScrollableFrame(self.tab_sys, height=400, label_text="Top Processes")
        self.proc_list_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.tab_sys.grid_rowconfigure(2, weight=1)
        
        # Headers
        header_frame = ctk.CTkFrame(self.proc_list_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=5, pady=2)
        headers = ["PID", "Name", "Threads", "CPU", "RAM"]
        widths = [60, 200, 80, 80, 80]
        for h, w in zip(headers, widths):
             ctk.CTkLabel(header_frame, text=h, width=w, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=2)

        self.proc_rows = []

    def start_monitoring(self):
        def monitor_loop():
            while self.monitor_running:
                try:
                    metrics = monitor.get_system_metrics()
                    filter_txt = "" 
                    # Note: accessing GUI element from thread is unsafe, but here we just need to pass the filter text.
                    # Ideally we read it from a variable that the GUI updates properly or just pass it in.
                    # For simplicity, we won't filter constantly in the background loop based on changing GUI text immediately
                    # unless we use a thread-safe variable. Let's just push full list or filter if we can.
                    # We will push the whole heavy lifting to here.
                    
                    # We can't read self.entry_filter.get() safely here without risk. 
                    # So we will just get data and filter in UI or send a request.
                    # BETTER APPROACH: Just get data here.
                    
                    procs = monitor.get_process_list(limit=30) # get top 30
                    
                    self.monitor_queue.put(("STATS", metrics, procs))
                except Exception as e:
                    print(f"Monitor Error: {e}")
                
                time.sleep(2) # Update every 2 seconds
                
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()

    def trigger_refresh(self):
        # We can force a refresh if we want, but the loop handles it.
        pass

    def check_monitor_queue(self):
        try:
            while True:
                msg_type, metrics, procs_df = self.monitor_queue.get_nowait()
                if msg_type == "STATS":
                    self.lbl_cpu.configure(text=f"CPU: {metrics['cpu_percent']}%")
                    self.lbl_mem.configure(text=f"RAM: {metrics['memory_percent']}%")
                    self.lbl_threads.configure(text=f"Threads: {metrics['total_threads']}")
                    
                    self.update_process_list(procs_df)
        except queue.Empty:
            pass
        finally:
            self.after(500, self.check_monitor_queue)

    def update_process_list(self, df):
        # Clear old rows efficiently
        for widget in self.proc_rows:
            widget.destroy()
        self.proc_rows.clear()
        
        filter_txt = self.entry_filter.get().lower()

        # Add new rows
        if not df.empty:
            for _, row in df.iterrows():
                name = str(row['Name'])
                if filter_txt and filter_txt not in name.lower():
                    continue
                    
                row_frame = ctk.CTkFrame(self.proc_list_frame, fg_color="transparent")
                row_frame.pack(fill="x", padx=5, pady=2)
                
                vals = [str(row['PID']), name, str(row['Threads']), f"{row['CPU %']}%", f"{row['Memory %']}%"]
                widths = [60, 200, 80, 80, 80]
                
                for v, w in zip(vals, widths):
                    lbl = ctk.CTkLabel(row_frame, text=v, width=w, anchor="w")
                    lbl.pack(side="left", padx=2)
                
                self.proc_rows.append(row_frame)

    # ---------------- HPC ENGINE ----------------
    def setup_hpc_tab(self):
        self.tab_hpc = self.tabview.tab("HPC Engine")
        self.tab_hpc.grid_columnconfigure(0, weight=1)
        self.tab_hpc.grid_rowconfigure(1, weight=1) # Chart expands
        
        # Controls
        ctrl = ctk.CTkFrame(self.tab_hpc)
        ctrl.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        ctk.CTkLabel(ctrl, text="Workers:").pack(side="left", padx=10)
        self.entry_workers = ctk.CTkEntry(ctrl, width=60)
        self.entry_workers.insert(0, "8")
        self.entry_workers.pack(side="left", padx=5)
        
        self.btn_init = ctk.CTkButton(ctrl, text="Init Pool", command=self.init_pool, fg_color="green")
        self.btn_init.pack(side="left", padx=20)
        
        self.lbl_pool_status = ctk.CTkLabel(ctrl, text="Status: STOPPED", text_color="red")
        self.lbl_pool_status.pack(side="left", padx=10)
        
        # Task Submission
        ctk.CTkLabel(ctrl, text="|").pack(side="left", padx=10)
        
        self.slider_tasks = ctk.CTkSlider(ctrl, from_=100, to=5000, number_of_steps=50)
        self.slider_tasks.set(1000)
        self.slider_tasks.pack(side="left", padx=10)
        
        self.btn_fire = ctk.CTkButton(ctrl, text="Fire Workload", command=self.submit_workload, fg_color="orange")
        self.btn_fire.pack(side="left", padx=10)

        # Charts Area
        self.chart_frame = ctk.CTkFrame(self.tab_hpc)
        self.chart_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        # Matplotlib setup
        self.setup_chart()

    def setup_chart(self):
        # Use dark style for plot
        plt.style.use('dark_background')
        
        self.fig, self.ax = plt.subplots(figsize=(6, 4), dpi=100)
        self.fig.patch.set_facecolor('#2b2b2b') # Match CTk dark background approx
        self.ax.set_facecolor('#2b2b2b')
        
        self.ax.set_title("Worker Activity", color='white')
        self.ax.set_xlabel("Time", color='white')
        self.line_active, = self.ax.plot([], [], label="Active Workers", color='#00ff00')
        self.line_busy, = self.ax.plot([], [], label="Busy Workers", color='#ff9900')
        self.ax.legend()
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.chart_time = []
        self.chart_active = []
        self.chart_busy = []
        self.start_time = time.time()
        
        self.ani = FuncAnimation(self.fig, self.animate_chart, interval=500, blit=False)

    def init_pool(self):
        try:
            if self.thread_pool:
                self.thread_pool.shutdown(wait=False)
            
            w = int(self.entry_workers.get())
            self.thread_pool = ThreadPool(min_workers=4, max_workers=w, idle_timeout=2.0)
            
            self.lbl_pool_status.configure(text="Status: RUNNING", text_color="green")
            self.btn_init.configure(state="disabled")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def submit_workload(self):
        if not self.thread_pool:
            messagebox.showwarning("Warning", "Init pool first!")
            return
            
        count = int(self.slider_tasks.get())
        
        def task_cpu(idx):
            x = 0
            for i in range(5000): 
                x += (i*i)%97
            return x

        def submitter():
            for i in range(count):
                self.thread_pool.submit(task_cpu, i)
        
        threading.Thread(target=submitter, daemon=True).start()
        print(f"Submitted {count} tasks")

    def animate_chart(self, i):
        if self.thread_pool:
            stats = self.thread_pool.get_stats()
            active = self.thread_pool.active_worker_count
            busy = stats.current_running
            
            elapsed = time.time() - self.start_time
            self.chart_time.append(elapsed)
            self.chart_active.append(active)
            self.chart_busy.append(busy)
            
            if len(self.chart_time) > 50:
                self.chart_time.pop(0)
                self.chart_active.pop(0)
                self.chart_busy.pop(0)
            
            self.line_active.set_data(self.chart_time, self.chart_active)
            self.line_busy.set_data(self.chart_time, self.chart_busy)
            
            self.ax.set_xlim(min(self.chart_time), max(self.chart_time) + 1)
            self.ax.set_ylim(0, max(max(self.chart_active)+5, 10))


    def on_closing(self):
        self.monitor_running = False
        if self.thread_pool:
            self.thread_pool.shutdown(wait=False)
        self.destroy()

if __name__ == "__main__":
    app = ThreadManagerApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
