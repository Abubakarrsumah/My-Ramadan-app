import streamlit as st
import requests
import random
import json
import os
from datetime import datetime

# --- CONFIGURATION & STYLING ---
st.set_page_config(page_title="Ramadan Coach 2026", page_icon="🌙", layout="wide")

st.markdown("""
    <style>
    .arabic-text { font-family: 'Amiri', serif; font-size: 32px; direction: rtl; text-align: right; color: #1B5E20; line-height: 2; padding: 10px; }
    .translation-text { font-size: 18px; color: #444; margin-bottom: 20px; }
    .prayer-card { background-color: #e8f5e9; padding: 10px; border-radius: 8px; margin-bottom: 5px; border-right: 5px solid #2E7D32; }
    .vocab-card { border: 1px solid #ddd; border-radius: 10px; padding: 15px; text-align: center; background-color: #fafafa; }
    </style>
    """, unsafe_allow_html=True)

# --- PROGRESS TRACKER LOGIC ---
PROGRESS_FILE = "quran_progress.json"

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_progress(surah_name):
    progress = load_progress()
    progress[surah_name] = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f)

# --- SIDEBAR: PRAYERS & TRACKER ---
with st.sidebar:
    st.title("📍 Your Ramadan Hub")
    city = st.text_input("City", "Kabala")
    country = st.text_input("Country", "Sierra Leone")
    
    try:
        p_res = requests.get(f"https://api.aladhan.com/v1/timingsByCity?city={city}&country={country}&method=2").json()
        t = p_res['data']['timings']
        st.subheader("Prayer Times")
        st.markdown(f"<div class='prayer-card'><b>Fajr (Suhoor Ends):</b> {t['Fajr']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='prayer-card'><b>Dhuhr:</b> {t['Dhuhr']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='prayer-card'><b>Asr:</b> {t['Asr']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='prayer-card' style='background-color:#ffebee;'><b>Maghrib (Iftar):</b> {t['Maghrib']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='prayer-card'><b>Isha:</b> {t['Isha']}</div>", unsafe_allow_html=True)
    except:
        st.warning("Please check city/country spelling.")

    st.divider()
    st.subheader("📊 Reading Progress")
    history = load_progress()
    if history:
        for s, d in history.items():
            st.caption(f"✅ {s} (Completed: {d})")
    else:
        st.write("No Surahs finished yet. Keep going!")

# --- MAIN INTERFACE ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📖 Quran", "🧠 Vocab", "💰 Zakat", "🥗 Recipes", "✨ Daily"])

with tab1:
    st.header("Whole Quran Explorer")
    surah_num = st.number_input("Select Surah (1-114):", 1, 114, 1)
    
    if st.button("Load Surah & Audio"):
        with st.spinner("Fetching Ayahs..."):
            # Fetch Arabic and English editions
            res = requests.get(f"https://api.alquran.cloud/v1/surah/{surah_num}/editions/quran-uthmani,en.sahih").json()
            ar_data = res['data'][0]
            en_data = res['data'][1]
            
            st.subheader(f"{ar_data['name']} - {ar_data['englishName']}")
            
            # Audio Translation (Full Surah Recitation)
            audio_url = f"https://cdn.islamic.network/quran/audio-surah/128/ar.alafasy/{surah_num}.mp3"
            st.write("🔊 **Recitation by Mishary Rashid Alafasy:**")
            st.audio(audio_url)
            
            if st.button("Mark Surah as Finished"):
                save_progress(ar_data['englishName'])
                st.success(f"Saved {ar_data['englishName']} to your progress!")

            for ar_v, en_v in zip(ar_data['ayahs'], en_data['ayahs']):
                st.markdown(f"<p class='arabic-text'>{ar_v['text']}</p>", unsafe_allow_html=True)
                st.markdown(f"<p class='translation-text'>{en_v['text']}</p>", unsafe_allow_html=True)
                st.divider()

with tab2:
    st.header("🧠 High-Frequency Quranic Vocabulary")
    vocabs = [
        {"ar": "اللّه", "en": "Allah", "note": "2699 occurrences"},
        {"ar": "رَبّ", "en": "Lord", "note": "975 occurrences"},
        {"ar": "قُل", "en": "Say", "note": "332 occurrences"},
        {"ar": "أَرْض", "en": "Earth", "note": "461 occurrences"},
        {"ar": "عَلِيم", "en": "All-Knowing", "note": "158 occurrences"},
        {"ar": "صَبْر", "en": "Patience", "note": "103 occurrences"}
    ]
    cols = st.columns(2)
    for idx, item in enumerate(vocabs):
        with cols[idx % 2]:
            st.markdown(f"""<div class='vocab-card'><h2>{item['ar']}</h2><h3>{item['en']}</h3><p>{item['note']}</p></div>""", unsafe_allow_html=True)

with tab3:
    st.header("💰 Zakat Calculator (2026)")
    total_assets = st.number_input("Enter Total Wealth (Gold, Cash, etc):", min_value=0.0)
    if total_assets > 0:
        zakat_due = total_assets * 0.025
        st.balloons()
        st.success(f"Your Zakat obligation is: **{zakat_due:,.2f}**")

with tab4:
    st.header("🥗 Ramadan Nutrition")
    col_suhoor, col_iftar = st.columns(2)
    with col_suhoor:
        st.info("🌅 **Suhoor (Energy)**")
        st.write("- **Oatmeal/Porridge:** Slow release energy.")
        st.write("- **Healthy Fats:** Avocado or Peanut Butter.")
        st.write("- **Hydration:** 2 glasses of water.")
    with col_iftar:
        st.success("🌙 **Iftar (Recovery)**")
        st.write("- **Dates:** Natural sugars for instant energy.")
        st.write("- **Soup:** Rehydrates gently.")
        st.write("- **Protein:** Chicken or Beans.")

with tab5:
    st.header("✨ Verse of the Day")
    if st.button("Surprise Me"):
        rand = random.randint(1, 6236)
        v = requests.get(f"https://api.alquran.cloud/v1/ayah/{rand}/editions/quran-uthmani,en.sahih").json()
        st.markdown(f"<p class='arabic-text'>{v['data'][0]['text']}</p>", unsafe_allow_html=True)
        st.info(f"**Meaning:** {v['data'][1]['text']}")
        st.caption(f"Surah {v['data'][0]['surah']['englishName']}, Ayah {v['data'][0]['numberInSurah']}")
