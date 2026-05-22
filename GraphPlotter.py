import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox, colorchooser
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import random
import math
import numpy as np
import os

import Style


class CustomToolbar(NavigationToolbar2Tk):
    """
    Custom toolbar logic wrapper.
    We won't pack this visually, but we use it to access standard matplotlib functions like save_figure.
    """
    toolitems = [t for t in NavigationToolbar2Tk.toolitems if
                 t[0] not in ('Home', 'Pan', 'Zoom', 'Subplots', 'Back', 'Forward')]


class GraphPlotter:
    def __init__(self, root):
        self.scrollable_frame = None
        self.root = root

        # Variables for graph settings
        self.log_x = tk.BooleanVar(value=False)
        self.log_y = tk.BooleanVar(value=False)

        # Graph labels variables
        self.graph_title = "Data Visualization"
        self.x_label = "X Axis"
        self.y_label = "Y Axis"

        # Target column names for import (None means default 1st and 2nd columns)
        self.target_y_col = "Current[A]"
        self.target_x_col = "Voltage[V]"

        # Tuple to store manual axis limits: (xmin, xmax, ymin, ymax)
        self.axis_limits = {'x_min': None, 'x_max': None, 'y_min': None, 'y_max': None}

        # List to store information about loaded files
        self.datasets = []

        # State for info label
        self.cursor_str = "Cursor: N/A"

        # Main layout setup
        # --- Top Section: The Graph ---
        self.main_container = tk.Frame(self.root, bg=Style.BG_COLOR)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        self.main_container.rowconfigure(0, weight=3, uniform="main_rows")
        self.main_container.rowconfigure(1, weight=1, uniform="main_rows")
        self.main_container.columnconfigure(0, weight=1)

        self.top_frame = tk.Frame(self.main_container, bg=Style.BG_COLOR, relief="solid")
        self.top_frame.grid(row=0, column=0, sticky="nsew")
        self.setup_graph()

        # --- BOTTOM PART: Results Table ---
        self.bottom_frame = tk.Frame(self.main_container, bg=Style.BG_COLOR)
        self.bottom_frame.grid(row=1, column=0, sticky="nsew")

        self.setup_controls()

    def setup_graph(self):
        """Sets up the Matplotlib graph area with maximum space."""
        self.figure, self.ax = plt.subplots(figsize=(5, 4), dpi=100)

        self.figure.tight_layout(rect=[0, 0, 0.85, 1])

        self.ax.set_title(self.graph_title)
        self.ax.set_xlabel(self.x_label)
        self.ax.set_ylabel(self.y_label)
        self.ax.grid(True, linestyle='--', alpha=0.6)

        self.canvas = FigureCanvasTkAgg(self.figure, master=self.top_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

        self.toolbar = CustomToolbar(self.canvas, self.root)
        self.toolbar.pack_forget()

    def setup_controls(self):
        """Sets up the control buttons and the scrollable list of graphs."""
        # --- Info Row (Cursor & Limits) ---
        info_frame = ttk.Frame(self.bottom_frame)
        info_frame.pack(side=tk.TOP, fill=tk.X, padx=15, pady=(5, 2))

        self.info_label = ttk.Label(info_frame, text="Cursor: N/A | Limits: N/A", font=("Consolas", 9))
        self.info_label.pack(side=tk.LEFT)

        # --- Main Action Buttons ---
        actions_frame = ttk.Frame(self.bottom_frame)
        actions_frame.pack(side=tk.TOP, fill=tk.X, padx=15, pady=5)

        upl_btn = Style.create_action_button(actions_frame, "Upload", self.open_data_loader,Style.COLOR_POSITIVE)
        upl_btn.pack(padx=5, side=tk.LEFT)

        exp_btn = Style.create_action_button(actions_frame, "Export Data", self.export_all_data, Style.COLOR_POSITIVE)
        exp_btn.pack(padx=5, side=tk.LEFT)

        ttk.Separator(actions_frame, orient='vertical').pack(side=tk.LEFT, fill='y', padx=10)

        lbl_btn = Style.create_action_button(actions_frame, "Labels", self.open_graph_details_dialog)
        lbl_btn.pack(padx=5, side=tk.LEFT)

        axs_btn = Style.create_action_button(actions_frame, "Edit axes", self.open_limits_dialog)
        axs_btn.pack(padx=5, side=tk.LEFT)

        ttk.Separator(actions_frame, orient='vertical').pack(side=tk.LEFT, fill='y', padx=10)

        crt_btn = Style.create_action_button(actions_frame, "Create Graph", self.create_equation_graph)
        crt_btn.pack(padx=5, side=tk.LEFT)

        gety_btn = Style.create_action_button(actions_frame, "getYforX", self.open_get_y_dialog)
        gety_btn.pack(padx=5, side=tk.LEFT)

        clr_btn = Style.create_action_button(actions_frame, "Delete Graphs", self.clear_all, Style.COLOR_ERASE)
        clr_btn.pack(padx=5, side=tk.RIGHT)

        rst_btn = Style.create_action_button(actions_frame, "Reset axes", self.reset_params,Style.COLOR_ERASE)
        rst_btn.pack(padx=5, side=tk.RIGHT)


        # --- Scrollable List Area (Table) ---
        list_outer_frame = ttk.Frame(self.bottom_frame, style="TFrame")
        list_outer_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=15, pady=(5, 15))

        self.canvas_scroll = tk.Canvas(list_outer_frame, bg=Style.BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_outer_frame, orient="vertical", command=self.canvas_scroll.yview)
        self.scrollable_frame = ttk.Frame(self.canvas_scroll, style="TFrame")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas_scroll.configure(scrollregion=self.canvas_scroll.bbox("all"))
        )

        self.canvas_window = self.canvas_scroll.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas_scroll.configure(yscrollcommand=scrollbar.set)

        self.canvas_scroll.bind("<Configure>", self.on_canvas_configure)

        self.canvas_scroll.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def export_all_data(self):
        """Merges all datasets on their X values and exports to Excel/CSV."""
        if not self.datasets:
            messagebox.showinfo("Export", "There is no data to export.")
            return

        # Open a save file dialog
        file_path = filedialog.asksaveasfilename(
            title="Export Data",
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx"), ("CSV Files", "*.csv")]
        )

        if not file_path:
            return

        try:
            merged_df = None

            for ds in self.datasets:
                # Copy the original, unmodified data for the current graph
                # We only take the first two columns (X and Y)
                df = ds['data'].copy().iloc[:, [0, 1]]
                x_col_name = df.columns[0]
                y_col_name = df.columns[1]

                # Rename the X column to a standard 'X' so pandas can merge them
                # Rename the Y column to the Graph's specific label
                df = df.rename(columns={x_col_name: 'X', y_col_name: ds['label']})

                if merged_df is None:
                    # First graph becomes our base DataFrame
                    merged_df = df
                else:
                    # Perform an "outer join" on the X column.
                    # This ensures that if graphs have slightly different X points,
                    # they are aligned properly without losing any data.
                    merged_df = pd.merge(merged_df, df, on='X', how='outer')

            # Sort the merged data chronologically by the X axis
            merged_df = merged_df.sort_values(by='X')

            # Export based on the user's chosen file extension
            if file_path.endswith('.csv'):
                merged_df.to_csv(file_path, index=False)
            else:
                merged_df.to_excel(file_path, index=False)

            messagebox.showinfo("Success", f"Original data successfully exported to:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export data:\n{e}")
    def on_mouse_move(self, event):
        if event.inaxes:
            self.cursor_str = f"Cursor: x={event.xdata:.4g}, y={event.ydata:.4g}"
        else:
            self.cursor_str = "Cursor: Outside Graph"
        self.update_info_label()

    def update_info_label(self):
        if hasattr(self, 'ax'):
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
            limits_str = f"X Range: [{xlim[0]:.4g}, {xlim[1]:.4g}]   Y Range: [{ylim[0]:.4g}, {ylim[1]:.4g}]"
        else:
            limits_str = "Limits: N/A"

        full_text = f"{self.cursor_str}   |   {limits_str}"
        self.info_label.config(text=full_text)

    def open_data_loader(self):
        """Opens a dialog to specify column names and upload multiple files."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Load Data")
        dialog.configure(bg=Style.BG_COLOR)

        input_frame = tk.Frame(dialog, bg=Style.BG_COLOR)
        input_frame.pack(expand=True)

        tk.Label(input_frame, text="X Column Name:", bg=Style.BG_COLOR,
                 font=Style.GLOBAL_FONT).grid(row=0, column=0, padx=10, pady=10, sticky="e")
        entry_x = tk.Entry(input_frame, width=20)
        entry_x.grid(row=0, column=1, padx=10, pady=10)
        entry_x.insert(0, self.target_x_col)

        tk.Label(input_frame, text="Y Column Name:", bg=Style.BG_COLOR,
                 font=Style.GLOBAL_FONT).grid(row=1, column=0, padx=10, pady=10, sticky="e")
        entry_y = tk.Entry(input_frame, width=20)
        entry_y.grid(row=1, column=1, padx=10, pady=10)
        entry_y.insert(0, self.target_y_col)

        def upload_files():
            self.target_x_col = entry_x.get().strip()
            self.target_y_col = entry_y.get().strip()

            if not self.target_x_col or not self.target_y_col:
                messagebox.showwarning("Missing Input", "Please enter both X and Y column names.")
                return

            file_paths = filedialog.askopenfilenames(
                title="Select Data Files",
                filetypes=[
                    ("Excel Files", "*.xlsx *.xls"),
                    ("Text/CSV Files", "*.txt *.csv"),
                    ("All Files", "*.*")
                ]
            )

            if file_paths:
                self.read_files(file_paths)
                dialog.destroy()

        btn_frame = tk.Frame(dialog, bg=Style.BG_COLOR)
        btn_frame.pack(side=tk.BOTTOM, pady=20)

        # Added .pack() here!
        Style.create_popup_button(btn_frame, "Open Files", upload_files, Style.COLOR_SUCCESS).pack(pady=10)

    def on_canvas_configure(self, event):
        self.canvas_scroll.itemconfig(self.canvas_window, width=event.width)

    def open_column_selector(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Target Columns")
        dialog.configure(bg=Style.BG_COLOR)

        tk.Label(dialog, text="Enter Header Names to use for Axes\n(Leave empty to use default 1st and 2nd columns)",
                 justify=tk.CENTER, bg=Style.BG_COLOR, font=Style.GLOBAL_FONT).pack(pady=10)

        frame = tk.Frame(dialog, bg=Style.BG_COLOR)
        frame.pack(pady=5)

        tk.Label(frame, text="X Column Name:", bg=Style.BG_COLOR).grid(row=0, column=0, padx=5, pady=5, sticky="e")
        e_x = ttk.Entry(frame)
        e_x.insert(0, self.target_x_col)
        e_x.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(frame, text="Y Column Name:", bg=Style.BG_COLOR).grid(row=1, column=0, padx=5, pady=5, sticky="e")
        e_y = ttk.Entry(frame)
        e_y.insert(0, self.target_y_col)
        e_y.grid(row=1, column=1, padx=5, pady=5)

        def save_cols():
            self.target_x_col = e_x.get().strip()
            self.target_y_col = e_y.get().strip()

            msg = "Default (1st & 2nd columns)"
            if self.target_x_col and self.target_y_col:
                msg = f"X='{self.target_x_col}', Y='{self.target_y_col}'"

            messagebox.showinfo("Columns Set", f"Future uploads will use:\n{msg}")
            dialog.destroy()

        # Added .pack() here!
        Style.create_popup_button(frame, "Save Settings", save_cols).pack(pady=15)

    def create_equation_graph(self):
        """Opens a dialog to create a graph from a mathematical equation."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Create Graph from Equation")
        dialog.configure(bg=Style.BG_COLOR)

        tk.Label(dialog, text="Equation y = f(x):", bg=Style.BG_COLOR, font=Style.GLOBAL_FONT).pack(pady=(15, 5))
        tk.Label(dialog,
                 text="(Use 'x' as variable. Must use valid Python/Numpy syntax.\ne.g., 'np.sin(x) * x**2' or 'np.exp(-x)')",
                 bg=Style.BG_COLOR, font=Style.GLOBAL_FONT, fg="#555").pack(pady=5)
        e_eq = ttk.Entry(dialog, width=40)
        e_eq.pack(pady=5)

        frame_range = tk.Frame(dialog, bg=Style.BG_COLOR)
        frame_range.pack(pady=10)

        tk.Label(frame_range, text="X Min:", bg=Style.BG_COLOR).grid(row=0, column=0, padx=5)
        e_xmin = ttk.Entry(frame_range, width=8)
        e_xmin.insert(0, "-10")
        e_xmin.grid(row=0, column=1, padx=5)

        tk.Label(frame_range, text="X Max:", bg=Style.BG_COLOR).grid(row=0, column=2, padx=5)
        e_xmax = ttk.Entry(frame_range, width=8)
        e_xmax.insert(0, "10")
        e_xmax.grid(row=0, column=3, padx=5)

        tk.Label(frame_range, text="Points:", bg=Style.BG_COLOR).grid(row=1, column=0, padx=5, pady=5)
        e_pts = ttk.Entry(frame_range, width=8)
        e_pts.insert(0, "1000")
        e_pts.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(dialog, text="Graph Name:", bg=Style.BG_COLOR).pack(pady=(5, 2))
        e_name = ttk.Entry(dialog, width=20)
        e_name.insert(0, "Equation Graph")
        e_name.pack(pady=5)

        def generate():
            try:
                eq_str = e_eq.get()
                x_min = float(e_xmin.get())
                x_max = float(e_xmax.get())
                n_pts = int(e_pts.get())
                name = e_name.get()

                if n_pts <= 0: raise ValueError("Points must be > 0")

                x = np.linspace(x_min, x_max, n_pts)

                allowed_locals = {"x": x, "np": np, "math": math}
                y = eval(eq_str, {"__builtins__": {}}, allowed_locals)

                if np.isscalar(y):
                    y = np.full_like(x, y)

                df = pd.DataFrame({'X': x, 'Y': y})
                color = "#{:06x}".format(random.randint(0, 0xFFFFFF))

                dataset = {
                    'data': df,
                    'filename': "Equation",
                    'label': name,
                    'color': color,
                    'style_config': {'linestyle': '-', 'marker': None, 'fillstyle': 'full'}
                }
                self.datasets.append(dataset)
                self.update_plot()
                self.update_table_view()
                dialog.destroy()

            except Exception as e:
                messagebox.showerror("Error", f"Invalid Equation or Parameters:\n{e}")

        # Added .pack() here!
        Style.create_popup_button(dialog, "Create", generate, Style.COLOR_SUCCESS).pack(pady=15)

    def read_files(self, file_paths):
        first_load_in_session = True
        files_loaded = False
        for file_path in file_paths:
            try:
                ext = os.path.splitext(file_path)[1].lower()

                if ext in ['.xlsx', '.xls']:
                    df = pd.read_excel(file_path)
                else:
                    df = pd.read_csv(file_path, sep=None, engine='python')

                if self.target_x_col and self.target_y_col:
                    if self.target_x_col in df.columns and self.target_y_col in df.columns:
                        df = df[[self.target_x_col, self.target_y_col]]
                    else:
                        messagebox.showwarning("Column Mismatch",
                                               f"File: {os.path.basename(file_path)}\n"
                                               f"Could not find columns '{self.target_x_col}' or '{self.target_y_col}'.\n"
                                               "Skipping file.")
                        continue

                if first_load_in_session:
                    self.x_label = str(df.columns[0])
                    self.y_label = str(df.columns[1])
                    first_load_in_session = False

                color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
                filename = os.path.basename(file_path)

                dataset = {
                    'data': df,
                    'filename': filename,
                    'label': filename,
                    'color': color,
                    'style_config': {'linestyle': '-', 'marker': None, 'fillstyle': 'full'}
                }
                self.datasets.append(dataset)
                files_loaded = True

            except Exception as e:
                messagebox.showerror("Error", f"Could not load file {file_path}:\n{e}")

        if files_loaded:
            self.update_plot()
            self.update_table_view()

    def update_plot(self):
        """Redraws all graphs with current settings."""
        self.ax.clear()

        self.ax.set_title(self.graph_title)
        self.ax.set_xlabel(self.x_label)
        self.ax.set_ylabel(self.y_label)
        self.ax.grid(True, linestyle='--', alpha=0.6)

        if self.log_x.get():
            self.ax.set_xscale('log')
        if self.log_y.get():
            self.ax.set_yscale('log')

        for ds in self.datasets:
            df = ds['data']
            x = df.iloc[:, 0]
            y = df.iloc[:, 1]

            style = ds.get('style_config', {'linestyle': '-', 'marker': None, 'fillstyle': 'full'})

            kwargs = {
                'label': ds['label'],
                'color': ds['color'],
                'linewidth': 2 if style['linestyle'] != 'None' else 0,
                'linestyle': style.get('linestyle', '-'),
                'marker': style.get('marker', None),
                'fillstyle': style.get('fillstyle', 'full'),
                'markersize': 4
            }

            if style.get('fillstyle') == 'none':
                kwargs['markerfacecolor'] = 'none'
                kwargs['markeredgecolor'] = ds['color']

            self.ax.plot(x, y, **kwargs)

            # Error bars support
            if 'y_error' in ds and ds['y_error'] is not None:
                err_minus, err_plus = ds['y_error']
                self.ax.errorbar(x, y, yerr=[[err_minus] * len(x), [err_plus] * len(x)],
                                 fmt='none', ecolor=ds['color'], alpha=0.5, capsize=3)

        # Set manual limits if they exist
        if self.axis_limits['x_min'] is not None or self.axis_limits['x_max'] is not None:
            self.ax.set_xlim(left=self.axis_limits['x_min'], right=self.axis_limits['x_max'])
        if self.axis_limits['y_min'] is not None or self.axis_limits['y_max'] is not None:
            self.ax.set_ylim(bottom=self.axis_limits['y_min'], top=self.axis_limits['y_max'])

        if self.datasets:
            self.ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)

        self.canvas.draw()
        self.update_info_label()

    def change_style_dialog(self, idx):
        """Opens a dialog to choose graph style."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Style")
        dialog.geometry("250x250")
        dialog.configure(bg=Style.BG_COLOR)

        tk.Label(dialog, text=f"Style for: {self.datasets[idx]['label']}",
                 bg=Style.BG_COLOR, font=Style.HEADER_FONT, wraplength=230).pack(pady=10)

        def set_style(name):
            if name == 'solid':
                cfg = {'linestyle': '-', 'marker': None, 'fillstyle': 'full'}
            elif name == 'dashed':
                cfg = {'linestyle': '--', 'marker': None, 'fillstyle': 'full'}
            elif name == 'dots':
                cfg = {'linestyle': 'None', 'marker': 'o', 'fillstyle': 'full'}
            elif name == 'hollow':
                cfg = {'linestyle': 'None', 'marker': 'o', 'fillstyle': 'none'}

            self.datasets[idx]['style_config'] = cfg
            self.update_plot()
            dialog.destroy()

        btn_opts = {'bg': "#E0E0E0", 'relief': tk.FLAT, 'width': 20, 'pady': 5}

        tk.Button(dialog, text="Solid", command=lambda: set_style('solid'), **btn_opts).pack(pady=5)
        tk.Button(dialog, text="Dashed", command=lambda: set_style('dashed'), **btn_opts).pack(pady=5)
        tk.Button(dialog, text="Dots", command=lambda: set_style('dots'), **btn_opts).pack(pady=5)
        tk.Button(dialog, text="Hollow Dots", command=lambda: set_style('hollow'), **btn_opts).pack(pady=5)

    def update_table_view(self):
        """Rebuilds the list of graphs using Grid for perfect alignment."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.scrollable_frame.columnconfigure(0, weight=3, uniform="cols")
        self.scrollable_frame.columnconfigure(1, weight=3, uniform="cols")
        self.scrollable_frame.columnconfigure(2, weight=1, uniform="cols")
        self.scrollable_frame.columnconfigure(3, weight=4, uniform="cols")

        header_font = Style.HEADER_FONT
        header_bg = Style.NEUTRAL_BTN_COLOR

        tk.Label(self.scrollable_frame, text="Filename", font=header_font, bg=header_bg, anchor="w", padx=10,
                 pady=5).grid(row=0, column=0, sticky="ew")
        tk.Label(self.scrollable_frame, text="Graph Name", font=header_font, bg=header_bg, anchor="w", padx=10,
                 pady=5).grid(row=0, column=1, sticky="ew")
        tk.Label(self.scrollable_frame, text="Color", font=header_font, bg=header_bg, anchor="center", padx=10,
                 pady=5).grid(row=0, column=2, sticky="ew")
        tk.Label(self.scrollable_frame, text="Actions", font=header_font, bg=header_bg, anchor="w", padx=10,
                 pady=5).grid(row=0, column=3, sticky="ew")

        tk.Frame(self.scrollable_frame, height=1, bg="#b0b0b0").grid(row=1, column=0, columnspan=4, sticky="ew")

        for idx, ds in enumerate(self.datasets):
            row = idx * 2 + 2

            tk.Label(self.scrollable_frame, text=ds['filename'], bg=Style.BG_COLOR, font=Style.GLOBAL_FONT,
                     anchor="w").grid(
                row=row, column=0, sticky="ew", padx=10, pady=8)
            tk.Label(self.scrollable_frame, text=ds['label'], bg=Style.BG_COLOR, font=Style.GLOBAL_FONT, fg="#007AFF",
                     anchor="w").grid(row=row, column=1, sticky="ew", padx=10, pady=8)

            color_cell = tk.Frame(self.scrollable_frame, bg=Style.BG_COLOR)
            color_cell.grid(row=row, column=2, sticky="ew", pady=8)
            tk.Label(color_cell, bg=ds['color'], width=4, height=1, relief="solid", bd=1).pack(anchor="center")

            action_cell = tk.Frame(self.scrollable_frame, bg=Style.BG_COLOR)
            action_cell.grid(row=row, column=3, sticky="ew", padx=10, pady=8)

            Style.create_table_button(action_cell, "Rename", lambda i=idx: self.rename_graph(i)).pack(
                side=tk.LEFT, padx=2)
            Style.create_table_button(action_cell, "Color", lambda i=idx: self.change_color(i)).pack(
                side=tk.LEFT, padx=2)
            Style.create_table_button(action_cell, "Style", lambda i=idx: self.change_style_dialog(i)).pack(
                side=tk.LEFT, padx=2)
            Style.create_table_button(action_cell, "Error bar", lambda i=idx: self.open_error_bar_dialog(i)).pack(
                side=tk.LEFT, padx=2)
            Style.create_table_button(action_cell, "Delete", lambda i=idx: self.delete_graph(i)).pack(
                side=tk.LEFT, padx=2)

            tk.Frame(self.scrollable_frame, height=1, bg="#e0e0e0").grid(row=row + 1, column=0, columnspan=4,
                                                                         sticky="ew")

    def rename_graph(self, idx):
        current_label = self.datasets[idx]['label']
        new_label = simpledialog.askstring("Rename", "Enter new name:", initialvalue=current_label)
        if new_label:
            self.datasets[idx]['label'] = new_label
            self.update_table_view()
            self.update_plot()

    def change_color(self, idx):
        current_color = self.datasets[idx]['color']
        color_code = colorchooser.askcolor(title="Choose color", color=current_color)
        if color_code[1]:
            self.datasets[idx]['color'] = color_code[1]
            self.update_table_view()
            self.update_plot()

    def delete_graph(self, idx):
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{self.datasets[idx]['label']}'?"):
            del self.datasets[idx]
            self.update_plot()
            self.update_table_view()

    def open_error_bar_dialog(self, idx):
        """Opens a dialog to set error bars for a specific graph with Order of Magnitude."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Error Bars")
        dialog.configure(bg=Style.BG_COLOR)

        tk.Label(dialog, text=f"Set Error Bars for:\n{self.datasets[idx]['label']}",
                 bg=Style.BG_COLOR, font=Style.HEADER_FONT, justify=tk.CENTER).pack(pady=10, padx=20)

        f_in = tk.Frame(dialog, bg=Style.BG_COLOR)
        f_in.pack(pady=5)

        default_order = 0
        try:
            df = self.datasets[idx]['data']
            y_vals = pd.to_numeric(df.iloc[:, 1], errors='coerce').dropna()
            max_val = y_vals.abs().max()
            if max_val > 0:
                default_order = int(math.floor(math.log10(max_val)))
        except:
            pass

        tk.Label(f_in, text="+Y Error:", bg=Style.BG_COLOR).grid(row=0, column=0, padx=5, pady=5, sticky="e")
        e_plus = ttk.Entry(f_in, width=10)
        e_plus.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(f_in, text="-Y Error:", bg=Style.BG_COLOR).grid(row=1, column=0, padx=5, pady=5, sticky="e")
        e_minus = ttk.Entry(f_in, width=10)
        e_minus.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(f_in, text="x 10^", bg=Style.BG_COLOR).grid(row=0, column=2, rowspan=2, padx=2, sticky="e")
        e_order = ttk.Entry(f_in, width=5)
        e_order.grid(row=0, column=3, rowspan=2, padx=5, sticky="w")
        e_order.insert(0, str(default_order))

        current_err = self.datasets[idx].get('y_error')
        if current_err:
            scale = 10 ** default_order
            e_minus.insert(0, str(current_err[0] / scale))
            e_plus.insert(0, str(current_err[1] / scale))

        def update_error():
            p_val = e_plus.get().strip()
            m_val = e_minus.get().strip()
            ord_val = e_order.get().strip()

            if not p_val and not m_val:
                self.datasets[idx]['y_error'] = None
            else:
                try:
                    order = int(ord_val) if ord_val else 0
                    multiplier = 10 ** order

                    p_float = float(p_val) * multiplier if p_val else 0.0
                    m_float = float(m_val) * multiplier if m_val else 0.0

                    if p_float < 0 or m_float < 0:
                        messagebox.showerror("Error", "Error values must be non-negative.")
                        return

                    if p_float == 0 and m_float == 0:
                        self.datasets[idx]['y_error'] = None
                    else:
                        self.datasets[idx]['y_error'] = (m_float, p_float)
                except ValueError:
                    messagebox.showerror("Error", "Please enter valid numbers.")
                    return

            self.update_plot()
            dialog.destroy()

        Style.create_popup_button(dialog, "Update", update_error, Style.COLOR_SUCCESS).pack(pady=15)

    def reset_params(self):
        """Resets all graph parameters (Log scale, Limits) to default."""
        self.log_x.set(False)
        self.log_y.set(False)
        self.axis_limits = {'x_min': None, 'x_max': None, 'y_min': None, 'y_max': None}
        self.update_plot()

    def get_default_order_of_magnitude(self, axis='x'):
        max_val = 0
        has_data = False
        for ds in self.datasets:
            df = ds['data']
            col_idx = 0 if axis == 'x' else 1
            if df.shape[1] > col_idx:
                try:
                    current_max = df.iloc[:, col_idx].max()
                    if pd.notna(current_max):
                        max_val = max(max_val, abs(current_max))
                        has_data = True
                except:
                    pass
        if not has_data or max_val == 0: return 0
        try:
            return int(math.floor(math.log10(max_val)))
        except:
            return 0

    def open_limits_dialog(self):
        """Opens a custom dialog to set X and Y axis limits with Order of Magnitude."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Set Axis Limits & Order")
        dialog.geometry("600x350")
        dialog.configure(bg=Style.BG_COLOR)

        tk.Label(dialog, text="X Limits:", bg=Style.BG_COLOR,font=Style.HEADER_FONT).pack(pady=(20, 10))

        x_frame = tk.Frame(dialog, bg=Style.BG_COLOR)
        x_frame.pack(pady=5)

        tk.Label(x_frame, text="Min:", bg=Style.BG_COLOR).pack(side=tk.LEFT, padx=5)
        e_x_min = tk.Entry(x_frame, width=10)
        e_x_min.pack(side=tk.LEFT, padx=5)

        tk.Label(x_frame, text="Max:", bg=Style.BG_COLOR).pack(side=tk.LEFT, padx=5)
        e_x_max = tk.Entry(x_frame, width=10)
        e_x_max.pack(side=tk.LEFT, padx=5)

        tk.Label(x_frame, text="x 10^", bg=Style.BG_COLOR).pack(side=tk.LEFT, padx=5)
        e_x_order = tk.Entry(x_frame, width=5)
        e_x_order.pack(side=tk.LEFT, padx=5)

        x_log_frame = tk.Frame(dialog, bg=Style.BG_COLOR)
        x_log_frame.pack(pady=2)

        cb_x = tk.Checkbutton(x_log_frame, text="LogX",
                              variable=self.log_x, bg=Style.BG_COLOR)
        cb_x.pack()

        ttk.Separator(dialog, orient='horizontal').pack(fill='x', padx=20, pady=15)

        tk.Label(dialog, text="Y Limits:", bg=Style.BG_COLOR, font=Style.HEADER_FONT).pack(pady=(10, 10))

        y_frame = tk.Frame(dialog, bg=Style.BG_COLOR)
        y_frame.pack(pady=5)

        tk.Label(y_frame, text="Min:", bg=Style.BG_COLOR).pack(side=tk.LEFT, padx=5)
        e_y_min = tk.Entry(y_frame, width=10)
        e_y_min.pack(side=tk.LEFT, padx=5)

        tk.Label(y_frame, text="Max:", bg=Style.BG_COLOR).pack(side=tk.LEFT, padx=5)
        e_y_max = tk.Entry(y_frame, width=10)
        e_y_max.pack(side=tk.LEFT, padx=5)

        tk.Label(y_frame, text="x 10^", bg=Style.BG_COLOR).pack(side=tk.LEFT, padx=5)
        e_y_order = tk.Entry(y_frame, width=5)
        e_y_order.pack(side=tk.LEFT, padx=5)

        y_log_frame = tk.Frame(dialog, bg=Style.BG_COLOR)
        y_log_frame.pack(pady=2)

        cb_y = tk.Checkbutton(y_log_frame, text="LogY",
                              variable=self.log_y, bg=Style.BG_COLOR)
        cb_y.pack()

        default_x_order = self.get_default_order_of_magnitude(axis='x')
        e_x_order.insert(0, str(default_x_order))
        if self.axis_limits['x_min'] is not None:
            e_x_min.insert(0, str(self.axis_limits['x_min'] / (10 ** default_x_order)))
        if self.axis_limits['x_max'] is not None:
            e_x_max.insert(0, str(self.axis_limits['x_max'] / (10 ** default_x_order)))

        default_y_order = self.get_default_order_of_magnitude(axis='y')
        e_y_order.insert(0, str(default_y_order))
        if self.axis_limits['y_min'] is not None:
            e_y_min.insert(0, str(self.axis_limits['y_min'] / (10 ** default_y_order)))
        if self.axis_limits['y_max'] is not None:
            e_y_max.insert(0, str(self.axis_limits['y_max'] / (10 ** default_y_order)))

        def apply_limits():
            cur_xlim = self.ax.get_xlim()
            cur_ylim = self.ax.get_ylim()

            try:
                x_order = int(e_x_order.get() or 0)
                x_mult = 10 ** x_order

                val_x_min = e_x_min.get().strip()
                val_x_max = e_x_max.get().strip()

                if val_x_min and not val_x_max:
                    self.axis_limits['x_min'] = float(val_x_min) * x_mult
                    self.axis_limits['x_max'] = cur_xlim[1]
                elif val_x_max and not val_x_min:
                    self.axis_limits['x_min'] = cur_xlim[0]
                    self.axis_limits['x_max'] = float(val_x_max) * x_mult
                else:
                    self.axis_limits['x_min'] = float(val_x_min) * x_mult if val_x_min else None
                    self.axis_limits['x_max'] = float(val_x_max) * x_mult if val_x_max else None

                y_order = int(e_y_order.get() or 0)
                y_mult = 10 ** y_order

                val_y_min = e_y_min.get().strip()
                val_y_max = e_y_max.get().strip()

                if val_y_min and not val_y_max:
                    self.axis_limits['y_min'] = float(val_y_min) * y_mult
                    self.axis_limits['y_max'] = cur_ylim[1]
                elif val_y_max and not val_y_min:
                    self.axis_limits['y_min'] = cur_ylim[0]
                    self.axis_limits['y_max'] = float(val_y_max) * y_mult
                else:
                    self.axis_limits['y_min'] = float(val_y_min) * y_mult if val_y_min else None
                    self.axis_limits['y_max'] = float(val_y_max) * y_mult if val_y_max else None

                self.update_plot()
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers.")

        Style.create_popup_button(dialog, "Apply Changes", apply_limits, Style.COLOR_SUCCESS).pack(pady=20)

    def open_graph_details_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Graph Details")
        dialog.geometry("450x300")
        dialog.configure(bg=Style.BG_COLOR)

        container = tk.Frame(dialog, bg=Style.BG_COLOR)
        container.pack(expand=True)

        entries = {}
        defaults = {
            "title": ("Graph Title:", self.ax.get_title()),
            "x_label": ("X Axis Label:", self.ax.get_xlabel()),
            "y_label": ("Y Axis Label:", self.ax.get_ylabel())
        }

        row = 0
        for key, (label_text, current_val) in defaults.items():
            lbl = tk.Label(container, text=label_text, bg=Style.BG_COLOR,
                           font=("Arial", 10, "bold"))
            lbl.grid(row=row, column=0, padx=(10, 5), pady=10, sticky="e")

            entry = tk.Entry(container, width=30)
            entry.insert(0, current_val)
            entry.grid(row=row, column=1, padx=(5, 10), pady=10, sticky="w")

            entries[key] = entry
            row += 1

        def apply_changes():
            self.graph_title = entries["title"].get()
            self.x_label = entries["x_label"].get()
            self.y_label = entries["y_label"].get()
            self.update_plot()
            dialog.destroy()

        btn_frame = tk.Frame(dialog, bg=Style.BG_COLOR)
        btn_frame.pack(pady=20)

        Style.create_popup_button(btn_frame, "Apply Changes", apply_changes, Style.COLOR_SUCCESS).pack(side=tk.LEFT,
                                                                                                       padx=10)

    def open_get_y_dialog(self):
        """Opens a dialog to calculate interpolated Y for a given X with Export Option."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Get Y for X")
        dialog.configure(bg=Style.BG_COLOR)

        # --- Input Section (Horizontal Layout) ---
        input_frame = tk.Frame(dialog, bg=Style.BG_COLOR)
        input_frame.pack(pady=15)

        tk.Label(input_frame, text="Enter X:", bg=Style.BG_COLOR,font=Style.GLOBAL_FONT).pack(side=tk.LEFT, padx=5)
        e_x = ttk.Entry(input_frame, width=12)
        e_x.pack(side=tk.LEFT, padx=5)

        tk.Label(input_frame, text="x 10^", bg=Style.BG_COLOR,font=Style.GLOBAL_FONT).pack(side=tk.LEFT)
        e_x_order = tk.Entry(input_frame, width=5)
        e_x_order.pack(side=tk.LEFT, padx=5)

        # Pre-fill the order of magnitude automatically based on existing data
        default_x_order = self.get_default_order_of_magnitude(axis='x')
        e_x_order.insert(0, str(default_x_order))

        # --- Results Section ---
        result_text = tk.Text(dialog, height=15, width=40, highlightthickness=1, bd=0, highlightbackground="black",
                              highlightcolor="black", font=("Consolas", 9))
        result_text.pack(pady=10, padx=10)

        self.last_calculation = []

        def calculate():
            try:
                # 1. Get the base value
                base_x = float(e_x.get())

                # 2. Get the order (default to 0 if left empty)
                order_str = e_x_order.get().strip()
                x_order = int(order_str) if order_str else 0

                # 3. Calculate the actual target X
                target_x = base_x * (10 ** x_order)

                result_text.delete(1.0, tk.END)
                self.last_calculation = []

                results_str = []
                for ds in self.datasets:
                    df = ds['data']
                    subset = df.iloc[:, [0, 1]].apply(pd.to_numeric, errors='coerce')
                    data_clean = subset.dropna()

                    val_str = ""
                    y_val = None

                    if data_clean.shape[0] < 2:
                        val_str = "Not enough data"
                    else:
                        data_clean = data_clean.sort_values(by=data_clean.columns[0])
                        xs = data_clean.iloc[:, 0].values
                        ys = data_clean.iloc[:, 1].values

                        if target_x < xs[0] or target_x > xs[-1]:
                            val_str = "Out of range"
                        else:
                            y_interp = np.interp(target_x, xs, ys)
                            y_val = y_interp
                            val_str = f"{y_interp:.6e}"

                    self.last_calculation.append({
                        "Graph Name": ds['label'],
                        "X Value": target_x,  # Saving the true value
                        "Y Value": y_val if y_val is not None else val_str
                    })
                    results_str.append(f"{ds['label']}: {val_str}")

                result_text.insert(tk.END, "\n".join(results_str))

            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers for X and Order.")

        def export_results():
            if not self.last_calculation:
                messagebox.showinfo("Info", "Please calculate values first.")
                return
            file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                     filetypes=[("Excel files", "*.xlsx")])
            if file_path:
                try:
                    df_export = pd.DataFrame(self.last_calculation)
                    df_export.to_excel(file_path, index=False)
                    messagebox.showinfo("Success", "Results exported successfully.")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to export: {e}")

        # --- Buttons Section ---
        btn_frame = tk.Frame(dialog, bg=Style.BG_COLOR)
        btn_frame.pack(pady=10)

        Style.create_popup_button(btn_frame, "Calculate", calculate, Style.COLOR_SUCCESS).pack(pady=5)
        Style.create_popup_button(btn_frame, "Export to Excel", export_results, Style.COLOR_PRIMARY).pack(pady=5)

    def clear_all(self):
        if messagebox.askyesno("Confirm", "Delete all graphs?"):
            self.datasets = []
            self.axis_limits = {'x_min': None, 'x_max': None, 'y_min': None, 'y_max': None}
            self.update_plot()
            self.update_table_view()