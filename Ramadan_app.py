import streamlit as st
import requests
import random
import pandas as pd
from datetime import datetime

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Ramadan Coach 2026", page_icon="🌙", layout="wide")

# --- USER SETTINGS: GOOGLE SHEETS ---
# Replace with your actual Sheet ID from the URL
SHEET_ID = "YOUR_GOOGLE_SHEET_ID_HERE" 
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

# --- CUSTOM STYLING ---
st.markdown("""
    <style>
    .arabic-text { font-family: 'Amiri', serif; font-size: 34px; direction: rtl; text-align: right; color: #1B5E20; line-height: 2.2; }
    .translation-text { font-size: 18px; color: #444; margin-bottom: 25px; border-left: 3px solid #eee; padding-left: 15px; }
    .prayer-card { background-color: #f1f8e9; padding: 15px; border-radius: 10px; border-right: 6px solid #2E7D32; margin-bottom: 10px; }
    .vocab-card { border: 1px solid #e0e0e0; border-radius: 12px; padding: 15px; background-color: #ffffff; text-align: center; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCTIONS ---
def get_prayer_times(city, country):
    try:
        url = f"https://api.aladhan.com/v1/timingsByCity?city={city}&country={country}&method=2"
        res = requests.get(url).json()
        return res['data']['timings']
    except:
        return None

def load_google_progress():
    try:
        return pd.read_csv(SHEET_URL)
    except:
        return pd.DataFrame(columns=["Surah", "Date"])

# --- SIDEBAR: KABALA HUB ---
with st.sidebar:
    st.title("🕌 My Ramadan Hub")
    city = st.text_input("Current City", "Kabala")
    
    times = get_prayer_times(city, "Sierra Leone")
    if times:
        st.subheader(f"📅 Prayer Times ({city})")
        st.markdown(f"<div class='prayer-card'>🚩 <b>Fajr (Suhoor Ends):</b> {times['Fajr']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='prayer-card'>☀️ <b>Dhuhr:</b> {times['Dhuhr']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='prayer-card'>🌥️ <b>Asr:</b> {times['Asr']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='prayer-card' style='background-color:#fff3e0;'>🌙 <b>Maghrib (Iftar):</b> {times['Maghrib']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='prayer-card'>🌌 <b>Isha:</b> {times['Isha']}</div>", unsafe_allow_html=True)
        
        st.info(f"🔔 **Notification:** Set your IFTTT alarm to {times['Fajr']} minus 30 minutes!")
    
    st.divider()
    st.subheader("📊 Permanent Progress")
    df_prog = load_google_progress()
    st.dataframe(df_prog, hide_index=True)
    st.link_button("📝 Open Tracking Sheet", f"https://docs.google.com/spreadsheets/d/{SHEET_ID}")

# --- MAIN APP INTERFACE ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📖 Quran", "🧠 Vocab", "💰 Zakat", "🥗 Food", "✨ Daily", "🌙 Moon"])

with tab1:
    st.header("Whole Quran & Audio Translation")
    s_num = st.number_input("Select Surah (1-114):", 1, 114, 1)
    
    if st.button("Load Surah"):
        with st.spinner("Connecting to API..."):
            res = requests.get(f"https://api.alquran.cloud/v1/surah/{s_num}/editions/quran-uthmani,en.sahih").json()
            ar_data = res['data'][0]
            en_data = res['data'][1]
            
            st.subheader(f"{ar_data['name']} - {ar_data['englishName']}")
            st.audio(f"https://cdn.islamic.network/quran/audio-surah/128/ar.alafasy/{s_num}.mp3")
            
            for ar, en in zip(ar_data['ayahs'], en_data['ayahs']):
                st.markdown(f"<p class='arabic-text'>{ar['text']}</p>", unsafe_allow_html=True)
                st.markdown(f"<div class='translation-text'>{en['text']}</div>", unsafe_allow_html=True)

with tab2:
    st.header("🧠 High-Frequency Quranic Vocabulary")
    st.write("These words appear thousands of times. Learn these to understand 50% of the Quran!")
    vocabs = [
        {"ar": "اللّه", "en": "Allah", "frq": "2699x"},
        {"ar": "رَبّ", "en": "Lord/Sustainer", "frq": "975x"},
        {"ar": "قُل", "en": "Say", "frq": "332x"},
        {"ar": "أَرْض", "en": "Earth", "frq": "461x"},
        {"ar": "عَلِيم", "en": "All-Knowing", "frq": "158x"},
        {"ar": "يَوْم", "en": "Day", "frq": "405x"}
    ]
    c1, c2 = st.columns(2)
    for idx, item in enumerate(vocabs):
        with (c1 if idx % 2 == 0 else c2):
            st.markdown(f"<div class='vocab-card'><h2>{item['ar']}</h2><b>{item['en']}</b><br><small>{item['frq']}</small></div>", unsafe_allow_html=True)

with tab3:
    st.header("💰 Zakat Calculator")
    assets = st.number_input("Total Savings/Wealth:", min_value=0.0)
    if assets > 0:
        st.success(f"Zakat Due (2.5%): **{assets * 0.025:,.2f}**")
        st.caption("Note: Zakat is only due if wealth is above the Nisab threshold.")

with tab4:
    st.header("🥗 Ramadan Nutrition Guide")
    col_suhoor, col_iftar = st.columns(2)
    with col_suhoor:
        st.info("🌅 **Suhoor (The Fuel)**")
        st.write("1. **Slow Carbs:** Oats, Brown Rice, or Whole Wheat Bread.")
        st.write("2. **Protein:** Eggs or Beans.")
        st.write("3. **Hydration:** Drink 1L water slowly.")
    with col_iftar:
        st.success("🌙 **Iftar (The Recovery)**")
        st.write("1. **Dates:** 3 pieces to restore blood sugar.")
        st.write("2. **Soup:** Warm liquid to wake up the stomach.")
        st.write("3. **Water:** Avoid sugary drinks immediately.")

with tab5:
    st.header("✨ Verse of the Day")
    if st.button("Generate Surprise Verse"):
        r_num = random.randint(1, 6236)
        v = requests.get(f"https://api.alquran.cloud/v1/ayah/{r_num}/editions/quran-uthmani,en.sahih").json()
        st.markdown(f"<p class='arabic-text'>{v['data'][0]['text']}</p>", unsafe_allow_html=True)
        st.info(f"**Meaning:** {v['data'][1]['text']}")
        st.caption(f"Source: Surah {v['data'][0]['surah']['englishName']}, Ayah {v['data'][0]['numberInSurah']}")

with tab6:
    st.header("🌙 Moon Phase Tracker")
    st.write("Keep track of the month's progress (Ramadan 2026).")
    # A simple progress bar to visualize the 29-30 days
    day_of_ramadan = st.slider("Current Day of Ramadan", 1, 30, 1)
    st.progress(day_of_ramadan / 30)
    st.write(f"You have completed **{int((day_of_ramadan/30)*100)}%** of the Holy Month!")
