import streamlit as st
import requests
import random
import pandas as pd
from datetime import datetime

# --- 1. APP CONFIGURATION ---
st.set_page_config(page_title="Islam & Ramadan Hub 2026", page_icon="🌙", layout="wide")

# --- 2. USER SETTINGS (GOOGLE SHEETS) ---
# Replace with your actual Google Sheet ID
SHEET_ID = "YOUR_SHEET_ID_HERE" 
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

# --- 3. CUSTOM CSS STYLING ---
st.markdown("""
    <style>
    .arabic-text { font-family: 'Amiri', serif; font-size: 36px; direction: rtl; text-align: right; color: #1B5E20; line-height: 2.2; margin-bottom: 10px;}
    .translation-text { font-size: 18px; color: #444; margin-bottom: 25px; border-left: 3px solid #4CAF50; padding-left: 15px; }
    .card { background-color: #fdfdfd; padding: 20px; border-radius: 10px; border-left: 5px solid #00796B; margin-bottom: 20px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    .prayer-card { background-color: #e8f5e9; padding: 12px; border-radius: 8px; border-right: 5px solid #2E7D32; margin-bottom: 8px; font-size: 16px;}
    </style>
    """, unsafe_allow_html=True)

# --- 4. HELPER FUNCTIONS ---
@st.cache_data(ttl=3600)
def get_prayer_times(city):
    try:
        res = requests.get(f"https://api.aladhan.com/v1/timingsByCity?city={city}&country=Sierra%20Leone&method=2").json()
        return res['data']['timings']
    except: return None

def load_progress():
    try: return pd.read_csv(SHEET_URL)
    except: return pd.DataFrame(columns=["Surah", "Date"])

# --- 5. SIDEBAR: HUB, PRAYER TIMES & IFTTT ALERTS ---
with st.sidebar:
    st.title("🕌 My Deen Center")
    city = st.text_input("Current City", "Kabala")
    times = get_prayer_times(city)
    
    if times:
        st.subheader(f"📅 Prayer Times ({city})")
        st.markdown(f"<div class='prayer-card'>🌅 <b>Fajr (Suhoor Ends):</b> {times['Fajr']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='prayer-card'>☀️ <b>Dhuhr:</b> {times['Dhuhr']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='prayer-card'>🌥️ <b>Asr:</b> {times['Asr']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='prayer-card' style='background-color:#fff3e0;'>🌙 <b>Maghrib (Iftar):</b> {times['Maghrib']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='prayer-card'>🌌 <b>Isha:</b> {times['Isha']}</div>", unsafe_allow_html=True)
        
        st.warning(f"🔔 **Daily Goal Notification:**\nSet your phone's IFTTT alarm to **{times['Fajr']}** to wake up for Suhoor and read your daily verse!")

    st.divider()
    st.subheader("📊 My Quran Tracker")
    st.dataframe(load_progress(), hide_index=True)
    st.link_button("📝 Save Progress to Sheet", f"https://docs.google.com/spreadsheets/d/{SHEET_ID}")
    
    st.divider()
    st.subheader("📿 Digital Tasbeeh")
    if 'tasbeeh' not in st.session_state:
        st.session_state.tasbeeh = 0
    if st.button("SubhanAllah (+1)"):
        st.session_state.tasbeeh += 1
    st.write(f"**Count: {st.session_state.tasbeeh}**")
    if st.button("Reset"):
        st.session_state.tasbeeh = 0

# --- 6. MAIN APP TABS ---
tabs = st.tabs([
    "📖 Quran & Audio", 
    "📜 History & Sunnah", 
    "🌙 Ramadan Complete Guide", 
    "🥗 Recipes & Zakat", 
    "🧠 Vocab Builder", 
    "✨ Daily Verse"
])

# --- TAB 1: QURAN ---
with tabs[0]:
    st.header("The Holy Quran & Audio Recitation")
    s_num = st.number_input("Select Surah (1-114):", 1, 114, 1)
    if st.button("Load Surah"):
        with st.spinner("Loading verses and audio..."):
            try:
                res = requests.get(f"https://api.alquran.cloud/v1/surah/{s_num}/editions/quran-uthmani,en.sahih").json()
                st.subheader(f"{res['data'][0]['name']} - {res['data'][0]['englishName']}")
                
                # Full Surah Audio Link
                st.audio(f"https://cdn.islamic.network/quran/audio-surah/128/ar.alafasy/{s_num}.mp3")
                
                for ar, en in zip(res['data'][0]['ayahs'], res['data'][1]['ayahs']):
                    st.markdown(f"<p class='arabic-text'>{ar['text']}</p>", unsafe_allow_html=True)
                    st.markdown(f"<div class='translation-text'>{en['text']}</div>", unsafe_allow_html=True)
            except:
                st.error("Network error. Please check your internet connection.")

