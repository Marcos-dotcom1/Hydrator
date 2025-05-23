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
        self.running = True

    def load_or_create_settings(self):
        try:
            if not os.path.exists("settings.json"):
                self.create_default_settings()
                print("First Run: Default settings created! You can customize settings.json")
            
            with open("settings.json") as f:
                loaded = json.load(f)
                return {**DEFAULT_SETTINGS, **loaded}  # Merge with defaults
        except Exception as e:
            print(f"Error loading settings, using defaults: {str(e)}")
            return DEFAULT_SETTINGS.copy()

    def create_default_settings(self):
        with open("settings.json", "w") as f:
            json.dump(DEFAULT_SETTINGS, f, indent=4)

    def save_settings(self):
        try:
            with open("settings.json", "w") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {str(e)}")

    def get_schedule(self):
        fmt = "%H:%M"
        if self.settings.get("custom_times"):
            custom_times = self.settings["custom_times"]
            times = []
            for t in custom_times:
                try:
                    times.append(datetime.datetime.strptime(t, fmt).time())
                except ValueError:
                    print(f"Invalid time format: {t}")
                    continue
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
        try:
            if self.root and self.root.winfo_exists():
                self.root.deiconify()
                self.root.lift()
                self.root.attributes('-topmost', True)
                
                message = f"Time to drink {ml} mL of water!"
                response = messagebox.askyesno("💧 Water Reminder", message, parent=self.root)
                
                self.root.withdraw()
                return response if troll_mode else True
            else:
                print(f"Reminder: Time to drink {ml} mL of water!")
                return True
        except Exception as e:
            print(f"Error showing popup: {str(e)}")
            return True

    def process_queue(self):
        try:
            while not self.queue.empty():
                ml, troll_mode = self.queue.get()
                if not self.show_popup(ml, troll_mode):
                    # If user says no in troll mode, remind again in 2 minutes
                    def delayed_reminder():
                        time.sleep(120)  # 2 minutes
                        if self.running:
                            self.queue.put((ml, troll_mode))
                    
                    Thread(target=delayed_reminder, daemon=True).start()
            
            if self.root and self.root.winfo_exists() and self.running:
                self.root.after(1000, self.process_queue)  # Check every second
        except Exception as e:
            print(f"Error processing queue: {str(e)}")
            if self.root and self.root.winfo_exists() and self.running:
                self.root.after(1000, self.process_queue)

    def reminder_loop(self):
        times, ml = self.get_schedule()
        triggered = set()
        today = datetime.date.today()
        
        print(f"Water reminder started! Schedule: {[t.strftime('%H:%M') for t in times]}")
        print(f"Daily goal: {self.settings['daily_goal_ml']} mL, {ml} mL per reminder")

        while self.running:
            try:
                now = datetime.datetime.now()
                current_date = now.date()

                # Reset triggers for new day
                if current_date != today:
                    triggered.clear()
                    today = current_date
                    print(f"New day started: {today}")

                # Check each scheduled time
                for t in times:
                    scheduled_time = datetime.datetime.combine(today, t)
                    # Trigger if current time is within 1 minute of scheduled time
                    if (abs((now - scheduled_time).total_seconds()) <= 30 and 
                        t not in triggered):
                        with self.lock:
                            triggered.add(t)
                            self.queue.put((ml, self.settings["troll_mode"]))
                            print(f"Reminder triggered at {now.strftime('%H:%M:%S')}")

                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                print(f"Error in reminder loop: {str(e)}")
                time.sleep(60)  # Wait longer on error

    def create_image(self):
        # Create a simple water drop icon
        image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        
        # Water drop shape
        dc.ellipse((20, 35, 44, 59), fill=(70, 130, 180, 255))  # Blue circle (bottom)
        dc.polygon([(32, 10), (20, 35), (44, 35)], fill=(70, 130, 180, 255))  # Triangle (top)
        
        # Highlight
        dc.ellipse((26, 20, 32, 26), fill=(173, 216, 230, 200))
        
        return image

    def setup_icon(self):
        menu = Menu(
            MenuItem("Settings", self.show_settings),
            MenuItem("Set Goal", self.set_goal),
            MenuItem("Toggle Troll Mode", self.toggle_troll_mode),
            MenuItem("Test Reminder", self.test_reminder),
            Menu.SEPARATOR,
            MenuItem("Quit", self.quit_app)
        )
        self.icon = Icon("Water Reminder", self.create_image(), menu=menu)

    def show_settings(self, icon=None, item=None):
        def show_settings_dialog():
            if self.root and self.root.winfo_exists():
                self.root.deiconify()
                self.root.lift()
                
                settings_text = f"""Current Settings:
Start Time: {self.settings['start_time']}
End Time: {self.settings['end_time']}
Interval: {self.settings['interval_min']} minutes
Daily Goal: {self.settings['daily_goal_ml']} mL
Troll Mode: {'ON' if self.settings['troll_mode'] else 'OFF'}
Custom Times: {', '.join(self.settings['custom_times']) if self.settings.get('custom_times') else 'None'}"""
                
                messagebox.showinfo("Current Settings", settings_text, parent=self.root)
                self.root.withdraw()
        
        Thread(target=show_settings_dialog, daemon=True).start()

    def set_goal(self, icon=None, item=None):
        def set_goal_dialog():
            if self.root and self.root.winfo_exists():
                self.root.deiconify()
                self.root.lift()
                
                new_goal = simpledialog.askinteger(
                    "Set Goal", 
                    "Daily water goal (mL):", 
                    initialvalue=self.settings["daily_goal_ml"],
                    minvalue=500,
                    maxvalue=5000,
                    parent=self.root
                )
                
                if new_goal:
                    self.settings["daily_goal_ml"] = new_goal
                    self.save_settings()
                    messagebox.showinfo("Success", f"Daily goal set to {new_goal} mL", parent=self.root)
                
                self.root.withdraw()
        
        Thread(target=set_goal_dialog, daemon=True).start()

    def toggle_troll_mode(self, icon=None, item=None):
        def toggle_troll_dialog():
            self.settings["troll_mode"] = not self.settings["troll_mode"]
            self.save_settings()
            status = "ON" if self.settings["troll_mode"] else "OFF"
            
            if self.root and self.root.winfo_exists():
                self.root.deiconify()
                self.root.lift()
                messagebox.showinfo("Troll Mode", f"Troll mode is now {status}", parent=self.root)
                self.root.withdraw()
            else:
                print(f"Troll mode is now {status}")
        
        Thread(target=toggle_troll_dialog, daemon=True).start()

    def test_reminder(self, icon=None, item=None):
        _, ml = self.get_schedule()
        self.queue.put((ml, self.settings["troll_mode"]))
        print("Test reminder triggered")

    def quit_app(self, icon=None, item=None):
        print("Shutting down water reminder...")
        self.running = False
        
        if self.icon:
            self.icon.stop()
        
        if self.root and self.root.winfo_exists():
            self.root.quit()
            self.root.destroy()

    def run(self):
        try:
            # Initialize tkinter root
            self.root = tk.Tk()
            self.root.title("Water Reminder")
            self.root.withdraw()  # Hide the main window
            
            # Start the queue processor
            self.root.after(1000, self.process_queue)
            
            # Setup system tray icon
            self.setup_icon()
            
            # Start reminder thread
            self.reminder_thread = Thread(target=self.reminder_loop, daemon=True)
            self.reminder_thread.start()
            
            print("Water Reminder App started successfully!")
            print("Right-click the system tray icon to access settings.")
            
            # Run the system tray icon (this blocks)
            self.icon.run()
            
        except Exception as e:
            print(f"Error starting application: {str(e)}")
        finally:
            self.running = False

if __name__ == "__main__":
    try:
        app = WaterReminderApp()
        app.run()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        print(f"Fatal error: {str(e)}")