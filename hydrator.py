import json
import os
import time
import datetime
import tkinter as tk
from tkinter import messagebox, simpledialog
from queue import Queue
from threading import Thread, Lock
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw

DEFAULT_SETTINGS = {
    "start_time": "08:00",
    "end_time": "17:00",
    "interval_min": 20,
    "daily_goal_ml": 2000,
    "troll_mode": False,
    "custom_times": ["08:15", "09:30", "11:00", "13:00", "15:30", "17:00"]
}

class WaterReminderApp:
    def __init__(self):
        self.settings = self.load_or_create_settings()
        self.queue = Queue()
        self.lock = Lock()
        self.root = None
        self.icon = None
        self.reminder_thread = None

    def load_or_create_settings(self):
        try:
            if not os.path.exists("settings.json"):
                self.create_default_settings()
                messagebox.showinfo("First Run", "Default settings created!\nYou can customize settings.json")
            
            with open("settings.json") as f:
                loaded = json.load(f)
                return {**DEFAULT_SETTINGS, **loaded}  # Merge with defaults
        except Exception as e:
            messagebox.showerror("Error", f"Using default settings:\n{str(e)}")
            return DEFAULT_SETTINGS

    def create_default_settings(self):
        with open("settings.json", "w") as f:
            json.dump(DEFAULT_SETTINGS, f, indent=4)

    def get_schedule(self):
        fmt = "%H:%M"
        if self.settings.get("custom_times"):
            custom_times = self.settings["custom_times"]
            times = [datetime.datetime.strptime(t, fmt).time() for t in custom_times]
        else:
            start = datetime.datetime.strptime(self.settings["start_time"], fmt)
            end = datetime.datetime.strptime(self.settings["end_time"], fmt)
            if end < start:
                end += datetime.timedelta(days=1)
            interval = self.settings["interval_min"]
            times = []
            current = start
            while current <= end:
                times.append(current.time())
                current += datetime.timedelta(minutes=interval)
        ml_per = self.settings["daily_goal_ml"] // len(times) if times else 0
        return times, ml_per

    def show_popup(self, ml, troll_mode):
        self.root.deiconify()
        self.root.attributes('-topmost', True)
        message = f"Time to drink {ml} mL of water!"
        response = messagebox.askyesno("💧 Water Reminder", message)
        self.root.withdraw()
        return response if troll_mode else True

    def process_queue(self):
        while not self.queue.empty():
            ml, troll_mode = self.queue.get()
            if not self.show_popup(ml, troll_mode):
                self.queue.put((ml, troll_mode))
        self.root.after(100, self.process_queue)

    def reminder_loop(self):
        times, ml = self.get_schedule()
        triggered = set()
        today = datetime.date.today()

        while True:
            now = datetime.datetime.now()
            current_date = now.date()

            if current_date != today:
                triggered.clear()
                today = current_date

            for t in times:
                scheduled_time = datetime.datetime.combine(today, t)
                if now >= scheduled_time and t not in triggered:
                    with self.lock:
                        triggered.add(t)
                        self.queue.put((ml, self.settings["troll_mode"]))

            time.sleep(10)

    def create_image(self):
        image = Image.new("RGB", (64, 64), "white")
        dc = ImageDraw.Draw(image)
        dc.ellipse((16, 16, 48, 48), fill="blue")
        return image

    def setup_icon(self):
        menu = Menu(
            MenuItem("Set Goal", self.set_goal),
            MenuItem("Toggle Troll Mode", self.toggle_troll_mode),
            MenuItem("Quit", self.quit_app)
        )
        self.icon = Icon("Water Reminder", self.create_image(), menu=menu)
        self.reminder_thread = Thread(target=self.reminder_loop, daemon=True)
        self.reminder_thread.start()

    def set_goal(self, icon, item):
        new_goal = simpledialog.askinteger("Set Goal", "Daily goal (mL):", 
                                         initialvalue=self.settings["daily_goal_ml"])
        if new_goal:
            self.settings["daily_goal_ml"] = new_goal

    def toggle_troll_mode(self, icon, item):
        self.settings["troll_mode"] = not self.settings["troll_mode"]
        status = "ON" if self.settings["troll_mode"] else "OFF"
        messagebox.showinfo("Troll Mode", f"Troll mode {status}")

    def quit_app(self, icon, item):
        self.icon.stop()
        self.root.destroy()

    def run(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.after(100, self.process_queue)
        self.setup_icon()
        self.icon.run()

if __name__ == "__main__":
    app = WaterReminderApp()
    app.run()