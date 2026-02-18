import streamlit as st
import requests
import random
import pandas as pd
from datetime import datetime

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Ramadan Coach 2026", page_icon="🌙", layout="wide")

# --- USER SETTINGS ---
SHEET_ID = "YOUR_SHEET_ID_HERE" 
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .arabic-text { font-family: 'Amiri', serif; font-size: 34px; direction: rtl; text-align: right; color: #1B5E20; line-height: 2.2; }
    .translation-text { font-size: 18px; color: #444; margin-bottom: 25px; border-left: 3px solid #eee; padding-left: 15px; }
    .prayer-card { background-color: #f1f8e9; padding: 15px; border-radius: 10px; border-right: 6px solid #2E7D32; margin-bottom: 10px; }
    .vocab-card { border: 1px solid #e0e0e0; border-radius: 12px; padding: 15px; background-color: #ffffff; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCTIONS ---
def get_prayer_times(city, country):
    try:
        url = f"https://api.aladhan.com/v1/timingsByCity?city={city}&country={country}&method=2"
        res = requests.get(url).json()
        return res['data']['timings']
    except: return None

def load_google_progress():
    try: return pd.read_csv(SHEET_URL)
    except: return pd.DataFrame(columns=["Surah", "Date"])

# --- SIDEBAR: KABALA HUB & NOTIFICATIONS ---
with st.sidebar:
    st.title("🕌 My Ramadan Hub")
    city = st.text_input("Current City", "Kabala")
    
    times = get_prayer_times(city, "Sierra Leone")
    if times:
        st.subheader(f"📅 Prayer Times ({city})")
        st.markdown(f"<div class='prayer-card'>🚩 <b>Suhoor Ends:</b> {times['Fajr']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='prayer-card' style='background-color:#fff3e0;'>🌙 <b>Iftar:</b> {times['Maghrib']}</div>", unsafe_allow_html=True)
        
        st.info(f"🔔 **IFTTT Goal:** Set your phone alarm to {times['Fajr']} to hit your Daily Goal!")

    st.divider()
    st.subheader("📊 Permanent Tracker")
    df_prog = load_google_progress()
    st.dataframe(df_prog, hide_index=True)
    st.link_button("📝 Open Tracking Sheet", f"https://docs.google.com/spreadsheets/d/{SHEET_ID}")

# --- MAIN APP INTERFACE ---
tabs = st.tabs(["📖 Quran", "🧠 Vocab", "💰 Zakat", "🥗 Food", "✨ Daily", "🌙 Moon"])

# 1. QURAN TAB
with tabs[0]:
    st.header("Whole Quran & Audio")
    s_num = st.number_input("Select Surah (1-114):", 1, 114, 1)
    if st.button("Load Surah"):
        res = requests.get(f"https://api.alquran.cloud/v1/surah/{s_num}/editions/quran-uthmani,en.sahih").json()
        st.subheader(f"{res['data'][0]['name']} - {res['data'][0]['englishName']}")
        st.audio(f"https://cdn.islamic.network/quran/audio-surah/128/ar.alafasy/{s_num}.mp3")
        for ar, en in zip(res['data'][0]['ayahs'], res['data'][1]['ayahs']):
            st.markdown(f"<p class='arabic-text'>{ar['text']}</p>", unsafe_allow_html=True)
            st.markdown(f"<div class='translation-text'>{en['text']}</div>", unsafe_allow_html=True)

# 2. VOCABULARY TAB (With Audio)
with tabs[1]:
    st.header("🧠 Vocabulary Builder")
    vocabs = [
        {"ar": "اللّه", "en": "Allah", "audio": "https://everyayah.com/data/Arabic_Words/001001.mp3"},
        {"ar": "رَبّ", "en": "Lord", "audio": "https://everyayah.com/data/Arabic_Words/001002.mp3"},
        {"ar": "عَلِيم", "en": "All-Knowing", "audio": "https://everyayah.com/data/Arabic_Words/002032.mp3"}
    ]
    for item in vocabs:
        col1, col2 = st.columns([1, 3])
        with col1: st.subheader(item['ar'])
        with col2: 
            st.write(f"**{item['en']}**")
            st.audio(item['audio'])
        st.divider()

# 3. ZAKAT TAB
with tabs[2]:
    st.header("💰 Zakat Calculator")
    assets = st.number_input("Total Wealth:", min_value=0.0)
    if assets > 0: st.success(f"Zakat Due: **{assets * 0.025:,.2f}**")

# 4. RECIPE TAB
with tabs[3]:
    st.header("🥗 Ramadan Recipes")
    st.info("🌅 **Suhoor:** Oats + Dates + 1L Water.")
    st.success("🌙 **Iftar:** 3 Dates + Lentil Soup + Protein.")

# 5. DAILY VERSE TAB
with tabs[4]:
    st.header("✨ Verse of the Day")
    if st.button("Surprise Me"):
        r = random.randint(1, 6236)
        v = requests.get(f"https://api.alquran.cloud/v1/ayah/{r}/editions/quran-uthmani,en.sahih").json()
        st.markdown(f"<p class='arabic-text'>{v['data'][0]['text']}</p>", unsafe_allow_html=True)
        st.info(v['data'][1]['text'])

# 6. MOON TAB
with tabs[5]:
    st.header("🌙 Ramadan Progress")
    day = st.slider("Current Day of Ramadan", 1, 30, 1)
    st.progress(day / 30)
    st.write(f"**{int((day/30)*100)}%** of the month completed. Stay strong!")
