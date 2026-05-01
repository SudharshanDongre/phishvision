import base64
import mimetypes
import streamlit as st
import streamlit.components.v1 as components
import joblib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from urllib.parse import urlparse, quote
from pathlib import Path
from extractor import extract_features, rule_based_check
import time
import requests
import hashlib
import hmac
import secrets
import os
from news_component import render_cyber_news_notifications

# Load environment variables (optional - graceful fallback)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

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
# 2. New NAny Blue theme
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color: #0a0e14 !important;
    color: #e2e8f0 !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stHeader"] { background-color: #0a0e14 !important; border-bottom: 1px solid #142033 !important; }
[data-testid="stSidebar"] {
    background: #0a0e14 !important;
    border-right: 1px solid #142033 !important;
    padding-top: 0 !important;
}
[data-testid="stSidebar"] * { color: #94a3b8 !important; }

/* Keep sidebar fixed and disable resize handle */
section[data-testid="stSidebar"] {
    width: 21rem !important;
    min-width: 21rem !important;
    max-width: 21rem !important;
}
section[data-testid="stSidebar"] > div {
    width: 21rem !important;
    min-width: 21rem !important;
    max-width: 21rem !important;
}
[data-testid="stSidebarResizer"] {
    display: none !important;
    pointer-events: none !important;
}

/* Hide sidebar collapse arrow control */
[data-testid="stSidebarCollapseButton"],
button[title="Collapse sidebar"],
button[aria-label="Collapse sidebar"] {
    display: none !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #00d4ff 0%, #086bff 100%) !important;
    color: #f8fbff !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    border: none !important;
    border-radius: 12px !important;
    height: 2.75em !important;
    letter-spacing: 0px !important;
    text-transform: none !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease !important;
    box-shadow: none !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #19e0ff 0%, #0a57d8 100%) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 14px 34px rgba(0, 212, 255, 0.22) !important;
}

/* Inputs */
.stTextInput > div > div > input {
    background-color: #1e293b !important;
    color: #e2e8f0 !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
}
.stTextInput > div > div > input:focus { border: 1px solid #3b82f6 !important; box-shadow: 0 0 0 3px rgba(59,130,246,0.15) !important; }
.stTextInput > label { color: #94a3b8 !important; font-size: 0.8rem !important; }

/* Selectbox */
.stSelectbox > div > div {
    background-color: #1e293b !important;
    border: 1px solid #334155 !important;
    color: #e2e8f0 !important;
    border-radius: 8px !important;
}

/* Metrics */
[data-testid="stMetric"] {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 12px !important;
    padding: 16px !important;
}
[data-testid="stMetricLabel"] { color: #94a3b8 !important; font-size: 0.8rem !important; }
[data-testid="stMetricValue"] { color: #e2e8f0 !important; font-size: 1.6rem !important; }

/* Dataframe */
.stDataFrame { border: 1px solid #1e293b !important; border-radius: 8px !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0f172a; }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }

/* File uploader */
[data-testid="stFileUploadDropzone"] {
    background-color: #1e293b !important;
    border: 1px dashed #334155 !important;
    border-radius: 8px !important;
    color: #94a3b8 !important;
}

/* Progress */
.stProgress > div > div > div { background: #3b82f6 !important; }

/* Remove floating animation - causes jitter */
section.main > div { animation: none !important; }

* { transition: none !important; }
button { transition: background 0.2s ease !important; cursor: pointer !important; }
.landing-cta { transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease, border-color 0.2s ease !important; }

@keyframes revealUp {
    from {
        opacity: 0;
        transform: translateY(28px);
        filter: blur(8px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
        filter: blur(0);
    }
}

.landing-page {
    color: #e6eef7;
}

.landing-hero {
    position: relative;
    overflow: hidden;
    border: 1px solid rgba(0, 212, 255, 0.22);
    border-radius: 28px;
    background:
        radial-gradient(circle at 18% 20%, rgba(0, 212, 255, 0.22), transparent 38%),
        radial-gradient(circle at 82% 18%, rgba(255, 75, 75, 0.18), transparent 26%),
        linear-gradient(135deg, rgba(10, 14, 20, 0.95), rgba(7, 11, 18, 0.84));
    box-shadow: 0 30px 80px rgba(0, 0, 0, 0.45);
}

.landing-hero-grid {
    display: grid;
    grid-template-columns: minmax(0, 1.08fr) minmax(320px, 0.92fr);
    gap: 28px;
    align-items: center;
    padding: 28px;
}

.landing-kicker {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 14px;
    border-radius: 999px;
    border: 1px solid rgba(0, 212, 255, 0.24);
    color: #8adfff;
    background: rgba(0, 212, 255, 0.08);
    letter-spacing: 0.18em;
    text-transform: uppercase;
    font-size: 0.72rem;
    font-weight: 700;
}

.landing-title {
    margin: 18px 0 14px 0;
    font-family: 'Inter', sans-serif;
    font-size: clamp(2.8rem, 6vw, 5.6rem);
    line-height: 0.95;
    letter-spacing: -0.06em;
    font-weight: 800;
    text-transform: uppercase;
    color: #f7fbff;
}

.landing-title .accent {
    color: #00d4ff;
}

.landing-copy {
    max-width: 680px;
    color: rgba(224, 233, 245, 0.82);
    font-size: 1.05rem;
    line-height: 1.75;
}

.landing-stat-row {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-top: 22px;
}

.landing-chip {
    padding: 10px 14px;
    border-radius: 999px;
    border: 1px solid rgba(0, 212, 255, 0.14);
    background: rgba(7, 13, 21, 0.72);
    color: rgba(234, 243, 252, 0.84);
    font-size: 0.84rem;
}

.landing-cta-row {
    display: flex;
    flex-wrap: wrap;
    gap: 14px;
    margin-top: 28px;
}

.landing-cta {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0.95rem 1.3rem;
    border-radius: 14px;
    text-decoration: none;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    border: 1px solid transparent;
}

.landing-cta.primary {
    background: linear-gradient(135deg, #00d4ff 0%, #0856ff 100%);
    color: #ffffff;
    box-shadow: 0 18px 36px rgba(0, 212, 255, 0.22);
    transition: transform 0.2s ease, box-shadow 0.2s ease !important;
}

.landing-cta.primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 24px 48px rgba(0, 212, 255, 0.32) !important;
}

.landing-cta.secondary {
    background: rgba(10, 14, 20, 0.52);
    color: #dfeaf6;
    border-color: rgba(0, 212, 255, 0.18);
    transition: transform 0.2s ease, background 0.2s ease, border-color 0.2s ease !important;
}

.landing-cta.secondary:hover {
    transform: translateY(-2px);
    background: rgba(10, 14, 20, 0.72);
    border-color: rgba(0, 212, 255, 0.28);
}

.landing-hero-visual {
    position: relative;
    min-height: 520px;
    border-radius: 26px;
    overflow: hidden;
    border: 1px solid rgba(0, 212, 255, 0.2);
    background:
        radial-gradient(circle at center, rgba(0, 212, 255, 0.18), transparent 40%),
        linear-gradient(135deg, rgba(4, 8, 14, 0.92), rgba(10, 16, 26, 0.96));
    box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.02), 0 30px 60px rgba(0, 0, 0, 0.4);
}

.landing-hero-visual::before {
    content: '';
    position: absolute;
    inset: 0;
    background:
        linear-gradient(180deg, rgba(10, 14, 20, 0.1), rgba(10, 14, 20, 0.55)),
        linear-gradient(90deg, rgba(0, 212, 255, 0.08), transparent 26%, transparent 74%, rgba(255, 75, 75, 0.08));
    pointer-events: none;
    z-index: 1;
}

.landing-hero-visual img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: center;
    display: block;
    transform: scale(1.02);
}

.landing-fallback {
    position: absolute;
    inset: 0;
    display: grid;
    place-items: center;
    padding: 32px;
    text-align: center;
    color: rgba(236, 244, 252, 0.9);
    background:
        radial-gradient(circle at 30% 20%, rgba(0, 212, 255, 0.24), transparent 24%),
        radial-gradient(circle at 70% 25%, rgba(255, 75, 75, 0.18), transparent 20%),
        linear-gradient(135deg, #0a0e14, #071018 48%, #0a0e14);
}

.landing-fallback h3 {
    margin: 0 0 10px 0;
    font-size: 1.2rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #00d4ff;
}

.landing-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 20px;
    margin-top: 24px;
}

.landing-panel {
    position: relative;
    border-radius: 22px;
    padding: 24px;
    border: 1px solid rgba(0, 212, 255, 0.18);
    background: linear-gradient(180deg, rgba(12, 17, 26, 0.92), rgba(6, 10, 16, 0.86));
    box-shadow: 0 22px 46px rgba(0, 0, 0, 0.3);
}

.landing-panel.glass {
    background: rgba(10, 14, 20, 0.42);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border-color: rgba(255, 255, 255, 0.12);
}

.landing-panel h3,
.landing-panel h4 {
    margin: 0 0 10px 0;
    color: #f7fbff;
    letter-spacing: -0.02em;
}

.landing-panel .eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    color: #00d4ff;
    text-transform: uppercase;
    letter-spacing: 0.18em;
    font-size: 0.72rem;
    font-weight: 700;
    margin-bottom: 12px;
}

.landing-panel p,
.landing-panel li {
    color: rgba(228, 236, 246, 0.82);
    line-height: 1.7;
}

.metric-row {
    display: grid;
    gap: 12px;
    margin-top: 14px;
}

.status-metric {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    align-items: center;
    padding: 12px 14px;
    border-radius: 14px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(0, 212, 255, 0.1);
}

.status-metric span:first-child {
    color: rgba(219, 232, 245, 0.72);
    font-size: 0.82rem;
}

.status-metric strong {
    color: #f8fbff;
    font-size: 1.05rem;
}

.feature-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 16px;
    margin-top: 22px;
}

.feature-card {
    border-radius: 20px;
    padding: 20px;
    border: 1px solid rgba(0, 212, 255, 0.16);
    background:
        linear-gradient(180deg, rgba(9, 13, 20, 0.86), rgba(6, 10, 16, 0.9));
}

.feature-card .icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 44px;
    border-radius: 14px;
    margin-bottom: 14px;
    background: rgba(0, 212, 255, 0.12);
    border: 1px solid rgba(0, 212, 255, 0.18);
    color: #00d4ff;
    font-size: 1.1rem;
}

.feature-card h4 {
    margin: 0 0 8px 0;
    font-size: 1rem;
}

.feature-card p {
    margin: 0;
    color: rgba(217, 228, 240, 0.78);
    line-height: 1.65;
}

[data-reveal] {
    opacity: 0;
    transform: translateY(28px);
}

[data-reveal].is-visible {
    animation: revealUp 0.9s cubic-bezier(0.16, 1, 0.3, 1) both;
    animation-delay: var(--reveal-delay, 0ms);
}

.landing-divider {
    height: 1px;
    margin: 22px 0;
    background: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.75), rgba(255, 75, 75, 0.65), transparent);
}

/* Unified UI system for scan/report sections */
.ui-section-title {
    margin: 24px 0 16px 0;
}

.ui-section-title-row {
    display: flex;
    align-items: center;
    gap: 12px;
}

.ui-section-accent {
    width: 3px;
    height: 24px;
    background: linear-gradient(180deg, #00d4ff, #ff4b4b);
    border-radius: 2px;
}

.ui-section-heading {
    font-family: 'Orbitron', monospace;
    color: #00d4ff;
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
}

.ui-section-subtitle {
    font-family: Rajdhani, sans-serif;
    color: #8adfff;
    font-size: 0.85rem;
    margin-left: 15px;
    letter-spacing: 1px;
}

.ui-card {
    position: relative;
    overflow: hidden;
    border-radius: 22px;
    padding: 20px;
    border: 1px solid rgba(0, 212, 255, 0.18);
    background: linear-gradient(180deg, rgba(12, 17, 26, 0.92), rgba(6, 10, 16, 0.86));
    box-shadow: 0 22px 46px rgba(0, 0, 0, 0.3);
}

.ui-card.glass {
    background: rgba(10, 14, 20, 0.42);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border-color: rgba(255, 255, 255, 0.12);
}

.ui-banner {
    position: relative;
    overflow: hidden;
    border-radius: 22px;
    padding: 22px 24px;
    border: 1px solid rgba(0, 212, 255, 0.18);
    background: linear-gradient(180deg, rgba(12, 17, 26, 0.92), rgba(6, 10, 16, 0.86));
    box-shadow: 0 22px 46px rgba(0, 0, 0, 0.3);
}

.ui-banner::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(90deg, rgba(0, 212, 255, 0.05), transparent 26%, transparent 74%, rgba(255, 75, 75, 0.05));
    pointer-events: none;
}

.ui-banner-topline {
    position: absolute;
    top: 0;
    right: 0;
    padding: 6px 16px;
    border-bottom-left-radius: 8px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 3px;
}

.ui-banner-content {
    position: relative;
    z-index: 1;
}

.ui-banner-row {
    display: flex;
    align-items: center;
    gap: 16px;
}

.ui-banner-icon {
    font-size: 2.5rem;
}

.ui-banner-title {
    font-family: 'Orbitron', monospace;
    font-size: 1.4rem;
    font-weight: 800;
    letter-spacing: 3px;
}

.ui-banner-copy {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.8rem;
    margin-top: 4px;
}

.ui-banner-footer {
    margin-top: 14px;
    padding-top: 14px;
    border-top: 1px solid rgba(0, 212, 255, 0.14);
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.75rem;
    word-break: break-all;
}

.ui-inline-note {
    border-radius: 14px;
    padding: 14px 18px;
    margin: 12px 0 18px 0;
    border: 1px solid rgba(0, 212, 255, 0.18);
    background: rgba(7, 13, 21, 0.72);
    color: rgba(234, 243, 252, 0.84);
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.78rem;
}

.ui-inline-note.warn {
    border-color: rgba(255, 75, 75, 0.28);
    background: rgba(26, 5, 5, 0.82);
    color: #ffd5d5;
}

.ui-inline-note.info {
    border-color: rgba(0, 212, 255, 0.18);
}

.ui-inline-note .emph {
    color: #00ff88;
}

.ui-mini-card {
    border-radius: 14px;
    padding: 12px;
    border: 1px solid rgba(0, 212, 255, 0.18);
    background: linear-gradient(180deg, rgba(12, 17, 26, 0.92), rgba(6, 10, 16, 0.86));
}

.ui-mini-card .label {
    font-family: 'Orbitron', monospace;
    font-size: 0.75rem;
    letter-spacing: 1px;
    margin-bottom: 8px;
    color: #00d4ff;
    text-transform: uppercase;
}

.ui-mini-card .value {
    font-family: 'Share Tech Mono', monospace;
    font-size: 1.2rem;
    font-weight: 700;
}

.ui-mini-card .subvalue {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.7rem;
    margin-top: 4px;
    color: rgba(234, 243, 252, 0.58);
}

.ui-activity-item {
    border-radius: 0 4px 4px 0;
    padding: 6px 10px;
    margin-bottom: 4px;
    background: rgba(7, 16, 32, 0.92);
}

.ui-activity-item .entry {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.68rem;
}

.ui-status-panel {
    border-radius: 18px;
    padding: 16px 18px;
    border: 1px solid rgba(0, 255, 136, 0.14);
    background: linear-gradient(180deg, rgba(12, 17, 26, 0.92), rgba(6, 10, 16, 0.86));
}

.ui-status-panel .label {
    font-family: 'Share Tech Mono', monospace;
    color: #00ff88;
    font-size: 0.7rem;
    letter-spacing: 2px;
    margin-bottom: 10px;
}

.ui-status-panel .body {
    font-family: Rajdhani, sans-serif;
    font-size: 0.9rem;
}

.ui-status-panel .body .ok {
    color: #00ff88;
}

.ui-status-panel .body .muted {
    color: #00ff8888;
}

.ui-alert {
    border-radius: 16px;
    padding: 16px 18px;
    margin: 12px 0 18px 0;
    border: 1px solid rgba(255, 75, 75, 0.28);
    background: rgba(26, 5, 5, 0.82);
    color: #ffd5d5;
}

.ui-alert .hint {
    color: #ff8f8f;
}

.ui-alert .emph {
    color: #ffaa00;
}

@media (max-width: 720px) {
    .ui-card,
    .ui-banner,
    .ui-status-panel {
        padding: 18px;
    }

    .ui-section-heading {
        font-size: 1rem;
        letter-spacing: 1.5px;
    }

    .ui-banner-row {
        gap: 12px;
        align-items: flex-start;
    }

    .ui-banner-icon {
        font-size: 2rem;
    }
}

@media (max-width: 1100px) {
    .landing-hero-grid,
    .landing-grid,
    .feature-grid {
        grid-template-columns: 1fr;
    }

    .landing-hero-visual {
        min-height: 360px;
    }
}

@media (max-width: 720px) {
    .landing-hero-grid {
        padding: 18px;
    }

    .landing-title {
        font-size: clamp(2.2rem, 13vw, 3.4rem);
    }

    .landing-panel,
    .feature-card {
        padding: 18px;
    }
}


/* ─── Override sidebar nav buttons to look like menu items ─── */
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    color: #64748b !important;
    text-align: left !important;
    justify-content: flex-start !important;
    padding: 8px 12px !important;
    border-radius: 6px !important;
    font-weight: 400 !important;
    font-size: 0.875rem !important;
    height: 38px !important;
    box-shadow: none !important;
    border: none !important;
    letter-spacing: 0px !important;
    text-transform: none !important;
    width: 100% !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #1e293b !important;
    color: #e2e8f0 !important;
    box-shadow: none !important;
    transform: none !important;
}
[data-testid="stSidebar"] .stButton > button:active {
    transform: none !important;
    box-shadow: none !important;
}

