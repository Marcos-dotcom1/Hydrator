import json
import time
import datetime
import tkinter as tk
from tkinter import messagebox

def load_settings():
    with open("settings.json") as f:
        return json.load(f)

def get_schedule(s):
    fmt = "%H:%M"
    start = datetime.datetime.strptime(s["start_time"], fmt)
    end   = datetime.datetime.strptime(s["end_time"],   fmt)
    total_minutes = int((end - start).total_seconds() // 60)
    n = max(1, total_minutes // s["interval_min"])
    ml_per = s["daily_goal_ml"] // n
    times = []
    for i in range(n):
        t = start + datetime.timedelta(minutes=s["interval_min"] * i)
        times.append(t.time())
    return times, ml_per

def show_popup(ml, troll):
    root = tk.Tk()
    root.withdraw()  # hide main window
    msg = f"Drink {ml} ml now, bro!"
    resp = messagebox.askquestion("💧 Water Reminder", msg)
    root.destroy()
    if resp == "no" and troll:
        return False  # signal to repeat immediately
    return True

def main():
    s = load_settings()
    times, ml = get_schedule(s)
    print("Reminder times:", times)
    while True:
        now = datetime.datetime.now().time()
        for t in times:
            if now.hour == t.hour and now.minute == t.minute:
                ok = False
                while not ok:
                    ok = show_popup(ml, s["troll_mode"])
                # avoid double-triggering this minute
                time.sleep(60)
        time.sleep(5)

if __name__ == "__main__":
    main()
