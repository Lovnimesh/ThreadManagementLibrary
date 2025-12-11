import tkinter as tk
import ttkbootstrap as ttk
from collections import deque

class GraphWidget(tk.Canvas):
    def __init__(self, master, width=400, height=200, history_size=60, title="Real-time Data", line_color="#00ff00", **kwargs):
        super().__init__(master, width=width, height=height, bg="#111", highlightthickness=0, **kwargs)
        self.history_size = history_size
        self.data = deque([0]*history_size, maxlen=history_size)
        self.line_color = line_color
        self.title_text = title
        
        # Style
        self.grid_color = "#333"
        self.text_color = "#888"
        
        # Init
        self.bind("<Configure>", self.on_resize)
        self.draw_base()

    def add_value(self, value):
        """Adds a value (percentage 0-100 or raw with normalized scaling)."""
        self.data.append(value)
        self.redraw_line()

    def draw_base(self):
        self.delete("base")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 10: w = int(self["width"])
        if h < 10: h = int(self["height"])
        
        # Grid lines (Horizontal)
        for i in range(1, 5):
            y = i * (h / 5)
            self.create_line(0, y, w, y, fill=self.grid_color, tags="base", dash=(2, 4))
            
        # Title
        self.create_text(10, 10, text=self.title_text, fill=self.text_color, anchor="nw", font=("Helvetica", 10), tags="base")

    def redraw_line(self):
        self.delete("line")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 10: w = int(self["width"])
        if h < 10: h = int(self["height"])
        
        # Padding
        pad_bottom = 20
        pad_top = 20
        graph_h = h - pad_bottom - pad_top
        
        # Scale (Assuming 0-100 input for now, dynamic otherwise)
        max_val = 100
        # Dynamic max?
        current_max = max(self.data)
        if current_max > 100: max_val = current_max + 10
        
        if max_val == 0: max_val = 100

        # Points
        points = []
        step_x = w / (self.history_size - 1)
        
        for i, val in enumerate(self.data):
            x = i * step_x
            # Y driven by value (0 at bottom, 100 at top)
            # Invert Y: 0 -> h-pad, 100 -> pad_top
            ratio = val / max_val
            y = (h - pad_bottom) - (ratio * graph_h)
            points.append(x)
            points.append(y)
            
        if len(points) >= 4:
            # Line
            self.create_line(points, fill=self.line_color, width=2, tags="line", smooth=True)
            
            # Fill under line (Poly)
            # Add bottom-right and bottom-left to close poly
            poly_points = points + [w, h-pad_bottom, 0, h-pad_bottom]
            # Tkinter doesn't support alpha on canvas items natively without PIL hacks.
            # We skip transparent fill for simplicity/performance in pure Tk.
            # Or use a stipple for 'fake' transparency?
            # self.create_polygon(poly_points, fill=self.line_color, outline="", stipple="gray25", tags="line")

        # Current Value Text
        last_val = self.data[-1]
        self.create_text(w-10, 10, text=f"{last_val:.1f}", fill=self.line_color, anchor="ne", font=("Helvetica", 12, "bold"), tags="line")

    def on_resize(self, event):
        self.draw_base()
        self.redraw_line()