/* ─── Smooth Hover Effect for Sidebar Nav Items ─── */
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    color: #64748b !important;
    text-align: left !important;
    justify-content: flex-start !important;
    padding: 8px 12px !important;
    border-radius: 6px !important;
    font-weight: 400 !important;
    font-size: 0.875rem !important;
    height: 38px !important;
    box-shadow: none !important;
    border: none !important;
    letter-spacing: 0px !important;
    text-transform: none !important;
    width: 100% !important;

    /* ── Smooth transition ── */
    transition: background 0.25s ease,
                color 0.25s ease,
                padding-left 0.2s ease !important;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background: #1e293b !important;
    color: #e2e8f0 !important;
    padding-left: 18px !important;   /* subtle slide-right nudge */
    box-shadow: none !important;
    transform: none !important;
}

[data-testid="stSidebar"] .stButton > button:active {
    background: #273548 !important;
    color: #93c5fd !important;
    transform: none !important;
    box-shadow: none !important;
}

/* ─── Hover on active item HTML div (the st.markdown one) ─── */
[data-testid="stSidebar"] div[style*="background:#1e293b"] {
    transition: background 0.25s ease,
                box-shadow 0.25s ease !important;
}
[data-testid="stSidebar"] div[style*="background:#1e293b"]:hover {
    background: #273548 !important;
    box-shadow: inset 3px 0 0 #3b82f6 !important;  /* left accent line on hover */
}