# --- TAB 2: HISTORY & SUNNAH ---
with tabs[1]:
    st.header("📜 The Complete History of Islam")
    st.write("Islam is a monotheistic faith revealed to the Prophet Muhammad (Peace Be Upon Him) in the 7th century. It emphasizes the absolute oneness of God (Tawhid) and guides Muslims through the Quran and the Sunnah (teachings of the Prophet).")
    
    st.markdown("""<div class='card'><h3>From Mecca to the Golden Age</h3>
    <ul>
        <li><b>610 CE:</b> The first revelation in the Cave of Hira.</li>
        <li><b>622 CE (The Hijrah):</b> Migration to Medina, marking year 1 of the Islamic calendar.</li>
        <li><b>The Golden Age:</b> From the 8th to 14th century, the Islamic empire became the world's center for science, medicine, algebra, and astronomy, profoundly influencing the modern world.</li>
    </ul></div>""", unsafe_allow_html=True)
    
    st.header("📖 Sunnah of the Prophet (Hadith)")
    st.info("Abu Huraira reported: The Messenger of Allah, peace and blessings be upon him, said, **'When the month of Ramadan begins, the gates of the heaven are opened, the gates of Hellfire are closed, and the devils are chained.'** (Sahih al-Bukhari)")
    st.info("Anas ibn Malik reported: The Messenger of Allah said, **'Take the Suhoor meal, for there is blessing in it.'** (Sahih al-Bukhari)")

# --- TAB 3: RAMADAN GUIDE & MOON TRACKER ---
with tabs[2]:
    st.header("🌙 Everything About Ramadan")
    st.write("Ramadan is the 9th month of the Islamic lunar calendar. It is a profound period of physical fasting, intense spiritual reflection, charity, and connection with the Quran.")
    
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("""<div class='card'><h3>The Rules and Spirit of Fasting (Sawm)</h3>
        <ul>
            <li><b>Imsak (Restraint):</b> Complete abstention from food, drink (even water), and intimacy from dawn to sunset.</li>
            <li><b>Niyyah (Intention):</b> Must be made internally before Fajr.</li>
            <li><b>Taqwa (Consciousness):</b> Fasting the stomach is easy; fasting the tongue from gossip, the eyes from unlawful sights, and the heart from anger is the true goal.</li>
            <li><b>Exemptions:</b> The sick, elderly, travelers, and pregnant/nursing women are exempt and can make it up later or pay Fidyah.</li>
        </ul></div>""", unsafe_allow_html=True)
    
    st.divider()
    st.header("🌖 Ramadan Progress Tracker")
    st.write("Visually track your journey toward Eid al-Fitr. Today is **Day 4**.")
    
    # Hardcoded to Day 4 as requested
    day = 4
    st.progress(day / 30)
    st.write(f"You have completed **{int((day/30)*100)}%** of the month. You are currently in the **First 10 Days: The Days of Mercy (Rahmah)**.")

# --- TAB 4: RECIPES & ZAKAT ---
with tabs[3]:
    st.header("💰 Zakat Calculator")
    st.write("Zakat (2.5% of accumulated wealth) purifies your income and supports the needy.")
    assets = st.number_input("Enter Total Accumulated Wealth (Cash/Gold equivalent):", min_value=0.0)
    if assets > 0:
        st.success(f"**Your Zakat Due:** {assets * 0.025:,.2f}")

    st.divider()
    st.header("🥗 Ramadan Nutrition Guide")
    col_a, col_b = st.columns(2)
    with col_a:
        st.info("🌅 **Suhoor Recipe (Slow-Burn Energy):**\n* 1 Cup Oatmeal cooked with milk/water.\n* Topped with sliced bananas, dates, and a spoon of peanut butter.\n* Drink 2-3 large glasses of water slowly. \n* *Why?* Complex carbs release energy over 12 hours.")
    with col_b:
        st.success("🌙 **Iftar Recipe (Rapid Recovery):**\n* Break fast with 3 Dates and a glass of water.\n* Warm Lentil or Chicken Soup.\n* Avoid heavy fried foods immediately to prevent lethargy for Tarawih prayers.")

# --- TAB 5: VOCABULARY BUILDER (WITH AUDIO) ---
with tabs[4]:
    st.header("🧠 Quranic Vocabulary Builder")
    st.write("Listen and learn the most frequently used words in the Quran.")
    
    vocab = [
        {"ar": "صَبْر", "en": "Sabr (Patience/Perseverance)", "url": "https://everyayah.com/data/Arabic_Words/002153.mp3"},
        {"ar": "رَحْمَة", "en": "Rahma (Mercy)", "url": "https://everyayah.com/data/Arabic_Words/001001.mp3"},
        {"ar": "عَلِيم", "en": "Aleem (All-Knowing)", "url": "https://everyayah.com/data/Arabic_Words/002032.mp3"},
        {"ar": "أَرْض", "en": "Ardh (Earth)", "url": "https://everyayah.com/data/Arabic_Words/002011.mp3"}
    ]
    
    for v in vocab:
        c1, c2, c3 = st.columns([1, 2, 2])
        c1.markdown(f"<span class='arabic-text' style='font-size: 28px;'>{v['ar']}</span>", unsafe_allow_html=True)
        c2.write(f"**{v['en']}**")
        with c3:
            st.audio(v['url'])

# --- TAB 6: DAILY VERSE ---
with tabs[5]:
    st.header("✨ Daily Surprise Verse")
    st.write("Start your day with a random reflection from the Quran.")
    if st.button("Generate My Daily Verse"):
        with st.spinner("Fetching from the heavens..."):
            try:
                r = random.randint(1, 6236)
                v = requests.get(f"https://api.alquran.cloud/v1/ayah/{r}/editions/quran-uthmani,en.sahih").json()
                st.markdown(f"<p class='arabic-text'>{v['data'][0]['text']}</p>", unsafe_allow_html=True)
                st.success(f"**Translation:** {v['data'][1]['text']}")
                st.caption(f"Surah {v['data'][0]['surah']['englishName']}, Ayah {v['data'][0]['numberInSurah']}")
            except:
                st.error("Error fetching verse. Please try again.")
