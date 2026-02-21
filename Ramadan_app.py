import streamlit as st
import requests
import random
import pandas as pd
from datetime import datetime

# --- 1. APP CONFIGURATION ---
st.set_page_config(page_title="Islam & Ramadan Hub 2026", page_icon="🌙", layout="wide")

# --- 2. USER SETTINGS (GOOGLE SHEETS) ---
SHEET_ID = "YOUR_SHEET_ID_HERE" 
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

# --- 3. CUSTOM STYLING ---
st.markdown("""
    <style>
    .arabic-text { font-family: 'Amiri', serif; font-size: 34px; direction: rtl; text-align: right; color: #1B5E20; line-height: 2.2; }
    .translation-text { font-size: 18px; color: #444; margin-bottom: 25px; border-left: 3px solid #eee; padding-left: 15px; }
    .card { background-color: #fdfdfd; padding: 20px; border-radius: 10px; border-left: 5px solid #00796B; margin-bottom: 20px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    .prayer-card { background-color: #e8f5e9; padding: 12px; border-radius: 8px; border-right: 5px solid #2E7D32; margin-bottom: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. HELPER FUNCTIONS ---
@st.cache_data(ttl=3600)
def get_prayer_times(city):
    try:
        # Defaults to Sierra Leone based on your location
        res = requests.get(f"https://api.aladhan.com/v1/timingsByCity?city={city}&country=Sierra%20Leone&method=2").json()
        return res['data']['timings']
    except: return None

def load_progress():
    try: return pd.read_csv(SHEET_URL)
    except: return pd.DataFrame(columns=["Surah", "Date"])

# --- 5. SIDEBAR: HUB & IFTTT ALERTS ---
with st.sidebar:
    st.title("🕌 My Deen Center")
    city = st.text_input("City", "Kabala")
    times = get_prayer_times(city)
    
    if times:
        st.subheader(f"📅 Prayer Times ({city})")
        st.markdown(f"<div class='prayer-card'>🌅 <b>Fajr (Suhoor Ends):</b> {times['Fajr']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='prayer-card'>☀️ <b>Dhuhr:</b> {times['Dhuhr']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='prayer-card'>🌥️ <b>Asr:</b> {times['Asr']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='prayer-card' style='background-color:#fff3e0;'>🌙 <b>Maghrib (Iftar):</b> {times['Maghrib']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='prayer-card'>🌌 <b>Isha:</b> {times['Isha']}</div>", unsafe_allow_html=True)
        
        st.warning(f"🔔 **Daily Goal & IFTTT Alert:** Set your phone alarm to **{times['Fajr']}** to wake up for Suhoor and read your daily verse!")

    st.divider()
    st.subheader("📊 Permanent Tracker")
    st.dataframe(load_progress(), hide_index=True)
    st.link_button("📝 Save to Google Sheet", f"https://docs.google.com/spreadsheets/d/{SHEET_ID}")

# --- 6. MAIN APP TABS ---
tabs = st.tabs([
    "📖 Quran & Audio", 
    "📜 History & Sunnah", 
    "🌙 Ramadan Guide", 
    "🥗 Recipes & Zakat", 
    "🧠 Vocab Builder", 
    "✨ Daily & Moon"
])

# --- TAB 1: QURAN ---
with tabs[0]:
    st.header("Whole Quran & Recitation")
    s_num = st.number_input("Select Surah (1-114):", 1, 114, 1)
    if st.button("Load Surah"):
        with st.spinner("Loading verses and audio..."):
            try:
                res = requests.get(f"https://api.alquran.cloud/v1/surah/{s_num}/editions/quran-uthmani,en.sahih").json()
                st.subheader(f"{res['data'][0]['name']} - {res['data'][0]['englishName']}")
                # Full Surah Audio
                st.audio(f"https://cdn.islamic.network/quran/audio-surah/128/ar.alafasy/{s_num}.mp3")
                
                for ar, en in zip(res['data'][0]['ayahs'], res['data'][1]['ayahs']):
                    st.markdown(f"<p class='arabic-text'>{ar['text']}</p>", unsafe_allow_html=True)
                    st.markdown(f"<div class='translation-text'>{en['text']}</div>", unsafe_allow_html=True)
            except:
                st.error("Could not connect to the Quran API. Check your internet.")

# --- TAB 2: HISTORY & SUNNAH ---
with tabs[1]:
    st.header("📜 The Complete History of Islam")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""<div class='card'><h3>The Origins (7th Century)</h3>
        Islam was revealed to the <b>Prophet Muhammad (PBUH)</b> in 610 CE in the Cave of Hira, near Mecca. Over 23 years, the Quran was revealed through the Angel Jibril (Gabriel). It unified the Arabian Peninsula under the worship of One God (Tawhid).</div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""<div class='card'><h3>The Golden Age</h3>
        Following the Prophet's passing, Islam spread rapidly. During the Abbasid Caliphate (8th-13th century), Islamic scholars preserved ancient knowledge and made massive leaps in algebra, medicine, astronomy, and architecture.</div>""", unsafe_allow_html=True)

    st.divider()
    st.header("📖 Sunnah of the Prophet (Hadith)")
    hadiths = [
        "**On Fasting:** 'Whoever fasts Ramadan out of faith and in the hope of reward, his previous sins will be forgiven.' (Sahih Al-Bukhari)",
        "**On Character:** 'The best among you are those who have the best manners and character.' (Sahih Al-Bukhari)",
        "**On Charity:** 'Charity does not decrease wealth.' (Sahih Muslim)"
    ]
    for h in hadiths:
        st.info(h)

