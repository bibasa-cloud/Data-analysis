# =================================================================================
# APP 1: Signal Analyzer
# =================================================================================
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, colorchooser
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.lines import Line2D
from matplotlib.widgets import SpanSelector
import numpy as np
import os

import Style


class SignalAnalyzer:
    def __init__(self, root):
        self.span_remove = None
        self.span_add = None
        self.span_nav = None
        self.root = root

        # Target column names for import (None means default 1st and 2nd columns)
        self.target_y_col = "Current[A]"
        self.target_x_col = "Voltage[V]"

        self.datasets = None
        self.selected_points = {}

        self.x_label = "X"
        self.y_label = "Y"
        self.canvas = None
        self.ax_main = None
        self.ax_zoom = None
        self.main_scatter = None
        self.zoom_scatter = None
        self.x_plot = None
        self.y_plot = None

        self.setup_ui()

    def setup_ui(self):
        # --- Main Container (הבסיס ל-Grid) ---
        self.main_container = tk.Frame(self.root, bg=Style.BG_COLOR)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # הגדרת המשקלים של השורות - יחס נוקשה של 3:1 בדיוק כמו בגרפים
        self.main_container.rowconfigure(0, weight=3, uniform="main_rows")
        self.main_container.rowconfigure(1, weight=1, uniform="main_rows")
        self.main_container.columnconfigure(0, weight=1)

        # --- TOP PART: Controls + Graph ---
        self.top_container = tk.Frame(self.main_container, bg=Style.BG_COLOR)
        self.top_container.grid(row=0, column=0, sticky="nsew")

        # Controls Strip
        controls_frame = tk.Frame(self.top_container, bg=Style.BG_COLOR, pady=5)
        controls_frame.pack(side=tk.TOP, fill="x")

        # Graph Container
        self.graph_frame = tk.Frame(self.top_container, bg=Style.BG_COLOR, relief="solid")
        self.graph_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.init_graph()

        # --- BOTTOM PART: Results Table ---
        self.bottom_container = tk.Frame(self.main_container, bg=Style.BG_COLOR)
        self.bottom_container.grid(row=1, column=0, sticky="nsew")

        # Header with Buttons
        results_header = tk.Frame(self.bottom_container, bg=Style.BG_COLOR, pady=5)
        results_header.pack(fill="x", padx=10)

        # Using Style factory functions for buttons
        load_btn = Style.create_action_button(results_header, "Upload", self.open_data_loader, Style.COLOR_PRIMARY)
        load_btn.pack(side=tk.LEFT, padx=5, pady=5)

        export_btn = Style.create_action_button(results_header, "Export", self.export_to_excel, Style.COLOR_SUCCESS)
        export_btn.pack(side=tk.RIGHT, padx=5, pady=5)

        # Treeview Area
        tree_frame = tk.Frame(self.bottom_container, bg=Style.BG_COLOR)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        columns = ("Index", "Type", "X-Value", "Y-Value")
        self.results_tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=100, anchor="center")

        self.results_tree.tag_configure('max', foreground='red')
        self.results_tree.tag_configure('min', foreground='green')

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)

        self.results_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def init_graph(self):
        """Runs exactly once to create the Figure and Tkinter Canvas."""
        # Create a blank figure without subplots initially
        self.fig = plt.figure(figsize=(5, 4), dpi=100)
        self.fig.patch.set_facecolor(Style.BG_COLOR)

        # Setup the axes (this keeps the code DRY)
        self.setup_axes()

        # Create and pack the canvas only ONCE
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def setup_axes(self):
        """Clears the figure and prepares fresh axes (used on init and every reload)."""
        # Absolute clearance to avoid zombie events
        self.fig.clf()

        self.ax_main = self.fig.add_subplot(2, 1, 1)
        self.ax_zoom = self.fig.add_subplot(2, 1, 2)

        self.ax_main.set_title("Navigation", fontsize=10)
        self.ax_main.grid(True, linestyle='--', alpha=0.5)

        self.ax_zoom.set_title("Work Area (Left Click: Add, Right Click: Remove)", fontsize=10)
        self.ax_zoom.grid(True, linestyle='--', alpha=0.5)

        # Dynamic spacing layout
        self.fig.tight_layout(pad=2.0)

        # Critical reset of helper variables
        self.main_scatter = None
        self.zoom_scatter = None

    def plot_graphs(self):
        """Plots the data on completely fresh axes to avoid zombie selectors."""
        # 1. Reset axes using the helper function (DRY principle)
        self.setup_axes()

        # 2. Draw the actual data
        self.ax_main.plot(self.x_plot, self.y_plot, label='Signal', color='#1f77b4', linewidth=1, alpha=0.7)
        self.ax_main.set_xlim(self.x_plot.min(), self.x_plot.max())

        self.ax_zoom.plot(self.x_plot, self.y_plot, color='#1f77b4', linewidth=1.5, alpha=0.8)

        # 3. Attach completely fresh selectors
        self.span_nav = SpanSelector(self.ax_main, self.on_nav_select, 'horizontal', useblit=True,
                                     props=dict(alpha=0.3, facecolor='#2980b9'))
        self.span_add = SpanSelector(self.ax_zoom, self.on_add_select, 'horizontal', useblit=True, button=1,
                                     props=dict(alpha=0.2, facecolor='green'))
        self.span_remove = SpanSelector(self.ax_zoom, self.on_remove_select, 'horizontal', useblit=True, button=3,
                                        props=dict(alpha=0.2, facecolor='red'))

        self.canvas.draw()
        self.update_table()

    def load_file(self, file_path):
        if not file_path: return

        try:
            ext = os.path.splitext(file_path)[1].lower()

            if ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                df = pd.read_csv(file_path, sep=None, engine='python')

            df.columns = df.columns.str.strip()
            if len(df.columns) < 2: return

            self.x_label, self.y_label = self.target_x_col, self.target_y_col

            # Update Headers
            self.results_tree.heading("X-Value", text=self.x_label)
            self.results_tree.heading("Y-Value", text=self.y_label)

            df[self.x_label] = pd.to_numeric(df[self.x_label], errors='coerce')
            df[self.y_label] = pd.to_numeric(df[self.y_label], errors='coerce')

            valid = df[self.x_label].notna() & df[self.y_label].notna()
            if not valid.any(): return

            self.x_plot = df[self.x_label][valid]
            self.y_plot = df[self.y_label][valid]
            self.selected_points = {}
            self.plot_graphs()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def open_data_loader(self):
        """
        Opens a dialog to specify column names and upload a file.
        """
        # FIX: Changed self to self.root to prevent crashing
        dialog = tk.Toplevel(self.root)
        dialog.title("Load Data")
        dialog.geometry("400x250")
        dialog.configure(bg=Style.BG_COLOR)

        # --- Container for Centering Inputs ---
        input_frame = tk.Frame(dialog, bg=Style.BG_COLOR)
        input_frame.pack(expand=True)

        # 1. X Axis Column Input
        tk.Label(input_frame, text="X Column Name:", bg=Style.BG_COLOR,
                 font=Style.HEADER_FONT).grid(row=0, column=0, padx=10, pady=10, sticky="e")

        entry_x = tk.Entry(input_frame, width=20, font=Style.GLOBAL_FONT)
        entry_x.grid(row=0, column=1, padx=10, pady=10)
        entry_x.insert(0, self.target_x_col)

        # 2. Y Axis Column Input
        tk.Label(input_frame, text="Y Column Name:", bg=Style.BG_COLOR,
                 font=Style.HEADER_FONT).grid(row=1, column=0, padx=10, pady=10, sticky="e")

        entry_y = tk.Entry(input_frame, width=20, font=Style.GLOBAL_FONT)
        entry_y.grid(row=1, column=1, padx=10, pady=10)
        entry_y.insert(0, self.target_y_col)

        # --- Upload Logic ---
        def upload_files():
            self.target_x_col = entry_x.get().strip()
            self.target_y_col = entry_y.get().strip()

            if not self.target_x_col or not self.target_y_col:
                messagebox.showwarning("Missing Input", "Please enter both X and Y column names.")
                return

            # Open File Dialog
            file_path = filedialog.askopenfilename(
                title="Select Data File",
                filetypes=[
                    ("Excel Files", "*.xlsx *.xls"),
                    ("Text/CSV Files", "*.txt *.csv"),
                    ("All Files", "*.*")
                ]
            )

            if file_path:
                self.load_file(file_path)
                dialog.destroy()

        # --- Upload Button (Bottom) ---
        btn_frame = tk.Frame(dialog, bg=Style.BG_COLOR)
        btn_frame.pack(side=tk.BOTTOM, pady=30)

        # Using Style factory function
        Style.create_popup_button(btn_frame, "Upload File", upload_files, Style.COLOR_SUCCESS).pack()

    def redraw_markers(self):
        if self.main_scatter: self.main_scatter.remove()
        if self.zoom_scatter: self.zoom_scatter.remove()
        self.main_scatter = None
        self.zoom_scatter = None
        if not self.selected_points:
            self.canvas.draw_idle()
            return

        xs = [d['x'] for d in self.selected_points.values()]
        ys = [d['y'] for d in self.selected_points.values()]
        colors = ['red' if d['type'] == 'Maxima' else 'green' for d in self.selected_points.values()]
        self.main_scatter = self.ax_main.scatter(xs, ys, c=colors, s=30, edgecolors='black', zorder=5)

        zoom_xlim = self.ax_zoom.get_xlim()
        zoom_xs, zoom_ys, zoom_colors = [], [], []
        for d in self.selected_points.values():
            if zoom_xlim[0] <= d['x'] <= zoom_xlim[1]:
                zoom_xs.append(d['x'])
                zoom_ys.append(d['y'])
                zoom_colors.append('red' if d['type'] == 'Maxima' else 'green')

        if zoom_xs:
            self.zoom_scatter = self.ax_zoom.scatter(zoom_xs, zoom_ys, c=zoom_colors, s=80, edgecolors='black',
                                                     zorder=5)
        self.canvas.draw_idle()

    def update_table(self):
        for item in self.results_tree.get_children(): self.results_tree.delete(item)
        for idx in sorted(self.selected_points.keys()):
            data = self.selected_points[idx]
            tag = 'max' if data['type'] == 'Maxima' else 'min'
            self.results_tree.insert("", "end", values=(idx, data['type'], f"{data['x']:.5f}", f"{data['y']:.5g}"),
                                     tags=(tag,))

    def on_nav_select(self, xmin, xmax):
        self.ax_zoom.set_xlim(xmin, xmax)
        mask = (self.x_plot >= xmin) & (self.x_plot <= xmax)
        if mask.any():
            region_y = self.y_plot[mask]
            y_min, y_max = region_y.min(), region_y.max()
            margin = (y_max - y_min) * 0.05 if y_max != y_min else 1.0
            self.ax_zoom.set_ylim(y_min - margin, y_max + margin)
        self.redraw_markers()

    def on_add_select(self, xmin, xmax):
        mask = (self.x_plot >= xmin) & (self.x_plot <= xmax)
        if not mask.any() or len(self.x_plot[mask]) < 3: return

        region_y = self.y_plot[mask]
        max_idx, min_idx = region_y.argmax(), region_y.argmin()
        val_max, val_min = region_y.iloc[max_idx], region_y.iloc[min_idx]
        mean_val = region_y.mean()

        if abs(val_max - mean_val) > abs(val_min - mean_val):
            c_idx, c_type = region_y.index[max_idx], "Maxima"
        else:
            c_idx, c_type = region_y.index[min_idx], "Minima"

        self.selected_points[c_idx] = {'x': self.x_plot.loc[c_idx], 'y': self.y_plot.loc[c_idx], 'type': c_type}
        self.redraw_markers()
        self.update_table()

    def on_remove_select(self, xmin, xmax):
        to_del = [i for i, d in self.selected_points.items() if xmin <= d['x'] <= xmax]
        for i in to_del: del self.selected_points[i]
        if to_del:
            self.redraw_markers()
            self.update_table()

    def export_to_excel(self):
        if not self.selected_points: return
        data = [{"Index": i, "Type": p['type'], self.x_label: p['x'], self.y_label: p['y']} for i, p in
                self.selected_points.items()]
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=(("Excel", "*.xlsx"), ("CSV", "*.csv")))
        if path:
            try:
                pd.DataFrame(data).to_excel(path, index=False) if not path.endswith('.csv') else pd.DataFrame(
                    data).to_csv(path, index=False)
            except Exception as e:
                messagebox.showerror("Error", str(e))