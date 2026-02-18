#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
All-in-One Quran Companion App
--------------------------------
Features:
- Random verse of the day (with audio translation)
- Prayer times based on city (using Aladhan API)
- Zakat calculator
- Ramadan recipes
- Quran vocabulary builder with audio
- Progress tracker (local JSON, optional Google Sheets sync)
- Daily goal reminder (Suhoor time) via plyer notifications
- Moon phase & Ramadan progress bar
- Full Quran reader with audio for selected verses (sample)

Note: For full Quran text, download a complete JSON file and update the path.
For Google Sheets, set up credentials and enable API.
For IFTTT, configure webhook and replace key.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import datetime
import time
import threading
import random
import json
import os
import math
import webbrowser
from io import BytesIO
from pathlib import Path

# Third-party imports (with error handling)
try:
    import requests
except ImportError:
    requests = None
    print("Warning: requests not installed. Prayer times will be unavailable.")

try:
    from plyer import notification
except ImportError:
    notification = None
    print("Warning: plyer not installed. Notifications disabled.")

try:
    from gtts import gTTS
    import pygame
except ImportError:
    gTTS = None
    pygame = None
    print("Warning: gTTS/pygame not installed. Audio features disabled.")

# Google Sheets (optional, will be mocked if not available)
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
except ImportError:
    gspread = None
    print("Warning: gspread/oauth2client not installed. Google Sheets sync disabled.")

# ----------------------------------------------------------------------
# Constants and sample data
# ----------------------------------------------------------------------
CITY = "Mecca"
COUNTRY = "Saudi Arabia"
SUHOOR_HOUR = 3  # 3 AM Suhoor time
SUHOOR_MINUTE = 0
IFTTT_WEBHOOK_URL = "https://maker.ifttt.com/trigger/{event}/with/key/{key}"  # Replace with your key

