#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Streamlit Quran Companion App
--------------------------------
- Fetches full Quran from AlQuran.cloud (Arabic + English)
- Random verse of the day with audio
- Prayer times (Aladhan API)
- Zakat calculator
- Ramadan recipes
- Vocabulary builder with audio
- Progress tracker (local JSON + optional Google Sheets sync)
- Daily Suhoor reminder via IFTTT (user configurable)
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

# Optional imports (graceful fallback)
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    st.warning("⚠️ gTTS not installed. Audio features disabled. Run: pip install gtts")

try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    GSHEETS_AVAILABLE = True
except ImportError:
    GSHEETS_AVAILABLE = False
    st.warning("⚠️ gspread/oauth2client not installed. Google Sheets sync disabled.")

# ------------------------------
# Configuration
# ------------------------------
st.set_page_config(
    page_title="Quran Companion",
    page_icon="🕌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
DEFAULT_CITY = "Mecca"
DEFAULT_COUNTRY = "Saudi Arabia"

# Ramadan dates (adjust as needed)
RAMADAN_START = datetime.date(2025, 3, 1)
RAMADAN_END = datetime.date(2025, 3, 30)

# IFTTT webhook template (user must replace with their own key)
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
# Cached API functions
# ------------------------------
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_surah_list():
    """Fetch list of all surahs from AlQuran.cloud."""
    url = "http://api.alquran.cloud/v1/surah"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if data["code"] == 200:
            return data["data"]
    except Exception as e:
        st.error(f"Failed to fetch surah list: {e}")
    return []

@st.cache_data(ttl=3600)
def get_surah_with_translation(surah_number):
    """Fetch Arabic verses and English translation for a surah."""
    ar_url = f"http://api.alquran.cloud/v1/surah/{surah_number}"
    en_url = f"http://api.alquran.cloud/v1/surah/{surah_number}/en.sahih"
    try:
        ar_resp = requests.get(ar_url, timeout=10)
        en_resp = requests.get(en_url, timeout=10)
        if ar_resp.status_code == 200 and en_resp.status_code == 200:
            ar_data = ar_resp.json()["data"]
            en_data = en_resp.json()["data"]
            verses = []
            for i, ar_verse in enumerate(ar_data["ayahs"]):
                verses.append({
                    "arabic": ar_verse["text"],
                    "translation": en_data["ayahs"][i]["text"],
                    "number": ar_verse["numberInSurah"]
                })
            return {
                "name": ar_data["englishName"],
                "number": surah_number,
                "verses": verses
            }
    except Exception as e:
        st.error(f"Failed to fetch surah {surah_number}: {e}")
    return None

def get_random_verse():
    """Fetch a random verse from the Quran."""
    surah_list = get_surah_list()
    if not surah_list:
        return None
    surah = random.choice(surah_list)
    surah_data = get_surah_with_translation(surah["number"])
    if not surah_data or not surah_data["verses"]:
        return None
    verse = random.choice(surah_data["verses"])
    return {
        "surah": surah_data["name"],
        "arabic": verse["arabic"],
        "translation": verse["translation"],
        "verse_number": verse["number"]
    }

def get_prayer_times(city, country):
    """Fetch prayer times from Aladhan API."""
    today = datetime.date.today().strftime("%d-%m-%Y")
    url = f"http://api.aladhan.com/v1/timingsByCity/{today}?city={city}&country={country}&method=2"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if data["code"] == 200:
            return data["data"]["timings"]
    except Exception as e:
        st.error(f"Prayer times error: {e}")
    return None

# ------------------------------
# Audio helper
# ------------------------------
def text_to_audio(text, lang='en'):
    """Convert text to audio bytes (MP3). Returns bytes or None."""
    if not GTTS_AVAILABLE:
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
    if not GSHEETS_AVAILABLE:
        st.error("gspread not installed.")
        return False
    if not os.path.exists("credentials.json"):
        st.error("credentials.json not found in current directory.")
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
        requests.post(url, data=payload, timeout=10)
        return True
    except Exception as e:
        st.error(f"IFTTT trigger failed: {e}")
        return False

# ------------------------------
# Moon phase helper
# ------------------------------
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
# Main app
# ------------------------------
def main():
    st.sidebar.title("🌙 Quran Companion")
    menu = st.sidebar.radio(
        "Navigate",
        ["🏠 Home (Random Verse)",
         "📖 Quran Reader",
         "🕋 Prayer Times",
         "💰 Zakat Calculator",
         "🍽️ Ramadan Recipes",
         "📚 Vocabulary Builder",
         "📊 Progress Tracker",
         "🌒 Moon & Ramadan"]
    )

    # Sidebar: IFTTT setup (optional)
    with st.sidebar.expander("🔔 Daily Suhoor Reminder (IFTTT)"):
        st.markdown("""
        Get a notification on your phone every morning at Suhoor time.
        1. Create an IFTTT applet with **Webhook** trigger.
        2. Use event name: `suhoor_reminder`.
        3. Enter your IFTTT key below.
        """)
        ifttt_key = st.text_input("IFTTT Key", type="password")
        if st.button("Test Reminder Now"):
            if ifttt_key:
                if trigger_ifttt("suhoor_reminder", ifttt_key, "Suhoor time! Don't forget your intention."):
                    st.success("✅ Trigger sent!")
                else:
                    st.error("❌ Failed. Check key and internet.")
            else:
                st.warning("Please enter your IFTTT key.")

    # ------------------------------
    # Home: Random Verse
    # ------------------------------
    if menu == "🏠 Home (Random Verse)":
        st.header("✨ Random Verse of the Day")
        if st.button("Get New Random Verse"):
            with st.spinner("Fetching a verse..."):
                verse = get_random_verse()
                if verse:
                    st.session_state["random_verse"] = verse
                else:
                    st.error("Could not fetch verse. Please check your internet connection.")
        
        if "random_verse" in st.session_state:
            v = st.session_state["random_verse"]
            st.markdown(f"**Surah {v['surah']} (Verse {v['verse_number']})**")
            st.markdown(f"<h2 style='text-align: right; font-size: 28px;'>{v['arabic']}</h2>", unsafe_allow_html=True)
            st.markdown(f"*{v['translation']}*")
            
            # Audio buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔊 Play Translation (English)"):
                    audio = text_to_audio(v['translation'], lang='en')
                    if audio:
                        st.audio(audio, format='audio/mp3')
                    else:
                        st.warning("Audio not available (gTTS missing or error).")
            with col2:
                if st.button("🔊 Play Arabic (experimental)"):
                    audio = text_to_audio(v['arabic'], lang='ar')
                    if audio:
                        st.audio(audio, format='audio/mp3')
                    else:
                        st.warning("Arabic audio may not be accurate.")
        else:
            st.info("Click the button to get a random verse.")

    # ------------------------------
    # Quran Reader
    # ------------------------------
    elif menu == "📖 Quran Reader":
        st.header("📖 Quran Reader")
        surah_list = get_surah_list()
        if not surah_list:
            st.error("Failed to load surah list. Please check your internet connection.")
            return
        
        # Create selection box
        surah_names = [f"{s['number']}. {s['englishName']} ({s['name']})" for s in surah_list]
        selected = st.selectbox("Select Surah", surah_names, key="surah_selector")
        surah_number = int(selected.split('.')[0])
        
        if st.button("Load Surah"):
            with st.spinner("Loading verses..."):
                surah_data = get_surah_with_translation(surah_number)
                if surah_data:
                    st.session_state["current_surah"] = surah_data
                else:
                    st.error("Failed to load surah.")
        
        if "current_surah" in st.session_state and st.session_state["current_surah"]["number"] == surah_number:
            surah = st.session_state["current_surah"]
            st.subheader(f"Surah {surah['name']}")
            
            # Display verses
            for verse in surah["verses"]:
                with st.expander(f"Verse {verse['number']}"):
                    st.markdown(f"<p style='font-size:24px; text-align:right;'>{verse['arabic']}</p>", unsafe_allow_html=True)
                    st.markdown(f"*{verse['translation']}*")
                    if st.button(f"🔊 Play Verse {verse['number']}", key=f"play_q_{verse['number']}"):
                        audio = text_to_audio(verse['translation'], lang='en')
                        if audio:
                            st.audio(audio, format='audio/mp3')
            
            # Mark as read
            surah_name_for_progress = surah['name']
            progress = load_progress()
            if surah_name_for_progress not in progress["read_surahs"]:
                if st.button("✅ Mark this Surah as Read"):
                    progress["read_surahs"].append(surah_name_for_progress)
                    save_progress(progress)
                    st.success(f"Marked {surah_name_for_progress} as read.")
            else:
                st.info("You have already marked this surah as read.")

    # ------------------------------
    # Prayer Times
    # ------------------------------
    elif menu == "🕋 Prayer Times":
        st.header("🕋 Prayer Times")
        col1, col2 = st.columns(2)
        with col1:
            city = st.text_input("City", value=DEFAULT_CITY)
        with col2:
            country = st.text_input("Country", value=DEFAULT_COUNTRY)
        
        if st.button("Get Today's Prayer Times"):
            with st.spinner("Fetching..."):
                timings = get_prayer_times(city, country)
                if timings:
                    st.success(f"Prayer times for {city}, {country} on {datetime.date.today().strftime('%d %B %Y')}:")
                    # Display in a clean table
                    for name, time_str in timings.items():
                        st.write(f"**{name}:** {time_str}")
                else:
                    st.error("Could not fetch prayer times. Check city/country or try again later.")

    # ------------------------------
    # Zakat Calculator
    # ------------------------------
    elif menu == "💰 Zakat Calculator":
        st.header("💰 Zakat Calculator (2.5%)")
        wealth = st.number_input("Total Wealth (in USD)", min_value=0.0, step=100.0, value=10000.0)
        if st.button("Calculate Zakat"):
            zakat = wealth * 0.025
            st.success(f"Zakat due: **${zakat:,.2f}**")

    # ------------------------------
    # Ramadan Recipes
    # ------------------------------
    elif menu == "🍽️ Ramadan Recipes":
        st.header("🍽️ Ramadan Recipes")
        for recipe in RECIPES:
            with st.expander(recipe["name"]):
                st.markdown(f"**Ingredients:** {recipe['ingredients']}")
                st.markdown(f"**Instructions:** {recipe['instructions']}")

    # ------------------------------
    # Vocabulary Builder
    # ------------------------------
    elif menu == "📚 Vocabulary Builder":
        st.header("📚 Quranic Vocabulary Builder")
        for word in VOCAB:
            with st.expander(word["arabic"]):
                st.markdown(f"**Translation:** {word['translation']}")
                st.markdown(f"**Example:** {word['example']}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"🔊 Hear Arabic", key=f"ar_{word['arabic']}"):
                        audio = text_to_audio(word['arabic'], lang='ar')
                        if audio:
                            st.audio(audio, format='audio/mp3')
                        else:
                            st.warning("Audio unavailable.")
                with col2:
                    if st.button(f"🔊 Hear Meaning", key=f"en_{word['arabic']}"):
                        audio = text_to_audio(f"{word['arabic']} means {word['translation']}", lang='en')
                        if audio:
                            st.audio(audio, format='audio/mp3')

    # ------------------------------
    # Progress Tracker
    # ------------------------------
    elif menu == "📊 Progress Tracker":
        st.header("📊 Your Reading Progress")
        progress = load_progress()
        read_surahs = progress.get("read_surahs", [])
        
        if read_surahs:
            st.write("✅ Surahs you've marked as read:")
            for surah in read_surahs:
                st.write(f"- {surah}")
        else:
            st.info("No surahs marked as read yet. Go to the Quran Reader tab and start reading!")
        
        # Google Sheets sync
        if st.button("☁️ Sync with Google Sheets"):
            if sync_to_google_sheets(progress):
                st.success("Progress synced successfully!")
            else:
                st.error("Sync failed. Check credentials and sheet name.")
        
        # Reset local progress
        if st.button("🔄 Reset Local Progress"):
            save_progress({"read_surahs": []})
            st.success("Local progress reset.")
            st.rerun()

    # ------------------------------
    # Moon & Ramadan Progress
    # ------------------------------
    elif menu == "🌒 Moon & Ramadan":
        st.header("🌒 Moon Phase & Ramadan Progress")
        
        # Moon phase
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
            st.info("Ramadan hasn't started yet.")
        elif passed_days > total_days:
            passed_days = total_days
            st.info("Ramadan has ended. Eid Mubarak! 🎉")
        
        progress_value = passed_days / total_days if total_days > 0 else 0
        st.progress(progress_value)
        st.write(f"📅 Ramadan: **{passed_days}** days passed, **{total_days - passed_days}** days until Eid.")

    # ------------------------------
    # Footer with credits
    # ------------------------------
    st.sidebar.markdown("---")
    st.sidebar.info(
        "**Data sources:**\n"
        "- Quran: [AlQuran.cloud](https://alquran.cloud)\n"
        "- Prayer times: [Aladhan.com](https://aladhan.com)\n"
        "- Audio: gTTS\n\n"
        "Built with ❤️ using Streamlit"
    )

if __name__ == "__main__":
    main()
