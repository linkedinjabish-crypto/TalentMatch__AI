import streamlit as st
import sqlite3
import os
import time
import pdfplumber
import docx
import base64
import pandas as pd
import re
import datetime
import math
import random
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from tech_library import SKILL_LIBRARY, PRO_VERBS, STOP_WORDS
import recruiter_logic

# ================= CONFIG =================
# Offline Deterministic Keyword Engine Active + AI Enhancement Layer
st.set_page_config(page_title="TalentMatch Pro", layout="wide")

# AI Integration Layer
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.warning("⚠️ GEMINI_API_KEY not found in secrets. AI features will be limited.")
 
def cleanup_candidates():
    """Removes existing duplicates from the database keeping the most recent."""
    with get_connection() as conn:
        # 🧪 Strategy: Keep the MAX(id) (most recent) for each unique Email OR Name+Phone combo.
        # We handle '-' specifically to avoid grouping all candidates with missing emails together.
        cursor = conn.cursor()
        
        # 1. Deduplicate by Email (where email isn't '-')
        cursor.execute("""
            DELETE FROM candidates 
            WHERE email != '-' AND id NOT IN (
                SELECT MAX(id) FROM candidates WHERE email != '-' GROUP BY email
            )
        """)
        
        # 2. Deduplicate by Name + Phone (where phone isn't '-')
        cursor.execute("""
            DELETE FROM candidates 
            WHERE phone != '-' AND id NOT IN (
                SELECT MAX(id) FROM candidates WHERE phone != '-' GROUP BY name, phone
            )
        """)
        conn.commit()
    return True

# ================= UI =================
st.markdown("""
<style>
 
/* 🌌 BACKGROUND ANIMATION: MIDNIGHT AURORA */
.stApp {
    background: linear-gradient(-45deg, #0f0c29, #302b63, #24243e, #0f0c29);
    background-size: 400% 400%;
    animation: gradientBG 15s ease infinite;
}

@keyframes gradientBG {
    0% {background-position: 0% 50%;}
    50% {background-position: 100% 50%;}
    100% {background-position: 0% 50%;}
}

/* 🧾 TEXT */
h1, h2, h3 {
    color: #ffffff !important;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-shadow: 0 2px 10px rgba(0,0,0,0.3);
}



label {
    color: #e2e8f0 !important;
    font-weight: 500;
}

/* 🌈 BUTTONS: AURORA GLASS */
.stButton>button {
    width: 100%;
    height: 48px;
    font-size: 15px;
    font-weight: 600;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.15);
    color: white !important;
    background: rgba(25, 20, 45, 0.95);
    backdrop-filter: blur(16px);
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(0,0,0,0.4);
}

/* HOVER ANIMATION */
.stButton>button:hover {
    background: rgba(255, 255, 255, 0.15);
    transform: translateY(-3px) scale(1.01);
    box-shadow: 0 8px 25px rgba(138, 43, 226, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.3);
}

/* 🧊 GLASS CARD */
.card {
    background: rgba(15, 10, 30, 0.85);
    padding: 22px;
    border-radius: 16px;
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.1);
    box-shadow: 0 10px 30px rgba(0,0,0,0.6);
    margin-bottom: 20px;
}

/* INPUT */
.stTextInput input, .stTextArea textarea {
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.2) !important;
    background-color: rgba(5, 5, 15, 0.8) !important;
    color: white !important;
    transition: all 0.3s ease;
}

.stTextInput input:focus, .stTextArea textarea:focus {
    border: 1px solid #a855f7 !important;
    box-shadow: 0 0 0 3px rgba(168, 85, 247, 0.25) !important;
}

/* TABLE */
.stDataFrame {
    border-radius: 14px;
    overflow: hidden;
    background: rgba(10, 5, 20, 0.9);
    border: 1px solid rgba(255,255,255,0.1);
}

/* FADE IN ANIMATION */
div[data-testid="stVerticalBlock"] > div {
    animation: gentleFade 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
}

@keyframes gentleFade {
    0% {opacity: 0; transform: translateY(15px);}
    100% {opacity: 1; transform: translateY(0);}
}

/* GLOWING PULSE FOR HERO */
@keyframes glowingPulse {
    0% {text-shadow: 0 0 10px #a855f7, 0 0 20px #a855f7; opacity: 0.8;}
    50% {text-shadow: 0 0 20px #3b82f6, 0 0 30px #3b82f6; opacity: 1;}
    100% {text-shadow: 0 0 10px #a855f7, 0 0 20px #a855f7; opacity: 0.8;}
}

@keyframes floatHero {
    0% {transform: translateY(0px);}
    50% {transform: translateY(-8px);}
    100% {transform: translateY(0px);}
}

@keyframes scanLine {
    0% { top: 5%; opacity: 0; }
    10% { opacity: 1; }
    90% { opacity: 1; }
    95% { top: 90%; opacity: 0; }
    100% { top: 5%; opacity: 0; }
}
/* 🚫 HIDE STREAMLIT CHROME (Maintain header for sidebar toggle) */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

</style>
""", unsafe_allow_html=True)
 
# ================= LOGIN STATE =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
 
# ================= LOGIN =================
if not st.session_state.get('logged_in', False):
    try:
        with open("assets/doodles_bg.png", "rb") as image_file:
            doodle_b64 = base64.b64encode(image_file.read()).decode()
        st.markdown(f"""
        <style>
        /* Force steady layout without scrollbars on the login view */
        .stApp, .main, .block-container {{
            overflow: hidden !important;
        }}
        html, body {{
            overflow: hidden !important;
        }}
        /* Disable top whitespace */
        .block-container {{
            padding-top: 1rem !important;
            padding-bottom: 0 !important;
            max-width: 100% !important;
        }}
        .stApp::before {{
            content: "";
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            background: url(data:image/png;base64,{doodle_b64});
            background-size: 800px;
            opacity: 0.3;
            -webkit-mask-image: linear-gradient(to bottom, black 0%, transparent 50%);
            mask-image: linear-gradient(to bottom, black 0%, transparent 50%);
            pointer-events: none;
            z-index: -1;
        }}
        </style>
        """, unsafe_allow_html=True)
    except: pass

    col_img, col_login = st.columns([0.9, 1.3], gap="large")
    
    with col_img:
        try:
            with open("assets/hero.png", "rb") as image_file:
                hero_b64 = base64.b64encode(image_file.read()).decode()
            st.markdown(f"""
            <div style='animation: floatHero 6s ease-in-out infinite; text-align: center; position: relative;'>
                <img src='data:image/png;base64,{hero_b64}' style='width: 100%; border-radius: 16px;' />
                <div style='position: absolute; left: 5%; width: 90%; height: 3px; background: #a855f7; box-shadow: 0 0 15px 6px rgba(168, 85, 247, 0.7); animation: scanLine 3s ease-in-out infinite;'></div>
            </div>
            """, unsafe_allow_html=True)
        except Exception:
            st.image("assets/hero.png", use_container_width=True)
            
        st.markdown("<h3 style='margin-top: 15px; font-size: 22px; text-align:center; font-weight: 700; color: #e2e8f0; animation: glowingPulse 3s infinite;'>TalentMatch is parsing resumes...<br><span style='color: #cbd5e1; font-weight: 400;'>Sit back and grab a coffee</span></h3>", unsafe_allow_html=True)

    with col_login:
        st.markdown("""
        <style>
        /* ── LOGIN CARD: style the column container itself ── */
        div[data-testid="column"]:nth-child(2) [data-testid="stVerticalBlock"] {
            background: rgba(12, 8, 30, 0.92) !important;
            border: 1px solid rgba(168, 85, 247, 0.3) !important;
            border-radius: 20px !important;
            padding: 30px 32px 24px 32px !important; 
            backdrop-filter: blur(24px) !important;
            box-shadow: 0 8px 48px rgba(0,0,0,0.65) !important;
        }
        .login-field-label {
            font-size: 11px;
            color: #64748b;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 3px;
            margin-top: 2px;
        }
        .login-divider {
            border: none;
            border-top: 1px solid rgba(255,255,255,0.07);
            margin: 18px 0 16px 0;
        }
        .trust-row {
            display: flex;
            justify-content: center;
            gap: 18px;
            margin-top: 18px;
            padding-top: 14px;
            border-top: 1px solid rgba(255,255,255,0.1);
        }
        .trust-item { font-size: 11px; color: #94a3b8; }
        .login-foot {
            text-align: center;
            font-size: 11px;
            color: #64748b;
            margin-top: 12px;
            letter-spacing: 0.5px;
        }
        /* Login button — restore original purple gradient */
        .stButton > button {
            background: linear-gradient(135deg, #7c3aed, #a855f7) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            font-size: 15px !important;
            font-weight: 700 !important;
            letter-spacing: 0.4px !important;
            height: 46px !important;
            width: 100% !important;
            box-shadow: 0 4px 20px rgba(168,85,247,0.45) !important;
            transition: all 0.2s ease !important;
        }
        .stButton > button:hover {
            background: linear-gradient(135deg, #6d28d9, #c084fc) !important;
            box-shadow: 0 6px 28px rgba(168,85,247,0.65) !important;
            transform: translateY(-2px) !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # ── Brand Header ──
        st.markdown("""
        <div style='text-align:center; padding-bottom:12px;'>
            <div style='font-size:32px; font-weight:900; color:#ffffff; letter-spacing:-1px; margin-bottom: 2px;'>
                Talent<span style='color:#a855f7;'>Match</span>
                <span style='color:#a855f7; font-size:16px; font-weight:800; vertical-align: super; margin-left: 2px; opacity: 0.9;'>PRO</span>
            </div>
            <div style='font-size:13px; color:#94a3b8; font-weight:500; letter-spacing:1px; text-transform: uppercase; opacity: 0.8;'>
                Recruiter Intelligence Platform
            </div>
            <div style='margin-top: 12px; display: flex; justify-content: center;'>
                <div style='background: rgba(168, 85, 247, 0.08); border: 1px solid rgba(168, 85, 247, 0.3); 
                     color: #a855f7; padding: 4px 12px; border-radius: 6px; font-size: 10px; font-weight: 700; 
                     letter-spacing: 0.5px; text-transform: uppercase; box-shadow: 0 0 10px rgba(168, 85, 247, 0.1);'>
                    ✨ A Recruiter Friendly Tool
                </div>
            </div>
        </div>
        <div style='height: 1px; background: linear-gradient(to right, transparent, rgba(255,255,255,0.1), transparent); margin: 20px 0;'></div>
        """, unsafe_allow_html=True)

        # ── Fields ──
        st.markdown("<div class='login-field-label'>Username</div>", unsafe_allow_html=True)
        username = st.text_input("u", placeholder="Enter your username", label_visibility="collapsed")

        st.markdown("<div class='login-field-label' style='margin-top:10px;'>Password</div>", unsafe_allow_html=True)
        password = st.text_input("p", type="password", placeholder="••••••••", label_visibility="collapsed")

        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

        # ── Button + Error ──
        if st.button("Access Dashboard →", use_container_width=True):
            if username == "admin" and password == "1234":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.markdown("""
                <div style='background:rgba(239,68,68,0.1); border:1px solid rgba(239,68,68,0.3);
                     border-radius:8px; padding:9px 14px; font-size:13px; color:#f87171; margin-top:6px;'>
                    ⚠️ Invalid credentials. Please try again.
                </div>
                """, unsafe_allow_html=True)

        # ── Footer ──
        st.markdown("""
        <div class='trust-row' style='margin-top: 10px; padding-top: 10px;'>
            <span class='trust-item'>🔒 Intelligence-Driven</span>
            <span class='trust-item'>🔒 Intelligence-Driven</span>
            <span class='trust-item'>🛡️ Privacy</span>
        </div>
        <div class='login-foot' style='margin-top: 8px;'>© 2025 TalentMatch · Powered by Marvel Technologies</div>
        """, unsafe_allow_html=True)

 
    st.stop()
   
# ================= SIDEBAR =================
with st.sidebar:
    st.image("assets/logo.png", use_container_width=True)
    st.markdown("<div style='margin-top: -20px; text-align: center; font-size: 11px; color: #64748b; font-weight: 500; letter-spacing: 1px; text-transform: uppercase;'>Recruitment Intelligence</div>", unsafe_allow_html=True)
    st.markdown("<hr style='border: 1px solid rgba(255,255,255,0.05); margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)
    st.markdown("<div style='color: #a855f7; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 15px;'>Main Navigation</div>", unsafe_allow_html=True)
    
    if st.button("🏠 Home Dashboard", use_container_width=True):
        st.session_state.page = "home"
        st.rerun()
    if st.button("🔍 Smart Evaluation", use_container_width=True):
        st.session_state.page = "eval"
        st.rerun()
    if st.button("👥 Internal DB", use_container_width=True):
        st.session_state.page = "internal"
        st.rerun()
    if st.button("📝 Interview Questions", use_container_width=True):
        st.session_state.page = "ai"
        st.rerun()
    if st.button("📚 Job Library", use_container_width=True):
        st.session_state.page = "jd_library"
        st.rerun()


# ================= STATE =================
if "page" not in st.session_state:
    st.session_state.page = "home"
 
if "preview_id" not in st.session_state:
    st.session_state.preview_id = None

if "eval_results" not in st.session_state:
    st.session_state.eval_results = None
 
# ================= DB =================
def get_connection():
    return sqlite3.connect("database.db")

import contextlib
import time
import recruiter_logic

@contextlib.contextmanager
def custom_ai_loading(message="TalentMatch is actively processing..."):
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("<div style='text-align: center; margin: 40px 0; animation: gentleFade 0.5s ease-in;'>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='color: #a855f7; margin-top: 15px; animation: glowingPulse 2s infinite;'>{message}</h3>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        with st.spinner(""):
            yield
    placeholder.empty()

with get_connection() as conn:
    conn.execute("""
    CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    phone TEXT,
    resume_path TEXT,
    resume_text TEXT,
    matching TEXT,
    missing TEXT,
    score INTEGER,
    decision TEXT,
    reason TEXT,
    jd TEXT
)
    """)
 
    conn.execute("""
    CREATE TABLE IF NOT EXISTS job_descriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        jd TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS candidate_tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_id INTEGER NOT NULL,
        jd_id INTEGER NOT NULL,
        tagged_date TEXT,
        UNIQUE(candidate_id, jd_id)
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS candidate_attachments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_id INTEGER NOT NULL,
        filename TEXT,
        filepath TEXT,
        filesize INTEGER,
        uploaded_date TEXT
    )
    """)

    # Apply Database Schema migrations dynamically safely
    for col in ["linkedin", "uploaded_date", "expected_rate", "designation", "location"]:
        try:
            conn.execute(f"ALTER TABLE candidates ADD COLUMN {col} TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass
 
# ================= FOLDER =================
if not os.path.exists("resumes"):
    os.makedirs("resumes")
if not os.path.exists("attachments"):
    os.makedirs("attachments")
 
# ================= FUNCTIONS =================
def extract_text(path):
    text = ""
    if path.endswith(".pdf"):
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
    elif path.endswith(".docx"):
        doc = docx.Document(path)
        text = "\n".join([p.text for p in doc.paragraphs])
    return text.lower()
 
def extract_email(text):
    e = re.findall(r'\S+@\S+', text)
    return e[0] if e else "-"
 
def extract_phone(text):
    p = re.findall(r'\+?\d[\d\s\-]{9,}', text)
    return p[0] if p else "-"

def extract_location(text):
    """
    Multi-strategy location extractor.
    Looks for: explicit label, City/State patterns, known city list, country names.
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # Strategy 1: Explicit label — "Location:", "Address:", "City:"
    for line in lines[:25]:
        m = re.match(r'^(location|address|city|city[,/\s]state|residing at)[:\s]+(.+)', line, re.IGNORECASE)
        if m:
            val = m.group(2).strip()
            if 3 < len(val) < 80:
                return val.title()

    # Strategy 2: "City, State" or "City, Country" pattern
    m2 = re.search(r'([A-Z][a-z]{2,20}),\s*([A-Z][a-z]{2,20}|[A-Z]{2})', text)
    if m2:
        return m2.group(0).strip()

    # Strategy 3: Match known Indian cities
    indian_cities = [
        "Mumbai", "Delhi", "Bengaluru", "Bangalore", "Hyderabad", "Chennai",
        "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Surat", "Lucknow",
        "Kanpur", "Nagpur", "Indore", "Coimbatore", "Kochi", "Patna",
        "Bhopal", "Vadodara", "Gurgaon", "Gurugram", "Noida", "Chandigarh",
        "Mysore", "Mysuru", "Thiruvananthapuram", "Vizag", "Visakhapatnam",
        "Madurai", "Nashik", "Faridabad", "Meerut", "Rajkot", "Amritsar",
        "Varanasi", "Agra", "Thane", "Navi Mumbai", "Aurangabad", "Jodhpur",
    ]
    for city in indian_cities:
        if re.search(r'\b' + city + r'\b', text, re.IGNORECASE):
            return city

    # Strategy 4: Country match
    countries = ["India", "USA", "UK", "Canada", "Australia", "Germany", "Singapore", "UAE"]
    for country in countries:
        if re.search(r'\b' + country + r'\b', text, re.IGNORECASE):
            return country

    return "-"

 
