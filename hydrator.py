import json
import os
import time
import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sys
from tkinter import font

class WaterReminderGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        self.load_settings()
        self.reminder_thread = None
        self.running = False
        self.triggered_times = set()
        self.setup_gui()
        self.center_window()
        
    def setup_window(self):
        self.root.title("💧 Hydrator")
        self.root.geometry("500x650")
        self.root.resizable(False, False)
        
        # Set icon (creates a simple water drop icon)
        try:
            # Create icon data
            icon_data = """
            iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAdgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAIXSURBVFiFtZc9SwNBEIafRLBQsLGwsLa0sLW1tbW1tLGwsLCwsLGwsLW1tbW1tLGwsLCwsLGwsLW1tbW1tbGwsLCwsLGwsLW1tbW1tbGwsLCwsLGwsLW1tbW1tbGwsLCwsLGwsLW1tbW1tbGw==
            """
            self.root.iconbitmap(default='water_icon.ico')
        except:
            pass
        
        # Modern color scheme
        self.bg_color = "#2c3e50"
        self.accent_color = "#3498db"
        self.text_color = "#ecf0f1"
        self.button_color = "#34495e"
        
        self.root.configure(bg=self.bg_color)
        
    def center_window(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.root.winfo_screenheight() // 2) - (650 // 2)
        self.root.geometry(f"500x650+{x}+{y}")
    
    def load_settings(self):
        self.default_settings = {
            "daily_goal_ml": 2000,
            "reminder_interval_min": 30,
            "start_time": "08:00",
            "end_time": "18:00",
            "water_per_reminder": 250,
            "sound_enabled": True,
            "custom_message": "Time to drink water!"
        }
        
        try:
            if os.path.exists("water_settings.json"):
                with open("water_settings.json", "r") as f:
                    loaded = json.load(f)
                    self.settings = {**self.default_settings, **loaded}
            else:
                self.settings = self.default_settings.copy()
                self.save_settings()
        except:
            self.settings = self.default_settings.copy()
    
    def save_settings(self):
        try:
            with open("water_settings.json", "w") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Could not save settings: {str(e)}")
    
    def setup_gui(self):
        # Configure ttk styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure custom styles
        style.configure('Title.TLabel', 
                       background=self.bg_color, 
                       foreground=self.accent_color,
                       font=('Arial', 16, 'bold'))
        
        style.configure('Custom.TLabel',
                       background=self.bg_color,
                       foreground=self.text_color,
                       font=('Arial', 10))
        
        style.configure('Custom.TButton',
                       background=self.button_color,
                       foreground=self.text_color,
                       font=('Arial', 10, 'bold'),
                       borderwidth=0)
        
        style.map('Custom.TButton',
                 background=[('active', self.accent_color)])
        
        # Main container
        main_frame = tk.Frame(self.root, bg=self.bg_color, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="💧 Hydrator", style='Title.TLabel')
        title_label.pack(pady=(0, 30))
        
        # Settings Frame
        settings_frame = tk.LabelFrame(main_frame, text="⚙️ Settings", 
                                     bg=self.bg_color, fg=self.text_color,
                                     font=('Arial', 12, 'bold'), padx=15, pady=15)
        settings_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Daily Goal
        goal_frame = tk.Frame(settings_frame, bg=self.bg_color)
        goal_frame.pack(fill=tk.X, pady=5)
        ttk.Label(goal_frame, text="Daily Goal (ML):", style='Custom.TLabel').pack(side=tk.LEFT)
        self.goal_var = tk.StringVar(value=str(self.settings["daily_goal_ml"]))
        goal_entry = tk.Entry(goal_frame, textvariable=self.goal_var, width=10, 
                             font=('Arial', 10), justify='center')
        goal_entry.pack(side=tk.RIGHT)
        
        # Water per reminder
        water_frame = tk.Frame(settings_frame, bg=self.bg_color)
        water_frame.pack(fill=tk.X, pady=5)
        ttk.Label(water_frame, text="Water per Reminder (ML):", style='Custom.TLabel').pack(side=tk.LEFT)
        self.water_var = tk.StringVar(value=str(self.settings["water_per_reminder"]))
        water_entry = tk.Entry(water_frame, textvariable=self.water_var, width=10,
                              font=('Arial', 10), justify='center')
        water_entry.pack(side=tk.RIGHT)
        
        # Reminder Interval
        interval_frame = tk.Frame(settings_frame, bg=self.bg_color)
        interval_frame.pack(fill=tk.X, pady=5)
        ttk.Label(interval_frame, text="Reminder Interval (minutes):", style='Custom.TLabel').pack(side=tk.LEFT)
        self.interval_var = tk.StringVar(value=str(self.settings["reminder_interval_min"]))
        interval_entry = tk.Entry(interval_frame, textvariable=self.interval_var, width=10,
                                 font=('Arial', 10), justify='center')
        interval_entry.pack(side=tk.RIGHT)
        
        # Time Range
        time_frame = tk.Frame(settings_frame, bg=self.bg_color)
        time_frame.pack(fill=tk.X, pady=5)
        ttk.Label(time_frame, text="Active Hours:", style='Custom.TLabel').pack(side=tk.LEFT)
        
        time_inputs = tk.Frame(time_frame, bg=self.bg_color)
        time_inputs.pack(side=tk.RIGHT)
        
        self.start_time_var = tk.StringVar(value=self.settings["start_time"])
        start_entry = tk.Entry(time_inputs, textvariable=self.start_time_var, width=6,
                              font=('Arial', 10), justify='center')
        start_entry.pack(side=tk.LEFT)
        
        ttk.Label(time_inputs, text=" to ", style='Custom.TLabel').pack(side=tk.LEFT)
        
        self.end_time_var = tk.StringVar(value=self.settings["end_time"])
        end_entry = tk.Entry(time_inputs, textvariable=self.end_time_var, width=6,
                            font=('Arial', 10), justify='center')
        end_entry.pack(side=tk.LEFT)
        
        # Custom Message
        msg_frame = tk.Frame(settings_frame, bg=self.bg_color)
        msg_frame.pack(fill=tk.X, pady=5)
        ttk.Label(msg_frame, text="Custom Message:", style='Custom.TLabel').pack(anchor=tk.W)
        self.message_var = tk.StringVar(value=self.settings["custom_message"])
        msg_entry = tk.Entry(msg_frame, textvariable=self.message_var, width=40,
                            font=('Arial', 10))
        msg_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Control Buttons
        button_frame = tk.Frame(main_frame, bg=self.bg_color)
        button_frame.pack(fill=tk.X, pady=20)
        
        self.start_btn = tk.Button(button_frame, text="🚀 Start Reminders", 
                                  command=self.toggle_reminders,
                                  bg=self.accent_color, fg='white',
                                  font=('Arial', 12, 'bold'),
                                  relief=tk.FLAT, padx=20, pady=10)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        save_btn = tk.Button(button_frame, text="💾 Save Settings",
                            command=self.save_current_settings,
                            bg=self.button_color, fg='white',
                            font=('Arial', 12, 'bold'),
                            relief=tk.FLAT, padx=20, pady=10)
        save_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        test_btn = tk.Button(button_frame, text="Test",
                            command=self.test_reminder,
                            bg='#e74c3c', fg='white',
                            font=('Arial', 12, 'bold'),
                            relief=tk.FLAT, padx=20, pady=10)
        test_btn.pack(side=tk.LEFT)
        
        # Status Frame
        status_frame = tk.LabelFrame(main_frame, text="📊 Status", 
                                   bg=self.bg_color, fg=self.text_color,
                                   font=('Arial', 12, 'bold'), padx=15, pady=15)
        status_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        self.status_label = tk.Label(status_frame, text="Ready to start reminders",
                                   bg=self.bg_color, fg=self.text_color,
                                   font=('Arial', 11), justify=tk.LEFT)
        self.status_label.pack(anchor=tk.W)
        
        # Progress info
        self.progress_label = tk.Label(status_frame, text="",
                                     bg=self.bg_color, fg=self.accent_color,
                                     font=('Arial', 10), justify=tk.LEFT)
        self.progress_label.pack(anchor=tk.W, pady=(10, 0))
        
        # Next reminder info
        self.next_reminder_label = tk.Label(status_frame, text="",
                                          bg=self.bg_color, fg='#f39c12',
                                          font=('Arial', 10), justify=tk.LEFT)
        self.next_reminder_label.pack(anchor=tk.W, pady=(5, 0))
        
    def save_current_settings(self):
        try:
            self.settings["daily_goal_ml"] = int(self.goal_var.get())
            self.settings["water_per_reminder"] = int(self.water_var.get())
            self.settings["reminder_interval_min"] = int(self.interval_var.get())
            self.settings["start_time"] = self.start_time_var.get().strip()
            self.settings["end_time"] = self.end_time_var.get().strip()
            self.settings["custom_message"] = self.message_var.get().strip()
            
            # Validate time format
            datetime.datetime.strptime(self.settings["start_time"], "%H:%M")
            datetime.datetime.strptime(self.settings["end_time"], "%H:%M")
            
            self.save_settings()
            self.status_label.config(text="✅ Settings saved successfully!")
            self.root.after(3000, lambda: self.status_label.config(text="Ready to start reminders"))
            
        except ValueError as e:
            messagebox.showerror("Invalid Input", "Please check your input values:\n- Numbers must be valid integers\n- Times must be in HH:MM format")
    
    def toggle_reminders(self):
        if not self.running:
            self.save_current_settings()
            self.running = True
            self.triggered_times.clear()
            self.start_btn.config(text="⏹️ Stop Reminders", bg='#e74c3c')
            self.status_label.config(text="🔔 Reminders are active!")
            
            self.reminder_thread = threading.Thread(target=self.reminder_loop, daemon=True)
            self.reminder_thread.start()
            
            self.update_status_display()
        else:
            self.running = False
            self.start_btn.config(text="🚀 Start Reminders", bg=self.accent_color)
            self.status_label.config(text="⏸️ Reminders stopped")
            self.progress_label.config(text="")
            self.next_reminder_label.config(text="")
    
    def test_reminder(self):
        self.show_water_reminder(self.settings["water_per_reminder"])
    
    def show_water_reminder(self, amount):
        # Create error-style popup that stays on top
        def show_error_popup():
            error_root = tk.Toplevel()
            error_root.title("💧 HYDRATION ALERT 💧")
            error_root.geometry("400x200")
            error_root.configure(bg='#e74c3c')
            error_root.resizable(False, False)
            error_root.attributes('-topmost', True)
            
            # Center the error window
            error_root.update_idletasks()
            x = (error_root.winfo_screenwidth() // 2) - (400 // 2)
            y = (error_root.winfo_screenheight() // 2) - (200 // 2)
            error_root.geometry(f"400x200+{x}+{y}")
            
            # Error icon and message
            main_frame = tk.Frame(error_root, bg='#e74c3c', padx=20, pady=20)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Big warning icon
            icon_label = tk.Label(main_frame, text="⚠️", font=('Arial', 48), 
                                bg='#e74c3c', fg='white')
            icon_label.pack(pady=(0, 10))
            
            # Custom message
            msg_label = tk.Label(main_frame, text=self.settings["custom_message"],
                               font=('Arial', 14, 'bold'), bg='#e74c3c', fg='white',
                               wraplength=350, justify=tk.CENTER)
            msg_label.pack(pady=(0, 5))
            
            # Amount
            amount_label = tk.Label(main_frame, text=f"Drink {amount} mL of water NOW!",
                                  font=('Arial', 12), bg='#e74c3c', fg='#ffff99',
                                  wraplength=350, justify=tk.CENTER)
            amount_label.pack(pady=(0, 15))
            
            # OK button
            ok_btn = tk.Button(main_frame, text="✅ I'LL DRINK NOW", 
                             command=error_root.destroy,
                             bg='white', fg='#e74c3c',
                             font=('Arial', 12, 'bold'),
                             relief=tk.RAISED, padx=20, pady=5)
            ok_btn.pack()
            
            # Auto-close after 30 seconds
            error_root.after(30000, error_root.destroy)
            
            # Make sound (system beep)
            try:
                error_root.bell()
            except:
                pass
        
        # Run in main thread
        self.root.after(0, show_error_popup)
    
    def get_next_reminder_time(self):
        try:
            now = datetime.datetime.now()
            start_time = datetime.datetime.strptime(self.settings["start_time"], "%H:%M").time()
            end_time = datetime.datetime.strptime(self.settings["end_time"], "%H:%M").time()
            interval = self.settings["reminder_interval_min"]
            
            # Check if we're in active hours
            current_time = now.time()
            if current_time < start_time or current_time > end_time:
                # Next reminder is at start time tomorrow or today
                if current_time > end_time:
                    next_date = now.date() + datetime.timedelta(days=1)
                else:
                    next_date = now.date()
                return datetime.datetime.combine(next_date, start_time)
            
            # Find next interval time
            start_datetime = datetime.datetime.combine(now.date(), start_time)
            minutes_since_start = (now - start_datetime).total_seconds() / 60
            
            if minutes_since_start < 0:
                return start_datetime
            
            next_interval = ((int(minutes_since_start) // interval) + 1) * interval
            next_reminder = start_datetime + datetime.timedelta(minutes=next_interval)
            
            # Check if next reminder is past end time
            end_datetime = datetime.datetime.combine(now.date(), end_time)
            if next_reminder > end_datetime:
                # Next reminder is tomorrow at start time
                tomorrow = now.date() + datetime.timedelta(days=1)
                return datetime.datetime.combine(tomorrow, start_time)
            
            return next_reminder
        except:
            return None
    
    def update_status_display(self):
        if self.running:
            now = datetime.datetime.now()
            
            # Calculate daily progress
            total_reminders_today = self.calculate_daily_reminders()
            completed_today = len(self.triggered_times)
            water_consumed = completed_today * self.settings["water_per_reminder"]
            
            progress_text = f"Today: {water_consumed}/{self.settings['daily_goal_ml']} mL ({completed_today}/{total_reminders_today} reminders)"
            self.progress_label.config(text=progress_text)
            
            # Next reminder time
            next_time = self.get_next_reminder_time()
            if next_time:
                time_until = next_time - now
                if time_until.total_seconds() > 0:
                    hours = int(time_until.total_seconds() // 3600)
                    minutes = int((time_until.total_seconds() % 3600) // 60)
                    next_text = f"Next reminder: {next_time.strftime('%H:%M')} (in {hours}h {minutes}m)"
                    self.next_reminder_label.config(text=next_text)
            
            # Schedule next update
            self.root.after(60000, self.update_status_display)  # Update every minute
    
    def calculate_daily_reminders(self):
        try:
            start_time = datetime.datetime.strptime(self.settings["start_time"], "%H:%M")
            end_time = datetime.datetime.strptime(self.settings["end_time"], "%H:%M")
            interval = self.settings["reminder_interval_min"]
            
            total_minutes = (end_time - start_time).total_seconds() / 60
            return int(total_minutes / interval) + 1
        except:
            return 1
    
    def reminder_loop(self):
        last_date = None
        
        while self.running:
            try:
                now = datetime.datetime.now()
                current_date = now.date()
                
                # Reset daily tracking
                if last_date != current_date:
                    self.triggered_times.clear()
                    last_date = current_date
                
                # Check if we should show a reminder
                if self.should_show_reminder(now):
                    current_minute = now.hour * 60 + now.minute
                    if current_minute not in self.triggered_times:
                        self.triggered_times.add(current_minute)
                        self.show_water_reminder(self.settings["water_per_reminder"])
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"Reminder loop error: {e}")
                time.sleep(60)
    
    def should_show_reminder(self, now):
        try:
            start_time = datetime.datetime.strptime(self.settings["start_time"], "%H:%M").time()
            end_time = datetime.datetime.strptime(self.settings["end_time"], "%H:%M").time()
            current_time = now.time()
            
            # Check if we're in active hours
            if current_time < start_time or current_time > end_time:
                return False
            
            # Check if it's time for a reminder based on interval
            start_datetime = datetime.datetime.combine(now.date(), start_time)
            minutes_since_start = (now - start_datetime).total_seconds() / 60
            
            if minutes_since_start < 0:
                return False
            
            interval = self.settings["reminder_interval_min"]
            return minutes_since_start % interval < 0.5  # Within 30 seconds of interval
            
        except:
            return False
    
    def on_closing(self):
        self.running = False
        self.save_settings()
        self.root.destroy()
    
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

def main():
    app = WaterReminderGUI()
    app.run()

if __name__ == "__main__":
    main()