import tkinter as tk
from tkinter import colorchooser
try:
    import pyautogui
except ImportError:
    pyautogui = None

def pick_screen_color():
    if pyautogui is None:
        return colorchooser.askcolor()[0]
    root = tk.Tk()
    root.withdraw()
    tk.messagebox.showinfo("屏幕取色", "请将鼠标移动到需要取色的位置，3秒后自动取色。")
    import time
    time.sleep(3)
    x, y = pyautogui.position()
    rgb = pyautogui.screenshot().getpixel((x, y))
    root.destroy()
    return rgb