def extract_name(text, filename=""):
    """
    Multi-strategy name extractor. Never returns 'Unknown Candidate'.
    Strategy 1: Look for explicit 'Name:' label
    Strategy 2: Find 2-3 properly capitalized words in first 10 lines (classic name pattern)
    Strategy 3: Derive from filename
    Strategy 4: Return generic 'Candidate'
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    
    # SKIP LIST — lines that are headers, not names
    skip_words = {
        "resume", "curriculum vitae", "c.v", "cv", "profile", "summary",
        "contact", "objective", "experience", "education", "skills",
        "address", "email", "phone", "mobile", "linkedin", "github",
        "declaration", "references", "projects", "certifications"
    }
    
    # --- Strategy 1: Explicit "Name:" label (Priority Search) ---
    for line in lines[:8]:
        if re.match(r'^(full\s*)?name\s*[:\-]', line, re.IGNORECASE):
            name_val = re.sub(r'^(full\s*)?name\s*[:\-]\s*', '', line, flags=re.IGNORECASE).strip()
            if 3 < len(name_val) < 50:
                return name_val.title()
    
    # --- Strategy 2: First-Line Priority (Top of Resume) ---
    for line in lines[:3]:
        clean = line.strip()
        # Regex for 2-3 capitalized words (Classic Resume Name)
        if re.match(r'^([A-Z][a-z]+(?:\s[A-Z][a-z]+){1,2})$', clean):
            if clean.lower() not in skip_words:
                return clean
    
    # --- Strategy 2: Pattern — 2 or 3 capitalized words, no numbers, not a skip word ---
    name_pattern = re.compile(r'^([A-Z][a-z]+(?:\s[A-Z][a-z]+){1,3})$')
    for line in lines[:12]:
        clean = line.strip()
        # Must be 3-40 chars, no digits, no special chars except space/dot/hyphen
        if not (3 < len(clean) < 45):
            continue
        if any(c.isdigit() for c in clean):
            continue
        if clean.lower().split()[0] in skip_words:
            continue
        if re.search(r'[@|•|:|\|/\\]', clean):
            continue
        # Match classic name: 2–4 capitalized words
        if name_pattern.match(clean):
            return clean
    
    # --- Strategy 3: Loose heuristic — first short clean line that looks like a name ---
    for line in lines[:10]:
        clean = line.strip()
        if not (4 < len(clean) < 40):
            continue
        words = clean.split()
        if len(words) < 2 or len(words) > 4:
            continue
        if any(c.isdigit() for c in clean):
            continue
        if clean.lower().split()[0] in skip_words:
            continue
        if all(w[0].isupper() for w in words if w):
            return clean
    
    # --- Strategy 4: Derive from filename ---
    if filename:
        base = re.sub(r'\.(pdf|docx|doc|txt)$', '', filename, flags=re.IGNORECASE)
        base = re.sub(r'[_\-\d]+', ' ', base).strip()
        # Remove common resume suffixes
        base = re.sub(r'\b(resume|cv|application|updated|final|new)\b', '', base, flags=re.IGNORECASE).strip()
        if len(base) > 2:
            return base.title()
    
    return "Candidate"

def extract_linkedin(text):
    ln = re.findall(r'linkedin\.com/in/[a-zA-Z0-9_-]+', text, re.IGNORECASE)
    return "https://" + ln[0] if ln else ""

def extract_designation(text):
    t = text.lower()
    mapping = {
        'data scientist': ['data scientist', 'machine learning', 'deep learning'],
        'python developer': ['python developer', 'python engineer', 'backend developer'],
        'java developer': ['java developer', 'java engineer', 'spring boot'],
        'frontend developer': ['frontend', 'react', 'angular', 'vue', 'ui developer'],
        'backend developer': ['backend', 'node', 'django', 'flask', 'php'],
        'full stack developer': ['full stack', 'mern', 'mean'],
        'devops engineer': ['devops', 'kubernetes', 'docker', 'aws', 'cloud engineer'],
        'qa engineer': ['qa engineer', 'tester', 'automation tester', 'quality assurance'],
        'tech lead': ['lead', 'manager', 'architect']
    }
    for role, needles in mapping.items():
        if any(needle in t for needle in needles):
            return role.title()
    return 'Uncategorized'

def extract_experience_years(text):
    if not text: return 0
    patterns = [
        r'(?:over|at least|more than|minimum of|approx|around)\s*(\d+)\+?\s*years?',
        r'(\d+)\+?\s*years?\s*(?:of)?\s*exp',
        r'(\d+)\+?\s*years?',
        r'(\d+)\+?\s*yrs?',
        r'experience\s*of\s*(\d+)',
        r'(\d+)\s*years?\s*of\s*experience'
    ]
    years = []
    t = text.lower()
    for p in patterns:
        matches = re.findall(p, t)
        years.extend([int(m) for m in matches])
    
    # 🧠 Fallback: Tenure Heuristic (e.g. 2018 - 2024 = 6 yrs)
    if not years:
        found_years = [int(y) for y in re.findall(r'\b(20[0-2][0-9]|19[8-9][0-9])\b', t)]
        if found_years:
            tenure = max(found_years) - min(found_years)
            if 0 < tenure < 40:
                years.append(tenure)

    # Filter out year numbers like 2023, 2024
    years = [y for y in years if y < 50]
    return max(years) if years else 0

def extract_domain(text):
    domains = {
        'Fintech': ['bank', 'finance', 'trading', 'payment', ' fintech'],
        'Healthcare': ['health', 'medical', 'hospital', 'pharma'],
        'E-commerce': ['shop', 'retail', 'e-commerce', 'ecommerce', 'marketplace'],
        'Software/Tech': ['software', 'technology', 'saas', 'cloud'],
        'Education': ['edtech', 'education', 'school', 'university']
    }
    t = text.lower()
    for d, needles in domains.items():
        if any(n in t for n in needles):
            return d
    return 'General Tech'

def extract_career_growth(text):
    progression = ['junior', 'trainee', 'associate', 'senior', 'lead', 'principal', 'head', 'vp', 'cto']
    found = []
    for p in progression:
        if p in text.lower():
            found.append(progression.index(p))
    if len(found) > 1 and found[-1] > found[0]:
        return "Positive Growth"
    return "Stable" if len(found) > 0 else "Baseline"

def calculate_stability(text):
    # Regex to find date ranges (approximate)
    dates = re.findall(r'(20\d{2}|19\d{2})', text)
    if not dates: return 100
    # If many unique years in a short text, it might be job hopping
    unique_years = len(list(set(dates)))
    if unique_years > 8: return 100 # Long career
    if unique_years > 1 and (len(dates) / unique_years) > 2.5:
        return 40 # High frequency of dates relative to years
    return 80

def evaluate_company_quality(text):
    product_tier = ['google', 'amazon', 'microsoft', 'netflix', 'facebook', 'apple', 'uber', 'airbnb', 'goldman']
    service_tier = ['tcs', 'infosys', 'wipro', 'accenture', 'capgemini', 'cognizant', 'hcl']
    t = text.lower()
    if any(p in t for p in product_tier): return "Product Tier"
    if any(s in t for s in service_tier): return "Service Tier"
    if 'startup' in t or 'series' in t: return "Startup"
    return "Standard"

def analyze_skill_depth(text, skill):
    t = text.lower()
    depth_words = ["architect", "lead", "optimized", "scaled", "expert", "mastered"]
    basic_words = ["knowledge", "basics", "familiar", "learning", "exposure"]
    
    # Simple proximity check
    if skill in t:
        idx = t.find(skill)
        snippet = t[max(0, idx-50):min(len(t), idx+50)]
        if any(d in snippet for d in depth_words): return 100 # Deep
        if any(b in snippet for b in basic_words): return 30 # Basic
        return 70 # Competent
    return 0

def detect_project_evidence(text):
    action_verbs = ["built", "developed", "implemented", "scaled", "optimized", "architected", "delivered"]
    metrics = [r'\d+%', r'\$\d+', r'\d+\+', r'users']
    t = text.lower()
    verb_count = sum(1 for v in action_verbs if v in t)
    metric_count = sum(1 for m in metrics if re.search(m, t))
    
    score = (verb_count * 10) + (metric_count * 15)
    return min(100, score)

def boolean_search(df, query):
    def check(text):
        if not text or not isinstance(text, str):
            return False
        text = text.lower()
        
        # Break the query into logic operators and search keywords
        tokens = re.split(r'\b(AND|OR|NOT)\b|(\()|(\))', query, flags=re.IGNORECASE)
        
        expr = ""
        for t in tokens:
            if t is None: 
                continue
            ts = t.strip().lower()
            if not ts: 
                continue
                
            if ts in ['and', 'or', 'not', '(', ')']:
                expr += f" {ts} "
            else:
                ts_escaped = ts.replace("'", "\\'")
                expr += f" ('{ts_escaped}' in text) "
                
        try:
            return eval(expr)
        except:
            return False

    # Check against the resume text
    return df[df["Text"].apply(check)]
 
# ================= OFFLINE RULE-BASED ENGINE =================

SYNONYMS = {
    "js": "javascript", "py": "python", "reactjs": "react", "node.js": "node", "nodejs": "node",
    "k8s": "kubernetes", "aws": "amazon web services", "gcp": "google cloud", "ms azure": "azure",
    "ml": "machine learning", "ai": "artificial intelligence", "mern": "mongodb express react node",
    "mean": "mongodb express angular node", "nextjs": "next.js", "vuejs": "vue", "native": "react native",
    "ts": "typescript", "microservices": "microservices architecture", "ci/cd": "continuous integration",
    "qa": "quality assurance", "sdet": "software developer in test", "llm": "large language models",
    "rag": "retrieval augmented generation"
}



def analyze_impact_score(text):
    """Calculates an authority/achievement score based on metrics and action verbs."""
    if not text: return 0
    t = text.lower()
    
    # 1. Metric Detection (Numbers, Percentages, Currency)
    metrics = re.findall(r"(\d+%|\$\d+|\d+\+?\s*(?:million|billion|users|clients|customers|requests|transactions))", t)
    metric_points = min(50, len(metrics) * 10) # Max 50 points from metrics
    
    # 2. Action Verb Detection
    verb_count = sum(1 for v in PRO_VERBS if v in t)
    verb_points = min(50, verb_count * 5) # Max 50 points from verbs
    
    return metric_points + verb_points


def profile_tech_domain(text):
    if not text: return {}
    t = text.lower(); profile = {}
    for cat, needles in SKILL_LIBRARY.items():
        count = sum(1 for n in needles if n in t)
        if count > 0: profile[cat] = count
    sorted_p = sorted(profile.items(), key=lambda x: x[1], reverse=True)
    return {k: v for k, v in sorted_p[:3]}

# 💼 ELITE RECRUITER GRADE FILTERS
INVALID_SKILLS = {
    "collaboration", "communication", "teamwork", "stakeholders", "management", "support",
    "business", "process", "operations", "system", "data", "various", "multiple", "across",
    "generation", "new", "next", "solutions", "good", "strong", "knowledge", "ability"
}

# 🚫 PRO-RECRUITER BLOCKED SKILLS (Purge AI Buzzwords/Concepts)
BLOCKED_SKILLS = {
    "gpt", "openai", "claude", "gemini", "llm", "unstructured", "prompt", 
    "generation", "rag", "langchain", "llamaindex", "transformers", "bert"
}

CORE_SKILLS = {"python", "aws", "docker", "kubernetes", "sql"}

# Pre-compute Elite Tech-Only Whitelist (Comprehensive 1250+ Expansion)
ELITE_CATEGORIES = [
    "Backend Technologies", "Frontend Technologies", "Cloud Platforms", 
    "DevOps & Tools", "Databases", "Data & Analytics", "Security", 
    "Mobile Development", "Testing", "Architecture & Design",
    "Industry Verticals", "Enterprise Software & ERP", 
    "Networking & Infrastructure", "Embedded & Hardware", 
    "Compliance & Quality"
]

VALID_SKILLS_LIST = []
for cat, skills in SKILL_LIBRARY.items():
    if cat in ELITE_CATEGORIES:
        VALID_SKILLS_LIST.extend([s.lower() for s in skills])
VALID_SKILLS = set(VALID_SKILLS_LIST)

def extract_skills(text):
    if not text: return set()
    text = text.lower()
    found = set()
    
    # We only iterate through the pre-computed VALID_SKILLS whitelist
    for skill in VALID_SKILLS:
        if skill in BLOCKED_SKILLS: continue
        # Regex for whole-word boundary check
        if re.search(r'\b' + re.escape(skill) + r'\b', text):
            if skill not in INVALID_SKILLS:
                found.add(skill)
                    
    return found

def extract_keywords(text):
    """Legacy wrapper for backward compatibility, now uses strict tech extraction"""
    return extract_skills(text)

def smart_extract_skills(text):
    if not text: return []
    t = text.lower()
    
    # 1. PRIORITY PHRASE EXTRACTION
    # Look for content after priority markers
    priority_markers = [
        r"(?:must\s+have|required|strong\s+experience\s+in|looking\s+for|hands-on\s+experience\s+with)\s+([^.\n,]{5,50})",
        r"(?:skills?|technologies?|stack)\s*(?::|-)?\s*([^.\n,]{5,50})"
    ]
    
    found_phrases = []
    for pattern in priority_markers:
        matches = re.findall(pattern, t)
        for m in matches:
            # Clean match
            clean_m = m.strip().split(",")[0].split("and")[0].strip()
            if len(clean_m) > 3:
                found_phrases.append(clean_m)
    
    # 2. ADD GENERIC KEYWORDS (WEIGHTED)
    keywords = list(extract_keywords(text))
    # Filter for known technical terms (heuristic: length and context)
    tech_keywords = [k for k in keywords if len(k) > 3]
    
    # 3. COMBINE AND SORT BY RELEVANCE (QUICK WIN HEURISTIC: LENGTH)
    combined = list(set(found_phrases + tech_keywords))
    # Sort by length to prioritize phrases over single words
    sorted_skills = sorted(combined, key=len, reverse=True)
    
    return sorted_skills[:10]

def categorize_skills(skills):
    if not skills: return {}
    result = {cat: [] for cat in SKILL_LIBRARY}
    for skill in skills:
        s = skill.lower()
        for cat, needles in SKILL_LIBRARY.items():
            if any(n in s for n in needles):
                result[cat].append(skill)
                break
    return {k: v for k, v in sorted(result.items(), key=lambda x: len(x[1]), reverse=True) if v}

def calculate_semantic_similarity(jd, resume):
    try:
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf = vectorizer.fit_transform([jd, resume])
        return cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0] * 100
    except:
        return 0

def rule_based_analysis(jd, resume, candidate_id):
    jd_text = jd.lower()
    resume_text = resume.lower()
    
    # 1. Domain Coverage (Master Mapping Upgrade)
    jd_profile = profile_tech_domain(jd)
    res_profile = profile_tech_domain(resume)
    target_cats = list(jd_profile.keys())
    if target_cats:
        cat_matches = sum(1 for c in target_cats if c in res_profile)
        category_score = (cat_matches / len(target_cats)) * 100
    else:
        category_score = 75

    # 1. Skills Match (30%) - ELITE RECRUITER LOGIC
    # Both JD and Resume use the same strict Tech-Only Extraction
    jd_skills = extract_skills(jd)
    resume_skills = extract_skills(resume)
    
    # Strict matching - Only show JD-relevant engineering skills
    matched = jd_skills.intersection(resume_skills)
    missing = jd_skills.difference(resume_skills)
    
    # Elite Truncation: 8 for match, 5 for missing (as per Final Polish instruction)
    matched_skills_list = sorted(list(matched))[:8]
    missing_skills_list = sorted(list(missing))[:5]
    # --- AI Calibrated Scoring Logic (Matching ChatGPT Reasoning) ---
    # 1. Soft-Linear Skills Match (Boosted Baseline)
    # A person with 50% technical match is often an 80% human match given learning agility
    skill_score = min(100, (len(matched) / len(jd_skills) * 125) + 15) if jd_skills else 0
    
    # 2. Experience Match (Generous Curve)
    jd_exp = extract_experience_years(jd)
    res_exp = extract_experience_years(resume)
    if jd_exp == 0: exp_score = 100
    else:
        diff = res_exp - jd_exp
        if diff >= 0: exp_score = 100
        else: exp_score = max(0, 100 + (diff * 15)) # Lower penalty per missing year
        
    # 3. Role Relevance (Professional Flexibility)
    jd_role = extract_designation(jd)
    res_role = extract_designation(resume)
    role_score = 100 if jd_role == res_role else (75 if res_role != 'Uncategorized' else 40)
    
    # 4. Domain Fit (Transferability Focus)
    jd_domain = extract_domain(jd)
    res_domain = extract_domain(resume)
    domain_score = 100 if jd_domain == res_domain else 65
    
    # 5. Evidence Checks (Static weights)
    project_score = detect_project_evidence(resume)
    depth_scores = [analyze_skill_depth(resume, s) for s in list(matched)[:3]]
    depth_score = (sum(depth_scores) / len(depth_scores)) if depth_scores else 50
    stability_score = calculate_stability(resume)
    company_type = evaluate_company_quality(resume)
    company_score = 100 if company_type == "Product Tier" else (80 if company_type == "Startup" else 60)
    
    # --- Final Weighted Blending (Semantic-First Priority) ---
    # Rule-based foundation (Reduced weight to 45% to allow Semantic Intelligence to lead)
    keyword_score = (
        (skill_score * 0.35) + 
        (exp_score * 0.20) + 
        (role_score * 0.15) + 
        (domain_score * 0.10) + 
        (project_score * 0.10) + 
        (depth_score * 0.05) + 
        (stability_score * 0.02) + 
        (company_score * 0.03)
    )
    
    # Semantic Score (TF-IDF Understanding) - INCREASED WEIGHT
    semantic_score = calculate_semantic_similarity(jd, resume)
    
    # 6. Pro-Recruiter Cognitive Layer (Stability, Growth, Density)
    stability_val = recruiter_logic.analyze_stability_score(resume)
    growth_val = recruiter_logic.analyze_career_growth(resume)
    density_val = recruiter_logic.analyze_seniority_density(resume, jd)
    
    # --- Final Weighted Blending (Pro-Recruiter Calibration) ---
    # Keywords (25%) + Category (15%) + Impact (20%) + Semantic (20%) + Pro-Logic (20%)
    weighted_keyword = keyword_score * 0.25
    weighted_category = category_score * 0.15
    authority_score = analyze_impact_score(resume)
    weighted_authority = authority_score * 0.20
    weighted_semantic = semantic_score * 0.20
    weighted_pro = ((stability_val + growth_val + density_val) / 3) * 0.20
    
    final_score = int(weighted_keyword + weighted_category + weighted_authority + weighted_semantic + weighted_pro)
    
    # 7. Strategic Core Skill Boost (Senior Recruiter Logic)
    # Grant +5 point bonus if any industry elite skills are found
    if any(s in resume_skills for s in CORE_SKILLS):
        final_score = min(100, final_score + 5)
    
    # Consistency Offset (LLM-style baseline shift)
    if semantic_score > 60:
        final_score = max(final_score, int(semantic_score + 5))
    
    # Red Flags & Insights
    insights = recruiter_logic.get_recruiter_insights(resume, jd, final_score)
    
    # Confidence Score Heuristic
    conf_raw = 100
    if not matched: conf_raw -= 40
    if len(resume.split()) < 200: conf_raw -= 30
    confidence = "High" if conf_raw > 80 else ("Medium" if conf_raw > 50 else "Low")
    
    # Decision Logic (Tiered Classification)
    if final_score >= 85: decision = "Very Strong"
    elif final_score >= 70: decision = "Strong"
    elif final_score >= 50: decision = "Backup"
    else: decision = "Not a Match"
    
    # ================= TIER 2 RECRUITER VERDICT & CLIENT NOTES =================
    # 🎯 Verdict: Immediate Recruiter Justification (Visible on Card)
    verdict_pt = f"**{decision}** choice due to {', '.join(matched_skills_list[:2])} mastery." if matched_skills_list else f"Reflects a **{decision}** technical alignment."
    if res_exp >= jd_exp and jd_exp > 0:
        verdict_pt += f" Experience ({res_exp}yr) fits the {jd_exp}yr senior requirement."
    else:
        verdict_pt += f" Foundational candidate with {res_exp}yr relevant tenure."

    # 💼 Client Notes: Formal Professional Narrative (Under Toggle)
    client_paras = [
        f"Candidate {res_name} presents a compelling professional profile with approximately {res_exp}+ years of relevant technical experience.",
        f"Key technical strengths and areas of expertise include: {', '.join(matched_skills_list[:6])}." if matched_skills_list else "They demonstrate a versatile understanding of the required software engineering stack.",
        f"This profile represents a {final_score}% match against the core job description requirements."
    ]
    if missing_skills_list:
        client_paras.append(f"Primary areas for development and scaling include: {', '.join(missing_skills_list[:3])}.")
    else:
        client_paras.append("No critical technical gaps were identified for this specific role and requirements.")
        
    client_paras.append(f"**Recommendation**: We suggest this candidate as a {decision} fit for your current technical needs.")
    client_notes = " ".join(client_paras)
    
    return f"""Candidate Name: {res_name}