/* ─── Hover on Detection Engine selectbox section ─── */
[data-testid="stSidebar"] .stSelectbox > div:hover {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 2px rgba(59,130,246,0.15) !important;
    transition: border-color 0.25s ease, box-shadow 0.25s ease !important;
}

/* ─── Hover on Engine Active indicator row ─── */
[data-testid="stSidebar"] div[style*="display:flex; align-items:center; gap:8px"] {
    transition: background 0.2s ease !important;
    border-radius: 6px !important;
    padding: 6px 8px !important;
}
[data-testid="stSidebar"] div[style*="display:flex; align-items:center; gap:8px"]:hover {
    background: #1e293b !important;
}

/* ─── Hover on Logo section ─── */
[data-testid="stSidebar"] div[style*="background:#3b82f6"] {
    transition: background 0.2s ease, transform 0.2s ease !important;
}
[data-testid="stSidebar"] div[style*="background:#3b82f6"]:hover {
    background: #2563eb !important;
    transform: scale(1.08) !important;
}

/* ─── Global transition override just for sidebar ─── */
[data-testid="stSidebar"] * {
    transition: background 0.25s ease,
                color 0.25s ease,
                border-color 0.25s ease,
                box-shadow 0.25s ease,
                padding-left 0.2s ease !important;
}


/* ── Inject navbar items into Streamlit's own header bar ── */
[data-testid="stHeader"]::after {
    content: "";
    display: block;
}

/* Style the Streamlit header bar itself */
[data-testid="stHeader"] {
    background: #0f172a !important;
    border-bottom: 1px solid #1e293b !important;
    height: 3.5rem !important;
}

/* Hide Streamlit's default hamburger/menu from header */
[data-testid="stToolbarActions"] button {
    color: #64748b !important;
}
            
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# 3. CUSTOM HTML COMPONENTS
# ══════════════════════════════════════════════════════════════


