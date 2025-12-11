import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import math
from src.core.engine import hpc_engine, Priority

class HPCEngineTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        self.pack(fill=BOTH, expand=YES)
        
        # --- Top Control Panel ---
        self.control_frame = ttk.Labelframe(self, text="HPC Controls", padding=10, bootstyle="secondary")
        self.control_frame.pack(fill=X, pady=(0, 10))
        
        # 1. Worker Scaling
        self.scale_frame = ttk.Frame(self.control_frame)
        self.scale_frame.pack(side=LEFT, padx=5)
        ttk.Label(self.scale_frame, text="Workers:").pack(side=LEFT)
        
        self.btn_sub_worker = ttk.Button(self.scale_frame, text="-", width=2, command=self.remove_worker, bootstyle="warning-outline")
        self.btn_sub_worker.pack(side=LEFT, padx=2)
        
        n_workers = hpc_engine.num_workers
        self.worker_count_label = ttk.Label(self.scale_frame, text=str(n_workers), width=3, anchor=CENTER)
        self.worker_count_label.pack(side=LEFT, padx=2)
        
        self.btn_add_worker = ttk.Button(self.scale_frame, text="+", width=2, command=self.add_worker, bootstyle="success-outline")
        self.btn_add_worker.pack(side=LEFT, padx=2)

        ttk.Separator(self.control_frame, orient=VERTICAL).pack(side=LEFT, fill=Y, padx=10)

        # 2. Workload Config
        self.work_frame = ttk.Frame(self.control_frame)
        self.work_frame.pack(side=LEFT, padx=5)
        
        ttk.Label(self.work_frame, text="Task Type:").pack(side=LEFT)
        self.type_var = tk.StringVar(value="CPU")
        self.type_combo = ttk.Combobox(self.work_frame, textvariable=self.type_var, values=["CPU", "IO", "Mixed"], width=6, state="readonly")
        self.type_combo.pack(side=LEFT, padx=2)
        
        ttk.Label(self.work_frame, text="Priority:").pack(side=LEFT, padx=(5,0))
        self.prio_var = tk.StringVar(value="Normal")
        self.prio_combo = ttk.Combobox(self.work_frame, textvariable=self.prio_var, values=["High", "Normal", "Low"], width=7, state="readonly")
        self.prio_combo.pack(side=LEFT, padx=2)

        self.btn_fire = ttk.Button(self.work_frame, text="FIRE (x200)", command=self.fire_load, bootstyle="danger")
        self.btn_fire.pack(side=LEFT, padx=5)

        ttk.Separator(self.control_frame, orient=VERTICAL).pack(side=LEFT, fill=Y, padx=10)

        # 3. Queue Control
        self.q_frame = ttk.Frame(self.control_frame)
        self.q_frame.pack(side=LEFT, padx=5)
        
        self.btn_pause = ttk.Button(self.q_frame, text="Pause", command=self.toggle_pause, bootstyle="warning")
        self.btn_pause.pack(side=LEFT, padx=2)
        
        self.btn_cancel = ttk.Button(self.q_frame, text="Clear Queue", command=self.clear_queue, bootstyle="secondary-outline")
        self.btn_cancel.pack(side=LEFT, padx=2)
        
        # --- Stats Bar ---
        self.stats_frame = ttk.Frame(self)
        self.stats_frame.pack(fill=X, pady=(0, 5))
        
        self.lbl_pending = ttk.Label(self.stats_frame, text="Pending: 0", bootstyle="warning")
        self.lbl_pending.pack(side=LEFT, padx=10)
        
        self.lbl_active = ttk.Label(self.stats_frame, text="Running: 0", bootstyle="info")
        self.lbl_active.pack(side=LEFT, padx=10)
        
        self.lbl_completed = ttk.Label(self.stats_frame, text="Completed: 0", bootstyle="success")
        self.lbl_completed.pack(side=LEFT, padx=10)
        
        self.lbl_throughput = ttk.Label(self.stats_frame, text="Status: Ready", bootstyle="secondary")
        self.lbl_throughput.pack(side=RIGHT, padx=10)

        # --- Visualization Area ---
        self.vis_frame = ttk.Labelframe(self, text="Cluster Visualization", padding=10)
        self.vis_frame.pack(fill=BOTH, expand=YES)
        
        self.canvas = tk.Canvas(self.vis_frame, bg="#1e1e1e", highlightthickness=0)
        self.canvas.pack(fill=BOTH, expand=YES)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        
        # Tooltip Label (Floating)
        self.tooltip = ttk.Label(self.canvas, text="", bootstyle="inverse-light", relief="solid", padding=5)
        self.tooltip_visible = False
        
        # Internal State
        self.rects = [] # List of IDs
        self.worker_map = {} # Map ID -> Worker Index
        self.is_paused = False
        
        # Initial Render
        self.update_grid()
        self.animate_loop()

    def add_worker(self):
        hpc_engine.add_worker()
        self.update_grid()

    def remove_worker(self):
        hpc_engine.remove_worker()
        self.update_grid()

    def toggle_pause(self):
        if self.is_paused:
            hpc_engine.resume_workload()
            self.btn_pause.configure(text="Pause", bootstyle="warning")
            self.lbl_throughput.configure(text="Status: Resumed")
            self.is_paused = False
        else:
            hpc_engine.pause_workload()
            self.btn_pause.configure(text="Resume", bootstyle="success")
            self.lbl_throughput.configure(text="Status: PAUSED")
            self.is_paused = True

    def clear_queue(self):
        hpc_engine.cancel_all_tasks()
        self.lbl_throughput.configure(text="Status: Queue Cleared")

    def fire_load(self):
        p_text = self.prio_var.get()
        t_type = self.type_var.get()
        
        p_map = {"High": Priority.HIGH, "Normal": Priority.NORMAL, "Low": Priority.LOW}
        prio = p_map.get(p_text, Priority.NORMAL)
        
        # Increased to 200 tasks to ensure visibility on 64-core view
        hpc_engine.fire_workload(task_count=200, type=t_type, priority=prio)

    def update_grid(self):
        """Re-draws the grid squares."""
        self.canvas.delete("worker") # clear rects
        self.rects = []
        self.worker_map = {}
        
        n_workers = hpc_engine.num_workers
        self.worker_count_label.configure(text=str(n_workers))
        
        if n_workers == 0: return

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 10: w = 800
        if h < 10: h = 500
        
        cols = int(math.ceil(math.sqrt(n_workers * (w/h))))
        if cols == 0: cols = 1
        
        cell_w = w / cols
        cell_h = cell_w # make squares
        
        # If height overflow, shrink
        if (n_workers // cols + 1) * cell_h > h:
            cell_h = h / (n_workers // cols + 1)
            cell_w = cell_h

        for i in range(n_workers):
            r = i // cols
            c = i % cols
            
            x1 = c * cell_w + 2
            y1 = r * cell_h + 2
            x2 = x1 + cell_w - 4
            y2 = y1 + cell_h - 4
            
            rect_id = self.canvas.create_rectangle(x1, y1, x2, y2, fill="#2ecc71", outline="", tags="worker")
            self.rects.append(rect_id)
            self.worker_map[rect_id] = i

    def animate_loop(self):
        # 1. Get States
        stats = hpc_engine.get_stats()
        details = hpc_engine.get_worker_details()
        
        # 2. Update Labels
        self.lbl_pending.configure(text=f"Pending: {stats['pending_tasks']}")
        self.lbl_active.configure(text=f"Running: {stats['active_workers']}")
        self.lbl_completed.configure(text=f"Completed: {stats['total_completed']}")
        
        # 3. Update Visuals
        # If count mismatch, rebuild grid (lazy dynamic scaling update)
        if len(self.rects) != stats['total_workers']:
            self.update_grid()
            # If still mismatch (race condition), skip frame
            if len(self.rects) != len(details):
                 self.after(100, self.animate_loop)
                 return

        for i, rect_id in enumerate(self.rects):
            if i >= len(details): break
            
            info = details[i]
            if info['busy']:
                color = "#e74c3c" # Red (Normal)
                if info.get("priority") == Priority.HIGH:
                    color = "#9b59b6" # Purple (High)
                elif info.get("priority") == Priority.LOW:
                    color = "#3498db" # Blue (Low)
                elif info.get("current_task") == "IO":
                    color = "#f39c12" # Orange (IO)
                    
                self.canvas.itemconfig(rect_id, fill=color)
            else:
                self.canvas.itemconfig(rect_id, fill="#2ecc71") # Green
        
        self.after(100, self.animate_loop)

    def on_mouse_move(self, event):
        try:
            # Find item under mouse
            x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            found = self.canvas.find_closest(x, y)
            if not found:
                if self.tooltip_visible:
                    self.tooltip.place_forget()
                    self.tooltip_visible = False
                return
                
            item = found[0]
            idx = self.worker_map.get(item)
            
            if idx is not None:
                # Show tooltip
                details = hpc_engine.get_worker_details()
                if idx < len(details):
                    info = details[idx]
                    status = "BUSY" if info['busy'] else "IDLE"
                    text = f"Worker #{info['id']}\nStatus: {status}\nCompleted: {info['completed']}"
                    if info['busy']:
                        text += f"\nTask: {info['current_task']}"
                        if info.get("priority") == Priority.HIGH:
                            text += " (High Prio)"
                    
                    self.tooltip.configure(text=text)
                    self.tooltip.place(x=event.x + 10, y=event.y + 10)
                    self.tooltip_visible = True
                    self.canvas.tag_raise(self.tooltip) # Ensure on top
            else:
                if self.tooltip_visible:
                    self.tooltip.place_forget()
                    self.tooltip_visible = False
        except Exception:
            # Fallback for any canvas weirdness
            pass
