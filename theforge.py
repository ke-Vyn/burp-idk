# Incomplete & Discontinued (30/12/2025)

import cv2
import numpy as np
import pyautogui
import tkinter as tk
import threading
import time
import ctypes
import keyboard

# ================= SYSTEM =================
pyautogui.FAILSAFE = False
user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

bot_running = threading.Event()

# ================= MOUSE =================
def move_mouse(x, y):
    user32.SetCursorPos(int(x), int(y))

def click():
    pyautogui.mouseDown()
    pyautogui.mouseUp()

# ================= AREA SELECT =================
class AreaSelector:
    def __init__(self, text):
        self.result = None
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True, '-alpha', 0.3, '-topmost', True)
        self.root.overrideredirect(True)

        tk.Label(self.root, text=text, font=("Arial", 26),
                 fg="red", bg="black").pack(pady=20)

        self.canvas = tk.Canvas(self.root, bg="black")
        self.canvas.pack(fill="both", expand=True)

        self.start = None
        self.rect = None

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def on_press(self, e):
        self.start = (e.x, e.y)
        self.rect = self.canvas.create_rectangle(e.x, e.y, e.x, e.y,
                                                 outline="red", width=3)

    def on_drag(self, e):
        self.canvas.coords(self.rect, self.start[0], self.start[1], e.x, e.y)

    def on_release(self, e):
        x1, y1 = self.start
        x2, y2 = e.x, e.y
        self.result = (min(x1, x2), min(y1, y2),
                       abs(x2 - x1), abs(y2 - y1))
        self.root.quit()

    def get(self):
        self.root.mainloop()
        self.root.destroy()
        return self.result

# ================= CORE LOGIC =================
def forging_bot(scan_area, park_pos, tolerance, status):
    ax, ay, aw, ah = scan_area
    px, py = park_pos

    hovered = False
    green_frames = 0

    move_mouse(px, py)  # PARK CURSOR
    time.sleep(0.3)

    status.config(text="Status: WAITING CIRCLE", fg="white")

    while bot_running.is_set():
        shot = pyautogui.screenshot(region=scan_area)
        frame = cv2.cvtColor(np.array(shot), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (9, 9), 1.5)

        circles = cv2.HoughCircles(
            gray, cv2.HOUGH_GRADIENT,
            dp=1.2, minDist=50,
            param1=100, param2=30,
            minRadius=25, maxRadius=150
        )

        if circles is None:
            hovered = False
            green_frames = 0
            continue

        cx, cy, r = max(np.uint16(np.around(circles[0])), key=lambda c: c[2])
        sx, sy = ax + cx, ay + cy

        # MOVE ONLY ONCE
        if not hovered:
            move_mouse(sx, sy)
            hovered = True
            status.config(text="Status: HOVERING", fg="cyan")
            time.sleep(0.05)
            continue

        # ===== GREEN DETECTION =====
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        cv2.circle(mask, (cx, cy), int(r * 0.4), 255, -1)

        lower_green = np.array([40, 80, 80])
        upper_green = np.array([80, 255, 255])

        green_mask = cv2.inRange(hsv, lower_green, upper_green)
        green_pixels = cv2.countNonZero(
            cv2.bitwise_and(green_mask, green_mask, mask=mask)
        )

        if green_pixels >= tolerance:
            green_frames += 1
            status.config(text=f"Status: GREEN ({green_frames})", fg="green")
        else:
            green_frames = 0

        # CLICK ONLY IF GREEN STABLE
        if green_frames >= 2:
            click()
            status.config(text="Status: CLICKED", fg="lime")
            time.sleep(0.2)
            hovered = False
            green_frames = 0

        time.sleep(0.01)

    status.config(text="Status: STOPPED", fg="red")

# ================= GUI =================
def gui():
    win = tk.Tk()
    win.title("Forging Green Bot")
    win.geometry("330x340")
    win.attributes("-topmost", True)

    scan_area = [None]
    park_pos = [None]

    tolerance = tk.IntVar(value=40)

    def scan():
        win.withdraw()
        scan_area[0] = AreaSelector("SCAN CIRCLE AREA").get()
        park_pos[0] = AreaSelector("SCAN PARK POSITION").get()[:2]
        win.deiconify()
        status.config(text="Status: READY", fg="blue")

    def start():
        if scan_area[0] and park_pos[0]:
            bot_running.set()
            threading.Thread(
                target=forging_bot,
                args=(scan_area[0], park_pos[0], tolerance.get(), status),
                daemon=True
            ).start()

    def stop():
        bot_running.clear()

    tk.Button(win, text="SCAN AREA", width=25, command=scan).pack(pady=5)
    tk.Label(win, text="Green Tolerance").pack()
    tk.Entry(win, textvariable=tolerance, width=6).pack()
    tk.Button(win, text="START (F1)", bg="green", fg="white",
              width=25, command=start).pack(pady=5)
    tk.Button(win, text="STOP (F2)", bg="red", fg="white",
              width=25, command=stop).pack(pady=5)

    status = tk.Label(win, text="Status: IDLE", font=("Arial", 10, "bold"))
    status.pack(pady=10)

    keyboard.add_hotkey("f1", start)
    keyboard.add_hotkey("f2", stop)

    win.mainloop()

if __name__ == "__main__":
    gui()
