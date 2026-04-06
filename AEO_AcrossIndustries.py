# -*- coding: utf-8 -*-
"""
AEO Intelligence Hub v5 — India Edition
Flow: Google Trends keywords → each engine generates questions per keyword (ranked)
      → answers streamed → brand mentions extracted (Claude, context-aware)
Tabs: Keywords | Questions | Answers | Brand Mentions | Analytics | Week-on-Week
"""

import streamlit as st
import anthropic
import json, time, math, re, os, requests
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="AEO Intelligence Hub · India",
                   page_icon="🔍", layout="wide",
                   initial_sidebar_state="expanded")

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600&display=swap');

:root {
  --bg: #f0f2ff;
  --surface: #ffffff;
  --surface2: #f7f8ff;
  --surface3: #eef0ff;
  --text: #1a1a2e;
  --text2: #3d3d6b;
  --muted: #8888bb;
  --border: rgba(99,88,255,.15);
  --purple: #6358ff;
  --violet: #8b5cf6;
  --teal: #0ea5e9;
  --pink: #ec4899;
  --orange: #f97316;
  --green: #10b981;
  --yellow: #f59e0b;
  --grad1: linear-gradient(135deg,#6358ff,#a855f7);
  --grad2: linear-gradient(135deg,#0ea5e9,#10b981);
  --grad3: linear-gradient(135deg,#ec4899,#f97316);
}

html,body,[class*="css"] {
  font-family: 'Plus Jakarta Sans', sans-serif;
  background: var(--bg);
  color: var(--text);
}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding-top:1.2rem;padding-bottom:2rem;max-width:1380px;}

/* ── Hero ─────────────────────────────────────────── */
.hero {
  background: linear-gradient(135deg,#6358ff 0%,#a855f7 45%,#ec4899 100%);
  border-radius:20px; padding:2rem 2.6rem; margin-bottom:1.4rem;
  position:relative; overflow:hidden; box-shadow:0 8px 32px rgba(99,88,255,.35);
}
.hero::before {
  content:''; position:absolute; top:-60px; right:-60px;
  width:280px; height:280px;
  background:radial-gradient(circle,rgba(255,255,255,.18) 0%,transparent 65%);
  border-radius:50%;
}
.hero::after {
  content:''; position:absolute; bottom:-40px; left:20%;
  width:200px; height:200px;
  background:radial-gradient(circle,rgba(255,255,255,.1) 0%,transparent 65%);
  border-radius:50%;
}
.hero h1 {
  font-family:'Syne',sans-serif; font-weight:800; font-size:2.1rem;
  margin:0 0 .3rem; color:#fff; text-shadow:0 2px 12px rgba(0,0,0,.2);
}
.hero p{color:rgba(255,255,255,.85);font-size:.95rem;margin:0;}
.badge {
  display:inline-block;
  background:rgba(255,255,255,.25); border:1px solid rgba(255,255,255,.4);
  color:#fff; padding:3px 12px; border-radius:20px; font-size:.68rem;
  font-weight:700; letter-spacing:.1em; text-transform:uppercase; margin-bottom:.7rem;
  backdrop-filter:blur(4px);
}

/* ── Sidebar ──────────────────────────────────────── */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg,#1e1b4b 0%,#2d1b69 100%) !important;
  border-right:none !important;
  box-shadow: 4px 0 24px rgba(99,88,255,.2);
}
section[data-testid="stSidebar"] .block-container{padding-top:1rem;}
section[data-testid="stSidebar"] * {color:#e2e8f0 !important;}
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea {
  background:rgba(255,255,255,.08) !important;
  border:1px solid rgba(255,255,255,.15) !important;
  color:#fff !important; border-radius:9px !important;
}
section[data-testid="stSidebar"] [data-baseweb="select"] > div {
  background:rgba(255,255,255,.08) !important;
  border:1px solid rgba(255,255,255,.15) !important;
  color:#fff !important; border-radius:9px !important;
}
.stl {
  font-family:'Syne',sans-serif; font-size:.62rem; font-weight:700;
  letter-spacing:.14em; text-transform:uppercase;
  color:rgba(167,139,250,1) !important; margin:.9rem 0 .35rem;
}

/* ── Stat cards ───────────────────────────────────── */
.stat-card {
  background:#fff; border-radius:16px; padding:1rem 1.1rem; text-align:center;
  box-shadow:0 2px 16px rgba(99,88,255,.1);
  border:1px solid rgba(99,88,255,.08);
  transition:transform .15s,box-shadow .15s;
}
.stat-card:hover{transform:translateY(-2px);box-shadow:0 6px 24px rgba(99,88,255,.18);}
.stat-num {
  font-family:'Syne',sans-serif; font-size:1.9rem; font-weight:800;
  background:var(--grad1); -webkit-background-clip:text; -webkit-text-fill-color:transparent;
}
.stat-label{color:var(--muted);font-size:.7rem;margin-top:2px;font-weight:600;}

/* ── Keyword cards ────────────────────────────────── */
.q-card {
  background:#fff; border:1.5px solid rgba(99,88,255,.12);
  border-radius:14px; padding:.9rem 1.1rem; margin-bottom:.5rem;
  box-shadow:0 2px 10px rgba(99,88,255,.06);
  transition:transform .12s, box-shadow .12s, border-color .12s;
}
.q-card:hover {
  transform:translateY(-2px); box-shadow:0 6px 20px rgba(99,88,255,.14);
  border-color:rgba(99,88,255,.35);
}
.q-num {
  font-family:'Syne',sans-serif; font-size:.58rem; font-weight:800;
  color:var(--purple); letter-spacing:.12em; text-transform:uppercase;
}
.q-text{font-size:.93rem;color:var(--text);line-height:1.55;margin:.25rem 0 .45rem;font-weight:500;}
.q-tags{display:flex;gap:5px;flex-wrap:wrap;align-items:center;}

/* ── Tags ─────────────────────────────────────────── */
.tag {
  background:rgba(99,88,255,.08); border:1.5px solid rgba(99,88,255,.2);
  color:var(--purple); padding:2px 9px; border-radius:20px;
  font-size:.67rem; font-weight:600;
}
.intent-informational{background:#ecfdf5;border-color:#6ee7b7;color:#059669;}
.intent-commercial   {background:#fdf2f8;border-color:#f9a8d4;color:#be185d;}
.intent-navigational {background:#f0f0ff;border-color:#c4b5fd;color:#7c3aed;}
.intent-transactional{background:#fffbeb;border-color:#fcd34d;color:#b45309;}
.kw-tag {
  background:linear-gradient(135deg,rgba(14,165,233,.12),rgba(16,185,129,.12));
  border:1.5px solid rgba(14,165,233,.3); color:#0284c7;
  padding:2px 9px; border-radius:20px; font-size:.67rem; font-weight:700;
}

/* ── Importance bar ───────────────────────────────── */
.imp-wrap{display:flex;align-items:center;gap:7px;margin-top:4px;}
.imp-bg {
  flex:1; height:5px; background:rgba(99,88,255,.08);
  border-radius:3px; overflow:hidden;
}
.imp-fill{height:100%;border-radius:3px;}

/* ── Trend bar ────────────────────────────────────── */
.trend-bar{height:4px;border-radius:2px;background:var(--grad1);margin-top:4px;}

/* ── Answer box ───────────────────────────────────── */
.ans-box {
  background:linear-gradient(135deg,#f8f7ff,#f0f2ff);
  border:1.5px solid rgba(99,88,255,.15); border-radius:12px;
  padding:.9rem 1.1rem; margin-top:.4rem;
  font-size:.9rem; line-height:1.75; color:var(--text2);
  box-shadow:inset 0 1px 4px rgba(99,88,255,.06);
}

/* ── Engine badge ─────────────────────────────────── */
.engine-badge {
  font-family:'Syne',sans-serif; font-size:.88rem; font-weight:800;
  padding:4px 14px; border-radius:20px; display:inline-block;
  box-shadow:0 2px 8px rgba(0,0,0,.12);
}

/* ── Analytics panels ─────────────────────────────── */
.ana {
  background:#fff; border:1.5px solid rgba(99,88,255,.1);
  border-radius:16px; padding:1.2rem 1.4rem; margin-bottom:1rem;
  box-shadow:0 2px 12px rgba(99,88,255,.07);
}
.ana-title {
  font-family:'Syne',sans-serif; font-size:.7rem; font-weight:800;
  letter-spacing:.1em; text-transform:uppercase;
  background:var(--grad1); -webkit-background-clip:text; -webkit-text-fill-color:transparent;
  margin-bottom:.8rem;
}
.bar-row{display:flex;align-items:center;gap:10px;margin-bottom:.45rem;}
.bar-lbl{font-size:.79rem;color:var(--text2);min-width:140px;max-width:170px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-weight:500;}
.bar-bg{flex:1;height:8px;background:rgba(99,88,255,.07);border-radius:4px;overflow:hidden;}
.bar-fill{height:100%;border-radius:4px;}
.bar-val{font-size:.74rem;color:var(--muted);min-width:30px;text-align:right;font-weight:600;}

/* ── WoW deltas ───────────────────────────────────── */
.wow-up  {color:#059669;font-weight:800;}
.wow-down{color:#be185d;font-weight:800;}
.wow-flat{color:var(--muted);font-weight:500;}

/* ── Streamlit widget overrides ───────────────────── */
div[data-testid="stTextInput"]>div>div>input,
div[data-testid="stTextArea"]>div>div>textarea {
  background:#fff !important; border:1.5px solid rgba(99,88,255,.2) !important;
  color:var(--text) !important; border-radius:10px !important;
  box-shadow:0 1px 4px rgba(99,88,255,.08) !important;
}
div[data-testid="stTextInput"]>div>div>input:focus,
div[data-testid="stTextArea"]>div>div>textarea:focus {
  border-color:var(--purple) !important;
  box-shadow:0 0 0 3px rgba(99,88,255,.15) !important;
}
div[data-testid="stSelectbox"]>div>div {
  background:#fff !important; border:1.5px solid rgba(99,88,255,.2) !important;
  border-radius:10px !important; color:var(--text) !important;
}
div.stButton>button {
  background:var(--grad1) !important; color:#fff !important;
  border:none !important; border-radius:10px !important;
  font-family:'Syne',sans-serif !important; font-weight:800 !important;
  font-size:.92rem !important; padding:.55rem 1.4rem !important;
  width:100% !important; box-shadow:0 4px 14px rgba(99,88,255,.4) !important;
  transition:transform .12s, box-shadow .12s !important;
}
div.stButton>button:hover {
  transform:translateY(-1px) !important;
  box-shadow:0 6px 20px rgba(99,88,255,.5) !important;
}
div[data-testid="stMultiSelect"]>div {
  background:#fff !important; border:1.5px solid rgba(99,88,255,.2) !important;
  border-radius:10px !important;
}
.stProgress>div>div>div>div {
  background:var(--grad1) !important; border-radius:4px !important;
}
div[data-testid="stDownloadButton"]>button {
  background:#fff !important; border:1.5px solid rgba(99,88,255,.25) !important;
  color:var(--purple) !important; border-radius:10px !important;
  font-weight:700 !important; box-shadow:0 2px 8px rgba(99,88,255,.1) !important;
}
div[data-testid="stExpander"] {
  background:#fff !important; border:1.5px solid rgba(99,88,255,.12) !important;
  border-radius:12px !important; box-shadow:0 2px 8px rgba(99,88,255,.06) !important;
}
div[data-testid="stTabs"] [data-baseweb="tab"] {
  font-family:'Syne',sans-serif; font-weight:700; color:var(--text2) !important;
}
div[data-testid="stTabs"] [aria-selected="true"] {
  color:var(--purple) !important;
  border-bottom:3px solid var(--purple) !important;
}
.stAlert {border-radius:12px !important;}
div[data-testid="stCheckbox"] span {color:var(--text) !important;}
div[data-testid="stSlider"] [data-testid="stSliderThumb"] {
  background:var(--grad1) !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
HISTORY_FILE = "aeo_history.json"

ENGINES = {
    "ChatGPT":    {"color":"#10a37f","icon":"🤖","accent":"rgba(16,163,127,", "model":"gpt-4o"},
    "Gemini":     {"color":"#4285f4","icon":"✨","accent":"rgba(66,133,244,",  "model":"gemini-2.5-flash"},
    "Perplexity": {"color":"#ff6b35","icon":"🔮","accent":"rgba(255,107,53,",  "model":"sonar"},
    "Claude":     {"color":"#cc785c","icon":"🧠","accent":"rgba(204,120,92,",  "model":"claude-sonnet-4-20250514"},
}
INTENT_TYPES  = ["Informational","Commercial","Navigational","Transactional"]
INTENT_COLORS = {"Informational":"#6bffd8","Commercial":"#ff9bc4","Navigational":"#a89dff","Transactional":"#ffd46b"}

INDUSTRIES = {
    "🛒 E-Commerce & Retail":         ["Amazon India","Flipkart","Myntra","Nykaa","Meesho","Snapdeal","Ajio","Tata Cliq"],
    "🏥 Healthcare & Wellness":        ["Apollo Hospitals","1mg","PharmEasy","Cult.fit","Practo","Lybrate","MediBuddy","Healthkart"],
    "🍔 Food & Beverage":              ["Zomato","Swiggy","Domino's India","McDonald's India","Starbucks India","Burger King India","KFC India","Haldiram's"],
    "💰 Fintech & Banking":            ["Paytm","PhonePe","CRED","Groww","Razorpay","BharatPe","Zerodha","Slice"],
    "🎓 EdTech & Education":           ["BYJU'S","Unacademy","upGrad","Vedantu","Khan Academy India","Simplilearn","Physics Wallah","Classplus"],
    "✈️ Travel & Hospitality":         ["MakeMyTrip","OYO","Airbnb India","Booking.com India","Cleartrip","EaseMyTrip","Treebo","FabHotels"],
    "📱 Consumer Electronics":         ["Samsung India","Apple India","OnePlus India","realme","boAt","Xiaomi India","Sony India","LG India"],
    "🚗 Automotive":                   ["Tata Motors","Maruti Suzuki","Ola Electric","Mahindra","Hyundai India","Honda India","Kia India","BYD India"],
    "🎮 Gaming & Entertainment":       ["Netflix India","Hotstar","Spotify India","Dream11","MPL","JioCinema","SonyLIV","ZEE5"],
    "🏠 Real Estate & PropTech":       ["MagicBricks","Housing.com","NoBroker","Square Yards","99acres","CommonFloor","Anarock","PropTiger"],
    "🚚 Logistics & Supply Chain":     ["Delhivery","Blue Dart","Ekart","XpressBees","Shadowfax","Dunzo","Porter","Shiprocket"],
    "🧴 Beauty & Personal Care":       ["Mamaearth","WOW Skin Science","Plum","Minimalist","Lakme","L'Oreal India","Biotique","Forest Essentials"],
    "👗 Fashion & Apparel":            ["H&M India","Zara India","Fabindia","Biba","W","Manyavar","Raymond","Peter England"],
    "🏋️ Sports & Fitness":             ["Decathlon India","Nike India","Adidas India","Puma India","Asics India","Reebok India","Skechers India","HRX"],
    "🏦 Insurance":                    ["LIC","HDFC Life","Policybazaar","Acko","Digit Insurance","Star Health","Bajaj Allianz","ICICI Prudential"],
    "💼 HR Tech & Recruitment":        ["Naukri","LinkedIn India","Indeed India","Internshala","Apna","Unstop","Hirist","Shine"],
    "🌾 AgriTech":                     ["DeHaat","AgroStar","Ninjacart","BigHaat","Fasal","CropIn","Gramophone","Jai Kisan"],
    "🔋 Clean Energy & EV":            ["Ola Electric","Ather Energy","Tata Power","Adani Green","ReNew Power","Greaves Electric","Hero Electric","Revolt"],
    "💊 Pharma & Biotech":             ["Sun Pharma","Cipla","Dr. Reddy's","Biocon","Zydus","Lupin","Aurobindo","Divi's Labs"],
    "📡 Telecom":                      ["Jio","Airtel","Vi","BSNL","ACT Fibernet","Hathway","You Broadband","GTPL"],
    "🏪 Grocery & FMCG":               ["BigBasket","Blinkit","JioMart","Zepto","DMart","Reliance Fresh","More","Spencer's"],
    "🧠 AI & SaaS":                    ["Zoho","Freshworks","Chargebee","Postman","BrowserStack","CleverTap","MoEngage","LeadSquared"],
    "🏨 Hotels & Resorts":             ["Taj Hotels","ITC Hotels","Oberoi Hotels","Lemon Tree","Marriott India","Hyatt India","Hilton India","Radisson India"],
    "📺 Media & Publishing":           ["Times of India","NDTV","India Today","The Hindu","Zee Media","TV18","ABP News","Republic TV"],
    "🛡️ Cybersecurity":                ["Quick Heal","K7 Security","Seqrite","Symantec India","McAfee India","Kaspersky India","Palo Alto India","CrowdStrike India"],
    "🎨 Design & Creative Tools":      ["Canva India","Adobe India","Figma","CorelDRAW","Sketch","InVision","Procreate","Affinity"],
    "📦 D2C Brands":                   ["boAt","Wakefit","Bombay Shaving Co.","mCaffeine","The Man Company","Beardo","Ustraa","Sleepy Owl"],
    "🔬 MedTech & Diagnostics":        ["Thyrocare","Dr. Lal PathLabs","Redcliffe Labs","Metropolis","Portea Medical","Niramai","Dozee","Fitterfly"],
    "🌍 Travel Tech":                  ["ixigo","Skyscanner India","Google Flights India","Kayak India","Hopper","Rome2Rio","Tripadvisor India","GetYourGuide India"],
    "🍺 Alcohol & Beverages":          ["United Spirits","AB InBev India","Radico Khaitan","Sula Wines","Bira 91","United Breweries","Globus Spirits","Tilaknagar"],
    "🐾 Pet Care":                     ["Heads Up For Tails","PetSutra","Supertails","PawsIndia","DCC Petcare","Pedigree India","Royal Canin India","Drools"],
    "📚 Books & Publishing":           ["Amazon Kindle India","Flipkart Books","Juggernaut","Pratham Books","Scholastic India","Penguin India","HarperCollins India","Westland"],
    "🧩 Kids & Toys":                  ["Funskool","Hasbro India","LEGO India","Fisher-Price India","Mattel India","Skillmatics","Toysrus India","Imagimake"],
    "🌿 Organic & Natural Food":       ["Organic India","24 Mantra Organic","Conscious Food","Praakritik","Happa Foods","Farmley","Happilo","True Elements"],
    "🏫 Coaching & Test Prep":         ["Allen Career Institute","FIITJEE","Aakash Institute","Embibe","Doubtnut","Toppr","Meritnation","Career Launcher"],
    "🔧 Home Services":                ["Urban Company","Housejoy","Sulekha","Mr. Right","NoBroker Home Services","Zimmber","FixMyPhone","Taskmo"],
    "💍 Jewellery & Accessories":      ["Tanishq","Kalyan Jewellers","Malabar Gold","CaratLane","BlueStone","Melorra","PNG Jewellers","Tribhovandas"],
    "🛋️ Furniture & Home Décor":       ["IKEA India","Pepperfry","Urban Ladder","@home","Nilkamal","Godrej Interio","FabFurnish","Wooden Street"],
    "✈️ Aviation":                     ["IndiGo","Air India","SpiceJet","Vistara","GoFirst","AirAsia India","Star Air","Alliance Air"],
    "🎤 Events & Entertainment":       ["BookMyShow","Insider.in","Paytm Insider","Zomato Live","District","Kyazoonga","Townscript","Explara"],
    "🧪 Chemicals & Materials":        ["Pidilite","Asian Paints","Berger Paints","Nerolac","Atul Ltd","SRF","Navin Fluorine","Vinati Organics"],
    "🏭 Manufacturing & Industrial":   ["Tata Steel","JSW Steel","Hindustan Zinc","Hindalco","Bharat Forge","Sundaram Fasteners","Motherson","Minda Industries"],
    "💧 Water & Beverages":            ["Bisleri","Kinley","Aquafina","Bailley","Vedica","Himalayan","OxyRich","Tata Copper+"],
    "🛥️ Luxury & Premium":             ["Louis Vuitton India","Rolex India","Gucci India","BMW India","Mercedes India","Porsche India","Tiffany India","Montblanc India"],
    "🧵 Textiles & Yarn":              ["Vardhman Textiles","Welspun India","Arvind Ltd","Raymond","Trident Group","Bombay Dyeing","Himatsingka","RSWM"],
    "🏥 Mental Health & Therapy":      ["YourDost","iCall","MindPeers","Wysa","InnerHour","Vandrevala Foundation","Nimhans","Lissun"],
    "🔭 Space & Deep Tech":            ["ISRO","Skyroot Aerospace","Agnikul Cosmos","Pixxel","Dhruva Space","GalaxEye","Bellatrix Aerospace","Digantara"],
    "🌐 Web3 & Crypto":                ["CoinDCX","WazirX","CoinSwitch","ZebPay","Mudrex","Giottus","Bitbns","Unocoin"],
    "🚌 Urban Mobility":               ["Ola Cabs","Uber India","Rapido","Yulu","Bounce","BluSmart","Vogo","Drivezy"],
    "🏗️ Construction & Infra":         ["L&T","Ultratech Cement","ACC Cement","Ambuja Cements","NMDC","DLF","Godrej Properties","Prestige Group"],
}

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def classify_intent(q: str) -> str:
    q = q.lower()
    if any(w in q for w in ["buy","price","cost","discount","offer","cheap","deal","purchase","pay","order","book","subscription"]):
        return "Transactional"
    if any(w in q for w in ["best","review","compare","vs","worth","recommend","top","rating","better","alternative","which"]):
        return "Commercial"
    if any(w in q for w in ["how","what","why","when","explain","does","can i","where","is it","difference","guide","steps"]):
        return "Informational"
    return "Navigational"

def kw_importance(rank: int, n_keywords: int) -> float:
    """Keyword rank 1 = 1.0, last rank = 0.1"""
    return max(0.1, 1.0 - (rank - 1) / max(n_keywords - 1, 1) * 0.9)

def importance_label(s: float):
    if s >= 0.75: return "🔴 High",   "#ff6b6b"
    if s >= 0.45: return "🟡 Medium", "#ffd46b"
    return              "🟢 Low",    "#6bffd8"

def clean_industry(name: str) -> str:
    """Strip leading emoji/punctuation."""
    return re.sub(r'^[^\w]+', '', name).strip()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — FETCH TRENDING KEYWORDS FROM GOOGLE TRENDS (SerpAPI)
# ─────────────────────────────────────────────────────────────────────────────
def fetch_trending_keywords(industry_name: str, serpapi_key: str,
                            num: int = 15, city: str = "") -> list[dict]:
    """
    Fetch top trending search keywords for the industry in India (optionally
    scoped to a city) using SerpAPI's Google Trends + Autocomplete APIs.
    """
    keywords = []
    clean    = clean_industry(industry_name)
    primary  = clean.split("&")[0].split("/")[0].strip()
    # Append city to query for localised results
    geo_suffix = f" {city}" if city else ""
    location_label = city if city else "India"

    # Try Google Trends related queries first
    try:
        r = requests.get("https://serpapi.com/search", params={
            "engine":   "google_trends",
            "q":        f"{primary}{geo_suffix}",
            "geo":      "IN",
            "api_key":  serpapi_key,
            "data_type":"RELATED_QUERIES",
        }, timeout=30)
        data = r.json()

        # Top queries (highest relative search volume)
        top_qs = (data.get("related_queries", {})
                      .get("top", []))
        for item in top_qs[:num]:
            kw = item.get("query","").strip()
            val= item.get("value", 0)
            if isinstance(val, str):
                val = int(re.sub(r"[^\d]","",val) or "0")
            if kw:
                keywords.append({"keyword": kw, "trend_value": val, "source": "trends_top"})

        # Rising queries (breakout trends) — append after top
        rising_qs = (data.get("related_queries", {})
                         .get("rising", []))
        for item in rising_qs[:max(0, num - len(keywords))]:
            kw = item.get("query","").strip()
            val= item.get("value", 0)
            if isinstance(val, str):
                # Rising values can be "Breakout" — treat as high
                if "breakout" in str(val).lower():
                    val = 5000
                else:
                    val = int(re.sub(r"[^\d]","",str(val)) or "100")
            if kw and kw not in {k["keyword"] for k in keywords}:
                keywords.append({"keyword": kw, "trend_value": val, "source": "trends_rising"})

    except Exception as e:
        st.warning(f"Google Trends API: {e}")

    # Fallback: Google Autocomplete suggestions if Trends returned too few
    if len(keywords) < 5:
        try:
            for suffix in ["", " best", " how", " price", " review"]:
                r = requests.get("https://serpapi.com/search", params={
                    "engine":  "google_autocomplete",
                    "q":       f"{primary}{geo_suffix}{suffix} India",
                    "gl":      "in",
                    "hl":      "en",
                    "api_key": serpapi_key,
                }, timeout=12)
                for sug in r.json().get("suggestions", []):
                    kw = sug.get("value","").strip()
                    if kw and kw not in {k["keyword"] for k in keywords}:
                        keywords.append({"keyword": kw, "trend_value": 50,
                                         "source": "autocomplete"})
                if len(keywords) >= num:
                    break
        except Exception as e:
            st.warning(f"Autocomplete fallback: {e}")

    # Sort by trend_value descending, assign rank
    keywords = sorted(keywords, key=lambda x: -x.get("trend_value", 0))
    for i, kw in enumerate(keywords[:num], 1):
        kw["rank"] = i

    return keywords[:num]

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — EACH ENGINE GENERATES QUESTIONS FROM KEYWORDS
# ─────────────────────────────────────────────────────────────────────────────
def build_question_prompt(engine_name: str, industry: str,
                          keywords: list[dict], n_per_keyword: int,
                          brands: list[str], city: str = "") -> str:
    kw_block = "\n".join(
        f"  {kw['rank']}. \"{kw['keyword']}\"  (trend score: {kw.get('trend_value','?')})"
        for kw in keywords
    )
    brand_list = ", ".join(brands)
    city_ctx   = city if city else "India"
    return f"""You are an expert in consumer search behaviour in India and Answer Engine Optimization (AEO).

Below are the top trending search keywords for the **{industry}** industry in **{city_ctx}**, ranked by search volume (rank 1 = most searched):

{kw_block}

Task: For EACH keyword (in rank order), generate exactly {n_per_keyword} realistic question(s) that Indian consumers would type or speak into {engine_name}.

Rules:
- Questions must be GENERIC to the industry — do NOT ask about a specific brand unless the keyword itself includes a brand name
- Questions should reflect how real users phrase things in {engine_name} specifically (conversational for ChatGPT, research-style for Perplexity, Google-style short phrases for Gemini, thoughtful for Claude)
- Questions must be relevant to the Indian market context
- Questions about the industry will naturally surface brand mentions in answers — that is the goal
- Brands in this industry include: {brand_list} — but do not force them into questions
- Maintain the keyword rank order — questions for keyword #1 come first

Return ONLY a valid JSON array. No markdown, no explanation:
[
  {{
    "keyword": "<the keyword this question is based on>",
    "keyword_rank": <rank number>,
    "question": "<the full question>"
  }},
  ...
]"""


def generate_questions_from_keywords(engine_name: str, industry: str,
                                     keywords: list[dict], n_per_keyword: int,
                                     brands: list[str], city: str = "",
                                     retries: int = 3) -> list[dict]:
    """
    Use Claude to generate questions framed for a specific engine persona.
    Retries on rate-limit / transient errors with exponential backoff.
    """
    prompt   = build_question_prompt(engine_name, industry, keywords,
                                     n_per_keyword, brands, city=city)
    last_err = "Unknown error"

    for attempt in range(retries):
        try:
            client  = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2500,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = message.content[0].text.strip()
            # Strip markdown fences robustly
            raw = re.sub(r"^```(?:json)?", "", raw, flags=re.MULTILINE).strip()
            raw = re.sub(r"```$",          "", raw, flags=re.MULTILINE).strip()
            # Extract first JSON array in case model adds preamble text
            match = re.search(r"\[.*?\]", raw, re.DOTALL)
            if match:
                raw = match.group(0)

            items = json.loads(raw)
            n_kw  = len(keywords)
            out   = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                q_text  = item.get("question", "").strip()
                kw_rank = int(item.get("keyword_rank", 1))
                if not q_text:
                    continue
                imp_sc = kw_importance(kw_rank, n_kw)
                lb, co = importance_label(imp_sc)
                out.append({
                    "question":         q_text,
                    "keyword":          item.get("keyword", ""),
                    "keyword_rank":     kw_rank,
                    "engine":           engine_name,
                    "intent":           classify_intent(q_text),
                    "importance_score": imp_sc,
                    "importance_label": lb,
                    "importance_color": co,
                    "source":           "Keyword-driven",
                    "tags":             ["google-trends", "india"],
                    "brand_mentions":   {},
                })
            return out

        except anthropic.RateLimitError:
            wait = 2 ** attempt * 4   # 4s, 8s, 16s
            st.warning(f"⏳ Rate limit ({engine_name}, attempt {attempt+1}/{retries}). "
                       f"Waiting {wait}s…")
            time.sleep(wait)
            last_err = "Rate limit exceeded"

        except json.JSONDecodeError as e:
            last_err = f"JSON parse error — {e}"
            st.warning(f"⚠️ {engine_name} JSON parse failed: {e}. Raw (first 300 chars): {raw[:300]}")
            break   # no point retrying a parse error

        except Exception as e:
            last_err = str(e)
            st.warning(f"⚠️ {engine_name} attempt {attempt+1}: {e}")
            if attempt < retries - 1:
                time.sleep(3)

    st.error(f"❌ Question generation failed for **{engine_name}** after {retries} attempts: {last_err}")
    return []

# ─────────────────────────────────────────────────────────────────────────────
# API CLIENTS
# ─────────────────────────────────────────────────────────────────────────────
def _env(k):
    v = os.getenv(k)
    if not v: raise ValueError(f"{k} missing from .env")
    return v

def get_anthropic():
    return anthropic.Anthropic(api_key=_env("ANTHROPIC_API_KEY"))

def get_openai():
    from openai import OpenAI
    return OpenAI(api_key=_env("OPENAI_API_KEY"))

def get_gemini_client():
    from google import genai
    return genai.Client(api_key=_env("GEMINI_API_KEY"))

def get_perplexity():
    from openai import OpenAI
    return OpenAI(api_key=_env("PERPLEXITY_API_KEY"),
                  base_url="https://api.perplexity.ai")

# ─────────────────────────────────────────────────────────────────────────────
# STREAMING ANSWER FETCHERS
# ─────────────────────────────────────────────────────────────────────────────
def stream_claude(q, ph):
    c = get_anthropic(); full = ""
    with c.messages.stream(model=ENGINES["Claude"]["model"], max_tokens=600,
            messages=[{"role":"user","content":q}]) as s:
        for t in s.text_stream: full += t; ph.markdown(full + "▌")
    ph.markdown(full); return full

def stream_openai(q, ph):
    c = get_openai(); full = ""
    for chunk in c.chat.completions.create(
            model=ENGINES["ChatGPT"]["model"], max_tokens=600, stream=True,
            messages=[{"role":"user","content":q}]):
        d = chunk.choices[0].delta.content or ""; full += d; ph.markdown(full + "▌")
    ph.markdown(full); return full

def stream_gemini(q, ph):
    from google import genai
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))
    full = ""
    try:
        for chunk in client.models.generate_content_stream(
            model=ENGINES["Gemini"]["model"],
            contents=q,
        ):
            d = chunk.text or ""
            full += d
            if full:
                ph.markdown(full + "▌")
    except Exception as e:
        ph.markdown(f"⚠️ Gemini error: {e}")
        return f"Error: {e}"
    ph.markdown(full)
    return full

def stream_perplexity(q, ph):
    """Stream Perplexity answer. Returns (text, sources_list)."""
    c = get_perplexity(); full = ""
    response = c.chat.completions.create(
        model=ENGINES["Perplexity"]["model"], max_tokens=600, stream=True,
        messages=[{"role":"user","content":q}])
    for chunk in response:
        d = chunk.choices[0].delta.content or ""; full += d; ph.markdown(full + "▌")
    ph.markdown(full)
    return full

STREAMERS = {
    "Claude":     stream_claude,
    "ChatGPT":    stream_openai,
    "Gemini":     stream_gemini,
    "Perplexity": stream_perplexity,
}

def extract_sources_from_answer(answer_text: str, engine: str) -> list[dict]:
    """
    Extract cited sources from an answer using Claude Haiku.
    Returns list of {"title": str, "url": str, "domain": str}
    Works for all engines — looks for hyperlinks, footnotes, or inline citations.
    """
    if not answer_text or len(answer_text) < 50:
        return []
    try:
        client = get_anthropic()
        prompt = f"""Extract all sources, references, URLs, or citations from this AI-generated answer.

Answer from {engine}:
\"\"\"
{answer_text[:3000]}
\"\"\"

Return ONLY a JSON array of sources found. Each source:
{{"title": "page or source title (or domain if no title)", "url": "full URL if present else empty string", "domain": "domain name only e.g. wikipedia.org"}}

If no sources are cited, return [].
No explanation, JSON only."""
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = re.sub(r"```json|```", "", msg.content[0].text.strip()).strip()
        match = re.search(r"\[.*?\]", raw, re.DOTALL)
        if match:
            sources = json.loads(match.group(0))
            return [s for s in sources if isinstance(s, dict) and s.get("domain")]
        return []
    except Exception:
        # Fallback: regex-extract any URLs from text
        urls = re.findall(r"https?://[\w./\-?=&#%+]+", answer_text)
        return [{"title": u, "url": u,
                 "domain": re.sub(r"https?://(?:www\.)?([^/]+).*", r"\1", u)}
                for u in urls[:5]]

# ─────────────────────────────────────────────────────────────────────────────
# BRAND MENTION DETECTION (Claude Haiku, context-aware)
# ─────────────────────────────────────────────────────────────────────────────
def detect_brand_mentions(answer_text: str, brands: list,
                          industry: str) -> dict:
    if not answer_text.strip(): return {}
    try:
        client = get_anthropic()
        prompt = f"""You are analysing an AI answer about the {industry} industry in India.

Answer:
\"\"\"{answer_text[:3000]}\"\"\"

Brand list: {", ".join(brands)}

Which brands from the list are mentioned in the answer AS COMPANIES in the context of {industry}?
Avoid false positives — e.g. "Apple" = tech company not fruit, "Amazon" = e-commerce not river.

Return ONLY JSON: {{"Brand Name": count}} — only include brands that appear. Return {{}} if none.
No explanation."""
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{"role":"user","content":prompt}]
        )
        raw = re.sub(r"```json|```", "", msg.content[0].text.strip()).strip()
        return json.loads(raw)
    except Exception:
        # Simple fallback
        out = {}
        for brand in brands:
            word = brand.split()[0]
            cnt  = len(re.findall(r'\b' + re.escape(word) + r'\b',
                                  answer_text, re.IGNORECASE))
            if cnt: out[brand] = cnt
        return out

# ─────────────────────────────────────────────────────────────────────────────
# HISTORY (Week-on-Week)
# ─────────────────────────────────────────────────────────────────────────────
def load_history() -> dict:
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE) as f: return json.load(f)
        except Exception: pass
    return {}

def save_snapshot(industry: str, week_label: str, brand_data: dict):
    h = load_history()
    if industry not in h: h[industry] = {}
    h[industry][week_label] = brand_data
    with open(HISTORY_FILE, "w") as f: json.dump(h, f, indent=2)

def get_week_label() -> str:
    dt  = datetime.now()
    mon = dt - timedelta(days=dt.weekday())
    return mon.strftime("Week of %d %b %Y")

# ─────────────────────────────────────────────────────────────────────────────
# RENDER HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def intent_cls(i): return f"intent-{i.lower()}"

def eng_badge(engine):
    cfg = ENGINES.get(engine, {"color":"#7c6bff","icon":"🔍","accent":"rgba(124,107,255,"})
    return (f'<span class="engine-badge" style="background:{cfg["accent"]}0.15);'
            f'border:1.5px solid {cfg["accent"]}0.4);color:{cfg["color"]}">'
            f'{cfg["icon"]} {engine}</span>')

def imp_bar_html(score, label, color):
    pct = int(score * 100)
    return (f'<div class="imp-wrap">'
            f'<span style="font-size:.64rem;font-weight:700;color:{color};white-space:nowrap;">{label}</span>'
            f'<div class="imp-bg"><div class="imp-fill" '
            f'style="width:{pct}%;background:linear-gradient(90deg,{color}88,{color});"></div></div>'
            f'<span style="font-size:.61rem;color:var(--muted);">{pct}%</span></div>')

def q_card_html(item, idx, color="#7c6bff"):
    intent = item.get("intent", "Informational")
    qtext  = item.get("question", "")
    kw     = item.get("keyword", "")
    kw_rk  = item.get("keyword_rank", "")
    score  = item.get("importance_score", 0.3)
    lbl    = item.get("importance_label", "🟢 Low")
    icol   = item.get("importance_color", "#6bffd8")
    kw_tag = (f'<span class="kw-tag">#{kw_rk} {kw}</span>' if kw else "")
    return f"""
    <div class="q-card" style="border-left:3px solid {color};">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2px;">
        <span class="q-num">Q{idx:02d}</span>
        <span class="tag {intent_cls(intent)}">{intent}</span>
      </div>
      <div class="q-text">"{qtext}"</div>
      {imp_bar_html(score, lbl, icol)}
      <div class="q-tags" style="margin-top:5px;">{kw_tag}</div>
    </div>"""

def bar_row_html(label, val, max_val, color, suffix=""):
    pct = (val / max_val * 100) if max_val else 0
    return (f'<div class="bar-row">'
            f'<span class="bar-lbl" title="{label}">{label}</span>'
            f'<div class="bar-bg"><div class="bar-fill" style="width:{pct}%;background:{color};"></div></div>'
            f'<span class="bar-val">{val}{suffix}</span></div>')

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:.5rem 0 1.2rem;">
      <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:1.3rem;
        background:linear-gradient(90deg,#a78bfa,#38bdf8);-webkit-background-clip:text;
        -webkit-text-fill-color:transparent;letter-spacing:-.01em;">AEO Hub · India 🇮🇳</div>
      <div style="color:rgba(167,139,250,.8);font-size:.68rem;margin-top:3px;font-weight:600;
        letter-spacing:.06em;text-transform:uppercase;">Keyword-Driven Intelligence</div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="stl">Industry</div>', unsafe_allow_html=True)

    # Freetext input with autocomplete suggestions from INDUSTRIES list
    industry_suggestions = sorted(
        [re.sub(r"^[^\w]+", "", k).strip() for k in INDUSTRIES.keys()]
    )
    industry_input = st.text_input(
        "Type or select an industry",
        value=st.session_state.get("industry_input_val", ""),
        placeholder="e.g. Electric Vehicles, Quick Commerce, D2C Skincare…",
        label_visibility="collapsed",
        key="industry_text_input",
    )

    # Show matching suggestions from first character typed
    if industry_input:
        matches = [s for s in industry_suggestions
                   if industry_input.lower() in s.lower()][:8]
        if matches:
            pills_html = "".join(
                f'<span style="display:inline-block;background:rgba(99,88,255,.1);'
                f'border:1.5px solid rgba(99,88,255,.25);color:#6358ff;padding:3px 10px;'
                f'border-radius:20px;font-size:.7rem;font-weight:600;margin:2px 3px 2px 0;'
                f'cursor:pointer;">{s}</span>'
                for s in matches
            )
            st.markdown(
                f"<div style='font-size:.67rem;color:var(--muted);margin-bottom:4px;font-weight:600;"
                f"letter-spacing:.05em;text-transform:uppercase;'>Suggestions</div>"
                f"<div style='margin-bottom:6px;'>{pills_html}</div>",
                unsafe_allow_html=True)
            # Clickable buttons (Streamlit can't make HTML spans interactive, use columns)
            btn_cols = st.columns(min(len(matches), 3))
            for ci, sug in enumerate(matches):
                if btn_cols[ci % 3].button(sug, key=f"sug_{sug}", use_container_width=True):
                    st.session_state["industry_input_val"] = sug
                    st.rerun()

    industry_choice = industry_input.strip() if industry_input.strip() else "E-Commerce & Retail"

    # Brands — editable, pre-filled whenever industry_choice changes
    def _find_brands(ind: str) -> list:
        """Return brands for best-matching known industry, else []."""
        ind_l = ind.lower().strip()
        # 1. exact substring match on cleaned key
        for k in INDUSTRIES:
            clean_k = re.sub(r"^[^\w]+", "", k).strip().lower()
            if ind_l in clean_k or clean_k in ind_l:
                return INDUSTRIES[k]
        # 2. word-level overlap (≥1 significant word matches)
        ind_words = set(w for w in ind_l.split() if len(w) > 3)
        best_k, best_score = None, 0
        for k in INDUSTRIES:
            clean_k = re.sub(r"^[^\w]+", "", k).strip().lower()
            kw = set(w for w in clean_k.split() if len(w) > 3)
            score = len(ind_words & kw)
            if score > best_score:
                best_score, best_k = score, k
        return INDUSTRIES[best_k] if best_k and best_score > 0 else []

    # Recompute default brands whenever the industry input changes
    _prev_ind  = st.session_state.get("_prev_industry", "")
    _new_ind   = industry_choice
    if _new_ind != _prev_ind:
        st.session_state["_prev_industry"]   = _new_ind
        st.session_state["_default_brands"]  = _find_brands(_new_ind)
        # Clear the textarea so it re-renders with new defaults
        if "brands_textarea" in st.session_state:
            del st.session_state["brands_textarea"]

    default_brands = st.session_state.get("_default_brands", _find_brands(_new_ind))

    st.markdown('<div class="stl">Brands to Track</div>', unsafe_allow_html=True)
    st.caption("Auto-filled from industry · edit freely")
    brands_input = st.text_area(
        "Brands (one per line)",
        value="\n".join(default_brands) if default_brands else "",
        height=130,
        placeholder="e.g.\nZomato\nSwiggy\nMagicPin",
        label_visibility="collapsed",
        key="brands_textarea",
    )
    selected_brands = [b.strip() for b in brands_input.split("\n") if b.strip()]
    if not selected_brands:
        st.warning("Add at least one brand to track.")

    # City filter
    st.markdown('<div class="stl">City / Region (optional)</div>', unsafe_allow_html=True)
    INDIA_CITIES = [
        "All India", "Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Chennai",
        "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Lucknow", "Surat",
        "Chandigarh", "Kochi", "Indore", "Bhopal", "Nagpur", "Visakhapatnam",
        "Noida", "Gurugram",
    ]
    city_choice = st.selectbox("City", INDIA_CITIES, label_visibility="collapsed")

    st.markdown('<div class="stl">Answer Engines</div>', unsafe_allow_html=True)
    selected_engines = st.multiselect("Engines", list(ENGINES.keys()),
                                      default=list(ENGINES.keys()),
                                      label_visibility="collapsed")

    st.markdown('<div class="stl">Keywords to Fetch</div>', unsafe_allow_html=True)
    n_keywords = st.slider("", min_value=5, max_value=20, value=10,
                           label_visibility="collapsed")

    st.markdown('<div class="stl">Questions per Keyword per Engine</div>', unsafe_allow_html=True)
    n_per_kw = st.slider("", min_value=1, max_value=4, value=2,
                         label_visibility="collapsed",
                         key="nperkw")

    st.markdown('<div class="stl">Stream Answers</div>', unsafe_allow_html=True)
    fetch_answers = st.toggle("Auto-fetch & stream answers", value=False)
    if fetch_answers:
        st.caption("⚠️ Calls all 4 engine APIs — requires all keys in .env")

    st.markdown('<div class="stl">Sort Questions By</div>', unsafe_allow_html=True)
    sort_by = st.selectbox("Sort",
                           ["Keyword Rank (default)", "Importance ↓",
                            "Importance ↑", "Intent"],
                           label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button("🔍 Fetch Keywords & Generate Questions")

# ─────────────────────────────────────────────────────────────────────────────
# HERO
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="badge">✦ AEO Intelligence · India Edition 🇮🇳 · v5</div>
  <h1>Answer Engine Question Explorer</h1>
  <p>Top Google Trends keywords → each engine independently generates ranked questions →
     answers streamed live → brand mentions tracked with AI context-awareness.</p>
</div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────────────────────────────────────
serpapi_key = os.getenv("SERPAPI_KEY", "")
if not serpapi_key:
    st.error("❌ **SERPAPI_KEY** not found in `.env`. This is required to fetch Google Trends keywords.")
    st.stop()
if not selected_engines:
    st.warning("⚠️ Select at least one engine."); st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
for k, v in [("keywords", None), ("questions", None),
             ("answers", {}), ("brand_mentions", {}), ("answer_sources", {}),
             ("ts", 0), ("city_scope", ""), ("industry_input_val", "")]:
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────────────
# FETCH & GENERATE
# ─────────────────────────────────────────────────────────────────────────────
if run_btn:
    st.session_state.update({
        "ts": int(time.time()), "answers": {},
        "brand_mentions": {}, "answer_sources": {},
        "questions": None, "keywords": None
    })
    total_steps = 1 + len(selected_engines)
    bar = st.progress(0, "Fetching top trending keywords from Google Trends…")

    # Step 1: Keywords
    city_scope = "" if city_choice == "All India" else city_choice
    keywords = fetch_trending_keywords(industry_choice, serpapi_key,
                                       num=n_keywords, city=city_scope)
    if not keywords:
        st.error("Could not fetch keywords. Check SerpAPI key and quota at serpapi.com/dashboard")
        st.stop()
    st.session_state.keywords = keywords
    bar.progress(1 / total_steps, f"✅ {len(keywords)} keywords fetched. Generating questions…")

    # Step 2: Each engine generates questions (with delay to avoid rate limits)
    all_questions = []
    for i, engine in enumerate(selected_engines, 1):
        pct = 0.15 + (i - 1) / len(selected_engines) * 0.8
        bar.progress(pct, f"🤖 {engine} generating questions from keywords… ({i}/{len(selected_engines)})")
        qs = generate_questions_from_keywords(
            engine_name=engine,
            industry=industry_choice,
            keywords=keywords,
            n_per_keyword=n_per_kw,
            brands=selected_brands,
            city=city_scope,
        )
        all_questions.extend(qs)
        st.toast(f"✅ {engine}: {len(qs)} questions generated")
        # Small delay between engines to avoid Claude API rate limits
        if i < len(selected_engines):
            time.sleep(2)

    bar.progress(1.0, f"✅ {len(all_questions)} questions generated across {len(selected_engines)} engines!")
    time.sleep(0.5); bar.empty()

    if not all_questions:
        st.error("No questions generated. Check your ANTHROPIC_API_KEY.")
        st.stop()

    st.session_state.questions  = all_questions
    st.session_state.week_label = get_week_label()
    st.session_state.city_scope = city_scope

# ─────────────────────────────────────────────────────────────────────────────
# MAIN DISPLAY
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.questions and st.session_state.keywords:
    questions = st.session_state.questions
    keywords  = st.session_state.keywords

    # Sort
    if   sort_by == "Importance ↓":       questions = sorted(questions, key=lambda x: -x.get("importance_score", 0))
    elif sort_by == "Importance ↑":       questions = sorted(questions, key=lambda x:  x.get("importance_score", 0))
    elif sort_by == "Intent":             questions = sorted(questions, key=lambda x:  x.get("intent", ""))
    else:                                 questions = sorted(questions, key=lambda x:  x.get("keyword_rank", 99))

    # Stat strip
    cols = st.columns(5)
    for col, num, lbl in zip(cols,
        [len(keywords), len(questions), len(selected_engines),
         len(selected_brands), len(set(q["intent"] for q in questions))],
        ["🔑 Keywords","❓ Questions","🤖 Engines","🏷️ Brands","🎯 Intents"]):
        col.markdown(f'<div class="stat-card"><div class="stat-num">{num}</div>'
                     f'<div class="stat-label">{lbl}</div></div>',
                     unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # ── TABS ─────────────────────────────────────────────────────────────────
    tab_kw, tab_q, tab_a, tab_bm, tab_ana, tab_wow = st.tabs([
        "🔑 Keywords", "❓ Questions", "💬 Answers",
        "🏷️ Brand Mentions", "📊 Analytics", "📈 Week-on-Week"
    ])

    # =========================================================================
    # TAB 0 — KEYWORDS
    # =========================================================================
    with tab_kw:
        city_lbl = st.session_state.get("city_scope","") or "All India"
        st.markdown(f"<div style='color:var(--muted);font-size:.82rem;margin-bottom:.8rem;'>"
                    f"Top <b style='color:var(--text)'>{len(keywords)}</b> trending keywords for "
                    f"<b style='color:#c4baff;'>{clean_industry(industry_choice)}</b> · "
                    f"<span style='background:rgba(107,255,216,.1);border:1px solid rgba(107,255,216,.3);"
                    f"color:#6bffd8;padding:1px 8px;border-radius:10px;font-size:.7rem;'>📍 {city_lbl}</span> · "
                    f"Source: Google Trends + Autocomplete</div>", unsafe_allow_html=True)

        max_val = max((k.get("trend_value", 0) for k in keywords), default=1) or 1
        for kw in keywords:
            tv  = kw.get("trend_value", 0)
            pct = int(tv / max_val * 100) if max_val else 50
            src_badge = ("🔵 Trending" if kw.get("source") == "trends_top"
                         else "🟢 Rising" if kw.get("source") == "trends_rising"
                         else "🔍 Autocomplete")
            st.markdown(f"""
            <div class="q-card" style="border-left:3px solid #7c6bff;">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                <div style="display:flex;align-items:center;gap:8px;">
                  <span class="kw-rank" style="font-size:.9rem;">#{kw['rank']}</span>
                  <span class="kw-text" style="font-size:.96rem;font-weight:600;">{kw['keyword']}</span>
                </div>
                <div style="display:flex;align-items:center;gap:8px;">
                  <span style="font-size:.68rem;color:var(--muted);">{src_badge}</span>
                  <span style="font-size:.72rem;color:#6bffd8;font-weight:700;">
                    {f'Score: {tv}' if tv else ''}
                  </span>
                </div>
              </div>
              <div class="trend-bar" style="width:{pct}%;"></div>
              <div style="font-size:.68rem;color:var(--muted);margin-top:4px;">
                Generates questions for: {", ".join(selected_engines)}
              </div>
            </div>""", unsafe_allow_html=True)

        # Download keywords
        kw_csv = "Rank,Keyword,Trend Score,Source\n"
        for kw in keywords:
            kw_csv += f'{kw["rank"]},"{kw["keyword"]}",{kw.get("trend_value","")},{kw.get("source","")}\n'
        st.download_button("📥 Download Keywords CSV", data=kw_csv,
            file_name=f"keywords_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv")

    # =========================================================================
    # TAB 1 — QUESTIONS
    # =========================================================================
    with tab_q:
        fc1, fc2, fc3 = st.columns(3)
        f_engine = fc1.selectbox("Engine", ["All"] + selected_engines, key="fq_eng")
        f_intent = fc2.selectbox("Intent", ["All"] + INTENT_TYPES,     key="fq_int")
        f_kw     = fc3.selectbox("Keyword", ["All"] + [k["keyword"] for k in keywords], key="fq_kw")

        filtered = questions
        if f_engine != "All": filtered = [q for q in filtered if q["engine"] == f_engine]
        if f_intent != "All": filtered = [q for q in filtered if q["intent"] == f_intent]
        if f_kw     != "All": filtered = [q for q in filtered if q.get("keyword") == f_kw]

        st.markdown(f"<div style='color:var(--muted);font-size:.8rem;margin:.3rem 0 .7rem;'>"
                    f"Showing <b style='color:var(--text)'>{len(filtered)}</b> questions</div>",
                    unsafe_allow_html=True)

        for engine in (selected_engines if f_engine == "All" else [f_engine]):
            eng_qs = [q for q in filtered if q["engine"] == engine]
            if not eng_qs: continue
            cfg = ENGINES.get(engine, {})
            st.markdown(f'<div style="display:flex;align-items:center;gap:8px;margin:.7rem 0 .5rem;">'
                        f'{eng_badge(engine)}'
                        f'<span style="color:var(--muted);font-size:.76rem;">'
                        f'{len(eng_qs)} questions</span></div>', unsafe_allow_html=True)
            for i, q in enumerate(eng_qs):
                st.markdown(q_card_html(q, i + 1, cfg.get("color", "#7c6bff")),
                            unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

        q_csv = "Engine,Keyword,Keyword Rank,Intent,Importance,Score,Question\n"
        for q in filtered:
            q_csv += (f'{q["engine"]},"{q.get("keyword","")}",{q.get("keyword_rank","")}'
                      f',{q.get("intent","")},{q.get("importance_label","")}'
                      f',{q.get("importance_score",0):.2f}'
                      f',"{q["question"].replace(chr(34),chr(34)*2)}"\n')
        st.download_button("📥 Download Questions CSV", data=q_csv,
            file_name=f"questions_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv")

    # =========================================================================
    # TAB 2 — ANSWERS
    # =========================================================================
    with tab_a:
        if fetch_answers:
            unfetched = [q for q in questions
                         if (q["engine"], q["question"]) not in st.session_state.answers]
            if unfetched:
                bar2 = st.progress(0, "Streaming answers…")
                for idx, q_item in enumerate(unfetched):
                    eng   = q_item["engine"]
                    qtext = q_item["question"]
                    ck    = (eng, qtext)
                    streamer = STREAMERS.get(eng)
                    cfg_     = ENGINES.get(eng, {})
                    if streamer:
                        s = st.empty(); p = st.empty()
                        s.caption(f"{cfg_.get('icon','')} {eng}: *{qtext[:65]}…*")
                        try:
                            ans = streamer(qtext, p)
                            st.session_state.answers[ck] = ans
                            # Extract sources
                            sources = extract_sources_from_answer(ans, eng)
                            if sources:
                                st.session_state.answer_sources[ck] = sources
                            # Brand mention detection
                            mentions = detect_brand_mentions(ans, selected_brands, industry_choice)
                            imp = q_item.get("importance_score", 0.3)
                            for brand, cnt in mentions.items():
                                if brand not in st.session_state.brand_mentions:
                                    st.session_state.brand_mentions[brand] = {
                                        "total": 0, "weighted": 0.0,
                                        "engines": defaultdict(int)
                                    }
                                st.session_state.brand_mentions[brand]["total"]    += cnt
                                st.session_state.brand_mentions[brand]["weighted"] += cnt * imp
                                st.session_state.brand_mentions[brand]["engines"][eng] += cnt
                        except Exception as e:
                            st.session_state.answers[ck] = f"⚠️ Error: {e}"
                        p.empty(); s.empty()
                    bar2.progress((idx + 1) / len(unfetched),
                                  f"Fetched {idx+1}/{len(unfetched)}…")
                bar2.empty()

                # Save WoW snapshot
                if st.session_state.brand_mentions:
                    snap = {b: {"total": v["total"], "weighted": round(v["weighted"], 2)}
                            for b, v in st.session_state.brand_mentions.items()}
                    save_snapshot(industry_choice, get_week_label(), snap)

        else:
            st.info("💡 Enable **Auto-fetch & stream answers** in the sidebar to populate this tab.")

        # Filter & display
        ac1, ac2 = st.columns(2)
        f_eng_a = ac1.selectbox("Engine", ["All"] + selected_engines, key="fa_eng")
        f_kw_a  = ac2.selectbox("Keyword", ["All"] + [k["keyword"] for k in keywords], key="fa_kw")

        filt_a = questions
        if f_eng_a != "All": filt_a = [q for q in filt_a if q["engine"] == f_eng_a]
        if f_kw_a  != "All": filt_a = [q for q in filt_a if q.get("keyword") == f_kw_a]

        for engine in (selected_engines if f_eng_a == "All" else [f_eng_a]):
            eng_qs = [q for q in filt_a if q["engine"] == engine]
            if not eng_qs: continue
            cfg = ENGINES.get(engine, {})
            st.markdown(f'<div style="margin:.8rem 0 .5rem;">{eng_badge(engine)}</div>',
                        unsafe_allow_html=True)
            for i, q_item in enumerate(eng_qs):
                qtext = q_item["question"]
                ck    = (engine, qtext)
                label = f'Q{i+1:02d} [{q_item.get("keyword","")}] — "{qtext[:70]}{"…" if len(qtext)>70 else ""}"'
                with st.expander(label):
                    st.markdown(q_card_html(q_item, i + 1, cfg.get("color", "#7c6bff")),
                                unsafe_allow_html=True)
                    if ck in st.session_state.answers:
                        st.markdown(f'<div class="ans-box">{st.session_state.answers[ck]}</div>',
                                    unsafe_allow_html=True)
                        # Show sources if available
                        srcs = st.session_state.answer_sources.get(ck, [])
                        if srcs:
                            src_html = "".join(
                                f'<a href="{s.get("url","#")}" target="_blank" style="display:inline-flex;align-items:center;gap:5px;background:#f0f2ff;border:1.5px solid rgba(99,88,255,.2);color:#6358ff;padding:3px 10px;border-radius:20px;font-size:.68rem;font-weight:600;text-decoration:none;margin:2px 3px 2px 0;">🔗 {s.get("domain") or s.get("title","Source")}</a>'
                                for s in srcs[:8]
                            )
                            st.markdown(
                                f'<div style="margin-top:.5rem;"><span style="font-size:.65rem;font-weight:700;color:var(--muted);letter-spacing:.06em;text-transform:uppercase;">Sources</span></div><div style="margin-top:4px;">{src_html}</div>',
                                unsafe_allow_html=True)
                    else:
                        if st.button(f"Fetch {engine}'s answer",
                                     key=f"fa_{engine}_{i}_{st.session_state.ts}"):
                            streamer = STREAMERS.get(engine)
                            if streamer:
                                p = st.empty()
                                try:
                                    ans = streamer(qtext, p)
                                    st.session_state.answers[ck] = ans
                                    sources = extract_sources_from_answer(ans, engine)
                                    if sources:
                                        st.session_state.answer_sources[ck] = sources
                                    mentions = detect_brand_mentions(
                                        ans, selected_brands, industry_choice)
                                    imp = q_item.get("importance_score", 0.3)
                                    for brand, cnt in mentions.items():
                                        if brand not in st.session_state.brand_mentions:
                                            st.session_state.brand_mentions[brand] = {
                                                "total": 0, "weighted": 0.0,
                                                "engines": defaultdict(int)
                                            }
                                        st.session_state.brand_mentions[brand]["total"]    += cnt
                                        st.session_state.brand_mentions[brand]["weighted"] += cnt * imp
                                        st.session_state.brand_mentions[brand]["engines"][engine] += cnt
                                except Exception as e:
                                    st.error(str(e))

        if st.session_state.answers:
            a_csv = "Engine,Keyword,Keyword Rank,Intent,Importance,Question,Answer\n"
            for q in filt_a:
                ck  = (q["engine"], q["question"])
                ans = st.session_state.answers.get(ck, "").replace('"', '""')
                txt = q["question"].replace('"', '""')
                a_csv += (f'{q["engine"]},"{q.get("keyword","")}",{q.get("keyword_rank","")},'
                          f'{q.get("intent","")},{q.get("importance_label","")},"{txt}","{ans}"\n')
            st.download_button("📥 Download Answers CSV", data=a_csv,
                file_name=f"answers_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv")

    # =========================================================================
    # TAB 3 — BRAND MENTIONS
    # =========================================================================
    with tab_bm:
        bm = st.session_state.brand_mentions
        if not bm:
            st.info("💡 Brand mentions are detected from answers. Enable **Auto-fetch answers** and run to populate this tab.")
        else:
            st.markdown(
                f"<div style='color:var(--muted);font-size:.8rem;margin-bottom:.8rem;'>"
                f"<b style='color:var(--text)'>{len(bm)}</b> brands mentioned across "
                f"<b style='color:var(--text)'>{len(st.session_state.answers)}</b> answers · "
                f"Industry: <b style='color:#c4baff;'>{clean_industry(industry_choice)}</b> · "
                f"Weighted by keyword importance score</div>", unsafe_allow_html=True)

            sorted_bm    = sorted(bm.items(), key=lambda x: -x[1]["weighted"])
            max_total    = max((v["total"]    for v in bm.values()), default=1)
            max_weighted = max((v["weighted"] for v in bm.values()), default=1)

            col_t, col_w = st.columns(2)
            with col_t:
                rows = "".join(bar_row_html(b, v["total"], max_total,
                               "linear-gradient(90deg,#7c6bff,#6bffd8)")
                               for b, v in sorted_bm)
                st.markdown(f'<div class="ana"><div class="ana-title">🔢 Total Brand Mentions</div>'
                            f'{rows}</div>', unsafe_allow_html=True)
            with col_w:
                rows = "".join(bar_row_html(b, round(v["weighted"], 1), max_weighted,
                               "linear-gradient(90deg,#ff6b9d,#ffd46b)")
                               for b, v in sorted_bm)
                st.markdown(f'<div class="ana"><div class="ana-title">'
                            f'⚖️ Weighted Mentions (keyword importance × count)</div>'
                            f'{rows}</div>', unsafe_allow_html=True)

            # Per-engine breakdown
            st.markdown("<br>", unsafe_allow_html=True)
            eng_cols = st.columns(len(selected_engines))
            for col, engine in zip(eng_cols, selected_engines):
                cfg = ENGINES.get(engine, {})
                max_e = max(
                    (v.get("engines", {}).get(engine, 0) for v in bm.values()), default=1)
                rows = "".join(
                    bar_row_html(b, v.get("engines", {}).get(engine, 0), max_e or 1,
                                 cfg.get("color", "#7c6bff"))
                    for b, v in sorted_bm
                    if v.get("engines", {}).get(engine, 0) > 0
                )
                if not rows:
                    rows = '<div style="color:var(--muted);font-size:.78rem;">No mentions yet</div>'
                col.markdown(
                    f'<div class="ana"><div class="ana-title">'
                    f'{cfg.get("icon","")} {engine}</div>{rows}</div>',
                    unsafe_allow_html=True)

            bm_csv = "Brand,Total Mentions,Weighted Score," + ",".join(selected_engines) + "\n"
            for b, v in sorted_bm:
                eng_counts = ",".join(str(v.get("engines", {}).get(e, 0)) for e in selected_engines)
                bm_csv += f'{b},{v["total"]},{v["weighted"]:.2f},{eng_counts}\n'
            st.download_button("📥 Download Brand Mentions CSV", data=bm_csv,
                file_name=f"brand_mentions_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv")

    # =========================================================================
    # TAB 4 — ANALYTICS
    # =========================================================================
    with tab_ana:
        col1, col2 = st.columns(2)

        # Intent distribution
        intent_counts = defaultdict(int)
        for q in questions: intent_counts[q.get("intent", "Informational")] += 1
        max_ic = max(intent_counts.values(), default=1)
        rows = "".join(bar_row_html(i, intent_counts[i], max_ic, INTENT_COLORS.get(i, "#aaa"))
                       for i in INTENT_TYPES if intent_counts.get(i, 0) > 0)
        col1.markdown(f'<div class="ana"><div class="ana-title">🎯 Intent Distribution</div>'
                      f'{rows}</div>', unsafe_allow_html=True)

        # Keyword → question count
        kw_q_counts = defaultdict(int)
        for q in questions: kw_q_counts[q.get("keyword", "?")] += 1
        max_kq = max(kw_q_counts.values(), default=1)
        rows = "".join(bar_row_html(f"#{i+1} {kw['keyword']}", kw_q_counts.get(kw['keyword'], 0),
                       max_kq, "linear-gradient(90deg,#7c6bff88,#7c6bff)")
                       for i, kw in enumerate(keywords))
        col1.markdown(f'<div class="ana"><div class="ana-title">🔑 Questions per Keyword</div>'
                      f'{rows}</div>', unsafe_allow_html=True)

        # Engine distribution
        eng_counts = defaultdict(int)
        for q in questions: eng_counts[q.get("engine", "")] += 1
        max_ec = max(eng_counts.values(), default=1)
        rows = "".join(bar_row_html(e, eng_counts[e], max_ec,
                       ENGINES.get(e, {}).get("color", "#7c6bff"))
                       for e in selected_engines if eng_counts.get(e, 0) > 0)
        col2.markdown(f'<div class="ana"><div class="ana-title">🤖 Questions per Engine</div>'
                      f'{rows}</div>', unsafe_allow_html=True)

        # Importance distribution
        hi  = sum(1 for q in questions if q.get("importance_score", 0) >= 0.75)
        mid = sum(1 for q in questions if 0.45 <= q.get("importance_score", 0) < 0.75)
        lo  = sum(1 for q in questions if q.get("importance_score", 0) < 0.45)
        max_im = max(hi, mid, lo, 1)
        rows  = bar_row_html("🔴 High",   hi,  max_im, "#ff6b6b")
        rows += bar_row_html("🟡 Medium", mid, max_im, "#ffd46b")
        rows += bar_row_html("🟢 Low",    lo,  max_im, "#6bffd8")
        col2.markdown(f'<div class="ana"><div class="ana-title">⭐ Importance Distribution</div>'
                      f'{rows}</div>', unsafe_allow_html=True)

        # ── Source analytics ───────────────────────────────────────────────────
        all_sources_data = st.session_state.get("answer_sources", {})
        if all_sources_data:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div style="font-family:Syne,sans-serif;font-size:.85rem;font-weight:800;background:linear-gradient(135deg,#6358ff,#a855f7);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:.8rem;">🔗 Answer Source Analysis</div>',
                unsafe_allow_html=True)

            # Aggregate domain counts (total + weighted by question importance)
            domain_stats = {}  # domain → {total, weighted, engines}
            for q in questions:
                ck  = (q["engine"], q["question"])
                imp = q.get("importance_score", 0.3)
                for src in all_sources_data.get(ck, []):
                    dom = src.get("domain", "unknown")
                    if not dom: continue
                    if dom not in domain_stats:
                        domain_stats[dom] = {"total": 0, "weighted": 0.0,
                                             "engines": defaultdict(int),
                                             "titles": set()}
                    domain_stats[dom]["total"]            += 1
                    domain_stats[dom]["weighted"]         += imp
                    domain_stats[dom]["engines"][q["engine"]] += 1
                    t = src.get("title","")
                    if t and t != dom:
                        domain_stats[dom]["titles"].add(t[:50])

            if domain_stats:
                sorted_dom = sorted(domain_stats.items(), key=lambda x: -x[1]["weighted"])
                max_dt = max(v["total"]    for v in domain_stats.values())
                max_dw = max(v["weighted"] for v in domain_stats.values())

                sc1, sc2 = st.columns(2)
                with sc1:
                    rows = "".join(
                        bar_row_html(d, v["total"], max_dt,
                                     "linear-gradient(90deg,#0ea5e9,#6358ff)")
                        for d, v in sorted_dom[:15]
                    )
                    st.markdown(f'<div class="ana"><div class="ana-title">🌐 Sources by Total Appearances</div>{rows}</div>', unsafe_allow_html=True)

                with sc2:
                    rows = "".join(
                        bar_row_html(d, round(v["weighted"], 1), max_dw,
                                     "linear-gradient(90deg,#f97316,#ec4899)")
                        for d, v in sorted_dom[:15]
                    )
                    st.markdown(f'<div class="ana"><div class="ana-title">⚖️ Sources by Weighted Importance</div>{rows}</div>', unsafe_allow_html=True)

                # Per-engine source breakdown
                st.markdown("<br>", unsafe_allow_html=True)
                eng_src_cols = st.columns(len(selected_engines))
                for col_e, engine in zip(eng_src_cols, selected_engines):
                    cfg = ENGINES.get(engine, {})
                    eng_dom = {}
                    for d, v in domain_stats.items():
                        cnt = v["engines"].get(engine, 0)
                        if cnt: eng_dom[d] = cnt
                    max_ed = max(eng_dom.values()) if eng_dom else 1
                    rows = "".join(
                        bar_row_html(d, c, max_ed, cfg.get("color","#6358ff"))
                        for d, c in sorted(eng_dom.items(), key=lambda x: -x[1])[:8]
                    ) or '<div style="color:var(--muted);font-size:.75rem;">No sources yet</div>'
                    col_e.markdown(
                        f'<div class="ana"><div class="ana-title">{cfg.get("icon","")} {engine}</div>{rows}</div>',
                        unsafe_allow_html=True)

                # Download
                src_csv = "Domain,Total Appearances,Weighted Score," + ",".join(selected_engines) + "\n"
                for d, v in sorted_dom:
                    eng_counts = ",".join(str(v["engines"].get(e, 0)) for e in selected_engines)
                    src_csv += f'{d},{v["total"]},{v["weighted"]:.2f},{eng_counts}\n'
                st.download_button("📥 Download Sources CSV", data=src_csv,
                    file_name=f"sources_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv")
            else:
                st.info("Sources will appear here once answers are fetched.")
        else:
            st.info("💡 Enable **Auto-fetch answers** and run to see source analytics here.")

    # =========================================================================
    # TAB 5 — WEEK-ON-WEEK
    # =========================================================================
    with tab_wow:
        history     = load_history()
        ind_history = history.get(industry_choice, {})

        if not ind_history:
            st.info("📅 No historical data yet. Run the app with **Auto-fetch answers** enabled "
                    "across different weeks — snapshots are saved automatically to "
                    f"`{HISTORY_FILE}`.")
        else:
            weeks = sorted(ind_history.keys())
            st.markdown(
                f"<div style='color:var(--muted);font-size:.8rem;margin-bottom:1rem;'>"
                f"<b style='color:var(--text)'>{len(weeks)}</b> week(s) of data · "
                f"Industry: <b style='color:#c4baff;'>{clean_industry(industry_choice)}</b></div>",
                unsafe_allow_html=True)

            if len(weeks) == 1:
                st.warning("Only one week available. Run again next week for comparison.")
                data = ind_history[weeks[0]]
                max_t = max((v["total"] for v in data.values()), default=1)
                rows  = "".join(bar_row_html(b, v["total"], max_t,
                                "linear-gradient(90deg,#7c6bff,#6bffd8)")
                                for b, v in sorted(data.items(), key=lambda x: -x[1]["total"]))
                st.markdown(f'<div class="ana"><div class="ana-title">📅 {weeks[0]}</div>'
                            f'{rows}</div>', unsafe_allow_html=True)
            else:
                prev_w, curr_w = weeks[-2], weeks[-1]
                prev_data = ind_history[prev_w]
                curr_data = ind_history[curr_w]
                all_brands = sorted(set(list(prev_data) + list(curr_data)))

                st.markdown(
                    f'<div style="display:flex;gap:8px;margin-bottom:1rem;">'
                    f'<div style="background:rgba(124,107,255,.1);border:1px solid rgba(124,107,255,.3);'
                    f'padding:4px 14px;border-radius:20px;font-size:.75rem;color:#a89dff;">'
                    f'Previous: {prev_w}</div>'
                    f'<div style="background:rgba(107,255,216,.1);border:1px solid rgba(107,255,216,.3);'
                    f'padding:4px 14px;border-radius:20px;font-size:.75rem;color:#6bffd8;">'
                    f'Current: {curr_w}</div></div>', unsafe_allow_html=True)

                rows_html = ""
                for brand in all_brands:
                    pt = prev_data.get(brand, {}).get("total",    0)
                    ct = curr_data.get(brand, {}).get("total",    0)
                    pw = prev_data.get(brand, {}).get("weighted", 0.0)
                    cw = curr_data.get(brand, {}).get("weighted", 0.0)
                    dt = ct - pt; dw = cw - pw
                    dc = "wow-up" if dt > 0 else ("wow-down" if dt < 0 else "wow-flat")
                    da = f"▲ +{dt}" if dt > 0 else (f"▼ {dt}" if dt < 0 else "— 0")
                    wc = "wow-up" if dw > 0 else ("wow-down" if dw < 0 else "wow-flat")
                    wa = f"▲ +{dw:.1f}" if dw > 0 else (f"▼ {dw:.1f}" if dw < 0 else "— 0")
                    rows_html += (
                        f'<tr style="border-bottom:1px solid var(--border);">'
                        f'<td style="padding:.4rem .5rem;font-size:.8rem;color:var(--text);font-weight:600;">{brand}</td>'
                        f'<td style="padding:.4rem .5rem;font-size:.8rem;color:var(--muted);text-align:center;">{pt}</td>'
                        f'<td style="padding:.4rem .5rem;font-size:.8rem;color:var(--text);text-align:center;">{ct}</td>'
                        f'<td style="padding:.4rem .5rem;font-size:.8rem;text-align:center;" class="{dc}">{da}</td>'
                        f'<td style="padding:.4rem .5rem;font-size:.78rem;color:var(--muted);text-align:center;">{pw:.1f}</td>'
                        f'<td style="padding:.4rem .5rem;font-size:.78rem;color:var(--text);text-align:center;">{cw:.1f}</td>'
                        f'<td style="padding:.4rem .5rem;font-size:.78rem;text-align:center;" class="{wc}">{wa}</td>'
                        f'</tr>'
                    )

                ths = "padding:.45rem .5rem;font-family:'Syne',sans-serif;font-size:.62rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);text-align:center;"
                st.markdown(f"""
                <div class="ana">
                  <div class="ana-title">📈 Week-on-Week Brand Mention Comparison</div>
                  <table style="width:100%;border-collapse:collapse;">
                    <thead><tr>
                      <th style="{ths}text-align:left;">Brand</th>
                      <th style="{ths}">Total (Prev)</th><th style="{ths}">Total (Now)</th>
                      <th style="{ths}">Δ Total</th>
                      <th style="{ths}">Wtd (Prev)</th><th style="{ths}">Wtd (Now)</th>
                      <th style="{ths}">Δ Weighted</th>
                    </tr></thead>
                    <tbody>{rows_html}</tbody>
                  </table>
                </div>""", unsafe_allow_html=True)

                wow_csv = "Brand,Prev Total,Curr Total,Delta Total,Prev Weighted,Curr Weighted,Delta Weighted\n"
                for brand in all_brands:
                    pt=prev_data.get(brand,{}).get("total",0); ct=curr_data.get(brand,{}).get("total",0)
                    pw=prev_data.get(brand,{}).get("weighted",0); cw=curr_data.get(brand,{}).get("weighted",0)
                    wow_csv += f'{brand},{pt},{ct},{ct-pt},{pw:.2f},{cw:.2f},{cw-pw:.2f}\n'
                st.download_button("📥 Download WoW CSV", data=wow_csv,
                    file_name=f"wow_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv")

            if len(weeks) > 2:
                with st.expander("📅 All historical weeks"):
                    for w in reversed(weeks):
                        data  = ind_history[w]
                        max_t = max((v["total"] for v in data.values()), default=1)
                        rows  = "".join(bar_row_html(b, v["total"], max_t,
                                        "linear-gradient(90deg,#7c6bff,#6bffd8)")
                                        for b, v in sorted(data.items(), key=lambda x: -x[1]["total"]))
                        st.markdown(f'<div class="ana"><div class="ana-title">📅 {w}</div>'
                                    f'{rows}</div>', unsafe_allow_html=True)

else:
    st.markdown("""
    <div style="text-align:center;padding:4rem 2rem;">
      <div style="font-size:3.5rem;margin-bottom:1rem;">🔑</div>
      <div style="font-family:'Syne',sans-serif;font-size:1.2rem;font-weight:800;
        background:linear-gradient(135deg,#6358ff,#a855f7);-webkit-background-clip:text;
        -webkit-text-fill-color:transparent;margin-bottom:.6rem;">Ready to explore</div>
      <div style="font-size:.88rem;max-width:500px;margin:0 auto;line-height:1.8;color:#3d3d6b;">
        Type any industry in the sidebar → hit
        <b style="color:#6358ff;">Fetch Keywords & Generate Questions</b>.<br>
        Google Trends keywords for India → each engine generates ranked questions → 
        enable <b style="color:#6358ff;">Auto-fetch answers</b> to stream live responses
        and track brand mentions automatically.
      </div>
    </div>""", unsafe_allow_html=True)