Match Score: {final_score}%
Decision: {decision}
Recruiter Verdict: {verdict_pt}
Client Notes: {client_notes}
Matching Skills: {", ".join(matched_skills_list) if matched_skills_list else "None"}
Missing Skills: {", ".join(missing_skills_list) if missing_skills_list else "No critical technical gaps identified for this specific role"}
"""

def generate_eval_csv(results):
    import io, csv
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
    # Header
    writer.writerow(["Candidate Name", "Match Score", "Decision", "Recruiter Verdict", "Matching Skills", "Missing Skills", "Client Notes"])
    
    for res in results:
        m_skills = "; ".join(res.get('matching_skills', []))
        x_skills = "; ".join(res.get('missing_skills', []))
        writer.writerow([
            res['name'], 
            f"{res['score']}%", 
            res['decision'], 
            res.get('verdict', ''), 
            m_skills, 
            x_skills, 
            res['summary'] # Client Notes
        ])
    return output.getvalue()

def rule_based_questions(jd):
    if not jd: return "Please provide a Job Description to generate relevant interview questions."
    
    # 🧠 1. SMART EXTRACTION & CATEGORIZATION
    # Priority to phrases like "must have", "required"
    all_skills = smart_extract_skills(jd)
    categories = categorize_skills(all_skills)
    
    # Flatten top skills from categories for display
    display_skills = []
    for cat in categories:
        display_skills.extend(categories[cat][:2])
    if not display_skills: display_skills = all_skills[:5]
    
    # 🧠 2. QUESTION REPOSITORY (PHRASE-BARE TEMPLATES)
    TECH_TEMPLATES = {
        "Backend": [
            "Explain how you have designed and optimized {skill} systems for high availability.",
            "Describe your experience in building scalable architectures using {skill}.",
            "How do you handle performance bottlenecks and memory management when working with {skill}?"
        ],
        "Frontend": [
            "How do you ensure high performance and smooth user experience in {skill} applications?",
            "Describe your experience with {skill} state management and component lifecycle optimization.",
            "How do you handle complex UI interactions and cross-browser compatibility using {skill}?"
        ],
        "Cloud": [
            "Describe your experience in deploying and managing {skill} infrastructure for production-grade apps.",
            "How do you handle cloud security, IAM, and cost optimization when working with {skill}?",
            "Explain your process for architecting high-availability and disaster recovery solutions on {skill}."
        ],
        "Database": [
            "How do you optimize {skill} queries and indexing strategies for datasets with millions of records?",
            "Describe your experience with {skill} schema design and data consistency patterns.",
            "How do you handle database migrations and zero-downtime deployments for {skill}?"
        ],
        "DevOps": [
            "How do you build and maintain {skill} pipelines to ensure automated, reliable deployments?",
            "Describe your experience with container orchestration and secrets management using {skill}.",
            "How do you optimize {skill} workflows to improve developer productivity and system stability?"
        ]
    }

    SCENARIO_TEMPLATES = {
        "Backend": "If your {skill} API starts failing under high load in production, walk us through your troubleshooting and resolution steps.",
        "Cloud": "Your {skill} infrastructure is experiencing an unexpected spike in latency. How do you identify the root cause and scale effectively?",
        "DevOps": "A critical deployment via {skill} has failed and caused a partial outage. Describe your rollback and fix-forward strategy.",
        "General": "A critical system component starts failing intermittently under production load. Describe your approach to diagnosis and resolution."
    }

    # 🧠 3. BUILD THE 3-1-1 MATRIX
    # --- Technical Questions (3) ---
    final_tech = []
    # Pick top 3 skills from categories
    tech_candidates = []
    for cat in categories:
        for s in categories[cat]:
            tech_candidates.append((cat, s))
            
    if tech_candidates:
        for i in range(min(3, len(tech_candidates))):
            cat, skill = tech_candidates[i]
            template = random.choice(TECH_TEMPLATES.get(cat, TECH_TEMPLATES["Backend"]))
            final_tech.append(template.format(skill=skill.title()))
    
    # Fill remaining with general if needed
    while len(final_tech) < 3:
        skill = display_skills[len(final_tech)] if len(display_skills) > len(final_tech) else "Core Technologies"
        final_tech.append(f"Describe your hands-on experience in building and optimizing systems using {skill}.")

    # --- Scenario Question (1) ---
    primary_cat = list(categories.keys())[0] if categories else "General"
    primary_skill = categories[primary_cat][0] if categories and categories[primary_cat] else "System"
    final_scenario = SCENARIO_TEMPLATES.get(primary_cat, SCENARIO_TEMPLATES["General"]).format(skill=primary_skill.title())

    # --- Behavioral Question (1) ---
    BEHAVIORAL_QS = [
        "Tell us about a time you took ownership of a critical technical challenge outside your immediate scope.",
        "How do you handle technical disagreements within a team during the architecture phase of a project?",
        "Describe a challenging project where you had to lead a deliverable under a tight deadline."
    ]
    final_behavioral = random.choice(BEHAVIORAL_QS)

    # 🧠 4. BUILD PROFESSIONAL HTML OUTPUT
    # Skill Tags
    skill_tags = "".join(
        [f"<span style='display:inline-block; background:rgba(168,85,247,0.15); border:1px solid rgba(168,85,247,0.5); "
         f"color:#c084fc; padding:3px 12px; border-radius:20px; font-size:12px; font-weight:600; margin:3px 4px 3px 0;'>"
         f"{s.title()}</span>" for s in display_skills[:6]]
    )

    def q_row(num, badge, badge_color, badge_bg, text):
        return (
            f"<div style='display:flex; gap:14px; align-items:flex-start; padding:14px 0; "
            f"border-bottom:1px solid rgba(255,255,255,0.06);'>"
            f"<span style='min-width:26px; height:26px; border-radius:50%; background:rgba(255,255,255,0.06); "
            f"color:#94a3b8; font-size:12px; font-weight:700; display:flex; align-items:center; justify-content:center; flex-shrink:0;'>{num}</span>"
            f"<div style='flex:1;'>"
            f"<span style='background:{badge_bg}; border:1px solid {badge_color}; color:{badge_color}; "
            f"padding:1px 9px; border-radius:10px; font-size:10px; font-weight:700; letter-spacing:0.5px; margin-bottom:6px; display:inline-block;'>{badge}</span>"
            f"<div style='color:#e2e8f0; font-size:14px; line-height:1.6; margin-top:4px;'>{text}</div>"
            f"</div></div>"
        )

    q1 = q_row(1, "TECHNICAL", "#38bdf8", "rgba(56,189,248,0.12)", final_tech[0])
    q2 = q_row(2, "TECHNICAL", "#38bdf8", "rgba(56,189,248,0.12)", final_tech[1])
    q3 = q_row(3, "TECHNICAL", "#38bdf8", "rgba(56,189,248,0.12)", final_tech[2])
    q4 = q_row(4, "SCENARIO", "#fb923c", "rgba(251,146,60,0.12)",  final_scenario)
    q5 = q_row(5, "BEHAVIORAL", "#4ade80", "rgba(74,222,128,0.12)", final_behavioral)

    output = (
        "<div style='background:rgba(8,8,28,0.97); border:1px solid rgba(168,85,247,0.3); "
        "border-radius:14px; padding:24px 28px; box-shadow:0 4px 24px rgba(0,0,0,0.5);'>"
        # Section: Key Skills
        "<div style='margin-bottom:20px;'>"
        "<div style='font-size:10px; color:#64748b; text-transform:uppercase; letter-spacing:1.2px; "
        "font-weight:700; margin-bottom:10px;'>Key Skills Identified</div>"
        f"<div>{skill_tags}</div>"
        "</div>"
        "<hr style='border:none; border-top:1px solid rgba(255,255,255,0.06); margin:0 0 4px 0;'>"
        # Section: Interview Questions
        "<div style='font-size:10px; color:#64748b; text-transform:uppercase; letter-spacing:1.2px; "
        "font-weight:700; margin:16px 0 4px 0;'>Interview Questions</div>"
        + q1 + q2 + q3 + q4 + q5 +
        "</div>"
    )
    return output
def generate_eval_csv(results):
    if not results: return ""
    import io
    output = io.StringIO()
    # Flattens the skills lists into comma-separated strings for CSV readability
    processed_results = []
    for r in results:
        row = r.copy()
        if isinstance(row.get('matching_skills'), list):
            row['matching_skills'] = ", ".join(row['matching_skills'])
        if isinstance(row.get('missing_skills'), list):
            row['missing_skills'] = ", ".join(row['missing_skills'])
        processed_results.append(row)
    
    pd.DataFrame(processed_results).to_csv(output, index=False)
    return output.getvalue()

# ================= LOGOUT =================
st.markdown("""
<style>
/* Target the tiny column where the logout button sits */
.logout-container button {
    background: transparent !important;
    border: 2px solid #ef4444 !important;
    color: #ef4444 !important;
    border-radius: 50% !important;
    height: 50px !important;
    width: 50px !important;
    font-size: 20px !important;
    font-weight: 900;
    margin-left: auto;
    display: flex;
    justify-content: center;
    align-items: center;
    box-shadow: 0 0 15px rgba(239, 68, 68, 0.4) !important;
    transition: all 0.3s ease-in-out !important;
}
.logout-container button:hover {
    background: #ef4444 !important;
    color: white !important;
    box-shadow: 0 0 30px rgba(239, 68, 68, 0.9) !important;
    transform: scale(1.1);
}
</style>
""", unsafe_allow_html=True)

col1, col2 = st.columns([15, 1])
with col2:
    st.markdown("<div class='logout-container'>", unsafe_allow_html=True)
    if st.button("⏻", help="Disconnect System / Logout"):
        st.session_state.logged_in = False
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
 
 
# ================= HOME =================
if st.session_state.page == "home":

    try:
        with open("assets/doodles_bg.png", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        st.markdown(f"""
        <style>
        .stApp {{
            background: linear-gradient(-45deg, #0f0c29, #302b63, #24243e, #0f0c29) !important;
            background-size: 400% 400% !important;
            animation: gradientBG 15s ease infinite !important;
        }}
        .stApp::before {{
            content: "";
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            background: url(data:image/png;base64,{encoded_string});
            background-size: 800px;
            opacity: 0.3;
            -webkit-mask-image: linear-gradient(to bottom, black 0%, transparent 50%);
            mask-image: linear-gradient(to bottom, black 0%, transparent 50%);
            pointer-events: none;
        }}
        .main .block-container {{
            position: relative;
            z-index: 1;
        }}
        </style>
        """, unsafe_allow_html=True)
    except Exception:
        pass

    if st.session_state.page == "home":
        st.markdown("<br>", unsafe_allow_html=True)

        # --- 1. Top Navigation Actions (Neon Styled) ---
        st.markdown("""
        <style>
        div[data-testid="column"] .stButton>button {
            height: 100px; font-size: 18px; font-weight: 800; border-radius: 20px;
            margin-bottom: 20px; transition: all 0.3s ease; text-transform: uppercase;
        }
        /* Feature 1: AI Evaluation (Purple) */
        div[data-testid="stHorizontalBlock"] > div:nth-child(1) .stButton>button {
            background: rgba(168, 85, 247, 0.05) !important; border: 2px solid #a855f7 !important;
            color: #e2e8f0 !important; box-shadow: 0 0 15px rgba(168, 85, 247, 0.2) !important;
        }
        /* Feature 2: Internal DB (Blue) */
        div[data-testid="stHorizontalBlock"] > div:nth-child(2) .stButton>button {
            background: rgba(59, 130, 246, 0.05) !important; border: 2px solid #3b82f6 !important;
            color: #e2e8f0 !important; box-shadow: 0 0 15px rgba(59, 130, 246, 0.2) !important;
        }
        /* Feature 3: AI Questions (Emerald) */
        div[data-testid="stHorizontalBlock"] > div:nth-child(3) .stButton>button {
            background: rgba(16, 185, 129, 0.05) !important; border: 2px solid #10b981 !important;
            color: #e2e8f0 !important; box-shadow: 0 0 15px rgba(16, 185, 129, 0.2) !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Smart Evaluation", use_container_width=True):
                st.session_state.page="eval"; st.rerun()
        with c2:
            if st.button("Internal DB", use_container_width=True):
                st.session_state.page="internal"; st.rerun()
        with c3:
            if st.button("Interview Questions", use_container_width=True):
                st.session_state.page="ai"; st.rerun()

        st.markdown("<hr style='border: 1px solid rgba(255,255,255,0.05); margin: 30px 0;'>", unsafe_allow_html=True)

        # --- 2. KPI Metrics ---
        try:
            with get_connection() as conn:
                total_c = conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
                total_j = conn.execute("SELECT COUNT(*) FROM job_descriptions").fetchone()[0]
                avg_s = conn.execute("SELECT AVG(score) FROM candidates WHERE score > 0").fetchone()[0] or 0
        except: total_c, total_j, avg_s = 0, 0, 0

        st.markdown(f"""
        <div style="display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 40px;">
            <div class="card" style="flex: 1; text-align: center; min-width: 250px;">
                <p style="margin: 0; font-size: 12px; text-transform: uppercase; color: #94a3b8; font-weight: 700;">Total Candidates</p>
                <h1 style="margin: 10px 0 0 0; font-size: 3.5em; color: #ffffff;">{total_c}</h1>
            </div>
            <div class="card" style="flex: 1; text-align: center; min-width: 250px;">
                <p style="margin: 0; font-size: 12px; text-transform: uppercase; color: #94a3b8; font-weight: 700;">Job Profiles</p>
                <h1 style="margin: 10px 0 0 0; font-size: 3.5em; color: #ffffff;">{total_j}</h1>
            </div>
            <div class="card" style="flex: 1; text-align: center; min-width: 250px;">
                <p style="margin: 0; font-size: 12px; text-transform: uppercase; color: #94a3b8; font-weight: 700;">Avg Match Score</p>
                <h1 style="margin: 10px 0 0 0; font-size: 3.5em; color: #ffffff;">{round(avg_s,1)}</h1>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # --- 3. Charts ---
        ch1, ch2 = st.columns(2)
        with ch1:
            st.markdown("<h3 style='font-size:18px; color:#a855f7;'>🎯 Candidate Funnel</h3>", unsafe_allow_html=True)
            with get_connection() as conn:
                df_dec = pd.read_sql("SELECT decision, COUNT(*) as count FROM candidates WHERE decision != '' GROUP BY decision", conn)
            if not df_dec.empty:
                fig1 = px.pie(df_dec, names='decision', values='count', hole=0.5, color_discrete_sequence=['#a855f7','#3b82f6','#10b981','#ef4444'])
                fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), height=300, margin=dict(t=0,b=0,l=0,r=0))
                st.plotly_chart(fig1, use_container_width=True)
        
        with ch2:
            st.markdown("<h3 style='font-size:18px; color:#3b82f6;'>📅 Pipeline Activity</h3>", unsafe_allow_html=True)
            with get_connection() as conn:
                df_time = pd.read_sql("SELECT uploaded_date, COUNT(*) as count FROM candidates GROUP BY uploaded_date ORDER BY uploaded_date", conn)
            if not df_time.empty:
                fig2 = px.line(df_time, x='uploaded_date', y='count', markers=True, color_discrete_sequence=['#3b82f6'])
                fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), height=300, margin=dict(t=0,b=0,l=0,r=0))
                st.plotly_chart(fig2, use_container_width=True)

# ================= EVAL PAGE =================
elif st.session_state.page == "eval":

    try:
        with open("assets/ai_doodles_bg.png", "rb") as image_file:
            encoded_string_eval = base64.b64encode(image_file.read()).decode()
        st.markdown(f"""
        <style>
        .stApp {{
            background: linear-gradient(-45deg, #0f0c29, #302b63, #24243e, #0f0c29) !important;
            background-size: 400% 400% !important;
            animation: gradientBG 15s ease infinite !important;
        }}
        .stApp::before {{
            content: "";
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            background: url(data:image/png;base64,{encoded_string_eval});
            background-size: 800px;
            opacity: 0.3;
            -webkit-mask-image: linear-gradient(to bottom, black 0%, transparent 50%);
            mask-image: linear-gradient(to bottom, black 0%, transparent 50%);
            pointer-events: none;
        }}
        .main .block-container {{
            position: relative;
            z-index: 1;
        }}
        </style>
        """, unsafe_allow_html=True)
    except Exception:
        pass

    _hcol_back, _hcol_title = st.columns([1, 8])
    with _hcol_back:
        if st.button("← Back", key="back_eval", use_container_width=True):
            st.session_state.eval_results = None
            st.session_state.page = "home"; st.rerun()
    with _hcol_title:
        st.markdown("<h2 style='margin:0; padding:4px 0; font-size:26px; font-weight:800; color:#a855f7;'>Evaluation Matrix</h2>", unsafe_allow_html=True)

    col_jd, col_up = st.columns([1, 1], gap="large")
    with col_jd:
        st.markdown("<h3 style='color:#a855f7; font-size: 20px;'>Step 1: Define Job Description</h3>", unsafe_allow_html=True)
        jd = st.text_area("jd_input", height=230, label_visibility="collapsed", placeholder="Paste the full JD to extract matching criteria and technical matrices...")
        if st.button("Save JD to Library", use_container_width=True):
            if jd:
                with get_connection() as conn:
                    conn.execute("INSERT INTO job_descriptions (jd) VALUES (?)",(jd,))
                st.success("Job Description saved to internal library!")
    
    with col_up:
        st.markdown("<h3 style='color:#10b981; font-size: 20px;'>Step 2: Upload Resumes</h3>", unsafe_allow_html=True)
        files = st.file_uploader("Upload batch candidate documents (PDF/DOCX)", accept_multiple_files=True, label_visibility="collapsed", key="eval_uploader")
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        eval_btn = st.button("🚀 Run Smart Matrix Evaluation", use_container_width=True)

    st.markdown("""
    <style>
    .eval-card {
        background: rgba(8, 8, 28, 0.95); border: 1px solid rgba(168, 85, 247, 0.35);
        box-shadow: 0 0 10px rgba(168, 85, 247, 0.1) !important;
        border-radius: 12px; padding: 16px 20px; margin-bottom: 15px;
    }
    .score-badge { padding: 4px 12px; border-radius: 20px; font-weight: 800; font-size: 14px; }
    .domain-badge { font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 12px; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

    if eval_btn and files and jd:
        results = []
        for idx, file in enumerate(files):
            fname=f"{int(time.time()*1000)}_{file.name}"
            path=f"resumes/{fname}"
            with open(path,"wb") as f:
                f.write(file.getbuffer())
 
            text=extract_text(path)
            res_name = extract_name(text, file.name)
            res_role = extract_designation(text)
            res_exp = extract_experience_years(text)
            res_domain = extract_domain(text)
            
            with custom_ai_loading(f"Analyzing {res_name}..."):
                analysis_raw = rule_based_analysis(jd, text, res_name)

            res_score, res_decision, res_verdict, res_notes = 0, "Backup", "", ""
            m_skills, x_skills = [], []

            try:
                if "Match Score:" in analysis_raw: 
                    res_score = int(re.findall(r'Match\sScore:\s*(\d+)', analysis_raw)[0])
                if "Decision:" in analysis_raw: 
                    res_decision = analysis_raw.split("Decision:")[1].split("\n")[0].strip()
                if "Recruiter Verdict:" in analysis_raw: 
                    res_verdict = analysis_raw.split("Recruiter Verdict:")[1].split("\n")[0].strip()
                if "Client Notes:" in analysis_raw: 
                    res_notes = analysis_raw.split("Client Notes:")[1].split("Matching Skills:")[0].strip()
                if "Matching Skills:" in analysis_raw: 
                    mt = analysis_raw.split("Matching Skills:")[1].split("Missing Skills:")[0].strip()
                    m_skills = [s.strip() for s in mt.split(",") if s.strip() and s.strip().lower() != "none"]
                if "Missing Skills:" in analysis_raw: 
                    xt = analysis_raw.split("Missing Skills:")[1].strip()
                    x_skills = [s.strip() for s in xt.split(",") if s.strip() and s.strip().lower() not in ["none", "no critical technical gaps identified"]]
            except Exception: pass

            res_email, res_phone = extract_email(text), extract_phone(text)
            with get_connection() as conn:
                existing = conn.execute("SELECT id FROM candidates WHERE (email != '-' AND email = ?) OR (name = ? AND phone != '-' AND phone = ?)", (res_email, res_name, res_phone)).fetchone()
            
            if not existing:
                with get_connection() as conn:
                    conn.execute("""
                    INSERT INTO candidates (name,email,phone,resume_path,resume_text,score,decision,reason,jd,uploaded_date,designation,location)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (res_name, res_email, res_phone, path, text, res_score, res_decision, res_notes, jd, datetime.date.today().strftime('%Y-%m-%d'), res_role, extract_location(text)))

            results.append({
                "name": res_name, "score": res_score, "decision": res_decision, "verdict": res_verdict, "summary": res_notes,
                "role": res_role, "exp": f"{res_exp}yr", "domain": res_domain, "impact": analyze_impact_score(text),
                "matching_skills": m_skills, "missing_skills": x_skills
            })
        st.session_state.eval_results = results
        st.rerun()

    # --- Display Persistence & Filtering Layer (Detached from Button) ---
    if st.session_state.get("eval_results"):
        st.markdown("<hr style='border:1px solid rgba(255,255,255,0.05); margin: 30px 0;'>", unsafe_allow_html=True)
        
        # 🎯 Dynamic Filter UI
        results_list = st.session_state.eval_results
        vs_count = sum(1 for r in results_list if r['decision'] == "Very Strong")
        s_count = sum(1 for r in results_list if r['decision'] == "Strong")
        b_count = sum(1 for r in results_list if r['decision'] == "Backup")
        n_count = sum(1 for r in results_list if r['decision'] == "Not a Match")
        
        col_f1, col_f2, col_f3 = st.columns([2, 5, 2])
        with col_f1:
            st.markdown("<h3 style='color:#e2e8f0; margin-top:5px;'>Evaluation Results</h3>", unsafe_allow_html=True)
        with col_f2:
            filter_opt = st.selectbox(
                "Filter by Match Decision:",
                ["All Results", f"Very Strong ({vs_count})", f"Strong ({s_count})", f"Backup ({b_count})", f"Not a Match ({n_count})"],
                label_visibility="collapsed"
            )
        with col_f3:
            csv_data = generate_eval_csv(st.session_state.eval_results)
            st.download_button(
                label="📥 Download Report",
                data=csv_data,
                file_name=f"TalentMatch_Evaluation_{datetime.date.today()}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        # Filtering Implementation
        filtered_results = []
        if "All Results" in filter_opt:
            filtered_results = results_list
        else:
            search_decision = filter_opt.split(" (")[0]
            filtered_results = [r for r in results_list if r['decision'] == search_decision]

        import textwrap
        for i, res in enumerate(filtered_results):
            score = res['score']
            score_color = "#10b981" if score >= 75 else "#f59e0b" if score >= 50 else "#ef4444"
            
            # Expanders
            s_key = f"exp_summ_{i}"
            if s_key not in st.session_state: st.session_state[s_key] = False

            import html
            c_name = html.escape(res['name'])
            c_role = html.escape(res.get('role', 'Expert'))
            c_verdict = html.escape(res.get('verdict', f'Candidate is a {res["decision"]} match for this role.'))
            c_notes = html.escape(res['summary']).replace("\n", "<br>")
            
            m_list = res.get('matching_skills', [])
            x_list = res.get('missing_skills', [])
            
            m_pills = "".join([f"<span class='skill-pill-match'>&#10003; {s}</span>" for s in m_list[:12]]) or "<span style='color:#475569; font-size:11px;'>None</span>"
            x_pills = "".join([f"<span class='skill-pill-missing'>&#10007; {s}</span>" for s in x_list[:8]]) or "<span style='color:#10b981; font-weight:700; font-size:11px;'>No critical technical gaps identified</span>"

            # 🛠️ ABSOLUTE ZERO-INDENTATION HTML CONSTRUCTION
            card_html = f"""<div class='eval-card'>
<div style='display:flex; justify-content:space-between; align-items:flex-start;'>
<div>
<h4 style='display:block; margin:0; color:#e2e8f0; font-size:18px;'>{c_name}</h4>
<p style='margin:4px 0 10px 0; color:#94a3b8; font-size:13px;'>{c_role} · {res['exp']} Experience</p>
<div style='color:#cbd5e1; font-size:13px; font-style:italic; border-left:2px solid {score_color}66; padding-left:10px; margin-bottom:15px;'>
{c_verdict}
</div>
</div>
<div class='score-badge' style='background: {score_color}1a; color:{score_color}; border:1px solid {score_color}33;'>
{score}% Match
</div>
</div>
<div style='display:grid; grid-template-columns: 1fr 1fr; gap:15px; margin-top:5px;'>
<div>
<div class='skill-label'>Matching Skills</div>
<div style='display:flex; flex-wrap:wrap; gap:5px;'>{m_pills}</div>
</div>
<div>
<div class='skill-label'>Missing Skills</div>
<div style='display:flex; flex-wrap:wrap; gap:5px;'>{x_pills}</div>
</div>
</div>
</div>"""
            st.markdown(card_html, unsafe_allow_html=True)
            
            # Action Row
            if st.button("▲ Hide Client Notes" if st.session_state[s_key] else "▼ Generate Professional Client Notes", key=f"btn_s_{i}", use_container_width=True):
                st.session_state[s_key] = not st.session_state[s_key]; st.rerun()
            
            if st.session_state[s_key]:
                notes_html = f"""<div style='background:rgba(59, 130, 246, 0.05); border-left:3px solid #3b82f6; padding:15px; border-radius:4px; margin-top:5px; margin-bottom:20px;'>
<h5 style='margin:0 0 10px 0; font-size:12px; color:#3b82f6; text-transform:uppercase;'>Formal Client Submission Notes</h5>
<p style='margin:0 0 15px 0; font-size:13px; color:#cbd5e1; line-height:1.6;'>{c_notes}</p>
<div style='display:grid; grid-template-columns: 1fr 1fr; gap:15px; border-top:1px solid rgba(59, 130, 246, 0.15); padding-top:15px;'>
<div>
<div class='skill-label' style='color:#3b82f6; opacity:0.8;'>Matching Tech Stack</div>
<div style='display:flex; flex-wrap:wrap; gap:5px;'>{m_pills}</div>
</div>
<div>
<div class='skill-label' style='color:#3b82f6; opacity:0.8;'>Requirement Gaps</div>
<div style='display:flex; flex-wrap:wrap; gap:5px;'>{x_pills}</div>
</div>
</div>
</div>"""
                st.markdown(notes_html, unsafe_allow_html=True)
            st.markdown("<div style='margin-bottom:25px;'></div>", unsafe_allow_html=True)


# ================= INTERNAL DB =================
elif st.session_state.page == "internal":
    st.markdown("""
    <style>
    /* Neon Blue Styling for Internal DB */
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px 12px 0 0;
        padding: 8px 16px;
        transition: all 0.3s ease;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(59, 130, 246, 0.1) !important;
        border-bottom: 3px solid #3b82f6 !important;
        box-shadow: 0 5px 15px rgba(59, 130, 246, 0.3) !important;
        text-shadow: 0 0 5px rgba(59, 130, 246, 0.5);
    }
    /* Search Bar Neon Blue Focus */
    div[data-testid="stTextInput"] input:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 10px rgba(59, 130, 246, 0.4) !important;
    }
    /* Action Buttons (Edit/Save) Neon Blue */
    div.stButton > button[key*="save_"] {
        background: rgba(59, 130, 246, 0.2) !important;
        border: 1px solid #3b82f6 !important;
        box-shadow: 0 0 10px rgba(59, 130, 246, 0.3) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    try:
        with open("assets/doodles_bg.png", "rb") as image_file:
            encoded_string_internal = base64.b64encode(image_file.read()).decode()
        st.markdown(f"""
        <style>
        .stApp {{
            background: linear-gradient(-45deg, #0f0c29, #302b63, #24243e, #0f0c29) !important;
            background-size: 400% 400% !important;
            animation: gradientBG 15s ease infinite !important;
        }}
        .stApp::before {{
            content: "";
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            background: url(data:image/png;base64,{encoded_string_internal});
            background-size: 800px;
            opacity: 0.3;
            -webkit-mask-image: linear-gradient(to bottom, black 0%, transparent 50%);
            mask-image: linear-gradient(to bottom, black 0%, transparent 50%);
            pointer-events: none;
        }}
        .main .block-container {{
            position: relative;
            z-index: 1;
        }}
        /* Clear sheet for internal tab content */
        div[data-testid="stTabs"] > div[role="tabpanel"] {{
            background: rgba(48, 43, 99, 0.1) !important;
            padding: 30px;
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.05);
            backdrop-filter: blur(12px);
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            margin-top: 10px;
        }}
        </style>
        """, unsafe_allow_html=True)
    except Exception:
        pass

    _hcol_back, _hcol_title = st.columns([1, 8])
    with _hcol_back:
        if st.button("← Back", key="back_internal", use_container_width=True):
            st.session_state.page = "home"; st.rerun()
    with _hcol_title:
        st.markdown("<h2 style='margin:0; padding:4px 0; font-size:26px; font-weight:800; color:#10b981;'>Internal DB</h2>", unsafe_allow_html=True)

    # 🔥 SWITCH -> NATIVE TABS (SaaS STYLE)
    tab_candidates, tab_jds = st.tabs(["Candidates Database", "Job Descriptions Library"])

    # ================= CANDIDATES (SPLIT PANE) =================
    with tab_candidates:
        st.markdown("<h4 style='color: #a855f7; margin-bottom: 5px;'>Performance Insights</h4>", unsafe_allow_html=True)
        st.markdown("<p style='color: #94a3b8; font-size: 14px; margin-bottom: 25px;'>Analyze matching patterns and data health across your internal candidate pool.</p>", unsafe_allow_html=True)
        
        col_stat1, col_stat2 = st.columns([2, 2])
        with col_stat1:
            if st.button("🧹 Clean Duplicate Candidates", use_container_width=True):
                if cleanup_candidates():
                    st.success("✅ Database Cleanup Complete: Existing duplicates removed.")
                    st.rerun()
        with col_stat2:
            pass
            
        st.markdown("<hr style='border: 1px solid rgba(255,255,255,0.05); margin-top: 10px; margin-bottom: 30px;'>", unsafe_allow_html=True)

        if "active_resume" in st.session_state and st.session_state.active_resume:
            col_list, col_resume = st.columns([5, 7])
        else:
            col_list, col_resume = st.columns([99, 1])
        
        with col_list:
            st.markdown("<h3 style='margin-bottom: 5px; color:#10b981; font-weight: 600; font-size: 20px;'>Import Candidates</h3>", unsafe_allow_html=True)
            uploaded_resumes = st.file_uploader("Upload internal resumes (PDF/DOCX)", accept_multiple_files=True, label_visibility="collapsed")
            if uploaded_resumes and st.button("Save to Internal Database", use_container_width=True):
                with custom_ai_loading("Importing candidates to database..."):
                    with get_connection() as conn:
                        for f in uploaded_resumes:
                            path = f"resumes/{int(time.time()*1000)}_{f.name}"
                            with open(path, "wb") as file:
                                file.write(f.getbuffer())
                            text = extract_text(path)
                            
                            # Pre-check for duplicates
                            res_email = extract_email(text)
                            res_name = extract_name(text, f.name)
                            res_phone = extract_phone(text)
                            existing = conn.execute("""
                                SELECT id FROM candidates 
                                WHERE (email != '-' AND email = ?) 
                                OR (name = ? AND phone != '-' AND phone = ?)
                            """, (res_email, res_name, res_phone)).fetchone()
                            
                            if not existing:
                                conn.execute("""
                                INSERT INTO candidates 
                                (name,email,phone,resume_path,resume_text,matching,missing,score,decision,reason,jd,linkedin,uploaded_date,expected_rate,designation,location)
                                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                                """, (res_name, res_email, res_phone, path, text, "", "", 0, "Stored", "Saved directly to candidate pool.", "", extract_linkedin(text), datetime.date.today().strftime('%Y-%m-%d'), "", extract_designation(text), extract_location(text)))

                    st.success("Successfully imported all candidates!")
                    time.sleep(1)
                    st.rerun()

            st.markdown("<hr style='border:1px solid rgba(255,255,255,0.05); margin-top: 5px; margin-bottom: 20px;'>", unsafe_allow_html=True)

            search = st.text_input("Search Candidates")
            boolean_search_query = st.text_input("Boolean Search (AND / OR / NOT)")
     
            rows = get_connection().execute(
                "SELECT id,name,email,phone,resume_path,resume_text,linkedin,uploaded_date,expected_rate,designation,location FROM candidates"
            ).fetchall()
     
            df = pd.DataFrame(rows,columns=["ID","Name","Email","Phone","Resume","Text","LinkedIn","Date","Rate","Designation","Location"])
     
            if search:
                df = df[df["Name"].str.contains(search,case=False) |
                        df["Email"].str.contains(search,case=False)]
     
            if boolean_search_query:
                df = boolean_search(df, boolean_search_query)
     
            if not df.empty:
                # Table Header
                hc1, hc2, hc3, hc4, hc5, hc6, hc7, hc8 = st.columns([3.2, 2.5, 1.8, 1.8, 1.8, 1.8, 1.8, 1])
                hc1.markdown("**Name**")
                hc2.markdown("**Email**")
                hc3.markdown("**Phone**")
                hc4.markdown("**Location**")
                hc5.markdown("**Designation**")
                hc6.markdown("**Rate**")
                hc7.markdown("**LinkedIn**")
                st.markdown("<hr style='border:1px solid rgba(255,255,255,0.2); margin: 5px 0 15px 0;'>", unsafe_allow_html=True)
                
                for i, row in df.iterrows():
                    cid = row["ID"]
                    with st.container():
                        edit_key = f"edit_{cid}"
                        if edit_key not in st.session_state: st.session_state[edit_key] = False
                            
                        if st.session_state[edit_key]:
                            c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1, 1])
                            with c1: new_name = st.text_input("Name", str(row["Name"]), key=f"n_{cid}")
                            with c2: new_email = st.text_input("Email", str(row["Email"]), key=f"e_{cid}")
                            with c3: new_phone = st.text_input("Phone", str(row["Phone"]), key=f"p_{cid}")
                            with c4: new_linkedin = st.text_input("LinkedIn", str(row["LinkedIn"]), key=f"l_{cid}")
                            with c5: new_desig = st.text_input("Designation", str(row["Designation"]), key=f"d_{cid}")
                            with c6: new_rate = st.text_input("Rate", str(row["Rate"]), key=f"r_{cid}")
                            with c7: new_loc = st.text_input("Location", str(row["Location"]), key=f"loc_{cid}")
                            with c8:
                                st.markdown("<br>", unsafe_allow_html=True)
                                if st.button("", key=f"save_{cid}"):
                                    with get_connection() as conn:
                                        conn.execute("""
                                        UPDATE candidates SET name=?, email=?, phone=?, linkedin=?, expected_rate=?, designation=?, location=? WHERE id=?
                                        """, (new_name, new_email, new_phone, new_linkedin, new_rate, new_desig, new_loc, cid))
                                    st.session_state[edit_key] = False
                                    st.rerun()
                        else:
                            c1, c2, c3, c4, c5, c6, c7, c8, c9, c10 = st.columns([3.0, 2.4, 1.6, 1.6, 1.8, 1.6, 1.6, 1, 1, 1])
                            with c1:
                                if st.button(str(row['Name']), key=f"btn_name_{cid}", help="Click to view full resume"):
                                    st.session_state.active_resume = str(row["Resume"])
                                    st.rerun()
                            c2.markdown(str(row['Email']))
                            c3.markdown(str(row['Phone']))
                            c4.markdown(str(row['Location']) if row['Location'] else '-')
                            c5.markdown(str(row['Designation']) if row['Designation'] else '-')
                            c6.markdown(str(row['Rate']) if row['Rate'] else '-')
                            c7.markdown(str(row['LinkedIn']) if row['LinkedIn'] else '-')
                            with c8:
                                if st.button("✏️", key=f"btn_edit_{cid}"):
                                    st.session_state[edit_key] = True
                                    st.rerun()
                            with c9:
                                tag_key = f"show_tag_{cid}"
                                if tag_key not in st.session_state: st.session_state[tag_key] = False
                                if st.button("🏷️", key=f"btn_tag_{cid}", help="Tag for a Job"):
                                    st.session_state[tag_key] = not st.session_state[tag_key]
                                    st.session_state[f"show_att_{cid}"] = False
                                    st.rerun()
                            with c10:
                                att_key_btn = f"show_att_{cid}"
                                if att_key_btn not in st.session_state: st.session_state[att_key_btn] = False
                                att_count = get_connection().execute(
                                    "SELECT COUNT(*) FROM candidate_attachments WHERE candidate_id=?", (cid,)
                                ).fetchone()[0]
                                att_label = "📎" if att_count == 0 else f"📎{att_count}"
                                if st.button(att_label, key=f"btn_att_{cid}", help=f"Attachments ({att_count})"):
                                    st.session_state[att_key_btn] = not st.session_state[att_key_btn]
                                    st.session_state[f"show_tag_{cid}"] = False
                                    st.rerun()
                                    
                        # --- TAG PANEL (expandable inline below row) ---
                        tag_key = f"show_tag_{cid}"
                        if tag_key not in st.session_state: st.session_state[tag_key] = False
                        if st.session_state.get(tag_key, False):
                            st.markdown("<div style='background:rgba(168,85,247,0.07); border:1px solid rgba(168,85,247,0.25); border-radius:10px; padding:12px 16px; margin:4px 0 6px 0;'>", unsafe_allow_html=True)
                            jd_rows = get_connection().execute("SELECT id, jd FROM job_descriptions ORDER BY id DESC").fetchall()
                            if jd_rows:
                                jd_options = {f"#{r[0]}: {r[1][:60].replace(chr(10),' ')}...": r[0] for r in jd_rows}
                                already_tagged = [r[0] for r in get_connection().execute(
                                    "SELECT jd_id FROM candidate_tags WHERE candidate_id=?", (cid,)).fetchall()]
                                tag_sel_col, tag_btn_col = st.columns([5, 1])
                                with tag_sel_col:
                                    sel_label = st.selectbox(
                                        f"Tag {row['Name']}",
                                        options=list(jd_options.keys()),
                                        key=f"tag_sel_{cid}",
                                        label_visibility="collapsed"
                                    )
                                with tag_btn_col:
                                    if st.button("✅ Tag", key=f"do_tag_{cid}", use_container_width=True):
                                        sel_jd_id = jd_options[sel_label]
                                        with get_connection() as conn:
                                            conn.execute(
                                                "INSERT OR IGNORE INTO candidate_tags (candidate_id, jd_id, tagged_date) VALUES (?,?,?)",
                                                (cid, sel_jd_id, datetime.date.today().strftime('%Y-%m-%d'))
                                            )
                                        st.session_state[tag_key] = False
                                        st.rerun()
                                if already_tagged:
                                    tag_jd_names = get_connection().execute(
                                        f"SELECT id, jd FROM job_descriptions WHERE id IN ({','.join(str(x) for x in already_tagged)})"
                                    ).fetchall()
                                    st.markdown("<div style='margin-top:8px; font-size:11px; color:#94a3b8; margin-bottom:4px;'>Tagged for:</div>", unsafe_allow_html=True)
                                    for jrow in tag_jd_names:
                                        uc1, uc2 = st.columns([9, 1])
                                        uc1.markdown(f"<span style='background:rgba(168,85,247,0.15); border:1px solid rgba(168,85,247,0.4); color:#c084fc; padding:2px 10px; border-radius:12px; font-size:11px;'>#{jrow[0]}: {jrow[1][:60].replace(chr(10),' ')}...</span>", unsafe_allow_html=True)
                                        if uc2.button("✕", key=f"untag_{cid}_{jrow[0]}"):
                                            with get_connection() as conn:
                                                conn.execute("DELETE FROM candidate_tags WHERE candidate_id=? AND jd_id=?", (cid, jrow[0]))
                                            st.rerun()
                            else:
                                st.info("No saved JDs found. Save a JD first from the Evaluation page.")
                            st.markdown("</div>", unsafe_allow_html=True)

                        # --- ATTACHMENT PANEL ---
                        att_key = f"show_att_{cid}"
                        if att_key not in st.session_state: st.session_state[att_key] = False
                        if st.session_state.get(att_key, False):
                            st.markdown("<div style='background:rgba(59,130,246,0.07); border:1px solid rgba(59,130,246,0.25); border-radius:10px; padding:14px 16px; margin:4px 0 6px 0;'>", unsafe_allow_html=True)
                            st.markdown("<div style='font-size:11px; color:#94a3b8; font-weight:700; text-transform:uppercase; letter-spacing:0.8px; margin-bottom:10px;'>📎 Attachments</div>", unsafe_allow_html=True)

                            # Upload new attachment
                            att_up_col, att_btn_col = st.columns([5, 1])
                            with att_up_col:
                                uploaded_att = st.file_uploader(
                                    "Upload",
                                    key=f"att_up_{cid}",
                                    label_visibility="collapsed",
                                    accept_multiple_files=False
                                )
                            with att_btn_col:
                                st.markdown("<br>", unsafe_allow_html=True)
                                if st.button("⬆ Upload", key=f"att_save_{cid}", use_container_width=True):
                                    if uploaded_att:
                                        att_path = f"attachments/{cid}_{int(time.time()*1000)}_{uploaded_att.name}"
                                        with open(att_path, "wb") as af:
                                            af.write(uploaded_att.getbuffer())
                                        with get_connection() as conn:
                                            conn.execute(
                                                "INSERT INTO candidate_attachments (candidate_id, filename, filepath, filesize, uploaded_date) VALUES (?,?,?,?,?)",
                                                (cid, uploaded_att.name, att_path, uploaded_att.size, datetime.date.today().strftime('%Y-%m-%d'))
                                            )
                                        st.success("Attached!")
                                        st.rerun()
                                    else:
                                        st.warning("Select a file first.")

                            # Show existing attachments
                            att_files = get_connection().execute(
                                "SELECT id, filename, filepath, filesize, uploaded_date FROM candidate_attachments WHERE candidate_id=? ORDER BY id DESC",
                                (cid,)
                            ).fetchall()

                            if att_files:
                                st.markdown("<hr style='border:none; border-top:1px solid rgba(255,255,255,0.06); margin:10px 0;'>", unsafe_allow_html=True)
                                for af in att_files:
                                    af_id, af_name, af_path, af_size, af_date = af
                                    size_str = f"{af_size/1024:.1f} KB" if af_size else ""
                                    ac1, ac2, ac3 = st.columns([6, 2, 1])
                                    ac1.markdown(
                                        f"<span style='font-size:13px; color:#e2e8f0;'>📄 {af_name}</span>"
                                        f"<span style='font-size:11px; color:#64748b; margin-left:8px;'>{size_str} · {af_date}</span>",
                                        unsafe_allow_html=True
                                    )
                                    # Download button
                                    try:
                                        with open(af_path, "rb") as dl_f:
                                            ac2.download_button(
                                                "⬇ Download",
                                                data=dl_f.read(),
                                                file_name=af_name,
                                                key=f"dl_{af_id}",
                                                use_container_width=True
                                            )
                                    except Exception:
                                        ac2.markdown("<span style='color:#64748b; font-size:11px;'>File missing</span>", unsafe_allow_html=True)
                                    # Delete button
                                    if ac3.button("✕", key=f"del_att_{af_id}"):
                                        try:
                                            os.remove(af_path)
                                        except Exception:
                                            pass
                                        with get_connection() as conn:
                                            conn.execute("DELETE FROM candidate_attachments WHERE id=?", (af_id,))
                                        st.rerun()
                            else:
                                st.markdown("<div style='color:#475569; font-size:12px; margin-top:6px;'>No attachments yet. Upload offer letters, contracts, or notes.</div>", unsafe_allow_html=True)

                            st.markdown("</div>", unsafe_allow_html=True)

                        st.markdown("<hr style='border:1px solid rgba(255,255,255,0.05); margin: 5px 0;'>", unsafe_allow_html=True)

            else:
                st.info("No candidates found matching the criteria.")
                
        with col_resume:
            if "active_resume" in st.session_state and st.session_state.active_resume:
                c_close, _ = st.columns([1, 9])
                with c_close:
                    if st.button("", key="btn_close_res", help="Close preview"):
                        st.session_state.active_resume = None
                        st.rerun()
                path = st.session_state.active_resume
                if path.endswith(".pdf"):
                    try:
                        with open(path,"rb") as f:
                            b64 = base64.b64encode(f.read()).decode()
                        st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="800px" style="border: none; margin-top: 10px;"></iframe>', unsafe_allow_html=True)
                    except:
                        st.error("Resume file missing or unreadable.")
                elif path.endswith(".docx") or path.endswith(".doc"):
                    try:
                        text_content = extract_text(path)
                        st.markdown(f"<div style='background: rgba(255,255,255,0.02); padding: 10px; border-radius: 6px; margin-top: 10px; white-space: pre-wrap; font-size: 14px; line-height: 1.6;'>{text_content}</div>", unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Cannot read document: {e}")
                else:
                    st.warning("Unsupported file format for inline preview.")
 
    # ================= JOB DESCRIPTIONS =================
    with tab_jds:
        st.markdown("<h1 style='text-align:center; font-size: 36px; margin-bottom: 30px; font-weight: 800; color: #3b82f6;'>Job Descriptions Library</h1>", unsafe_allow_html=True)
        if "active_jd" in st.session_state and st.session_state.active_jd:
            col_jd_list, col_jd_view = st.columns([5, 7])
        else:
            col_jd_list, col_jd_view = st.columns([99, 1])
            
        with col_jd_list:
            search_jd = st.text_input("Search JD")
            rows = get_connection().execute("SELECT * FROM job_descriptions ORDER BY id DESC").fetchall()
            
            if rows:
                df_jd = pd.DataFrame(rows, columns=["ID", "JD"])
                if search_jd:
                    df_jd = df_jd[df_jd["JD"].str.contains(search_jd, case=False)]
                
                for i, row in df_jd.iterrows():
                    cid = row["ID"]
                    jd_text = row["JD"]
                    title_preview = jd_text[:55].replace("\n", " ") + "..." if len(jd_text) > 55 else jd_text

                    # Fetch tagged candidates for this JD
                    tagged = get_connection().execute("""
                        SELECT c.id, c.name, c.designation FROM candidates c
                        JOIN candidate_tags t ON c.id = t.candidate_id
                        WHERE t.jd_id = ?
                    """, (cid,)).fetchall()

                    with st.container():
                        j1, j2 = st.columns([8, 2])
                        with j1:
                            if st.button(title_preview, key=f"btn_jd_{cid}", help="Click to view full JD"):
                                st.session_state.active_jd = str(jd_text)
                                st.rerun()
                        with j2:
                            st.markdown(f"<span style='font-size:11px; color:#64748b;'>ID #{cid}</span>", unsafe_allow_html=True)

                        # Tagged candidates pills under JD
                        if tagged:
                            tags_html = "".join([
                                f"<span style='display:inline-block; background:rgba(16,185,129,0.12); border:1px solid rgba(16,185,129,0.4); "
                                f"color:#34d399; padding:2px 10px; border-radius:12px; font-size:11px; margin:2px 3px 2px 0;'>"
                                f"&#128100; {t[1]}{' · ' + t[2] if t[2] else ''}</span>" for t in tagged
                            ])
                            st.markdown(f"<div style='margin:4px 0 6px 0;'>{tags_html}</div>", unsafe_allow_html=True)
                        else:
                            st.markdown("<div style='font-size:11px; color:#475569; margin-bottom:4px;'>No candidates tagged</div>", unsafe_allow_html=True)

                        st.markdown("<hr style='border:1px solid rgba(255,255,255,0.05); margin:6px 0;'>", unsafe_allow_html=True)
            else:
                st.info("No Job Descriptions found.")

        with col_jd_view:
            if "active_jd" in st.session_state and st.session_state.active_jd:
                c_close, _ = st.columns([1, 9])
                with c_close:
                    if st.button("", key="btn_close_jd", help="Close JD view"):
                        st.session_state.active_jd = None
                        st.rerun()
                        
                st.markdown("### Job Description details")
                st.markdown(f"<div style='background: rgba(255,255,255,0.02); padding: 25px; border-radius: 12px; margin-top: 15px; white-space: pre-wrap; font-size: 15px; line-height: 1.7;'>{st.session_state.active_jd}</div>", unsafe_allow_html=True)
               
# ================= AI QUESTIONS =================
elif st.session_state.page=="ai":
    st.markdown("""
    <style>
    /* Neon Emerald Styling for AI Interview Questions */
    .ai-card {
        background: rgba(8, 20, 16, 0.9) !important;
        border: 1px solid rgba(16, 185, 129, 0.25) !important;
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.1) !important;
        padding: 26px;
        border-radius: 20px;
        margin-bottom: 20px;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        position: relative;
        overflow: hidden;
    }
    .ai-card::before {
        content: "";
        position: absolute;
        top: 0; left: 0; width: 4px; height: 100%;
        background: #10b981;
        box-shadow: 0 0 10px #10b981;
    }
    .ai-card:hover {
        border-color: #10b981 !important;
        box-shadow: 0 0 25px rgba(16, 185, 129, 0.4) !important;
        transform: scale(1.01);
    }
    </style>
    """, unsafe_allow_html=True)
 
    try:
        with open("assets/ai_doodles_bg.png", "rb") as image_file:
            encoded_string_ai = base64.b64encode(image_file.read()).decode()
        st.markdown(f"""
        <style>
        .stApp {{
            background: linear-gradient(-45deg, #0f0c29, #302b63, #24243e, #0f0c29) !important;
            background-size: 400% 400% !important;
            animation: gradientBG 15s ease infinite !important;
        }}
        .stApp::before {{
            content: "";
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            background: url(data:image/png;base64,{encoded_string_ai});
            background-size: 800px;
            opacity: 0.3;
            -webkit-mask-image: linear-gradient(to bottom, black 0%, transparent 50%);
            mask-image: linear-gradient(to bottom, black 0%, transparent 50%);
            pointer-events: none;
        }}
        .main .block-container {{
            position: relative;
            z-index: 1;
        }}
        </style>
        """, unsafe_allow_html=True)
    except Exception:
        pass
    st.markdown("<h1 style='text-align:center; font-size: 36px; margin-bottom: 30px; font-weight: 800; color: #3b82f6;'>Interview Question Matrix</h1>", unsafe_allow_html=True)

    _hcol_back, _hcol_title = st.columns([1, 8])
    with _hcol_back:
        if st.button("← Back", key="back_ai", use_container_width=True):
            st.session_state.page = "home"; st.rerun()
    with _hcol_title:
        st.markdown("<h2 style='margin:0; padding:4px 0; font-size:26px; font-weight:800; color:#3b82f6;'>Interview Question Matrix</h2>", unsafe_allow_html=True)

    jd = st.text_area("Paste JD to generate technical, situational, and behavioral questions", height=150)

    if st.button("Generate Interview Matrix", use_container_width=True):
        if jd:
            with custom_ai_loading("Generating Interview Matrix. Please wait..."):
                result = rule_based_questions(jd)
            st.markdown("<hr style='border:1px solid rgba(255,255,255,0.08); margin:20px 0;'>", unsafe_allow_html=True)
            st.markdown(result, unsafe_allow_html=True)

# ================= JD LIBRARY =================
elif st.session_state.page=="jd_library":

    try:
        with open("assets/doodles_bg.png", "rb") as image_file:
            encoded_string_lib = base64.b64encode(image_file.read()).decode()
        st.markdown(f"""
        <style>
        .stApp {{
            background: linear-gradient(-45deg, #0f0c29, #302b63, #24243e, #0f0c29) !important;
            background-size: 400% 400% !important;
            animation: gradientBG 15s ease infinite !important;
        }}
        .stApp::before {{
            content: "";
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            background: url(data:image/png;base64,{encoded_string_lib});
            background-size: 800px;
            opacity: 0.3;
            -webkit-mask-image: linear-gradient(to bottom, black 0%, transparent 50%);
            mask-image: linear-gradient(to bottom, black 0%, transparent 50%);
            pointer-events: none;
        }}
        .main .block-container {{
            position: relative;
            z-index: 1;
        }}
        </style>
        """, unsafe_allow_html=True)
    except Exception:
        pass

    _hcol_back, _hcol_title = st.columns([1, 8])
    with _hcol_back:
        if st.button("← Back", key="back_jd", use_container_width=True):
            st.session_state.page = "home"; st.rerun()
    with _hcol_title:
        st.markdown("<h2 style='margin:0; padding:4px 0; font-size:26px; font-weight:800; color:#3b82f6;'>Job Library</h2>", unsafe_allow_html=True)

    st.markdown("<p style='color: #94a3b8; font-size: 14px; margin-bottom: 25px;'>Manage and browse your organization's job requirements.</p>", unsafe_allow_html=True)

    search = st.text_input("Search Jobs", placeholder="Enter job title or keywords...")
    rows = get_connection().execute("SELECT * FROM job_descriptions ORDER BY id DESC").fetchall()
    
    if rows:
        df_jd = pd.DataFrame(rows, columns=["ID", "JD"])
        if search:
            df_jd = df_jd[df_jd["JD"].str.contains(search, case=False)]
        
        # Split into list and preview
        col_jd_list, col_jd_view = st.columns([5, 7])
            
        with col_jd_list:
            for i, row in df_jd.iterrows():
                cid = row["ID"]
                jd_text = row["JD"]
                title_preview = jd_text[:55].replace("\n", " ") + "..." if len(jd_text) > 55 else jd_text

                with st.container():
                    j1, j2 = st.columns([8, 2])
                    with j1:
                        if st.button(title_preview, key=f"btn_lib_jd_{cid}", help="Click to view full JD"):
                            st.session_state.active_lib_jd = str(jd_text)
                            st.rerun()
                    with j2:
                        st.markdown(f"<span style='font-size:11px; color:#64748b;'>ID #{cid}</span>", unsafe_allow_html=True)
                    st.markdown("<hr style='border:1px solid rgba(255,255,255,0.05); margin:6px 0;'>", unsafe_allow_html=True)
        
        with col_jd_view:
            if "active_lib_jd" in st.session_state and st.session_state.active_lib_jd:
                st.markdown(f"""
                <div style='background: rgba(12, 8, 30, 0.4); border: 1px solid rgba(59, 130, 246, 0.2); 
                     border-radius: 12px; padding: 25px; backdrop-filter: blur(8px);'>
                    <h4 style='color: #3b82f6; margin-bottom: 15px;'>Job Specification</h4>
                    <div style='white-space: pre-wrap; font-size: 15px; line-height: 1.7; color: #e2e8f0;'>
                        {st.session_state.active_lib_jd}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Close Preview", key="close_lib_jd"):
                    st.session_state.active_lib_jd = None
                    st.rerun()
            else:
                st.info("Select a job description from the list to preview details.")
    else:
        st.info("No Job Descriptions found. Save a JD first from the Evaluation page.")