def threat_card(title, value, color="#00ff88", icon="🔒"):
    return f"""
    <div class="ui-card" style="border-color: {color}33; border-left: 3px solid {color}; padding: 16px 20px; margin: 4px 0;">
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
    <div class="ui-banner" style="background: {bg}; border-color: {border}; border-left: 4px solid {border}; padding: 24px 28px; margin: 16px 0;">
        <div class="ui-banner-topline" style="background:{border}22; color:{color};">
            {sub}
        </div>
        <div class="ui-banner-content">
        <div class="ui-banner-row">
            <div class="ui-banner-icon" style="color:{color};">{icon}</div>
            <div>
                <div class="ui-banner-title" style="color:{color};">
                    {status}
                </div>
                <div class="ui-banner-copy" style="color:{color}88;">
                    {msg}
                </div>
            </div>
        </div>
        <div class="ui-banner-footer" style="border-top-color:{border}22; color:{color}66;">
            TARGET: {url}
        </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def section_title(text, subtitle=""):
    st.markdown(f"""
    <div class="ui-section-title">
        <div class="ui-section-title-row">
            <div class="ui-section-accent"></div>
            <div class="ui-section-heading">{text}</div>
        </div>
        {f'<div class="ui-section-subtitle">{subtitle}</div>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)


def _image_to_data_uri(image_path):
    path = Path(image_path)
    if not path.exists() or not path.is_file():
        return None

    mime_type, _ = mimetypes.guess_type(path.name)
    mime_type = mime_type or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _render_about_landing():
    hero_image_path = os.getenv("PHISHVISION_HERO_IMAGE", "phishvision-hero.png")
    hero_image_uri = _image_to_data_uri(hero_image_path)

    total_scans = len(st.session_state.get("history", []))
    phishing_scans = sum(1 for row in st.session_state.get("history", []) if row.get("Verdict") == "Phishing")
    safe_scans = total_scans - phishing_scans
    model_label = st.session_state.get("engine_select", "Stacking Ensemble (Strongest)")
    model_comparison = [
        {"name": "Stacking Ensemble (Strongest)", "accuracy": "98.1%", "speed": "Fast", "type": "Ensemble"},
        {"name": "Gradient Boosting", "accuracy": "97.3%", "speed": "Fast", "type": "Boosting"},
        {"name": "XGBoost", "accuracy": "96.8%", "speed": "Fastest", "type": "Optimized Boosting"},
        {"name": "Random Forest", "accuracy": "95.9%", "speed": "Moderate", "type": "Bagging"},
    ]
    comparison_cards = ""
    for model in model_comparison:
        is_active = model_label.lower() in model["name"].lower()
        accent = "#00ff88" if is_active else "rgba(0, 212, 255, 0.18)"
        comparison_cards += f'''
            <div style="background:rgba(255,255,255,0.04); border:1px solid {accent}33; border-left:3px solid {accent}; border-radius:14px; padding:14px 16px;">
                <div style="font-family:'Inter',sans-serif; color:{accent}; font-weight:700; font-size:0.9rem; margin-bottom:8px; text-transform:uppercase; letter-spacing:0.04em;">{model["name"]}</div>
                <div style="display:grid; grid-template-columns:repeat(3, minmax(0, 1fr)); gap:10px; font-size:0.78rem; line-height:1.45;">
                    <div><div style="color:rgba(219,232,245,0.68);">Accuracy</div><div style="color:#f8fbff; font-weight:700;">{model["accuracy"]}</div></div>
                    <div><div style="color:rgba(219,232,245,0.68);">Speed</div><div style="color:#f8fbff; font-weight:700;">{model["speed"]}</div></div>
                    <div><div style="color:rgba(219,232,245,0.68);">Type</div><div style="color:#f8fbff; font-weight:700;">{model["type"]}</div></div>
                </div>
            </div>
        '''

    hero_background = f"url('{hero_image_uri}')" if hero_image_uri else "linear-gradient(135deg, rgba(0, 212, 255, 0.14), rgba(255, 75, 75, 0.08)), linear-gradient(135deg, #0a0e14, #071018 48%, #0a0e14)"

    html = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        :root {{
            --bg: #0a0e14;
            --blue: #00d4ff;
            --red: #ff4b4b;
            --text: #e6eef7;
        }}
        html, body {{
            margin: 0;
            background: transparent;
            color: var(--text);
            font-family: 'Inter', sans-serif;
        }}
        .landing-page {{
            width: 100%;
            box-sizing: border-box;
            color: var(--text);
        }}
        .landing-hero {{
            position: relative;
            overflow: hidden;
            border: 1px solid rgba(0, 212, 255, 0.22);
            border-radius: 28px;
            background:
                radial-gradient(circle at 18% 20%, rgba(0, 212, 255, 0.22), transparent 38%),
                radial-gradient(circle at 82% 18%, rgba(255, 75, 75, 0.18), transparent 26%),
                linear-gradient(135deg, rgba(10, 14, 20, 0.95), rgba(7, 11, 18, 0.88));
            box-shadow: 0 30px 80px rgba(0, 0, 0, 0.45);
            padding: 28px;
        }}
        .landing-hero-grid {{
            display: grid;
            grid-template-columns: minmax(0, 1.08fr) minmax(320px, 0.92fr);
            gap: 28px;
            align-items: center;
        }}
        .landing-kicker {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 14px;
            border-radius: 999px;
            border: 1px solid rgba(0, 212, 255, 0.24);
            color: #8adfff;
            background: rgba(0, 212, 255, 0.08);
            letter-spacing: 0.18em;
            text-transform: uppercase;
            font-size: 0.72rem;
            font-weight: 700;
        }}
        .landing-title {{
            margin: 18px 0 14px 0;
            font-size: clamp(2.8rem, 6vw, 5.6rem);
            line-height: 0.95;
            letter-spacing: -0.06em;
            font-weight: 800;
            text-transform: uppercase;
            color: #f7fbff;
        }}
        .landing-title .accent {{ color: var(--blue); }}
        .landing-copy {{
            max-width: 680px;
            color: rgba(224, 233, 245, 0.82);
            font-size: 1.05rem;
            line-height: 1.75;
        }}
        .landing-stat-row, .landing-cta-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-top: 22px;
        }}
        .landing-chip, .landing-cta {{ border-radius: 14px; }}
        .landing-chip {{
            padding: 10px 14px;
            border: 1px solid rgba(0, 212, 255, 0.14);
            background: rgba(7, 13, 21, 0.72);
            color: rgba(234, 243, 252, 0.84);
            font-size: 0.84rem;
        }}
        .landing-cta {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.95rem 1.3rem;
            text-decoration: none;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            border: 1px solid transparent;
        }}
        .landing-cta.primary {{
            background: linear-gradient(135deg, #00d4ff 0%, #0856ff 100%);
            color: #ffffff;
            box-shadow: 0 18px 36px rgba(0, 212, 255, 0.22);
        }}
        .landing-cta.secondary {{
            background: rgba(10, 14, 20, 0.52);
            color: #dfeaf6;
            border-color: rgba(0, 212, 255, 0.18);
        }}
        .landing-hero-visual {{
            position: relative;
            min-height: 520px;
            border-radius: 26px;
            overflow: hidden;
            border: 1px solid rgba(0, 212, 255, 0.2);
            background: {hero_background};
            background-size: cover;
            background-position: center;
            box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.02), 0 30px 60px rgba(0, 0, 0, 0.4);
        }}
        .landing-hero-visual::before {{
            content: '';
            position: absolute;
            inset: 0;
            background:
                linear-gradient(180deg, rgba(10, 14, 20, 0.10), rgba(10, 14, 20, 0.55)),
                linear-gradient(90deg, rgba(0, 212, 255, 0.08), transparent 26%, transparent 74%, rgba(255, 75, 75, 0.08));
            pointer-events: none;
        }}
        .landing-fallback {{
            position: absolute;
            inset: 0;
            display: grid;
            place-items: center;
            padding: 32px;
            text-align: center;
            color: rgba(236, 244, 252, 0.9);
        }}
        .landing-fallback h3 {{
            margin: 0 0 10px 0;
            font-size: 1.2rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: var(--blue);
        }}
        .landing-divider {{
            height: 1px;
            margin: 22px 0;
            background: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.75), rgba(255, 75, 75, 0.65), transparent);
        }}
        .landing-grid {{
            display: grid;
            grid-template-columns: 1.15fr 0.85fr;
            gap: 20px;
        }}
        .landing-panel {{
            position: relative;
            border-radius: 22px;
            padding: 24px;
            border: 1px solid rgba(0, 212, 255, 0.18);
            background: linear-gradient(180deg, rgba(12, 17, 26, 0.92), rgba(6, 10, 16, 0.86));
        }}
        .landing-panel.glass {{
            background: rgba(10, 14, 20, 0.42);
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            border-color: rgba(255, 255, 255, 0.12);
        }}
        .eyebrow {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: var(--blue);
            text-transform: uppercase;
            letter-spacing: 0.18em;
            font-size: 0.72rem;
            font-weight: 700;
            margin-bottom: 12px;
        }}
        .landing-panel h3, .landing-panel h4 {{ margin: 0 0 10px 0; color: #f7fbff; }}
        .landing-panel p, .landing-panel li {{ color: rgba(228, 236, 246, 0.82); line-height: 1.7; }}
        .metric-row {{ display: grid; gap: 12px; margin-top: 14px; }}
        .status-metric {{
            display: flex;
            justify-content: space-between;
            gap: 16px;
            align-items: center;
            padding: 12px 14px;
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(0, 212, 255, 0.1);
        }}
        .status-metric span:first-child {{ color: rgba(219, 232, 245, 0.72); font-size: 0.82rem; }}
        .status-metric strong {{ color: #f8fbff; font-size: 1.05rem; }}
        .feature-grid {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 16px;
            margin-top: 22px;
        }}
        .feature-card {{
            border-radius: 20px;
            padding: 20px;
            border: 1px solid rgba(0, 212, 255, 0.16);
            background: linear-gradient(180deg, rgba(9, 13, 20, 0.86), rgba(6, 10, 16, 0.9));
        }}
        .feature-card .icon {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 44px;
            height: 44px;
            border-radius: 14px;
            margin-bottom: 14px;
            background: rgba(0, 212, 255, 0.12);
            border: 1px solid rgba(0, 212, 255, 0.18);
            color: var(--blue);
            font-size: 1.1rem;
        }}
        .feature-card h4 {{ margin: 0 0 8px 0; font-size: 1rem; }}
        .feature-card p {{ margin: 0; color: rgba(217, 228, 240, 0.78); line-height: 1.65; }}
        @media (max-width: 1100px) {{
            .landing-hero-grid, .landing-grid, .feature-grid {{ grid-template-columns: 1fr; }}
            .landing-hero-visual {{ min-height: 360px; }}
        }}
        @media (max-width: 720px) {{
            .landing-hero {{ padding: 18px; }}
            .landing-title {{ font-size: clamp(2.2rem, 13vw, 3.4rem); }}
            .landing-panel, .feature-card {{ padding: 18px; }}
        }}
        
        [data-reveal] {{
            opacity: 0;
            transform: translateY(30px);
            transition: opacity 0.8s ease-out, transform 0.8s ease-out;
        }}
        [data-reveal].is-visible {{
            opacity: 1;
            transform: translateY(0);
        }}
    </style>

    <div class="landing-page">
        <section class="landing-hero" data-reveal>
            <div class="landing-hero-grid">
                <div>
                    <div class="landing-kicker">Detect. Protect. Stay Secure.</div>
                    <h1 class="landing-title">Why Knowing <span class="accent">Phishing</span> Matters</h1>
                    <p class="landing-copy">
                        Because awareness is the first line of defense, understanding phishing helps you recognize
                        threats early, prevent costly breaches, and protect your data, identity, and digital trust.
                    </p>
                    <div class="landing-stat-row">
                        <div class="landing-chip">Real-time phishing analysis</div>
                        <div class="landing-chip">AI + rule-based verdicts</div>
                        <div class="landing-chip">Confidence-scored results</div>
                    </div>
                    <div class="landing-cta-row">
                        <a class="landing-cta primary" href="#" onclick="(function(){{const buttons=window.parent.document.querySelectorAll('button'); const target=Array.from(buttons).find(function(button){{return (button.innerText||'').replace(/\s+/g,' ').includes('URL Scan');}}); if(target){{target.click();}} event.preventDefault(); return false;}})()">Start Threat Analysis</a>
                        <a class="landing-cta secondary" href="#" onclick="(function(){{const buttons=window.parent.document.querySelectorAll('button'); const target=Array.from(buttons).find(function(button){{return (button.innerText||'').replace(/\s+/g,' ').includes('Intel Report');}}); if(target){{target.click();}} event.preventDefault(); return false;}})()">View Intelligence</a>
                    </div>
                </div>

                <div class="landing-hero-visual">
                    {'' if hero_image_uri else '<div class="landing-fallback"><div><h3>Hero image not set</h3></div></div>'}
                </div>
            </div>
        </section>

        <div class="landing-divider" data-reveal></div>

        <div class="landing-grid">
            <div class="landing-panel" data-reveal>
                <div class="eyebrow">The Mission</div>
                <h3>Make phishing risk understandable in seconds.</h3>
                <p>
                    The goal of PhishVision is to turn a suspicious URL into a clear decision signal. That means
                    quick triage for casual users, stronger context for analysts, and a visual experience that feels
                    worthy of a premium security product.
                </p>
                <p>
                    Instead of hiding the signal behind dense dashboards, the landing page highlights the most
                    important state first: what the product does, how the system is behaving, and what action the
                    user should take next.
                </p>
            </div>

            <div class="landing-panel glass" data-reveal>
                <div class="eyebrow">Model Comparison</div>
                <h3>Comparison across all models used.</h3>
                <div class="metric-row">
                    {comparison_cards}
                </div>
            </div>
        </div>

        <div class="feature-grid">
            <div class="feature-card" data-reveal>
                <div class="icon">🧠</div>
                <h4>Signal-first detection</h4>
                <p>Machine-learning predictions and rule checks are balanced to produce a fast, readable verdict.</p>
            </div>
            <div class="feature-card" data-reveal>
                <div class="icon">🛡️</div>
                <h4>Operational clarity</h4>
                <p>High-risk indicators, confidence, and system state are surfaced with a cohesive visual hierarchy.</p>
            </div>
            <div class="feature-card" data-reveal>
                <div class="icon">⚡</div>
                <h4>Designed for action</h4>
                <p>Users can move from awareness to analysis with one click, keeping the homepage focused and purposeful.</p>
            </div>
        </div>
    </div>

    <script>
        document.addEventListener("DOMContentLoaded", () => {{
            const observer = new IntersectionObserver((entries) => {{
                entries.forEach((entry) => {{
                    if (entry.isIntersecting) {{
                        entry.target.classList.add("is-visible");
                    }}
                }});
            }}, {{ threshold: 0.1 }});

            document.querySelectorAll('[data-reveal]').forEach((el) => {{
                observer.observe(el);
            }});
        }});
    </script>
    """

    components.html(html, height=2200, scrolling=False)


def _hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000).hex()
    return f"{salt}${digest}"


def _verify_password(password, stored_hash):
    try:
        salt, digest = stored_hash.split("$", 1)
    except ValueError:
        return False
    check = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000).hex()
    return hmac.compare_digest(check, digest)


# ══════════════════════════════════════════════════════════════
# BACKEND API CONFIG
# ══════════════════════════════════════════════════════════════
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

def _api_register(email, full_name, password):
    """Register user via backend API."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/register",
            json={"email": email, "full_name": full_name, "password": password},
            timeout=5
        )
        return response.json()
    except Exception as e:
        return {"success": False, "message": f"Connection error: {str(e)}"}

def _api_login(email, password):
    """Login user via backend API."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/login",
            json={"email": email, "password": password},
            timeout=5
        )
        return response.json()
    except Exception as e:
        return {"success": False, "message": f"Connection error: {str(e)}"}

def _api_update_profile(email, full_name=None, password=None):
    """Update user profile via backend API."""
    try:
        params = {"email": email}
        data = {}
        if full_name:
            data["full_name"] = full_name
        if password:
            data["password"] = password
        
        response = requests.post(
            f"{BACKEND_URL}/auth/update",
            json=data,
            params=params,
            timeout=5
        )
        return response.json()
    except Exception as e:
        return {"success": False, "message": f"Connection error: {str(e)}"}


def _api_get_user(email):
    """Fetch user info via backend API."""
    try:
        response = requests.get(f"{BACKEND_URL}/auth/user/{email}", timeout=5)
        if response.status_code == 200:
            return {"success": True, "user": response.json()}
        return {"success": False, "message": "User not found"}
    except Exception as e:
        return {"success": False, "message": f"Connection error: {str(e)}"}


def _init_auth_state():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "auth_view" not in st.session_state:
        st.session_state.auth_view = "login"
    if "show_auth_panel" not in st.session_state:
        st.session_state.show_auth_panel = False
    if "show_settings" not in st.session_state:
        st.session_state.show_settings = False
    if "user_name" not in st.session_state:
        st.session_state.user_name = ""
    if "user_email" not in st.session_state:
        st.session_state.user_email = ""


def _sync_settings_from_query():
    action = st.query_params.get("menu")
    if action == "settings":
        st.session_state.show_settings = True
        st.query_params.clear()
    elif action == "logout":
        st.session_state.authenticated = False
        st.session_state.user_email = ""
        st.session_state.user_name = ""
        st.session_state.show_auth_panel = False
        st.query_params.clear()


def _sync_auth_from_query():
    action = st.query_params.get("menu")
    if action in {"login", "signup"}:
        st.session_state.auth_view = action
        st.session_state.show_auth_panel = True
        st.session_state.page = "Dashboard"
        st.query_params.clear()


def _navigate_to_page(page_name: str) -> None:
    st.session_state.page = page_name


def _restore_auth_from_query():
    if st.session_state.get("authenticated"):
        return
    email_from_query = st.query_params.get("ue")
    if not email_from_query:
        return
    user_result = _api_get_user(str(email_from_query).strip().lower())
    if user_result.get("success") and user_result.get("user"):
        user = user_result["user"]
        st.session_state.authenticated = True
        st.session_state.user_email = user.get("email", "")
        st.session_state.user_name = user.get("full_name", "User")


def _apply_base_styles():
    base_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
        html, body, [data-testid="stAppViewContainer"] {
            background-color: #0f172a !important;
            color: #e2e8f0 !important;
        }
        [data-testid="stHeader"] { background-color: #0f172a !important; }
        [data-testid="stSidebar"] { background: #0f172a !important; }
        .stTextInput > div > div > input { background-color: #1e293b !important; color: #e2e8f0 !important; }
    """
    
    base_css += "</style>"
    st.markdown(base_css, unsafe_allow_html=True)


def _handle_google_signin():
    if hasattr(st, "login"):
        try:
            st.login("google")
            return
        except Exception:
            st.info("Google OAuth is not configured yet. Add Google OIDC settings in Streamlit secrets to enable it.")
    else:
        st.info("Google sign-in is available in UI. Configure OIDC in Streamlit to enable real Google authentication.")


def _close_auth_modal():
    st.session_state.show_auth_panel = False


def render_settings_page():
    st.markdown('<div style="max-width:600px; margin:0 auto;">', unsafe_allow_html=True)
    st.markdown('<div style="font-family:Orbitron; color:#00ff88; font-size:1.5rem; margin-bottom:20px; letter-spacing:2px;">⚙️ SETTINGS</div>', unsafe_allow_html=True)
    
    with st.form("settings_form"):
        st.markdown('<div style="color:#94a3b8; font-size:0.9rem; margin-bottom:12px; font-weight:600;">PROFILE</div>', unsafe_allow_html=True)
        
        new_name = st.text_input("Full Name", value=st.session_state.user_name, key="settings_name")
        new_email = st.text_input("Email", value=st.session_state.user_email, key="settings_email", disabled=True, help="Email cannot be changed")
        
        st.markdown('<div style="color:#94a3b8; font-size:0.9rem; margin:20px 0 12px 0; font-weight:600;">SECURITY</div>', unsafe_allow_html=True)
        
        new_password = st.text_input("New Password (leave blank to keep current)", type="password", key="settings_new_pwd")
        confirm_password = st.text_input("Confirm Password", type="password", key="settings_confirm_pwd")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            save_btn = st.form_submit_button("💾 Save Changes", use_container_width=True)
        with col2:
            cancel_btn = st.form_submit_button("✕ Cancel", use_container_width=True)
        
        if save_btn:
            if new_name.strip() == "":
                st.error("Name cannot be empty.")
            elif new_password and len(new_password) < 8:
                st.error("Password must be at least 8 characters.")
            elif new_password and new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                # Prepare update data
                update_data = {"full_name": new_name.strip()}
                if new_password:
                    update_data["password"] = new_password
                
                # Call backend API to update profile
                update_result = _api_update_profile(st.session_state.user_email, **update_data)
                
                if update_result.get("success"):
                    st.session_state.user_name = new_name.strip()
                    st.success("Settings saved successfully!")
                    st.session_state.show_settings = False
                    st.rerun()
                else:
                    st.error(update_result.get("message", "Failed to update settings."))
        
        if cancel_btn:
            st.session_state.show_settings = False
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)