# Sample Quran verses (Surah Al-Fatiha + Al-Ikhlas)
QURAN_SAMPLE = {
    "surahs": [
        {
            "name": "Al-Fatiha",
            "verses": [
                {"arabic": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", "translation": "In the name of Allah, the Most Gracious, the Most Merciful."},
                {"arabic": "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ", "translation": "Praise be to Allah, the Lord of all the worlds."},
                {"arabic": "الرَّحْمَٰنِ الرَّحِيمِ", "translation": "The Most Gracious, the Most Merciful."},
                {"arabic": "مَالِكِ يَوْمِ الدِّينِ", "translation": "Master of the Day of Judgment."},
                {"arabic": "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ", "translation": "You alone we worship, and You alone we ask for help."},
                {"arabic": "اهْدِنَا الصِّرَاطَ الْمُسْتَقِيمَ", "translation": "Guide us to the straight path."},
                {"arabic": "صِرَاطَ الَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ الْمَغْضُوبِ عَلَيْهِمْ وَلَا الضَّالِّينَ", "translation": "The path of those upon whom You have bestowed favor, not of those who have evoked anger or of those who are astray."}
            ]
        },
        {
            "name": "Al-Ikhlas",
            "verses": [
                {"arabic": "قُلْ هُوَ اللَّهُ أَحَدٌ", "translation": "Say, 'He is Allah, [who is] One."},
                {"arabic": "اللَّهُ الصَّمَدُ", "translation": "Allah, the Eternal Refuge."},
                {"arabic": "لَمْ يَلِدْ وَلَمْ يُولَدْ", "translation": "He neither begets nor is born."},
                {"arabic": "وَلَمْ يَكُن لَّهُ كُفُوًا أَحَدٌ", "translation": "Nor is there to Him any equivalent.'"}
            ]
        }
    ]
}

# Vocabulary words
VOCAB = [
    {"arabic": "الرَّحْمَٰنِ", "translation": "The Most Gracious", "example": "Ar-Rahman (The Most Gracious) – a name of Allah."},
    {"arabic": "الرَّحِيمِ", "translation": "The Most Merciful", "example": "Ar-Raheem (The Most Merciful) – a name of Allah."},
    {"arabic": "الْحَمْدُ", "translation": "Praise", "example": "Alhamdu lillah (All praise is due to Allah)."},
    {"arabic": "رَبِّ", "translation": "Lord", "example": "Rabb al-'alameen (Lord of the worlds)."},
    {"arabic": "مَالِكِ", "translation": "Master/Owner", "example": "Maliki yawm ad-deen (Master of the Day of Judgment)."},
]

# Ramadan recipes
RECIPES = [
    {"name": "Dates Milkshake", "ingredients": "Dates, milk, ice, cardamom", "instructions": "Blend all ingredients until smooth."},
    {"name": "Lentil Soup", "ingredients": "Lentils, onion, carrot, spices", "instructions": "Cook lentils with vegetables and spices."},
    {"name": "Samosa", "ingredients": "Potatoes, peas, spices, pastry sheets", "instructions": "Fill pastry with spiced potatoes and deep fry."},
]

# Moon phase calculation helper (simplified)
def moon_phase(date=None):
    if date is None:
        date = datetime.date.today()
    # Approximate moon phase: 0=new, 0.5=full, etc.
    # Using a known new moon: 2000-01-06
    known_new_moon = datetime.date(2000, 1, 6)
    diff = (date - known_new_moon).days
    lunations = diff / 29.53058867
    phase = lunations - math.floor(lunations)
    return phase  # 0 to 1

# Ramadan progress (example: assume Ramadan starts 2025-03-01, Eid 2025-03-30)
RAMADAN_START = datetime.date(2025, 3, 1)
RAMADAN_END = datetime.date(2025, 3, 30)
TODAY = datetime.date.today()
ramadan_days_total = (RAMADAN_END - RAMADAN_START).days + 1
ramadan_days_passed = (TODAY - RAMADAN_START).days
if ramadan_days_passed < 0:
    ramadan_days_passed = 0
elif ramadan_days_passed > ramadan_days_total:
    ramadan_days_passed = ramadan_days_total
ramadan_progress = ramadan_days_passed / ramadan_days_total if ramadan_days_total > 0 else 0

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def speak_text(text, lang='en'):
    """Convert text to speech using gTTS and play with pygame."""
    if not gTTS or not pygame:
        messagebox.showinfo("Audio Unavailable", "gTTS or pygame not installed.")
        return
    try:
        tts = gTTS(text=text, lang=lang)
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        pygame.mixer.init()
        pygame.mixer.music.load(fp)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
    except Exception as e:
        messagebox.showerror("Audio Error", str(e))

def send_notification(title, message):
    """Send desktop notification."""
    if notification:
        try:
            notification.notify(title=title, message=message, timeout=10)
        except Exception as e:
            print("Notification error:", e)
    else:
        print(f"Notification: {title} - {message}")

def ifttt_webhook(event, key, value1=None, value2=None, value3=None):
    """Trigger IFTTT webhook."""
    if not requests:
        return
    url = IFTTT_WEBHOOK_URL.format(event=event, key=key)
    payload = {}
    if value1:
        payload["value1"] = value1
    if value2:
        payload["value2"] = value2
    if value3:
        payload["value3"] = value3
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("IFTTT error:", e)

# ----------------------------------------------------------------------
# Main Application Class
# ----------------------------------------------------------------------
class QuranApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Quran Companion")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        # Data
        self.progress_file = "progress.json"
        self.progress_data = self.load_progress()
        self.city = CITY
        self.country = COUNTRY

        # Google Sheets client (mock if not available)
        self.gs_client = None
        if gspread:
            self.setup_google_sheets()

        # Create tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True)

        self.create_home_tab()
        self.create_quran_tab()
        self.create_prayer_tab()
        self.create_zakat_tab()
        self.create_recipes_tab()
        self.create_vocab_tab()
        self.create_progress_tab()
        self.create_moon_tab()

        # Start daily reminder thread
        self.start_reminder_thread()

        # On closing, save progress
        root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # ------------------------------------------------------------------
    # Progress persistence
    # ------------------------------------------------------------------
    def load_progress(self):
        """Load progress from local JSON file."""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"read_surahs": []}
        else:
            return {"read_surahs": []}

    def save_progress(self):
        """Save progress to local JSON."""
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress_data, f, indent=2)
        except Exception as e:
            print("Save error:", e)

    def sync_with_google_sheets(self):
        """Sync progress to Google Sheets (mock or real)."""
        if self.gs_client:
            try:
                sheet = self.gs_client.open("QuranProgress").sheet1
                # Simple sync: write read surahs as a comma-separated list
                sheet.update('A1', [[','.join(self.progress_data.get('read_surahs', []))]])
                messagebox.showinfo("Sync", "Progress synced with Google Sheets.")
            except Exception as e:
                messagebox.showerror("Sync Error", str(e))
        else:
            messagebox.showinfo("Sync", "Google Sheets not configured. Progress saved locally.")

    def setup_google_sheets(self):
        """Authenticate with Google Sheets (requires credentials.json)."""
        try:
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
            self.gs_client = gspread.authorize(creds)
        except Exception as e:
            print("Google Sheets setup failed:", e)
            self.gs_client = None

    # ------------------------------------------------------------------
    # Home Tab (Random Verse of the Day)
    # ------------------------------------------------------------------
    def create_home_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Home")

        ttk.Label(frame, text="Random Verse of the Day", font=('Arial', 16)).pack(pady=10)

        self.verse_text = tk.StringVar()
        verse_label = ttk.Label(frame, textvariable=self.verse_text, wraplength=600, font=('Arial', 12))
        verse_label.pack(pady=20)

        self.translation_text = tk.StringVar()
        trans_label = ttk.Label(frame, textvariable=self.translation_text, wraplength=600, font=('Arial', 10))
        trans_label.pack(pady=10)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="New Verse", command=self.random_verse).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Play Audio (English)", command=self.play_random_verse_audio).pack(side='left', padx=5)

        self.random_verse()  # initial

    def random_verse(self):
        surah = random.choice(QURAN_SAMPLE["surahs"])
        verse = random.choice(surah["verses"])
        self.current_verse = verse
        self.verse_text.set(f"{surah['name']}: {verse['arabic']}")
        self.translation_text.set(verse['translation'])

    def play_random_verse_audio(self):
        if hasattr(self, 'current_verse'):
            speak_text(self.current_verse['translation'], 'en')
        else:
            self.random_verse()
            speak_text(self.current_verse['translation'], 'en')

    # ------------------------------------------------------------------
    # Quran Reader Tab
    # ------------------------------------------------------------------
    def create_quran_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Quran Reader")

        # Surah selection
        top_frame = ttk.Frame(frame)
        top_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(top_frame, text="Select Surah:").pack(side='left')
        self.surah_var = tk.StringVar()
        surah_names = [s["name"] for s in QURAN_SAMPLE["surahs"]]
        surah_menu = ttk.Combobox(top_frame, textvariable=self.surah_var, values=surah_names, state='readonly')
        surah_menu.pack(side='left', padx=5)
        surah_menu.bind('<<ComboboxSelected>>', self.load_surah)

        # Text area for displaying Quran
        self.quran_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=70, height=20, font=('Arial', 12))
        self.quran_text.pack(fill='both', expand=True, padx=10, pady=5)

        # Buttons for audio and marking as read
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Play Selected Verse (English)", command=self.play_selected_verse).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Mark Surah as Read", command=self.mark_surah_read).pack(side='left', padx=5)

    def load_surah(self, event=None):
        surah_name = self.surah_var.get()
        self.quran_text.delete(1.0, tk.END)
        for s in QURAN_SAMPLE["surahs"]:
            if s["name"] == surah_name:
                for i, v in enumerate(s["verses"], 1):
                    self.quran_text.insert(tk.END, f"{i}. {v['arabic']}\n")
                    self.quran_text.insert(tk.END, f"   {v['translation']}\n\n")
                break

    def play_selected_verse(self):
        # Simple: get current selection if any, otherwise play first verse of current surah
        try:
            selected = self.quran_text.selection_get()
            # find verse translation? For simplicity, we'll just speak selected text.
            speak_text(selected, 'en')
        except:
            # speak first verse of current surah
            surah_name = self.surah_var.get()
            for s in QURAN_SAMPLE["surahs"]:
                if s["name"] == surah_name:
                    if s["verses"]:
                        speak_text(s["verses"][0]['translation'], 'en')
                    break

    def mark_surah_read(self):
        surah_name = self.surah_var.get()
        if surah_name:
            if surah_name not in self.progress_data["read_surahs"]:
                self.progress_data["read_surahs"].append(surah_name)
                self.save_progress()
                messagebox.showinfo("Progress", f"Marked {surah_name} as read.")
            else:
                messagebox.showinfo("Progress", f"{surah_name} already marked read.")

    # ------------------------------------------------------------------
    # Prayer Times Tab
    # ------------------------------------------------------------------
    def create_prayer_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Prayer Times")

        settings_frame = ttk.Frame(frame)
        settings_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(settings_frame, text="City:").pack(side='left')
        self.city_entry = ttk.Entry(settings_frame, width=15)
        self.city_entry.insert(0, self.city)
        self.city_entry.pack(side='left', padx=5)
        ttk.Label(settings_frame, text="Country:").pack(side='left')
        self.country_entry = ttk.Entry(settings_frame, width=15)
        self.country_entry.insert(0, self.country)
        self.country_entry.pack(side='left', padx=5)
        ttk.Button(settings_frame, text="Update", command=self.update_prayer_times).pack(side='left', padx=5)

        self.prayer_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=50, height=15, font=('Arial', 11))
        self.prayer_text.pack(fill='both', expand=True, padx=10, pady=5)

        self.update_prayer_times()

    def update_prayer_times(self):
        city = self.city_entry.get().strip()
        country = self.country_entry.get().strip()
        if not city or not country:
            messagebox.showerror("Error", "City and country required.")
            return

        if not requests:
            self.prayer_text.delete(1.0, tk.END)
            self.prayer_text.insert(tk.END, "Requests library not installed.\nCannot fetch prayer times.")
            return

        today = datetime.date.today().strftime("%d-%m-%Y")
        url = f"http://api.aladhan.com/v1/timingsByCity/{today}?city={city}&country={country}&method=2"
        try:
            response = requests.get(url)
            data = response.json()
            if data["code"] == 200:
                timings = data["data"]["timings"]
                self.prayer_text.delete(1.0, tk.END)
                for name, time_str in timings.items():
                    self.prayer_text.insert(tk.END, f"{name}: {time_str}\n")
            else:
                self.prayer_text.delete(1.0, tk.END)
                self.prayer_text.insert(tk.END, "Error fetching prayer times.")
        except Exception as e:
            self.prayer_text.delete(1.0, tk.END)
            self.prayer_text.insert(tk.END, f"Error: {e}")

    # ------------------------------------------------------------------
    # Zakat Calculator Tab
    # ------------------------------------------------------------------
    def create_zakat_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Zakat Calculator")

        ttk.Label(frame, text="Zakat Calculator (2.5% of wealth)", font=('Arial', 14)).pack(pady=10)

        input_frame = ttk.Frame(frame)
        input_frame.pack(pady=10)
        ttk.Label(input_frame, text="Total Wealth (in USD):").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.wealth_var = tk.DoubleVar()
        ttk.Entry(input_frame, textvariable=self.wealth_var).grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(frame, text="Calculate Zakat", command=self.calculate_zakat).pack(pady=10)

        self.zakat_result = tk.StringVar()
        ttk.Label(frame, textvariable=self.zakat_result, font=('Arial', 12), foreground='green').pack(pady=10)

    def calculate_zakat(self):
        try:
            wealth = self.wealth_var.get()
            if wealth < 0:
                raise ValueError
            zakat = wealth * 0.025
            self.zakat_result.set(f"Zakat due: ${zakat:.2f}")
        except:
            messagebox.showerror("Error", "Please enter a valid positive number.")

    # ------------------------------------------------------------------
    # Ramadan Recipes Tab
    # ------------------------------------------------------------------
    def create_recipes_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Ramadan Recipes")

        listbox_frame = ttk.Frame(frame)
        listbox_frame.pack(side='left', fill='y', padx=10, pady=10)
        ttk.Label(listbox_frame, text="Recipes").pack()
        self.recipe_listbox = tk.Listbox(listbox_frame, height=10)
        self.recipe_listbox.pack(fill='both', expand=True)
        for r in RECIPES:
            self.recipe_listbox.insert(tk.END, r['name'])
        self.recipe_listbox.bind('<<ListboxSelect>>', self.show_recipe)

        self.recipe_display = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=50, height=15)
        self.recipe_display.pack(fill='both', expand=True, padx=10, pady=10)

    def show_recipe(self, event):
        selection = self.recipe_listbox.curselection()
        if selection:
            idx = selection[0]
            recipe = RECIPES[idx]
            self.recipe_display.delete(1.0, tk.END)
            self.recipe_display.insert(tk.END, f"Recipe: {recipe['name']}\n\n")
            self.recipe_display.insert(tk.END, f"Ingredients:\n{recipe['ingredients']}\n\n")
            self.recipe_display.insert(tk.END, f"Instructions:\n{recipe['instructions']}")

    # ------------------------------------------------------------------
    # Vocabulary Builder Tab
    # ------------------------------------------------------------------
    def create_vocab_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Vocabulary Builder")

        listbox_frame = ttk.Frame(frame)
        listbox_frame.pack(side='left', fill='y', padx=10, pady=10)
        ttk.Label(listbox_frame, text="Arabic Words").pack()
        self.vocab_listbox = tk.Listbox(listbox_frame, height=10)
        self.vocab_listbox.pack(fill='both', expand=True)
        for v in VOCAB:
            self.vocab_listbox.insert(tk.END, v['arabic'])
        self.vocab_listbox.bind('<<ListboxSelect>>', self.show_vocab)

        # Right panel
        right_frame = ttk.Frame(frame)
        right_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)

        self.vocab_arabic = tk.StringVar()
        ttk.Label(right_frame, textvariable=self.vocab_arabic, font=('Arial', 20)).pack(pady=5)

        self.vocab_trans = tk.StringVar()
        ttk.Label(right_frame, textvariable=self.vocab_trans, font=('Arial', 14)).pack(pady=5)

        self.vocab_example = tk.StringVar()
        ttk.Label(right_frame, textvariable=self.vocab_example, wraplength=300).pack(pady=5)

        ttk.Button(right_frame, text="Play Translation Audio", command=self.play_vocab_audio).pack(pady=10)

    def show_vocab(self, event):
        selection = self.vocab_listbox.curselection()
        if selection:
            idx = selection[0]
            vocab = VOCAB[idx]
            self.current_vocab = vocab
            self.vocab_arabic.set(vocab['arabic'])
            self.vocab_trans.set(vocab['translation'])
            self.vocab_example.set(vocab['example'])

    def play_vocab_audio(self):
        if hasattr(self, 'current_vocab'):
            speak_text(f"{self.current_vocab['arabic']} means {self.current_vocab['translation']}", 'en')

    # ------------------------------------------------------------------
    # Progress Tracker Tab
    # ------------------------------------------------------------------
    def create_progress_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Progress Tracker")

        ttk.Label(frame, text="Surahs Read", font=('Arial', 14)).pack(pady=5)

        self.progress_listbox = tk.Listbox(frame, height=15)
        self.progress_listbox.pack(fill='both', expand=True, padx=10, pady=5)

        self.refresh_progress_list()

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Sync with Google Sheets", command=self.sync_with_google_sheets).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Refresh", command=self.refresh_progress_list).pack(side='left', padx=5)

    def refresh_progress_list(self):
        self.progress_listbox.delete(0, tk.END)
        for surah in self.progress_data.get("read_surahs", []):
            self.progress_listbox.insert(tk.END, surah)

    # ------------------------------------------------------------------
    # Moon Phase / Ramadan Progress Tab
    # ------------------------------------------------------------------
    def create_moon_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Moon & Ramadan")

        # Moon phase
        ttk.Label(frame, text="Current Moon Phase", font=('Arial', 14)).pack(pady=5)
        phase = moon_phase()
        phase_names = ["New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous", "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent"]
        idx = int(phase * 8) % 8
        phase_name = phase_names[idx]
        ttk.Label(frame, text=f"Phase: {phase_name}", font=('Arial', 12)).pack(pady=5)

        # Ramadan progress bar
        ttk.Label(frame, text="Ramadan Progress", font=('Arial', 14)).pack(pady=(20,5))
        progress_var = tk.DoubleVar(value=ramadan_progress)
        progress_bar = ttk.Progressbar(frame, orient='horizontal', length=400, mode='determinate', variable=progress_var)
        progress_bar.pack(pady=5)
        days_left = ramadan_days_total - ramadan_days_passed
        ttk.Label(frame, text=f"{ramadan_days_passed} days passed, {days_left} days until Eid").pack()

    # ------------------------------------------------------------------
    # Daily Reminder Thread
    # ------------------------------------------------------------------
    def reminder_loop(self):
        while True:
            now = datetime.datetime.now()
            # Check if it's Suhoor time (e.g., 3:00 AM)
            if now.hour == SUHOOR_HOUR and now.minute == SUHOOR_MINUTE:
                send_notification("Suhoor Reminder", "Time for Suhoor! Don't forget your intention for fasting.")
                # Optionally trigger IFTTT
                # ifttt_webhook("suhoor_reminder", "your_key", value1="Suhoor time")
                time.sleep(60)  # avoid multiple triggers
            time.sleep(30)  # check every 30 seconds

    def start_reminder_thread(self):
        thread = threading.Thread(target=self.reminder_loop, daemon=True)
        thread.start()

    # ------------------------------------------------------------------
    # Cleanup on close
    # ------------------------------------------------------------------
    def on_closing(self):
        self.save_progress()
        self.root.destroy()

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = QuranApp(root)
    root.mainloop()
