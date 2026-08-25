import os
import sys
import json
import time
import threading
import requests
from datetime import datetime, timedelta
import customtkinter as ctk
from plyer import notification
import pygame

# Initialize Pygame Mixer
pygame.mixer.init()

# Configure Modern Appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

def get_resource_path(relative_path):
    """Resolves resource paths for both standard execution and PyInstaller bundling."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

CONFIG_FILE = "config.json"

class ModernPrayerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Prayer Times Pro")
        self.geometry("480x580")
        self.resizable(False, False)

        # Config Defaults
        self.config = self.load_config()
        self.prayer_times = {}
        self.next_prayer_name = "--"
        self.next_prayer_time_str = ""

        self.setup_ui()
        self.fetch_prayer_times()

        # Start Background Engine Thread
        self.running = True
        self.engine_thread = threading.Thread(target=self.background_engine, daemon=True)
        self.engine_thread.start()

        # Start Live UI Countdown Loop
        self.update_live_ui()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"city": "Riyadh", "country": "Saudi Arabia", "method": 4}

    def save_config(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)

    def setup_ui(self):
        # Header / Settings Section
        self.settings_frame = ctk.CTkFrame(self, corner_radius=15)
        self.settings_frame.pack(padx=20, pady=15, fill="x")

        self.lbl_title = ctk.CTkLabel(self.settings_frame, text="Location Settings", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_title.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5))

        self.entry_city = ctk.CTkEntry(self.settings_frame, placeholder_text="City", width=160)
        self.entry_city.insert(0, self.config.get("city", "Riyadh"))
        self.entry_city.grid(row=1, column=0, padx=10, pady=10)

        self.entry_country = ctk.CTkEntry(self.settings_frame, placeholder_text="Country", width=160)
        self.entry_country.insert(0, self.config.get("country", "Saudi Arabia"))
        self.entry_country.grid(row=1, column=1, padx=10, pady=10)

        self.btn_save = ctk.CTkButton(self.settings_frame, text="Update & Save", command=self.on_save_settings, width=340)
        self.btn_save.grid(row=2, column=0, columnspan=2, padx=10, pady=(0, 10))

        # Main Highlight Banner (Next Prayer & Countdown)
        self.banner_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#1f538d")
        self.banner_frame.pack(padx=20, pady=5, fill="x")

        self.lbl_next_title = ctk.CTkLabel(self.banner_frame, text="NEXT PRAYER", font=ctk.CTkFont(size=12, weight="bold"), text_color="#a0c4ff")
        self.lbl_next_title.pack(pady=(12, 0))

        self.lbl_next_prayer = ctk.CTkLabel(self.banner_frame, text="-- : --", font=ctk.CTkFont(size=26, weight="bold"))
        self.lbl_next_prayer.pack(pady=2)

        self.lbl_countdown = ctk.CTkLabel(self.banner_frame, text="Remaining: --:--:--", font=ctk.CTkFont(size=14))
        self.lbl_countdown.pack(pady=(0, 12))

        # Prayer Times Grid
        self.times_frame = ctk.CTkFrame(self, corner_radius=15)
        self.times_frame.pack(padx=20, pady=15, fill="both", expand=True)

        self.cards = {}
        prayers = ["الفجر", "الظهر", "العصر", "المغرب", "العشاء"]
        for p in prayers:
            row_frame = ctk.CTkFrame(self.times_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=15, pady=6)

            name_lbl = ctk.CTkLabel(row_frame, text=p, font=ctk.CTkFont(size=15, weight="bold"))
            name_lbl.pack(side="left")

            time_lbl = ctk.CTkLabel(row_frame, text="--:--", font=ctk.CTkFont(size=15))
            time_lbl.pack(side="right")

            self.cards[p] = time_lbl

        # Footer Actions
        self.footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.footer_frame.pack(padx=20, pady=(0, 15), fill="x")

        self.btn_stop = ctk.CTkButton(self.footer_frame, text="Stop Audio", command=self.stop_audio, fg_color="#c92a2a", hover_color="#a61e1e", width=140)
        self.btn_stop.pack(side="left", padx=5)

        self.lbl_status = ctk.CTkLabel(self.footer_frame, text="Status: Ready", font=ctk.CTkFont(size=11), text_color="gray")
        self.lbl_status.pack(side="right", padx=5)

    def on_save_settings(self):
        self.config["city"] = self.entry_city.get().strip()
        self.config["country"] = self.entry_country.get().strip()
        self.save_config()
        self.fetch_prayer_times()

    def fetch_prayer_times(self):
        city = self.config["city"]
        country = self.config["country"]
        method = self.config.get("method", 4)
        url = f"http://api.aladhan.com/v1/timingsByCity?city={city}&country={country}&method={method}"

        try:
            res = requests.get(url, timeout=10).json()
            timings = res["data"]["timings"]
            self.prayer_times = {
                "الفجر": timings["Fajr"],
                "الظهر": timings["Dhuhr"],
                "العصر": timings["Asr"],
                "المغرب": timings["Maghrib"],
                "العشاء": timings["Isha"]
            }

            for p_name, p_time in self.prayer_times.items():
                self.cards[p_name].configure(text=p_time)

            self.lbl_status.configure(text=f"Updated ({city})", text_color="#4caf50")
            self.calculate_next_prayer()
        except Exception:
            self.lbl_status.configure(text="Connection Error", text_color="#f44336")

    def calculate_next_prayer(self):
        if not self.prayer_times:
            return

        now = datetime.now()
        fmt = "%H:%M"
        
        for p_name, p_time in self.prayer_times.items():
            p_dt = datetime.strptime(p_time, fmt).replace(year=now.year, month=now.month, day=now.day)
            if p_dt > now:
                self.next_prayer_name = p_name
                self.next_prayer_time_str = p_time
                self.lbl_next_prayer.configure(text=f"{p_name} - {p_time}")
                return

        # If all prayers today have passed, next is tomorrow's Fajr
        first_prayer = "الفجر"
        self.next_prayer_name = first_prayer
        self.next_prayer_time_str = self.prayer_times[first_prayer]
        self.lbl_next_prayer.configure(text=f"{first_prayer} - {self.next_prayer_time_str}")

    def update_live_ui(self):
        if self.prayer_times and self.next_prayer_time_str:
            now = datetime.now()
            fmt = "%H:%M"
            target = datetime.strptime(self.next_prayer_time_str, fmt).replace(year=now.year, month=now.month, day=now.day)
            
            if target < now:
                target += timedelta(days=1)

            diff = target - now
            hours, remainder = divmod(int(diff.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)

            self.lbl_countdown.configure(text=f"Remaining: {hours:02d}:{minutes:02d}:{seconds:02d}")

        self.after(1000, self.update_live_ui)

    def play_audio(self):
        try:
            path = get_resource_path("athan.mp3")
            if os.path.exists(path):
                pygame.mixer.music.load(path)
                pygame.mixer.music.play()
            else:
                print("athan.mp3 not found.")
        except Exception as e:
            print(f"Audio Error: {e}")

    def stop_audio(self):
        pygame.mixer.music.stop()

    def background_engine(self):
        while self.running:
            now_str = datetime.now().strftime("%H:%M")
            for p_name, p_time in self.prayer_times.items():
                if now_str == p_time:
                    msg = "الصلاة خير من النوم" if p_name == "الفجر" else "حيّ على الصلاة، حيّ على الفلاح"
                    try:
                        notification.notify(
                            title=f"أذان {p_name}",
                            message=msg,
                            app_name="Prayer App",
                            timeout=12
                        )
                    except Exception:
                        pass
                    
                    self.play_audio()
                    self.calculate_next_prayer()
                    time.sleep(61)
            
            time.sleep(5)

if __name__ == "__main__":
    app = ModernPrayerApp()
    app.mainloop()