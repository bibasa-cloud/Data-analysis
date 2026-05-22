import tkinter as tk
from tkinter import ttk
import ctypes
import sys  # ספרייה חיונית לסגירת התהליך

from GraphPlotter import GraphPlotter
from SignalAnalysis import SignalAnalyzer
from Style import setup_global_styles


class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.GraphsTab = None
        self.ExtremaTab = None

        # Setup the main window.
        self.title("Unified Scientific Workbench")
        self.state("zoomed")
        setup_global_styles()
        self.setupTabs()

        # setup the graphs plotter tab
        plotter = GraphPlotter(self.GraphsTab)

        # setup the extrema plotter tab
        analysis = SignalAnalyzer(self.ExtremaTab)

        # --- תיקון הבעיה ---
        # 1. הסרנו מכאן את self.mainloop() שהיה תוקע את התוכנה
        # 2. הגדרת מאזין ללחיצה על כפתור ה-"X" של החלון:
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        """פונקציה שמוודאת חיסול מוחלט של התהליך בעת סגירת התוכנה"""
        self.quit()  # עוצר את ה-mainloop
        self.destroy()  # הורס את כל רכיבי ה-GUI
        sys.exit(0)  # "הורג" את תהליך הפייתון/exe לחלוטין דרך מערכת ההפעלה

    def setupTabs(self):
        # 1. Setup the Style
        style = ttk.Style()
        style.theme_use('clam')

        # 2. Define Colors
        TAB_BG_NORMAL = "#97b9c3"
        TAB_BG_SELECTED = "#82e0b9"
        TEXT_COLOR = "black"
        CONTENT_BG = "#f0f0f0"
        TAB_PADDING = [20, 12]

        # 3. Configure the General Tab Style
        style.configure("TNotebook.Tab",
                        background=TAB_BG_NORMAL,
                        foreground=TEXT_COLOR,
                        padding=[20, 10],
                        font=("Segoe UI", 10),
                        borderwidth=0,
                        focuscolor="none"
                        )

        style.map("TNotebook.Tab",
                  background=[("selected", TAB_BG_SELECTED)],
                  foreground=[("selected", TEXT_COLOR)],
                  padding=[("selected", TAB_PADDING)]
                  )

        # 5. Configure the Notebook Container
        style.configure("TNotebook",
                        background=CONTENT_BG,
                        borderwidth=2
                        )

        # --- Creating the Layout ---
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True)

        self.GraphsTab = tk.Frame(notebook, bg=CONTENT_BG)
        self.ExtremaTab = tk.Frame(notebook, bg=CONTENT_BG)

        notebook.add(self.GraphsTab, text="Graphs plotter")
        notebook.add(self.ExtremaTab, text="Extrema finder")


if __name__ == '__main__':
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(0)
    except Exception:
        pass

    app = MainApp()
    app.mainloop()