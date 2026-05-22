import tkinter as tk
from tkinter import ttk

BG_COLOR = "white"
TEXT_COLOR = "#1d1d1f"
COLOR_PRIMARY = "#007AFF"  # main blue
COLOR_SUCCESS = "#34C759"  # confirm green
COLOR_POSITIVE= "#30a867" #dark green
COLOR_ERASE = "#65616c"  # brown erase
NEUTRAL_BTN_COLOR = "#e0e0e0"  # grey

GLOBAL_FONT = ("Segoe UI", 10)
HEADER_FONT = ("Segoe UI", 10, "bold")
TABLE_BTN_FONT = ("Segoe UI", 8)

ACTION_BTN_WIDTH = 12
POPUP_BTN_WIDTH = 15


def setup_global_styles():
    style = ttk.Style()
    style.theme_use('clam')

    style.configure("TFrame", background=BG_COLOR)
    style.configure("TLabel", background=BG_COLOR, foreground=TEXT_COLOR, font=GLOBAL_FONT)
    style.configure("TEntry", font=GLOBAL_FONT, padding=4)
    style.configure("TCheckbutton", background=BG_COLOR, font=GLOBAL_FONT)
    style.configure("Header.TLabel", font=HEADER_FONT, background=NEUTRAL_BTN_COLOR)


def create_action_button(parent, text, command, bg_color=COLOR_PRIMARY):
    return tk.Button(parent, text=text, command=command,
                     bg=bg_color, fg="white", font=HEADER_FONT,
                     width=ACTION_BTN_WIDTH, relief=tk.FLAT, cursor="hand2")


def create_popup_button(parent, text, command, bg_color=COLOR_PRIMARY):
    """יוצר כפתור אישור רחב יותר לחלונות קופצים"""
    return tk.Button(parent, text=text, command=command,
                     bg=bg_color, fg="white", font=HEADER_FONT,
                     width=POPUP_BTN_WIDTH, pady=5, relief=tk.FLAT, cursor="hand2")


def create_table_button(parent, text, command, bg_color=NEUTRAL_BTN_COLOR, fg_color="black"):
    """יוצר כפתור קטן לשורות בתוך הטבלה"""
    return tk.Button(parent, text=text, command=command,
                     bg=bg_color, fg=fg_color, font=TABLE_BTN_FONT,
                     padx=8, pady=2, relief=tk.FLAT, cursor="hand2")