# --- TAB 3: RAMADAN GUIDE ---
with tabs[2]:
    st.header("🌙 Everything About Ramadan")
    st.write("Ramadan is the 9th month of the Islamic lunar calendar. It is a time for physical purification, intense worship, and community.")
    
    st.markdown("""<div class='card'><h3>The Rules of Fasting (Sawm)</h3>
    <ul>
        <li><b>Niyyah (Intention):</b> You must silently intend to fast before dawn.</li>
        <li><b>Imsak:</b> Absolute restriction from food, drink (including water), and intimacy from Fajr (dawn) to Maghrib (sunset).</li>
        <li><b>Behavior:</b> Arguing, lying, and swearing diminish the spiritual reward of the fast.</li>
    </ul>
    </div>""", unsafe_allow_html=True)
    
    st.markdown("""<div class='card'><h3>Exemptions (Who doesn't have to fast)</h3>
    Children, the elderly, those who are chronically ill, pregnant/nursing women, women on their menstrual cycle, and travelers. Missed fasts are made up later, or compensated via <i>Fidyah</i> (feeding the poor).</div>""", unsafe_allow_html=True)

# --- TAB 4: RECIPES & ZAKAT ---
with tabs[3]:
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("🥗 Ramadan Recipes (Kabala Style)")
        st.info("🌅 **Suhoor (Pre-Dawn):**\n* Oatmeal with bananas and honey.\n* Boiled eggs for protein.\n* At least 2 glasses of water.")
        st.success("🌙 **Iftar (Sunset):**\n* 3 Dates and water (Sunnah).\n* Light soup or broth to warm the stomach.\n* Grilled chicken or fish with rice.")
    with col_b:
        st.subheader("💰 Zakat Calculator")
        st.write("Zakat is 2.5% of excess wealth held for a full lunar year.")
        assets = st.number_input("Total Savings/Gold Value:", min_value=0.0)
        if assets > 0:
            st.success(f"**Your Zakat Due:** {assets * 0.025:,.2f}")

# --- TAB 5: VOCABULARY BUILDER ---
with tabs[4]:
    st.header("🧠 Quranic Vocabulary & Audio")
    st.write("Learn these high-frequency words to understand the Quran faster.")
    
    vocab = [
        {"ar": "صَبْر", "en": "Sabr (Patience)", "url": "https://everyayah.com/data/Arabic_Words/002153.mp3"},
        {"ar": "رَحْمَة", "en": "Rahma (Mercy)", "url": "https://everyayah.com/data/Arabic_Words/001001.mp3"},
        {"ar": "عَلِيم", "en": "Aleem (All-Knowing)", "url": "https://everyayah.com/data/Arabic_Words/002032.mp3"},
        {"ar": "أَرْض", "en": "Ardh (Earth)", "url": "https://everyayah.com/data/Arabic_Words/002011.mp3"}
    ]
    
    for v in vocab:
        c1, c2, c3 = st.columns([1, 2, 2])
        c1.subheader(v['ar'])
        c2.write(f"**{v['en']}**")
        with c3:
            st.audio(v['url'])

# --- TAB 6: DAILY VERSE & MOON PHASE ---
with tabs[5]:
    st.header("✨ Daily Surprise Verse")
    if st.button("Get Random Ayah"):
        try:
            r = random.randint(1, 6236)
            v = requests.get(f"https://api.alquran.cloud/v1/ayah/{r}/editions/quran-uthmani,en.sahih").json()
            st.markdown(f"<p class='arabic-text'>{v['data'][0]['text']}</p>", unsafe_allow_html=True)
            st.info(f"**Meaning:** {v['data'][1]['text']}")
            st.caption(f"Surah {v['data'][0]['surah']['englishName']}, Ayah {v['data'][0]['numberInSurah']}")
        except:
            st.error("Error fetching verse. Please try again.")

    st.divider()
    st.header("🌙 Ramadan Moon & Progress Tracker")
    st.write("Track the phases of the moon to see how close you are to Eid al-Fitr!")
    
    day = st.slider("Current Day of Ramadan", 1, 30, 1)
    st.progress(day / 30)
    
    if day < 10:
        st.write("🌒 **First 10 Days:** The Days of Mercy (Rahmah).")
    elif day < 20:
        st.write("🌓 **Middle 10 Days:** The Days of Forgiveness (Maghfirah).")
    else:
        st.write("🌕 **Last 10 Days:** Seeking Refuge from the Fire, and searching for Laylat al-Qadr!")
