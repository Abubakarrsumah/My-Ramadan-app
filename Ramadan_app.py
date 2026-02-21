import streamlit as st
import requests
import random
import pandas as pd
from datetime import datetime

# --- 1. APP CONFIGURATION ---
st.set_page_config(page_title="Islam & Ramadan Hub 2026", page_icon="🌙", layout="wide")

# --- 2. USER SETTINGS (GOOGLE SHEETS) ---
# Replace this with the ID from your Google Sheet link
SHEET_ID = "YOUR_SHEET_ID_HERE" 
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

# --- 3. CUSTOM STYLING ---
st.markdown("""
    <style>
    .arabic-text { font-family: 'Amiri', serif; font-size: 34px; direction: rtl; text-align: right; color: #1B5E20; line-height: 2.2; }
    .translation-text { font-size: 18px; color: #444; margin-bottom: 25px; border-left: 3px solid #eee; padding-left: 15px; }
    .card { background-color: #fdfdfd; padding: 20px; border-radius: 10px; border-left: 5px solid #00796B; margin-bottom: 20px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    .prayer-card { background-color: #e8f5e9; padding: 12px; border-radius: 8px; border-right: 5px solid #2E7D32; margin-bottom: 8px; font-size: 16px;}
    </style>
    """, unsafe_allow_html=True)

# --- 4. HELPER FUNCTIONS ---
@st.cache_data(ttl=3600)
def get_prayer_times(city, country):
    try:
        url = f"https://api.aladhan.com/v1/timingsByCity?city={city}&country={country}&method=2"
        res = requests.get(url).json()
        return res['data']['timings']
    except: return None

def load_progress():
    try: return pd.read_csv(SHEET_URL)
    except: return pd.DataFrame(columns=["Surah/Item", "Date Completed"])

# --- 5. SIDEBAR: HUB & PRAYER TIMES ---
with st.sidebar:
    st.title("🕌 My Deen Center")
    city = st.text_input("City", "Kabala")
    country = st.text_input("Country", "Sierra Leone")
    times = get_prayer_times(city, country)
    
    if times:
        st.subheader(f"📅 Prayer Times")
        st.markdown(f"<div class='prayer-card'>🌅 <b>Fajr (Suhoor Ends):</b> {times['Fajr']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='prayer-card'>☀️ <b>Dhuhr:</b> {times['Dhuhr']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='prayer-card'>🌥️ <b>Asr:</b> {times['Asr']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='prayer-card' style='background-color:#fff3e0;'>🌙 <b>Maghrib (Iftar):</b> {times['Maghrib']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='prayer-card'>🌌 <b>Isha:</b> {times['Isha']}</div>", unsafe_allow_html=True)
        
        st.warning(f"🔔 **Daily Suhoor