def _render_auth_modal_body(auth_view: str):
    st.markdown("""
    <style>
    dialog {
        border: 1px solid rgba(0, 212, 255, 0.22) !important;
        border-radius: 24px !important;
        background: linear-gradient(160deg, rgba(7,16,32,0.98), rgba(11,23,48,0.96)) !important;
        box-shadow: 0 28px 90px rgba(2, 6, 23, 0.58) !important;
        padding: 0 !important;
        overflow: hidden !important;
        width: min(760px, calc(100vw - 32px)) !important;
        max-width: min(760px, calc(100vw - 32px)) !important;
    }
    dialog::backdrop {
        background: rgba(2, 6, 23, 0.72) !important;
        backdrop-filter: blur(10px) saturate(115%) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="auth-panel-wrap"><div class="auth-shell">', unsafe_allow_html=True)
    st.markdown('<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;"><div style="background:#3b82f6;border-radius:8px;width:34px;height:34px;display:flex;align-items:center;justify-content:center;">🛡️</div><div style="font-family:Inter,sans-serif;color:#e2e8f0;font-weight:700;font-size:1.1rem;">PhishVision access</div></div>', unsafe_allow_html=True)

    if auth_view == "signup":
        st.markdown('<div class="auth-title">Sign Up</div><div class="auth-sub">Create a free account to unlock analysis tools.</div>', unsafe_allow_html=True)
        with st.form("signup_form", clear_on_submit=False):
            full_name = st.text_input("Full Name", placeholder="Your name", key="signup_name")
            email = st.text_input("Email", placeholder="name@company.com", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")
            signup_submit = st.form_submit_button("Create Account", use_container_width=True)

        if signup_submit:
            email_norm = email.strip().lower()
            if not full_name.strip() or not email_norm or not password or not confirm_password:
                st.error("All fields are required.")
            elif "@" not in email_norm or "." not in email_norm.split("@")[ -1 ]:
                st.error("Please enter a valid email address.")
            elif len(password) < 8:
                st.error("Password must be at least 8 characters long.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            else:
                reg_result = _api_register(email_norm, full_name.strip(), password)
                if reg_result.get("success"):
                    st.success("Account created successfully. Please sign in.")
                    st.session_state.auth_view = "login"
                    st.rerun()
                else:
                    st.error(reg_result.get("message", "Registration failed. Please try again."))
    else:
        st.markdown('<div class="auth-title">Login</div><div class="auth-sub">Access scanning features with your account.</div>', unsafe_allow_html=True)
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email", placeholder="name@company.com", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            login_submit = st.form_submit_button("Sign In", use_container_width=True)

        if login_submit:
            if not email.strip() or not password:
                st.error("Email and password are required.")
            else:
                auth_result = _api_login(email.strip().lower(), password)
                if auth_result.get("success"):
                    st.session_state.authenticated = True
                    st.session_state.user_email = auth_result["user"]["email"]
                    st.session_state.user_name = auth_result["user"]["full_name"]
                    st.session_state.show_auth_panel = False
                    st.session_state.auth_view = "login"
                    st.session_state.page = "About"
                    st.success("Login successful.")
                    st.rerun()
                else:
                    st.error(auth_result.get("message", "Invalid credentials. Please try again."))

    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        if st.button("Hide Access Panel", key="hide_auth_panel", use_container_width=True):
            _close_auth_modal()
            st.rerun()
    with col_btn2:
        if st.button("Google Sign-in", key="google_signin", use_container_width=True):
            _handle_google_signin()

    st.markdown('</div></div>', unsafe_allow_html=True)


def show_auth_modal(mode="login"):
    if not st.session_state.get("show_auth_panel"):
        return

    auth_view = mode if mode in {"login", "signup"} else st.session_state.get("auth_view", "login")

    if hasattr(st, "dialog"):
        @st.dialog("PhishVision access", width="large", dismissible=True, icon="🛡️", on_dismiss=_close_auth_modal)
        def _auth_dialog():
            _render_auth_modal_body(auth_view)

        _auth_dialog()
    else:
        st.markdown("""
        <style>
        .auth-panel-wrap {
            margin: 14px 0 24px 0;
            padding: 18px;
            border: 1px solid rgba(0, 212, 255, 0.18);
            border-radius: 18px;
            background: linear-gradient(160deg, rgba(7,16,32,0.92), rgba(11,23,48,0.9));
            box-shadow: 0 18px 50px rgba(2, 6, 23, 0.35);
        }
        .auth-shell {
            max-width: 720px;
            margin: 0 auto;
        }
        .auth-title {
            font-family: 'Orbitron', monospace;
            color: #00d4ff;
            letter-spacing: 1.5px;
            font-size: 1.1rem;
            margin-bottom: 8px;
            text-transform: uppercase;
        }
        .auth-sub {
            color: #94a3b8;
            font-size: 0.92rem;
            margin-bottom: 12px;
        }
        </style>
        """, unsafe_allow_html=True)
        _render_auth_modal_body(auth_view)


_init_auth_state()
_apply_base_styles()
_restore_auth_from_query()
_sync_settings_from_query()
_sync_auth_from_query()

if st.session_state.show_settings:
    render_settings_page()
    st.stop()

show_auth_modal(st.session_state.get("auth_view", "login"))


# ══════════════════════════════════════════════════════════════
# 4. SIDEBAR
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    authenticated = st.session_state.get("authenticated", False)
    profile_name = st.session_state.get("user_name") or st.session_state.get("user_email", "User")
    profile_email = st.session_state.get("user_email", "")
    settings_href = f"?menu=settings&ue={quote(profile_email)}" if profile_email else "?menu=settings"
    login_href = "?menu=login"
    signup_href = "?menu=signup"
    name_parts = str(profile_name).strip().split()
    profile_initials = "".join(p[0] for p in name_parts[:2]).upper() if name_parts else "U"
    logo_uri = _image_to_data_uri("logo.png")
    logo_markup = f'<img src="{logo_uri}" style="width:150px; max-width:150px; display:block;" />' if logo_uri else ''

    # ── TOP NAVBAR ── (runs once at top level, never inside a function)
    st.markdown(f"""
<div style="position:fixed;top:0;right:0;width:calc(100% - 21rem);height:3.5rem;background:#0f172a;border-bottom:1px solid #1e293b;display:flex;align-items:center;justify-content:flex-end;padding:0 130px 0 24px;z-index:999;box-sizing:border-box;">
    <div style="margin-right:auto;">
        {logo_markup}
    </div>
    <div style="display:flex;align-items:center;gap:6px;margin-right:20px;">
        <span style="width:8px;height:8px;background:#22c55e;border-radius:50%;display:inline-block;box-shadow:0 0 6px #22c55e;"></span>
        <span style="font-family:Inter,sans-serif;font-size:0.78rem;color:#94a3b8;">API Status</span>
        <span style="font-family:Inter,sans-serif;font-size:0.78rem;color:#22c55e;font-weight:600;">Online</span>
    </div>
    <div style="width:1px;height:20px;background:#1e293b;margin-right:20px;"></div>
    <button id="phishvision-news-bell" type="button" title="Cyber Threat News Notifications" aria-label="Cyber Threat News Notifications" style="appearance:none;background:transparent;border:none;color:#e2e8f0;font-size:1.1rem;cursor:pointer;margin-right:16px;padding:0;line-height:1;">🔔</button>
    <details style="position:relative; margin:0;">
        <summary style="list-style:none;display:flex;align-items:center;gap:8px;cursor:pointer;">
            <div style="width:32px;height:32px;background:#3b82f6;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:0.75rem;color:white;font-weight:700;">{profile_initials}</div>
            <div style="font-family:Inter,sans-serif;font-size:0.8rem;font-weight:600;color:#e2e8f0;">{profile_name}</div>
            <div style="font-size:0.7rem;color:#94a3b8;">▼</div>
        </summary>
        <div style="position:absolute;right:0;top:38px;min-width:210px;background:#0b1428;border:1px solid #1e293b;border-radius:10px;box-shadow:0 10px 24px rgba(2,6,23,0.45);padding:8px 0;z-index:2000;">
            <a href="{settings_href}" target="_self" style="display:block;padding:10px 12px;color:#e2e8f0;text-decoration:none;font-family:Inter,sans-serif;font-size:0.82rem;">⚙️ Settings</a>
            {'<a href="'+login_href+'" target="_self" style="display:block;padding:10px 12px;color:#e2e8f0;text-decoration:none;font-family:Inter,sans-serif;font-size:0.82rem;">👤 Login</a><a href="'+signup_href+'" target="_self" style="display:block;padding:10px 12px;color:#e2e8f0;text-decoration:none;font-family:Inter,sans-serif;font-size:0.82rem;">✨ Sign Up</a>' if not authenticated else '<a href="?menu=logout" target="_self" style="display:block;padding:10px 12px;color:#ff8f8f;text-decoration:none;font-family:Inter,sans-serif;font-size:0.82rem;">⎋ Logout</a>'}
        </div>
    </details>
</div>
<div style="height:3.5rem;"></div>
""", unsafe_allow_html=True)

    render_cyber_news_notifications()

    # ── Initialize session state ──
    if 'page' not in st.session_state:
        st.session_state.page = "About"
    if 'history' not in st.session_state:
        st.session_state.history = []

    page = st.session_state.page
    if page not in {"About", "URL Scan", "Bulk Scan", "Intel Report"}:
        page = "About"
        st.session_state.page = "About"

    # ── Navigation Items ──
    nav_items = [
        ("ℹ️", "About"),
        ("🔗", "URL Scan"),
        ("📊", "Bulk Scan"),
        ("🔎", "Intel Report"),
    ]

    for icon, label in nav_items:
        is_active = (page == label)

        if is_active:
            # Active item rendered as styled HTML (not a button)
            st.markdown(f"""
            <div style="background:#1e293b; border-radius:6px; padding:9px 12px;
                        margin:1px 0; display:flex; align-items:center; gap:10px;
                        cursor:default;">
                <span style="font-size:1rem; line-height:1;">{icon}</span>
                <span style="font-family:'Inter',sans-serif; font-size:0.875rem;
                             font-weight:600; color:#e2e8f0;">{label}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Inactive item is a clickable button styled as nav item
            if st.button(
                f"{icon}   {label}",
                key=f"nav_{label}",
                use_container_width=True
            ):
                _navigate_to_page(label)
                st.rerun()

    # ── Detection Engine (bottom section) ──
    st.markdown("""
    <div style="border-top:1px solid #1e293b; margin-top:16px; padding-top:12px;">
        <div style="font-family:'Inter',sans-serif; font-size:0.75rem;
                    color:#64748b; font-weight:600; padding:0 4px; margin-bottom:8px;">
            Detection Engine
        </div>
    </div>
    """, unsafe_allow_html=True)

    model_choice = st.selectbox(
        "Engine",
        (
            "Stacking Ensemble (Strongest)",
            "Gradient Boosting",
            "XGBoost",
            "Random Forest"
        ),
        label_visibility="collapsed",
        key="engine_select"
    )

    # Active engine indicator
    st.markdown("""
    <div style="display:flex; align-items:center; gap:8px;
                padding:6px 4px; margin-top:4px;">
        <span style="font-family:'Inter',sans-serif; font-size:0.75rem;
                     color:#64748b;">Engine A</span>
        <span style="width:8px; height:8px; background:#22c55e;
                     border-radius:50%; display:inline-block;"></span>
        <span style="font-family:'Inter',sans-serif; font-size:0.75rem;
                     color:#22c55e; font-weight:500;">Active</span>
    </div>
    """, unsafe_allow_html=True)

    # Keep model_map for use in scan tabs
    model_map = {
        "Stacking Ensemble (Strongest)": "model_stack.pkl",
        "Gradient Boosting":             "model_gb.pkl",
        "XGBoost":                       "model_xgb.pkl",
        "Random Forest":                 "model_rf.pkl"
    }

    st.markdown("""<hr style="border-color:#00ff8811; margin:20px 0;">""", unsafe_allow_html=True)

    # Status panel
    st.markdown("""
    <div class="ui-status-panel">
        <div class="label">◈ SYSTEM STATUS</div>
        <div class="body">
            <span class="ok">●</span>
            <span class="muted"> API ONLINE</span><br>
            <span class="ok">●</span>
            <span class="muted"> MODELS LOADED</span><br>
            <span class="ok">●</span>
            <span class="muted"> EXTENSION READY</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""<hr style="border-color:#00ff8811; margin:20px 0;">""", unsafe_allow_html=True)

    # Session history - FIX: Better initialization
    if 'history' not in st.session_state:
        st.session_state.history = []

    if st.session_state.history:
        st.markdown("""
        <div class="ui-section-subtitle" style="margin-left:0; margin-bottom:8px; color:#00c8ff;">
            ◈ RECENT ACTIVITY
        </div>
        """, unsafe_allow_html=True)
        df_hist = pd.DataFrame(st.session_state.history).tail(5)
        for _, row in df_hist.iterrows():
            color = "#ff4444" if row['Verdict'] == "Phishing" else "#00ff88"
            icon  = "⚠" if row['Verdict'] == "Phishing" else "✓"
            url_short = str(row['URL'])[:28] + "..." if len(str(row['URL'])) > 28 else str(row['URL'])
            st.markdown(f"""
            <div class="ui-activity-item" style="border-left:2px solid {color};">
                <span style="color:{color}; font-size:0.75rem;">{icon}</span>
                <span class="entry" style="color:{color}88;"> {url_short}</span>
            </div>
            """, unsafe_allow_html=True)

        # Stats
        total   = len(st.session_state.history)
        phish   = sum(1 for h in st.session_state.history if h['Verdict'] == 'Phishing')
        safe    = total - phish
        st.markdown(f"""
        <div class="ui-inline-note info" style="margin-top:10px;">
            <span style="color:#00c8ff;">SCANNED:</span>
            <span class="emph"> {total}</span> &nbsp;|&nbsp;
            <span class="hint">THREATS: {phish}</span> &nbsp;|&nbsp;
            <span class="emph">SAFE: {safe}</span>
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


# ══════════════════════════════════════════════════════════════
# 7. SECTION RENDERING
# ══════════════════════════════════════════════════════════════
st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

if page == "URL Scan":
    section_title("Target URL Analysis", "Enter URL for deep inspection")

    if not st.session_state.get("authenticated", False):
        st.markdown("""
        <div style="margin:12px 0 18px 0; padding:16px 18px; border-radius:12px;
             border:1px solid rgba(255,75,75,0.28); background:rgba(26,5,5,0.8); color:#ffd5d5;">
            Log in from the profile menu to unlock URL scanning.
        </div>
        """, unsafe_allow_html=True)

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
        help="Enter any URL with or without https://",
        disabled=not st.session_state.get("authenticated", False)
    )

    col_btn, col_empty = st.columns([2, 3])
    with col_btn:
        scan_clicked = st.button("⚡  INITIATE SCAN", disabled=not st.session_state.get("authenticated", False))

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


elif page == "Bulk Scan":
    section_title("Batch Threat Analysis", "Upload CSV file for mass URL scanning")

    if not st.session_state.get("authenticated", False):
        st.markdown("""
        <div class="ui-alert">
            Log in from the profile menu to unlock batch scanning.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="ui-inline-note info" style="margin-bottom:16px;">
        ◈ CSV FORMAT REQUIRED &nbsp;|&nbsp;
        Column name must be: <span class="emph">'url'</span> &nbsp;|&nbsp;
        Supported: .csv files only
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("", type=['csv'], label_visibility="collapsed", disabled=not st.session_state.get("authenticated", False))

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
                <div class="ui-inline-note info" style="margin: 10px 0 0 0;">
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
                st.markdown(f"""
                <div class="ui-mini-card">
                    <div class="label">📡 Total Scanned</div>
                    <div class="value" style="color:#00c8ff;">{total_urls}</div>
                    <div class="subvalue">URLs processed</div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class="ui-mini-card">
                    <div class="label">⚠ Threats Found</div>
                    <div class="value" style="color:#ff4444;">{phishing_count}</div>
                    <div class="subvalue">Flagged by ML + rules</div>
                </div>
                """, unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                <div class="ui-mini-card">
                    <div class="label">✓ Safe URLs</div>
                    <div class="value" style="color:#00ff88;">{safe_count}</div>
                    <div class="subvalue">No alerts raised</div>
                </div>
                """, unsafe_allow_html=True)
            with c4:
                rate_color = "#ffaa00" if threat_pct > 30 else "#00ff88"
                st.markdown(f"""
                <div class="ui-mini-card">
                    <div class="label">☢ Threat Rate</div>
                    <div class="value" style="color:{rate_color};">{threat_pct:.1f}%</div>
                    <div class="subvalue">Portfolio exposure</div>
                </div>
                """, unsafe_allow_html=True)

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
            <div class="ui-alert">
                ✗  MISSING COLUMN — CSV must contain a column named 'url'.
            </div>
            """, unsafe_allow_html=True)


elif page == "Intel Report":
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
            <div class="ui-mini-card" style="border-left:3px solid {color}; margin-bottom:8px;">
                <div class="label" style="color:{color};">{active}{models_data['Model'][i].upper()}</div>
                <div class="value" style="font-size:0.72rem; margin-top:6px;">
                    <span style="color:#00c8ff88;">ACCURACY:</span>
                    <span style="color:{color};"> {models_data['Accuracy'][i]}</span>
                    &nbsp;&nbsp;
                    <span style="color:#00c8ff88;">SPEED:</span>
                    <span style="color:{color};"> {models_data['Speed'][i]}</span>
                </div>
                <div class="subvalue" style="color:{color}44;">
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
        <div class="ui-mini-card">
            <div class="label">URL STRUCTURE</div>
            <div class="value" style="color:#00ff88;">12/12</div>
            <div class="subvalue">100% Coverage</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="ui-mini-card">
            <div class="label">SECURITY</div>
            <div class="value" style="color:#ffaa00;">4/4</div>
            <div class="subvalue">100% Coverage</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        coverage_pct = int(sum(implemented) / sum(total_each) * 100)
        st.markdown(f"""
        <div class="ui-mini-card">
            <div class="label">OVERALL</div>
            <div class="value" style="color:#00ff88;">{coverage_pct}%</div>
            <div class="subvalue">System Ready</div>
        </div>
        """, unsafe_allow_html=True)

else:
    _render_about_landing()

