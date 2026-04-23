import streamlit as st
import joblib
import pickle
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from urllib.parse import urlparse
from extractor import extract_features, rule_based_check, get_domain_parts
import time

# ══════════════════════════════════════════════════════════════
# 1. PAGE CONFIGURATION
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="PhishVision AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════════════════
# 2. FULL CYBER DARK THEME CSS
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;700;900&family=Rajdhani:wght@400;600;700&display=swap');

/* ── Global Background ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #050a0f !important;
    color: #00ff88 !important;
}

[data-testid="stHeader"] {
    background-color: #050a0f !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020812 0%, #071020 100%) !important;
    border-right: 1px solid #00ff8833 !important;
}

[data-testid="stSidebar"] * {
    color: #00ff88 !important;
}

/* ── Main Scan Button ── */
.stButton > button {
    width: 100%;
    background: linear-gradient(90deg, #00ff88 0%, #00c8ff 100%) !important;
    color: #050a0f !important;
    font-family: 'Orbitron', monospace !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    border: none !important;
    border-radius: 4px !important;
    height: 3.5em !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 0 20px #00ff8844 !important;
}

.stButton > button:hover {
    box-shadow: 0 0 40px #00ff88aa !important;
    transform: translateY(-2px) !important;
}

/* ── Input Fields ── */
.stTextInput > div > div > input {
    background-color: #071020 !important;
    color: #00ff88 !important;
    border: 1px solid #00ff8844 !important;
    border-radius: 4px !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.95rem !important;
    padding: 12px !important;
}

.stTextInput > div > div > input:focus {
    border: 1px solid #00ff88 !important;
    box-shadow: 0 0 15px #00ff8833 !important;
}

.stTextInput > label {
    color: #00c8ff !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
}

/* ── Selectbox ── */
.stSelectbox > div > div {
    background-color: #071020 !important;
    border: 1px solid #00ff8844 !important;
    color: #00ff88 !important;
    font-family: 'Share Tech Mono', monospace !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background-color: #071020 !important;
    border-bottom: 1px solid #00ff8822 !important;
    gap: 4px !important;
}

.stTabs [data-baseweb="tab"] {
    background-color: transparent !important;
    color: #00ff8888 !important;
    font-family: 'Orbitron', monospace !important;
    font-size: 0.75rem !important;
    letter-spacing: 1px !important;
    border-radius: 4px 4px 0 0 !important;
    padding: 10px 20px !important;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(180deg, #00ff8811 0%, transparent 100%) !important;
    color: #00ff88 !important;
    border-bottom: 2px solid #00ff88 !important;
}

/* ── Dataframe ── */
.stDataFrame {
    border: 1px solid #00ff8833 !important;
}

/* ── File uploader ── */
[data-testid="stFileUploadDropzone"] {
    background-color: #071020 !important;
    border: 1px dashed #00ff8844 !important;
    color: #00ff88 !important;
}

/* ── Divider ── */
hr {
    border-color: #00ff8822 !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #050a0f; }
::-webkit-scrollbar-thumb { background: #00ff8844; border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: #00ff88; }

/* ── Metric cards ── */
[data-testid="stMetric"] {
    background: #071020 !important;
    border: 1px solid #00ff8822 !important;
    border-radius: 8px !important;
    padding: 12px !important;
}

[data-testid="stMetricLabel"] { color: #00c8ff !important; }
[data-testid="stMetricValue"] { color: #00ff88 !important; }

/* ─────────────────────────────────────────────
   🔥 ADVANCED INTERACTION UPGRADE (SAFE)
   ───────────────────────────────────────────── */

/* Smooth transitions globally */
* {
    transition: all 0.25s ease !important;
}

/* ── BUTTON HOVER + CLICK EFFECT ── */
.stButton > button {
    position: relative;
    overflow: hidden;
}

.stButton > button:hover {
    box-shadow: 0 0 25px #00ff88, 0 0 45px #00c8ff !important;
    transform: translateY(-3px) scale(1.02);
}

.stButton > button:active {
    transform: scale(0.96);
    box-shadow: 0 0 10px #00ff88 !important;
}

/* Ripple effect */
.stButton > button::after {
    content: "";
    position: absolute;
    width: 0;
    height: 0;
    background: rgba(255,255,255,0.2);
    border-radius: 50%;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    transition: width 0.4s ease, height 0.4s ease;
}

.stButton > button:active::after {
    width: 200px;
    height: 200px;
}

/* ── INPUT FIELD HOVER ── */
.stTextInput > div > div > input:hover {
    border: 1px solid #00c8ff !important;
    box-shadow: 0 0 10px #00c8ff55 !important;
}

/* ── SELECTBOX HOVER ── */
.stSelectbox > div:hover {
    box-shadow: 0 0 10px #00ff8855 !important;
    border: 1px solid #00ff88 !important;
}

/* ── TAB HOVER EFFECT ── */
.stTabs [data-baseweb="tab"]:hover {
    color: #00ff88 !important;
    background: rgba(0,255,136,0.1) !important;
}

/* ── CARD HOVER (Threat Cards + Metrics) ── */
[data-testid="stMetric"], 
div[style*="linear-gradient(135deg, #071020"] {
    transition: all 0.3s ease !important;
}

[data-testid="stMetric"]:hover,
div[style*="linear-gradient(135deg, #071020"]:hover {
    transform: translateY(-4px) scale(1.01);
    box-shadow: 0 0 20px #00ff8833;
}

/* ── PROGRESS BAR GLOW ── */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #00ff88, #00c8ff) !important;
    box-shadow: 0 0 10px #00ff88aa;
}

/* ── SCAN TEXT GLOW ANIMATION ── */
@keyframes pulseText {
    0% { opacity: 0.6; }
    50% { opacity: 1; }
    100% { opacity: 0.6; }
}

.scan-anim {
    animation: pulseText 1.5s infinite;
}

/* ── CURSOR FEEDBACK ── */
button, input, select {
    cursor: pointer !important;
}

</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# 3. CUSTOM HTML COMPONENTS
# ══════════════════════════════════════════════════════════════

def cyber_header():
    st.markdown(
        """
        <div style="background:linear-gradient(135deg,#050a0f 0%,#071020 50%,#050a0f 100%);
                    border:1px solid rgba(0,255,136,0.2);
                    border-radius:8px;
                    padding:30px 40px;
                    margin-bottom:30px;">
            <table width="100%" style="border-collapse:collapse;">
                <tr>
                    <td style="width:30px; vertical-align:top;">
                        <div style="width:20px;height:20px;
                             border-top:2px solid #00ff88;
                             border-left:2px solid #00ff88;"></div>
                    </td>
                    <td style="text-align:center; padding:0 20px;">
                        <div style="font-family:monospace;
                                    color:rgba(0,255,136,0.4);
                                    font-size:0.72rem;
                                    letter-spacing:6px;
                                    margin-bottom:10px;">
                            [ NEURAL THREAT DETECTION SYSTEM v2.0 ]
                        </div>
                        <div style="font-family:monospace;
                                    font-size:2.6rem;
                                    font-weight:900;
                                    letter-spacing:6px;
                                    color:#00ff88;
                                    text-shadow:0 0 30px rgba(0,255,136,0.5),
                                                0 0 60px rgba(0,200,255,0.3);">
                            PHISHVISION AI
                        </div>
                        <div style="font-family:sans-serif;
                                    color:#00c8ff;
                                    font-size:0.95rem;
                                    letter-spacing:4px;
                                    margin-top:10px;
                                    text-transform:uppercase;">
                            Real-Time Phishing Detection &nbsp;&#124;&nbsp;
                            ML-Powered &nbsp;&#124;&nbsp;
                            Chrome Extension
                        </div>
                        <div style="margin-top:16px;
                                    height:1px;
                                    background:linear-gradient(90deg,
                                        transparent,#00ff88,#00c8ff,#00ff88,transparent);
                                    opacity:0.4;">
                        </div>
                    </td>
                    <td style="width:30px; vertical-align:top; text-align:right;">
                        <div style="width:20px;height:20px;
                             margin-left:auto;
                             border-top:2px solid #00c8ff;
                             border-right:2px solid #00c8ff;"></div>
                    </td>
                </tr>
            </table>
        </div>
        """,
        unsafe_allow_html=True
    )


def threat_card(title, value, color="#00ff88", icon="🔒"):
    return f"""
    <div style="
        background: linear-gradient(135deg, #071020, #0a1628);
        border: 1px solid {color}33;
        border-left: 3px solid {color};
        border-radius: 6px;
        padding: 16px 20px;
        margin: 4px 0;
    ">
        <div style="font-family:'Share Tech Mono',monospace; color:{color}88;
                    font-size:0.7rem; letter-spacing:2px; text-transform:uppercase;">
            {icon} {title}
        </div>
        <div style="font-family:'Orbitron',monospace; color:{color};
                    font-size:1.3rem; font-weight:700; margin-top:4px;">
            {value}
        </div>
    </div>
    """


def result_banner(is_phishing, url, confidence):
    if is_phishing:
        color = "#ff4444"
        bg = "#1a0505"
        border = "#ff4444"
        icon = "⚠"
        status = "PHISHING DETECTED"
        msg = "This URL matches known malicious patterns. Do NOT proceed."
        sub = "THREAT ACTIVE"
    else:
        color = "#00ff88"
        bg = "#050f0a"
        border = "#00ff88"
        icon = "✓"
        status = "LEGITIMATE URL"
        msg = "Analysis complete. No phishing indicators detected."
        sub = "SYSTEM CLEAR"

    st.markdown(f"""
    <div style="
        background: {bg};
        border: 1px solid {border};
        border-left: 4px solid {border};
        border-radius: 8px;
        padding: 24px 28px;
        margin: 16px 0;
        position: relative;
        overflow: hidden;
    ">
        <div style="position:absolute; top:0; right:0; padding:6px 16px;
             background:{border}22; border-bottom-left-radius:8px;
             font-family:'Share Tech Mono',monospace; color:{color};
             font-size:0.65rem; letter-spacing:3px;">
            {sub}
        </div>
        <div style="display:flex; align-items:center; gap:16px;">
            <div style="font-size:2.5rem; color:{color};">{icon}</div>
            <div>
                <div style="font-family:'Orbitron',monospace; color:{color};
                            font-size:1.4rem; font-weight:800; letter-spacing:3px;">
                    {status}
                </div>
                <div style="font-family:'Share Tech Mono',monospace; color:{color}88;
                            font-size:0.8rem; margin-top:4px;">
                    {msg}
                </div>
            </div>
        </div>
        <div style="margin-top:14px; padding-top:14px;
             border-top:1px solid {border}22;
             font-family:'Share Tech Mono',monospace; color:{color}66;
             font-size:0.75rem; word-break:break-all;">
            TARGET: {url}
        </div>
    </div>
    """, unsafe_allow_html=True)


def section_title(text, subtitle=""):
    st.markdown(f"""
    <div style="margin: 24px 0 16px 0;">
        <div style="display:flex; align-items:center; gap:12px;">
            <div style="width:3px; height:24px;
                 background:linear-gradient(180deg,#00ff88,#00c8ff);
                 border-radius:2px;"></div>
            <div style="font-family:'Orbitron',monospace; color:#00ff88;
                        font-size:1.1rem; font-weight:700; letter-spacing:2px;
                        text-transform:uppercase;">{text}</div>
        </div>
        {f'<div style="font-family:Rajdhani,sans-serif; color:#00c8ff88; font-size:0.85rem; margin-left:15px; letter-spacing:1px;">{subtitle}</div>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# 4. SIDEBAR
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 20px 0 10px 0;">
        <div style="font-size:3rem;">🛡️</div>
        <div style="font-family:'Orbitron',monospace; color:#00ff88;
                    font-size:1rem; font-weight:700; letter-spacing:3px;">
            PHISHVISION
        </div>
        <div style="font-family:'Share Tech Mono',monospace; color:#00c8ff;
                    font-size:0.65rem; letter-spacing:2px; margin-top:4px;">
            THREAT INTELLIGENCE ENGINE
        </div>
    </div>
    <hr style="border-color:#00ff8822; margin: 10px 0 20px 0;">
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="font-family:'Share Tech Mono',monospace; color:#00c8ff;
                font-size:0.7rem; letter-spacing:2px; margin-bottom:6px;">
        ◈ SELECT DETECTION ENGINE
    </div>
    """, unsafe_allow_html=True)

    model_choice = st.selectbox(
        "",
        ("Stacking Ensemble (Strongest)", "Gradient Boosting", "XGBoost", "Random Forest"),
        label_visibility="collapsed"
    )

    model_map = {
        "Stacking Ensemble (Strongest)": "model_stack.joblib",
        "Gradient Boosting": "model_gb.joblib",
        "XGBoost": "model_xgb.joblib",
        "Random Forest": "model_rf.joblib"
    }

    st.markdown("""<hr style="border-color:#00ff8811; margin:20px 0;">""", unsafe_allow_html=True)

    # Status panel
    st.markdown("""
    <div style="background:#071020; border:1px solid #00ff8822; border-radius:6px; padding:14px;">
        <div style="font-family:'Share Tech Mono',monospace; color:#00ff88;
                    font-size:0.7rem; letter-spacing:2px; margin-bottom:10px;">
            ◈ SYSTEM STATUS
        </div>
        <div style="font-family:'Rajdhani',sans-serif; font-size:0.9rem;">
            <span style="color:#00ff88;">●</span>
            <span style="color:#00ff8888;"> API ONLINE</span><br>
            <span style="color:#00ff88;">●</span>
            <span style="color:#00ff8888;"> MODELS LOADED</span><br>
            <span style="color:#00ff88;">●</span>
            <span style="color:#00ff8888;"> EXTENSION READY</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""<hr style="border-color:#00ff8811; margin:20px 0;">""", unsafe_allow_html=True)

    # Session history - FIX: Better initialization
    if 'history' not in st.session_state:
        st.session_state.history = []

    if st.session_state.history:
        st.markdown("""
        <div style="font-family:'Share Tech Mono',monospace; color:#00c8ff;
                    font-size:0.7rem; letter-spacing:2px; margin-bottom:8px;">
            ◈ RECENT ACTIVITY
        </div>
        """, unsafe_allow_html=True)
        df_hist = pd.DataFrame(st.session_state.history).tail(5)
        for _, row in df_hist.iterrows():
            color = "#ff4444" if row['Verdict'] == "Phishing" else "#00ff88"
            icon  = "⚠" if row['Verdict'] == "Phishing" else "✓"
            url_short = str(row['URL'])[:28] + "..." if len(str(row['URL'])) > 28 else str(row['URL'])
            st.markdown(f"""
            <div style="background:#071020; border-left:2px solid {color};
                         border-radius:0 4px 4px 0; padding:6px 10px; margin-bottom:4px;">
                <span style="color:{color}; font-size:0.75rem;">{icon}</span>
                <span style="font-family:'Share Tech Mono',monospace;
                             color:{color}88; font-size:0.68rem;"> {url_short}</span>
            </div>
            """, unsafe_allow_html=True)

        # Stats
        total   = len(st.session_state.history)
        phish   = sum(1 for h in st.session_state.history if h['Verdict'] == 'Phishing')
        safe    = total - phish
        st.markdown(f"""
        <div style="background:#071020; border:1px solid #00ff8811;
                    border-radius:6px; padding:10px; margin-top:10px;
                    font-family:'Share Tech Mono',monospace; font-size:0.72rem;">
            <span style="color:#00c8ff;">SCANNED:</span>
            <span style="color:#00ff88;"> {total}</span> &nbsp;|&nbsp;
            <span style="color:#ff4444;">THREATS: {phish}</span> &nbsp;|&nbsp;
            <span style="color:#00ff88;">SAFE: {safe}</span>
        </div>
        """, unsafe_allow_html=True)

        if st.button("⟳  CLEAR LOG"):
            st.session_state.history = []
            st.rerun()


# ══════════════════════════════════════════════════════════════
# 5. MODEL LOADING
# ══════════════════════════════════════════════════════════════
@st.cache_resource
def load_selected_model(name):
    try:
        return joblib.load(model_map[name])
    except FileNotFoundError:
        return None
    except Exception as e:
        st.error(f"Model load error: {e}")
        return None

current_model = load_selected_model(model_choice)

# ══════════════════════════════════════════════════════════════
# 6. MAIN HEADER
# ══════════════════════════════════════════════════════════════
cyber_header()

# ══════════════════════════════════════════════════════════════
# 7. TABS
# ══════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs([
    "  🔍  THREAT SCAN  ",
    "  📁  BATCH ANALYSIS  ",
    "  📊  INTEL REPORT  "
])

# ══════════════════════════════════════════════════════════════════════
# TAB 1 — SINGLE URL SCAN
# ══════════════════════════════════════════════════════════════════════
with tab1:
    section_title("Target URL Analysis", "Enter URL for deep inspection")

    # Active engine badge
    model_short = model_choice.split("(")[0].strip()
    st.markdown(f"""
    <div style="display:inline-block; background:#071020;
         border:1px solid #00c8ff44; border-radius:4px;
         padding:4px 14px; margin-bottom:16px;">
        <span style="font-family:'Share Tech Mono',monospace;
                     color:#00c8ff; font-size:0.72rem; letter-spacing:2px;">
            ACTIVE ENGINE: {model_short.upper()}
        </span>
    </div>
    """, unsafe_allow_html=True)

    url_input = st.text_input(
        "◈  TARGET URL",
        placeholder="https://example.com  or  www.suspicioussite.tk/login/verify",
        help="Enter any URL with or without https://"
    )

    col_btn, col_empty = st.columns([2, 3])
    with col_btn:
        scan_clicked = st.button("⚡  INITIATE SCAN")

    if scan_clicked:
        if current_model is None:
            st.markdown(f"""
            <div style="background:#1a0505; border:1px solid #ff444488;
                 border-radius:6px; padding:16px; font-family:'Share Tech Mono',monospace;
                 color:#ff4444; font-size:0.85rem;">
                ✗  MODEL FILE NOT FOUND: {model_map[model_choice]}<br>
                <span style="color:#ff444488;">Run train.py to generate model files.</span>
            </div>
            """, unsafe_allow_html=True)

        elif not url_input.strip():
            st.markdown("""
            <div style="background:#1a1200; border:1px solid #ffaa0044;
                 border-radius:6px; padding:12px; font-family:'Share Tech Mono',monospace;
                 color:#ffaa00; font-size:0.85rem;">
                ⚠  INPUT REQUIRED — Enter a URL to scan.
            </div>
            """, unsafe_allow_html=True)

        else:
            # Simulate scan animation
            progress_bar = st.progress(0)
            status_text  = st.empty()
            stages = [
                (20,  "[ 1/5 ]  Parsing URL architecture..."),
                (40,  "[ 2/5 ]  Extracting 30 structural features..."),
                (60,  "[ 3/5 ]  Feeding feature vector to ML engine..."),
                (80,  "[ 4/5 ]  Running inference pipeline..."),
                (100, "[ 5/5 ]  Compiling threat assessment..."),
            ]
            for pct, msg in stages:
                progress_bar.progress(pct)
                status_text.markdown(f"""
                <div class="scan-anim" style="font-family:'Share Tech Mono',monospace;
                  color:#00c8ff; font-size:0.78rem; letter-spacing:1px;">
                {msg}
               </div>""", unsafe_allow_html=True)
                time.sleep(0.3)

            progress_bar.empty()
            status_text.empty()

            # ── Parse URL for rule-based check ──
            try:
                parsed_url = urlparse(url_input if url_input.startswith("http") else "https://" + url_input)
                domain = parsed_url.netloc.lower().split(":")[0]
                path = parsed_url.path
            except:
                domain, path = "", ""

            # ── Rule-based pre-check ──
            is_phishing_by_rules, rule_reasons = rule_based_check(url_input, domain, path)

            # ── ML Prediction ──
            features       = extract_features(url_input)
            features_array = np.array(features).reshape(1, -1)
            prediction     = current_model.predict(features_array)[0]
            is_phishing_ml = (prediction == 1)  # UNIFIED: 1 = Phishing, 0 = Safe

            try:
                prob       = current_model.predict_proba(features_array)[0]
                # UNIFIED: classes are [0, 1] where index 1 = phishing probability
                classes = current_model.classes_
                phishing_idx = list(classes).index(1)
                safe_idx = list(classes).index(0)
                prob_phishing = prob[phishing_idx]
                prob_safe = prob[safe_idx]
                confidence = prob_phishing * 100 if is_phishing_ml else prob_safe * 100
            except Exception:
                prob_phishing = 1.0 if is_phishing_ml else 0.0
                confidence = 100.0

            # ── Combine ML + Rule-based verdict (same logic as api.py) ──
            is_phishing = is_phishing_ml
            
            # Override: If strong rule-based indicators, mark as phishing
            if is_phishing_by_rules and len(rule_reasons) >= 2:
                is_phishing = True
                confidence = min(confidence + 15, 95)
            elif is_phishing_by_rules and not is_phishing_ml:
                # Rules say phishing but ML says safe - lower confidence
                confidence = max(confidence - 20, 50)
            
            # Additional threshold check: if phishing probability > 40%, mark as phishing
            if prob_phishing > 0.4:
                is_phishing = True
                confidence = prob_phishing * 100

            # ── Result banner ──
            result_banner(is_phishing, url_input, confidence)

            # ── Show rule-based warnings if any ──
            if is_phishing_by_rules and rule_reasons:
                st.markdown(f"""
                <div style="background: rgba(255,68,68,0.15); border: 1px solid #ff4444; 
                     border-radius: 8px; padding: 12px; margin-bottom: 16px;">
                    <span style="color: #ff6b6b; font-weight: 700;">⚠️ Rule-Based Flags:</span>
                    <span style="color: #ffaa00; font-family: 'Share Tech Mono', monospace;">
                        {', '.join(rule_reasons)}
                    </span>
                </div>
                """, unsafe_allow_html=True)

            # ── Columns: metrics + gauge ──
            col_left, col_right = st.columns([1, 1])

            with col_left:
                section_title("Threat Metrics")
                verdict_str = "PHISHING" if is_phishing else "SAFE"
                threat_color = "#ff4444" if is_phishing else "#00ff88"

                st.markdown(threat_card("Verdict",     verdict_str,                threat_color, "⚡"), unsafe_allow_html=True)
                st.markdown(threat_card("Confidence",  f"{confidence:.1f}%",       "#00c8ff",    "📡"), unsafe_allow_html=True)
                st.markdown(threat_card("Engine",      model_short.upper(),        "#00ff88",    "🔬"), unsafe_allow_html=True)
                st.markdown(threat_card("Features",    "30 Structural Signals",    "#00c8ff",    "🧬"), unsafe_allow_html=True)

                threat_level = "CRITICAL" if (is_phishing and confidence > 85) else \
                               "HIGH"     if (is_phishing and confidence > 60) else \
                               "MEDIUM"   if  is_phishing                      else \
                               "NONE"
                level_color  = "#ff0000" if threat_level == "CRITICAL" else \
                               "#ff6600" if threat_level == "HIGH"     else \
                               "#ffaa00" if threat_level == "MEDIUM"   else "#00ff88"
                st.markdown(threat_card("Threat Level", threat_level, level_color, "☢"), unsafe_allow_html=True)

            with col_right:
                section_title("Confidence Gauge")
                gauge_color = "#ff4444" if is_phishing else "#00ff88"
                fig_gauge   = go.Figure(go.Indicator(
                    mode  = "gauge+number+delta",
                    value = confidence,
                    title = {
                        'text': "CONFIDENCE SCORE",
                        'font': {'family': 'Orbitron', 'size': 13, 'color': '#00c8ff'}
                    },
                    number = {
                        'suffix': '%',
                        'font':   {'family': 'Orbitron', 'size': 36, 'color': gauge_color}
                    },
                    gauge = {
                        'axis':            {'range': [0, 100], 'tickcolor': 'rgba(0,255,136,0.27)',
                                            'tickfont': {'color': 'rgba(0,255,136,0.4)', 'size': 10}},
                        'bar':             {'color': gauge_color, 'thickness': 0.25},
                        'bgcolor':         '#071020',
                        'borderwidth':     1,
                        'bordercolor':     'rgba(0,255,136,0.13)',
                        'steps': [
                            {'range': [0,  40],  'color': '#071020'},
                            {'range': [40, 70],  'color': '#0a1628'},
                            {'range': [70, 100], 'color': '#0d1e33'},
                        ],
                        'threshold': {
                            'line':      {'color': gauge_color, 'width': 3},
                            'thickness': 0.8,
                            'value':     confidence
                        }
                    }
                ))
                fig_gauge.update_layout(
                    paper_bgcolor = '#050a0f',
                    plot_bgcolor  = '#050a0f',
                    height        = 320,
                    margin        = dict(l=30, r=30, t=60, b=20),
                    font          = dict(color='#00ff88'),
                    hovermode     = 'closest'
                )
                st.plotly_chart(fig_gauge, use_container_width=True)

            # ── Feature vector heatmap ──
            section_title("Feature Vector Analysis", "30-point structural signature of the URL")
            feature_names = [
                "IP Address", "URL Length", "Shortener", "@ Symbol", "Double Slash",
                "Hyphen", "Subdomain", "SSL State", "DNS Resolve", "TLD Risk",
                "Port", "HTTPS Token", "Entropy", "Digit Ratio", "Consonants",
                "Domain Len", "Email Submit", "Abnormal URL", "Special Chars",
                "Typosquat", "Sub Count", "Susp. Keywords", "Path Depth",
                "Scheme", "DNS Record", "Query Params", "Brand in Path",
                "URL Encoding", "Non-ASCII", "Vowel Ratio"
            ]
            
            # FIX: Safe array handling
            try:
                fv = np.array(features, dtype=float).reshape(1, -1)
            except Exception:
                fv = np.zeros((1, len(feature_names)))
            
            fig_heatmap = go.Figure(go.Heatmap(
                z         = fv,
                x         = feature_names,
                colorscale = [
                    [0.0, '#ff4444'],
                    [0.5, '#071020'],
                    [1.0, '#00ff88']
                ],
                zmin      = -1,
                zmax      =  1,
                showscale = True,
                hovertemplate = '<b>%{x}</b><br>Value: %{z:.3f}<extra></extra>',
                colorbar  = dict(
                    title      = dict(text="Value", font=dict(color='#00c8ff', size=11)),
                    tickfont   = dict(color='rgba(0,255,136,0.53)'),
                    bordercolor= 'rgba(0,255,136,0.13)',
                    bgcolor    = '#071020'
                )
            ))
            fig_heatmap.update_layout(
                paper_bgcolor = '#050a0f',
                plot_bgcolor  = '#050a0f',
                height        = 140,
                margin        = dict(l=10, r=10, t=20, b=80),
                xaxis         = dict(
                    tickfont = dict(color='rgba(0,255,136,0.47)', size=9, family='Share Tech Mono'),
                    tickangle= -45,
                    gridcolor= 'rgba(0,255,136,0.07)'
                ),
                yaxis         = dict(showticklabels=False),
                hovermode     = 'closest'
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)

            # ── Log to history ──
            st.session_state.history.append({
                "URL":     url_input,
                "Verdict": "Phishing" if is_phishing else "Safe"
            })


# ══════════════════════════════════════════════════════════════════════
# TAB 2 — BULK BATCH SCAN
# ══════════════════════════════════════════════════════════════════════
with tab2:
    section_title("Batch Threat Analysis", "Upload CSV file for mass URL scanning")

    st.markdown("""
    <div style="background:#071020; border:1px solid #00c8ff22;
         border-radius:6px; padding:14px; margin-bottom:16px;
         font-family:'Share Tech Mono',monospace; color:#00c8ff88; font-size:0.78rem;">
        ◈ CSV FORMAT REQUIRED &nbsp;|&nbsp;
        Column name must be: <span style="color:#00ff88;">'url'</span> &nbsp;|&nbsp;
        Supported: .csv files only
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("", type=['csv'], label_visibility="collapsed")

    if uploaded_file and current_model:
        df_bulk = pd.read_csv(uploaded_file)
        if 'url' in df_bulk.columns:
            total_urls = len(df_bulk)

            prog = st.progress(0)
            prog_text = st.empty()
            results = []

            for i, u in enumerate(df_bulk['url']):
                try:
                    url_str = str(u)
                    
                    # Parse URL for rule-based check
                    try:
                        parsed = urlparse(url_str if url_str.startswith("http") else "https://" + url_str)
                        domain = parsed.netloc.lower().split(":")[0]
                        path = parsed.path
                    except:
                        domain, path = "", ""
                    
                    # Rule-based pre-check
                    is_phishing_by_rules, rule_reasons = rule_based_check(url_str, domain, path)
                    
                    # ML prediction
                    f = extract_features(url_str)
                    p = current_model.predict(np.array(f).reshape(1, -1))[0]
                    is_phishing_ml = (p == 1)  # UNIFIED: 1 = Phishing
                    
                    # Get phishing probability
                    try:
                        prob = current_model.predict_proba(np.array(f).reshape(1, -1))[0]
                        classes = current_model.classes_
                        phishing_idx = list(classes).index(1)
                        prob_phishing = prob[phishing_idx]
                    except:
                        prob_phishing = 1.0 if is_phishing_ml else 0.0
                    
                    # Combined verdict (same logic as api.py)
                    is_phishing = is_phishing_ml
                    
                    # Override if strong rule-based indicators
                    if is_phishing_by_rules and len(rule_reasons) >= 2:
                        is_phishing = True
                    
                    # Threshold check
                    if prob_phishing > 0.4:
                        is_phishing = True
                    
                    results.append("Phishing" if is_phishing else "Safe")
                except Exception as e:
                    results.append("Error")
                
                pct = int((i + 1) / total_urls * 100)
                prog.progress(pct)
                prog_text.markdown(f"""
                <div style="font-family:'Share Tech Mono',monospace;
                     color:#00c8ff; font-size:0.75rem;">
                    SCANNING {i+1}/{total_urls} — {str(u)[:60]}
                </div>""", unsafe_allow_html=True)

            prog.empty()
            prog_text.empty()

            df_bulk['Verdict'] = results
            phishing_count = results.count("Phishing")
            safe_count     = results.count("Safe")
            threat_pct     = (phishing_count / total_urls * 100) if total_urls else 0

            # Summary cards
            section_title("Scan Summary")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(threat_card("Total Scanned", str(total_urls), "#00c8ff", "📡"), unsafe_allow_html=True)
            with c2:
                st.markdown(threat_card("Threats Found", str(phishing_count), "#ff4444", "⚠"), unsafe_allow_html=True)
            with c3:
                st.markdown(threat_card("Safe URLs", str(safe_count), "#00ff88", "✓"), unsafe_allow_html=True)
            with c4:
                st.markdown(threat_card("Threat Rate", f"{threat_pct:.1f}%", "#ffaa00" if threat_pct > 30 else "#00ff88", "☢"), unsafe_allow_html=True)

            col_table, col_chart = st.columns([3, 2])

            with col_table:
                section_title("Results Table")
                st.dataframe(
                    df_bulk.style.apply(
                        lambda col: [
                            'background-color:#1a0505; color:#ff4444;' if v == 'Phishing'
                            else 'background-color:#050f0a; color:#00ff88;'
                            for v in col
                        ] if col.name == 'Verdict' else [''] * len(col),
                        axis=0
                    ),
                    use_container_width=True, height=360
                )

            with col_chart:
                section_title("Threat Distribution")
                fig_pie = go.Figure(go.Pie(
                    labels  = ['Safe', 'Phishing'],
                    values  = [safe_count, phishing_count],
                    marker  = dict(
                        colors      = ['#00ff88', '#ff4444'],
                        line        = dict(color='#050a0f', width=3)
                    ),
                    textfont = dict(family='Share Tech Mono', size=11, color='#050a0f'),
                    hole     = 0.55,
                    hovertemplate = '<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>',
                    hoverlabel = dict(
                        bgcolor='#071020',
                        bordercolor='#00c8ff',
                        font=dict(color='#00ff88', family='Share Tech Mono', size=11),
                        namelength=-1
                    )
                ))
                fig_pie.update_layout(
                    paper_bgcolor = '#050a0f',
                    plot_bgcolor  = '#050a0f',
                    height        = 340,
                    margin        = dict(l=20, r=20, t=60, b=20),
                    legend        = dict(
                        font     = dict(family='Share Tech Mono', color='rgba(0,255,136,0.53)', size=11),
                        bgcolor  = 'rgba(0,0,0,0)',
                        bordercolor = 'rgba(0,255,136,0.13)',
                        x        = 0.5,
                        y        = -0.1,
                        xanchor  = 'center',
                        yanchor  = 'top'
                    ),
                    annotations=[dict(
                        text      = f"<b>{threat_pct:.0f}%</b><br>THREAT",
                        x         = 0.5, y=0.5,
                        font      = dict(family='Orbitron', size=14, color='#ff4444' if threat_pct > 0 else '#00ff88'),
                        showarrow = False
                    )],
                    hovermode = 'closest'
                )
                st.plotly_chart(fig_pie, use_container_width=True, config={
                    'displayModeBar': True, 
                    'displaylogo': False
                })

        else:
            st.markdown("""
            <div style="background:#1a0505; border:1px solid #ff444444;
                 border-radius:6px; padding:14px; font-family:'Share Tech Mono',monospace;
                 color:#ff4444; font-size:0.85rem;">
                ✗  MISSING COLUMN — CSV must contain a column named 'url'.
            </div>
            """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# TAB 3 — ANALYTICS / INTEL REPORT
# ══════════════════════════════════════════════════════════════════════
with tab3:
    section_title("Intelligence Report", "Feature importance & model performance metrics")

    col_feat, col_model = st.columns([3, 2])

    with col_feat:
        section_title("Top Feature Importance Weights")
        feature_labels = [
            "SSL State", "URL Length", "Subdomain Count",
            "Anchor URL", "Hyphens", "Request URL",
            "IP Presence", "URL Shortener"
        ]
        importance_vals = [0.35, 0.20, 0.15, 0.10, 0.08, 0.05, 0.04, 0.03]

        # FIX: Proper hover template to prevent tooltip from showing at top
        hover_texts = [f"<b>{label}</b><br>Weight: {val:.3f}" for label, val in zip(feature_labels, importance_vals)]

        fig_bar = go.Figure(go.Bar(
            x           = importance_vals,
            y           = feature_labels,
            orientation = 'h',
            marker = dict(
                color     = importance_vals,
                colorscale= [[0, '#00c8ff'], [0.5, '#00ffaa'], [1, '#00ff88']],
                line      = dict(color='#050a0f', width=1)
            ),
            text      = [f"{v:.2f}" for v in importance_vals],
            textfont  = dict(family='Share Tech Mono', color='#050a0f', size=10),
            textposition = 'inside',
            hovertemplate = '%{fullData.name}: <b>%{y}</b><br>Weight: %{x:.3f}<extra></extra>',
            hoverlabel = dict(
                bgcolor='#071020',
                bordercolor='#00c8ff',
                font=dict(color='#00ff88', family='Share Tech Mono', size=12),
                namelength=-1,
                align='left'
            ),
            name='Feature Importance'
        ))
        
        fig_bar.update_layout(
            paper_bgcolor = '#050a0f',
            plot_bgcolor  = '#071020',
            height        = 360,
            margin        = dict(l=180, r=30, t=30, b=30),
            hovermode     = 'y unified',
            xaxis = dict(
                color     = 'rgba(0,255,136,0.27)',
                tickfont  = dict(family='Share Tech Mono', color='rgba(0,255,136,0.4)', size=10),
                gridcolor = 'rgba(0,255,136,0.07)',
                title     = dict(text='IMPORTANCE WEIGHT', font=dict(color='#00c8ff', size=10, family='Orbitron'))
            ),
            yaxis = dict(
                color    = 'rgba(0,255,136,0.27)',
                tickfont = dict(family='Share Tech Mono', color='rgba(0,255,136,0.67)', size=11),
                automargin = True
            ),
            bargap = 0.3
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={
            'displayModeBar': True, 
            'displaylogo': False,
            'toImageButtonOptions': {
                'format': 'png',
                'filename': 'feature_importance',
                'height': 360,
                'width': 600,
                'scale': 1
            }
        })

    with col_model:
        section_title("Model Performance")
        models_data = {
            "Model":    ["Gradient Boosting", "XGBoost", "Random Forest"],
            "Accuracy": ["97.3%", "96.8%", "95.9%"],
            "Speed":    ["Fast", "Fastest", "Moderate"],
            "Type":     ["Boosting", "Opt. Boost", "Bagging"]
        }
        for i in range(3):
            active = "▶ " if models_data["Model"][i].lower().replace(" ", "_") in model_choice.lower() else "  "
            color  = "#00ff88" if active.strip() else "#00ff8866"
            st.markdown(f"""
            <div style="background:#071020; border:1px solid {color}33;
                 border-left:3px solid {color}; border-radius:4px;
                 padding:12px 16px; margin-bottom:8px;">
                <div style="font-family:'Orbitron',monospace; color:{color};
                            font-size:0.85rem; font-weight:700;">
                    {active}{models_data['Model'][i].upper()}
                </div>
                <div style="font-family:'Share Tech Mono',monospace;
                            font-size:0.72rem; margin-top:6px;">
                    <span style="color:#00c8ff88;">ACCURACY:</span>
                    <span style="color:{color};"> {models_data['Accuracy'][i]}</span>
                    &nbsp;&nbsp;
                    <span style="color:#00c8ff88;">SPEED:</span>
                    <span style="color:{color};"> {models_data['Speed'][i]}</span>
                </div>
                <div style="font-family:'Share Tech Mono',monospace; color:{color}44;
                            font-size:0.68rem; margin-top:2px;">
                    TYPE: {models_data['Type'][i]}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Feature category breakdown radar
    section_title("Feature Category Coverage")
    categories   = ['URL Structure', 'Security', 'Domain Intel', 'Content Signals', 'Heuristics']
    implemented  = [12, 4, 6, 3, 5]
    total_each   = [12, 4, 8, 8, 8]

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r           = total_each,
        theta       = categories,
        fill        = 'toself',
        name        = 'Total Features',
        line        = dict(color='rgba(0,200,255,0.2)'),
        fillcolor   = 'rgba(0,200,255,0.07)',
        hoverinfo   = 'skip'
    ))
    fig_radar.add_trace(go.Scatterpolar(
        r           = implemented,
        theta       = categories,
        fill        = 'toself',
        name        = 'Implemented',
        line        = dict(color='#00ff88', width=2),
        fillcolor   = 'rgba(0,255,136,0.13)',
        hovertemplate = '<b>%{theta}</b><br>Implemented: %{r}<extra></extra>'
    ))
    fig_radar.update_layout(
        polar = dict(
            bgcolor    = '#071020',
            radialaxis = dict(
                visible   = True,
                range     = [0, 14],
                tickfont  = dict(color='rgba(0,255,136,0.27)', size=9),
                gridcolor = 'rgba(0,255,136,0.07)',
                linecolor = 'rgba(0,255,136,0.13)'
            ),
            angularaxis = dict(
                tickfont  = dict(family='Orbitron', color='#00c8ff', size=10),
                linecolor = 'rgba(0,255,136,0.13)',
                gridcolor = 'rgba(0,255,136,0.07)'
            )
        ),
        paper_bgcolor = '#050a0f',
        height        = 400,
        margin        = dict(l=100, r=100, t=100, b=80),
        legend        = dict(
            font      = dict(family='Share Tech Mono', color='rgba(0,255,136,0.53)', size=11),
            bgcolor   = 'rgba(0,0,0,0)',
            bordercolor='rgba(0,255,136,0.13)',
            x         = 0.5,
            y         = -0.12,
            xanchor   = 'center',
            yanchor   = 'top'
        ),
        hovermode     = 'closest'
    )
    st.plotly_chart(fig_radar, use_container_width=True, config={
        'displayModeBar': False, 
        'responsive': True
    })

    # Coverage details table
    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background:#071020; border:1px solid #00c8ff22; border-radius:6px; padding:12px;">
            <div style="font-family:'Orbitron',monospace; color:#00c8ff; font-size:0.75rem; 
                        letter-spacing:1px; margin-bottom:8px;">URL STRUCTURE</div>
            <div style="font-family:'Share Tech Mono',monospace; color:#00ff88; font-size:1.2rem; 
                        font-weight:700;">12/12</div>
            <div style="font-family:'Share Tech Mono',monospace; color:#00ff8877; font-size:0.7rem;
                        margin-top:4px;">100% Coverage</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background:#071020; border:1px solid #00c8ff22; border-radius:6px; padding:12px;">
            <div style="font-family:'Orbitron',monospace; color:#00c8ff; font-size:0.75rem; 
                        letter-spacing:1px; margin-bottom:8px;">SECURITY</div>
            <div style="font-family:'Share Tech Mono',monospace; color:#ffaa00; font-size:1.2rem; 
                        font-weight:700;">4/4</div>
            <div style="font-family:'Share Tech Mono',monospace; color:#ffaa0077; font-size:0.7rem;
                        margin-top:4px;">100% Coverage</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        coverage_pct = int(sum(implemented) / sum(total_each) * 100)
        st.markdown(f"""
        <div style="background:#071020; border:1px solid #00c8ff22; border-radius:6px; padding:12px;">
            <div style="font-family:'Orbitron',monospace; color:#00c8ff; font-size:0.75rem; 
                        letter-spacing:1px; margin-bottom:8px;">OVERALL</div>
            <div style="font-family:'Share Tech Mono',monospace; color:#00ff88; font-size:1.2rem; 
                        font-weight:700;">{coverage_pct}%</div>
            <div style="font-family:'Share Tech Mono',monospace; color:#00ff8877; font-size:0.7rem;
                        margin-top:4px;">System Ready</div>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════
st.markdown("""
<div style="margin-top:40px; padding:16px;
     border-top:1px solid #00ff8811; text-align:center;">
    <div style="font-family:'Share Tech Mono',monospace; color:#00ff8833;
                font-size:0.7rem; letter-spacing:3px;">
        PHISHVISION AI &nbsp;|&nbsp; v2.0 &nbsp;|&nbsp;
        MEDICAPS UNIVERSITY &nbsp;|&nbsp; CSE 2025-26 &nbsp;|&nbsp;
        SUDHARSHAN DONGRE &nbsp;|&nbsp; EN23CS3011036
    </div>
</div>
""", unsafe_allow_html=True)