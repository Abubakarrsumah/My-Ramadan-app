#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Streamlit Quran Companion App
--------------------------------
- Fetches full Quran from AlQuran.cloud API (Arabic + English translation)
- Random verse of the day with audio
- Prayer times, Zakat calculator, Ramadan recipes
- Vocabulary builder with audio
- Progress tracker (local JSON + optional Google Sheets sync)
- Daily Suhoor reminder via IFTTT (user must set up)
- Moon phase & Ramadan progress bar
"""

import streamlit as st
import requests
import json
import os
import datetime
import math
import random
import time
from io import BytesIO
from pathlib import Path

# Optional imports with fallbacks
try:
    from gtts import gTTS
except ImportError:
    st.error("gTTS not installed. Audio features disabled. Run: pip install gtts")
    gTTS = None

try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
except ImportError:
    gspread = None
    st.warning("gspread/oauth2client not installed. Google Sheets sync disabled.")

# ------------------------------
# Configuration
# ------------------------------
st.set_page_config(
    page_title="Quran Companion",
    page_icon="🕌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Default city for prayer times
DEFAULT_CITY = "Mecca"
DEFAULT_COUNTRY = "Saudi Arabia"

# Ramadan dates (adjust as needed)
RAMADAN_START = datetime.date(2025, 3, 1)
RAMADAN_END = datetime.date(2025, 3, 30)

# IFTTT webhook (user must replace with their own)
IFTTT_WEBHOOK_URL = "https://maker.ifttt.com/trigger/{event}/with/key/{key}"

# Vocabulary list (Arabic words with translations)
VOCAB = [
    {"arabic": "الرَّحْمَٰنِ", "translation": "The Most Gracious", "example": "Ar-Rahman – a name of Allah."},
    {"arabic": "الرَّحِيمِ", "translation": "The Most Merciful", "example": "Ar-Raheem – a name of Allah."},
    {"arabic": "الْحَمْدُ", "translation": "Praise", "example": "Alhamdu lillah (All praise is due to Allah)."},
    {"arabic": "رَبِّ", "translation": "Lord", "example": "Rabb al-'alameen (Lord of the worlds)."},
    {"arabic": "مَالِكِ", "translation": "Master/Owner", "example": "Maliki yawm ad-deen (Master of the Day of Judgment)."},
]

# Ramadan recipes (static)
RECIPES = [
    {"name": "Dates Milkshake", "ingredients": "Dates, milk, ice, cardamom", "instructions": "Blend all until smooth."},
    {"name": "Lentil Soup", "ingredients": "Lentils, onion, carrot, spices", "instructions": "Cook lentils with vegetables and spices."},
    {"name": "Samosa", "ingredients": "Potatoes, peas, spices, pastry sheets", "instructions": "Fill pastry with spiced potatoes and deep fry."},
]

# ------------------------------
# Helper functions
# ------------------------------
def get_quran_surah_list():
    """Fetch list of all surahs from AlQuran.cloud API."""
    url = "http://api.alquran.cloud/v1/surah"
    try:
        response = requests.get(url)
        data = response.json()
        if data["code"] == 200:
            return data["data"]
    except:
        pass
    return []

def get_surah_verses(surah_number):
    """Fetch Arabic verses and English translation for a surah."""
    # Arabic
    ar_url = f"http://api.alquran.cloud/v1/surah/{surah_number}"
    # English translation (Saheeh International)
    en_url = f"http://api.alquran.cloud/v1/surah/{surah_number}/en.sahih"
    try:
        ar_resp = requests.get(ar_url)
        en_resp = requests.get(en_url)
        if ar_resp.status_code == 200 and en_resp.status_code == 200:
            ar_data = ar_resp.json()["data"]
            en_data = en_resp.json()["data"]
            verses = []
            for i, ar_verse in enumerate(ar_data["ayahs"]):
                verses.append({
                    "arabic": ar_verse["text"],
                    "translation": en_data["ayahs"][i]["text"]
                })
            return verses
    except:
        pass
    return []

def get_random_verse():
    """Fetch a random verse from the Quran."""
    surah_list = get_quran_surah_list()
    if not surah_list:
        return None
    surah = random.choice(surah_list)
    verses = get_surah_verses(surah["number"])
    if not verses:
        return None
    verse = random.choice(verses)
    return {
        "surah": surah["englishName"],
        "arabic": verse["arabic"],
        "translation": verse["translation"]
    }

def speak_text(text, lang='en'):
    """Convert text to speech and return audio bytes."""
    if gTTS is None:
        return None
    try:
        tts = gTTS(text=text, lang=lang)
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except Exception as e:
        st.error(f"Audio generation failed: {e}")
        return None

def get_prayer_times(city, country):
    """Fetch prayer times from Aladhan API."""
    today = datetime.date.today().strftime("%d-%m-%Y")
    url = f"http://api.aladhan.com/v1/timingsByCity/{today}?city={city}&country={country}&method=2"
    try:
        response = requests.get(url)
        data = response.json()
        if data["code"] == 200:
            return data["data"]["timings"]
    except:
        pass
    return None

def moon_phase(date=None):
    """Approximate moon phase (0=new, 0.5=full)."""
    if date is None:
        date = datetime.date.today()
    known_new_moon = datetime.date(2000, 1, 6)
    diff = (date - known_new_moon).days
    lunations = diff / 29.53058867
    phase = lunations - math.floor(lunations)
    return phase

# ------------------------------
# Progress persistence (local JSON)
# ------------------------------
PROGRESS_FILE = "progress.json"

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"read_surahs": []}
    else:
        return {"read_surahs": []}

def save_progress(progress):
    try:
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress, f, indent=2)
    except Exception as e:
        st.error(f"Failed to save progress: {e}")

# ------------------------------
# Google Sheets sync (optional)
# ------------------------------
def sync_to_google_sheets(progress):
    """Sync read surahs to a Google Sheet (requires credentials.json)."""
    if not gspread:
        st.error("gspread not installed.")
        return False
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open("QuranProgress").sheet1
        # Write read surahs as comma-separated list in cell A1
        sheet.update('A1', [[','.join(progress.get('read_surahs', []))]])
        return True
    except Exception as e:
        st.error(f"Google Sheets sync failed: {e}")
        return False

# ------------------------------
# IFTTT reminder trigger
# ------------------------------
def trigger_ifttt(event, key, value1=None, value2=None, value3=None):
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
        return True
    except:
        return False

# ------------------------------
# Streamlit UI
# ------------------------------
def main():
    st.sidebar.title("Quran Companion")
    menu = st.sidebar.radio("Navigate", [
        "Home (Random Verse)",
        "Quran Reader",
        "Prayer Times",
        "Zakat Calculator",
        "Ramadan Recipes",
        "Vocabulary Builder",
        "Progress Tracker",
        "Moon & Ramadan"
    ])

    # Sidebar: IFTTT setup (optional)
    with st.sidebar.expander("🔔 Daily Suhoor Reminder (IFTTT)"):
        st.markdown("""
        Set up an IFTTT webhook to get a notification on your phone every morning at Suhoor time.
        1. Create an IFTTT applet with Webhook trigger.
        2. Use event name `suhoor_reminder`.
        3. Enter your IFTTT key below.
        """)
        ifttt_key = st.text_input("IFTTT Key", type="password")
        if st.button("Test Reminder Now"):
            if ifttt_key:
                if trigger_ifttt("suhoor_reminder", ifttt_key, "Suhoor time!"):
                    st.success("Trigger sent!")
                else:
                    st.error("Failed. Check key and internet.")
            else:
                st.warning("Enter your key.")

    # ------------------------------
    # Home Tab: Random Verse of the Day
    # ------------------------------
    if menu == "Home (Random Verse)":
        st.header("Random Verse of the Day")
        if st.button("Get New Verse"):
            with st.spinner("Fetching a random verse..."):
                verse = get_random_verse()
                if verse:
                    st.session_state["random_verse"] = verse
                else:
                    st.error("Could not fetch verse. Check internet.")
        if "random_verse" in st.session_state:
            v = st.session_state["random_verse"]
            st.markdown(f"**Surah {v['surah']}**")
            st.markdown(f"<h2 style='text-align: right;'>{v['arabic']}</h2>", unsafe_allow_html=True)
            st.markdown(f"*{v['translation']}*")
            audio_bytes = speak_text(v['translation'])
            if audio_bytes:
                st.audio(audio_bytes, format="audio/mp3")
        else:
            st.info("Click the button to get a random verse.")

    # ------------------------------
    # Quran Reader Tab
    # ------------------------------
    elif menu == "Quran Reader":
        st.header("Quran Reader")
        # Fetch surah list
        surah_list = get_quran_surah_list()
        if not surah_list:
            st.error("Failed to load surah list. Check internet.")
            return
        surah_names = [f"{s['number']}. {s['englishName']} ({s['name']})" for s in surah_list]
        selected = st.selectbox("Select Surah", surah_names)
        surah_number = int(selected.split('.')[0])
        if st.button("Load Surah"):
            with st.spinner("Loading verses..."):
                verses = get_surah_verses(surah_number)
                if verses:
                    st.session_state["current_surah"] = {
                        "number": surah_number,
                        "verses": verses
                    }
                else:
                    st.error("Failed to load verses.")
        if "current_surah" in st.session_state and st.session_state["current_surah"]["number"] == surah_number:
            verses = st.session_state["current_surah"]["verses"]
            for i, v in enumerate(verses, 1):
                st.markdown(f"**{i}.** <span style='font-size:20px;'>{v['arabic']}</span>", unsafe_allow_html=True)
                st.markdown(f"*{v['translation']}*")
                if st.button(f"🔊 Play Verse {i}", key=f"play_{i}"):
                    audio = speak_text(v['translation'])
                    if audio:
                        st.audio(audio, format="audio/mp3")
            # Mark surah as read
            if st.button("Mark this Surah as Read"):
                progress = load_progress()
                surah_name = selected.split('(')[0].strip()
                if surah_name not in progress["read_surahs"]:
                    progress["read_surahs"].append(surah_name)
                    save_progress(progress)
                    st.success(f"Marked {surah_name} as read.")
                else:
                    st.info("Already marked read.")

    # ------------------------------
    # Prayer Times Tab
    # ------------------------------
    elif menu == "Prayer Times":
        st.header("Prayer Times")
        col1, col2 = st.columns(2)
        with col1:
            city = st.text_input("City", value=DEFAULT_CITY)
        with col2:
            country = st.text_input("Country", value=DEFAULT_COUNTRY)
        if st.button("Get Prayer Times"):
            with st.spinner("Fetching..."):
                timings = get_prayer_times(city, country)
                if timings:
                    st.success("Prayer times for today:")
                    for name, time_str in timings.items():
                        st.write(f"**{name}:** {time_str}")
                else:
                    st.error("Could not fetch prayer times. Check city/country.")

    # ------------------------------
    # Zakat Calculator Tab
    # ------------------------------
    elif menu == "Zakat Calculator":
        st.header("Zakat Calculator (2.5%)")
        wealth = st.number_input("Total Wealth (in USD)", min_value=0.0, step=100.0)
        if st.button("Calculate Zakat"):
            zakat = wealth * 0.025
            st.success(f"Zakat due: **${zakat:.2f}**")

    # ------------------------------
    # Ramadan Recipes Tab
    # ------------------------------
    elif menu == "Ramadan Recipes":
        st.header("Ramadan Recipes")
        for recipe in RECIPES:
            with st.expander(recipe["name"]):
                st.markdown(f"**Ingredients:** {recipe['ingredients']}")
                st.markdown(f"**Instructions:** {recipe['instructions']}")

    # ------------------------------
    # Vocabulary Builder Tab
    # ------------------------------
    elif menu == "Vocabulary Builder":
        st.header("Quranic Vocabulary Builder")
        for word in VOCAB:
            with st.expander(word["arabic"]):
                st.markdown(f"**Translation:** {word['translation']}")
                st.markdown(f"**Example:** {word['example']}")
                if st.button(f"🔊 Pronounce {word['arabic']}", key=word["arabic"]):
                    # Speak the Arabic word (try Arabic TTS)
                    audio = speak_text(word["arabic"], lang='ar')
                    if audio:
                        st.audio(audio, format="audio/mp3")
                    else:
                        # Fallback to English explanation
                        audio = speak_text(f"{word['arabic']} means {word['translation']}")
                        if audio:
                            st.audio(audio, format="audio/mp3")

    # ------------------------------
    # Progress Tracker Tab
    # ------------------------------
    elif menu == "Progress Tracker":
        st.header("Your Reading Progress")
        progress = load_progress()
        read_surahs = progress.get("read_surahs", [])
        if read_surahs:
            st.write("Surahs you've marked as read:")
            for surah in read_surahs:
                st.write(f"- {surah}")
        else:
            st.info("No surahs marked as read yet.")
        if st.button("Sync with Google Sheets"):
            if sync_to_google_sheets(progress):
                st.success("Synced successfully!")
            else:
                st.error("Sync failed. Check credentials and sheet name.")
        if st.button("Reset Progress (local)"):
            save_progress({"read_surahs": []})
            st.success("Progress reset locally.")

    # ------------------------------
    # Moon & Ramadan Tab
    # ------------------------------
    elif menu == "Moon & Ramadan":
        st.header("Moon Phase & Ramadan Progress")
        phase = moon_phase()
        phase_names = ["New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous",
                       "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent"]
        idx = int(phase * 8) % 8
        st.metric("Current Moon Phase", phase_names[idx])

        # Ramadan progress
        today = datetime.date.today()
        total_days = (RAMADAN_END - RAMADAN_START).days + 1
        passed_days = (today - RAMADAN_START).days
        if passed_days < 0:
            passed_days = 0
        elif passed_days > total_days:
            passed_days = total_days
        progress = passed_days / total_days if total_days > 0 else 0
        st.progress(progress)
        st.write(f"Ramadan: {passed_days} days passed, {total_days - passed_days} days until Eid.")

if __name__ == "__main__":
    main()
