"""Streamlit-side renderer for the cyber threat news dropdown."""

from __future__ import annotations

import json
from html import escape

import streamlit as st
import streamlit.components.v1 as components

from news_service import get_cyber_news


def _render_item_card(item: dict) -> str:
    headline = escape(item.get("headline", "Untitled story"))
    source = escape(item.get("source", "Unknown source"))
    published = escape(item.get("published", "Recently"))
    summary = escape(item.get("summary", ""))
    link = escape(item.get("link", "#"), quote=True)

    return f"""
    <article class="phishvision-news-item">
        <div class="phishvision-news-headline-row">
            <a class="phishvision-news-headline" href="{link}" target="_blank" rel="noopener noreferrer">{headline}</a>
        </div>
        <div class="phishvision-news-meta">
            <span>{source}</span>
            <span>•</span>
            <span>{published}</span>
        </div>
        <p class="phishvision-news-summary">{summary}</p>
        <a class="phishvision-news-readmore" href="{link}" target="_blank" rel="noopener noreferrer">Read More</a>
    </article>
    """


def render_cyber_news_notifications(refresh_minutes: int = 20, max_items: int = 5, bell_selector: str = "#phishvision-news-bell") -> None:
    data = get_cyber_news(refresh_minutes=refresh_minutes, max_items=max_items)
    items = data.get("items", [])
    items_html = "".join(_render_item_card(item) for item in items)
    refresh_ms = int(data.get("refresh_minutes", refresh_minutes)) * 60 * 1000
    updated_label = escape(data.get("fetched_at_label", "Recently"))
    status_copy = "Cached stories" if data.get("stale") else "Live stories"

    panel_html = f"""
    <div id="phishvision-cyber-news-panel" aria-hidden="true">
        <div class="phishvision-news-shell">
            <div class="phishvision-news-header">
                <div>
                    <div class="phishvision-news-kicker">Cyber Threat News</div>
                    <div class="phishvision-news-title">Real-time phishing, malware, ransomware, and breach updates</div>
                    <div class="phishvision-news-subtitle">{status_copy} updated {updated_label}. Auto-refresh every {data.get('refresh_minutes', refresh_minutes)} minutes.</div>
                </div>
                <button class="phishvision-news-close" type="button" aria-label="Close news panel">×</button>
            </div>
            <div class="phishvision-news-body">
                {items_html or '<div class="phishvision-news-empty">No items are available right now. The panel will retry automatically and reuse the last cached stories when the feed returns.</div>'}
            </div>
            <div class="phishvision-news-footer">
                <span class="phishvision-news-badge">Live source mix</span>
                <span>Open stories in a new tab</span>
            </div>
        </div>
    </div>
    """

    css_text = """
    #phishvision-cyber-news-panel {
        position: fixed;
        top: 58px;
        right: 24px;
        width: min(440px, calc(100vw - 32px));
        max-height: calc(100vh - 96px);
        overflow: hidden;
        background: linear-gradient(180deg, rgba(11, 20, 40, 0.98), rgba(7, 12, 22, 0.98));
        border: 1px solid rgba(0, 212, 255, 0.20);
        border-radius: 20px;
        box-shadow: 0 24px 60px rgba(0, 0, 0, 0.45);
        z-index: 999999;
        opacity: 0;
        transform: translateY(-10px) scale(0.98);
        transition: opacity 180ms ease, transform 180ms ease;
        display: none;
        color: #e2e8f0;
        font-family: Inter, sans-serif;
    }
    #phishvision-cyber-news-panel.phishvision-news-open {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
    .phishvision-news-shell {
        display: flex;
        flex-direction: column;
        max-height: calc(100vh - 96px);
    }
    .phishvision-news-header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 16px;
        padding: 16px 18px 12px 18px;
        border-bottom: 1px solid rgba(148, 163, 184, 0.14);
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.08), rgba(0, 0, 0, 0));
    }
    .phishvision-news-kicker {
        font-size: 0.72rem;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        color: #7dd3fc;
        font-weight: 700;
    }
    .phishvision-news-title {
        margin-top: 6px;
        font-size: 0.98rem;
        font-weight: 700;
        color: #f8fbff;
    }
    .phishvision-news-subtitle {
        margin-top: 4px;
        font-size: 0.8rem;
        color: #94a3b8;
        line-height: 1.45;
    }
    .phishvision-news-close {
        appearance: none;
        border: 1px solid rgba(148, 163, 184, 0.2);
        background: rgba(15, 23, 42, 0.7);
        color: #e2e8f0;
        width: 32px;
        height: 32px;
        border-radius: 999px;
        cursor: pointer;
        flex: 0 0 auto;
    }
    .phishvision-news-body {
        overflow-y: auto;
        padding: 10px 10px 14px 10px;
    }
    .phishvision-news-item {
        padding: 14px 14px 12px 14px;
        border: 1px solid rgba(148, 163, 184, 0.12);
        border-radius: 16px;
        background: rgba(15, 23, 42, 0.68);
        margin-bottom: 10px;
    }
    .phishvision-news-item:hover {
        border-color: rgba(0, 212, 255, 0.22);
        box-shadow: 0 10px 24px rgba(0, 0, 0, 0.18);
    }
    .phishvision-news-headline {
        color: #f8fbff;
        font-size: 0.94rem;
        font-weight: 700;
        text-decoration: none;
        line-height: 1.35;
    }
    .phishvision-news-headline:hover { color: #7dd3fc; }
    .phishvision-news-meta {
        display: flex;
        align-items: center;
        gap: 6px;
        margin-top: 8px;
        color: #94a3b8;
        font-size: 0.76rem;
    }
    .phishvision-news-summary {
        margin: 10px 0 10px 0;
        color: #cbd5e1;
        font-size: 0.84rem;
        line-height: 1.55;
    }
    .phishvision-news-readmore {
        color: #7dd3fc;
        font-size: 0.8rem;
        font-weight: 700;
        text-decoration: none;
    }
    .phishvision-news-footer {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        padding: 10px 16px 16px 16px;
        border-top: 1px solid rgba(148, 163, 184, 0.14);
        color: #94a3b8;
        font-size: 0.76rem;
    }
    .phishvision-news-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 10px;
        border-radius: 999px;
        background: rgba(0, 212, 255, 0.08);
        color: #7dd3fc;
        border: 1px solid rgba(0, 212, 255, 0.18);
        font-weight: 700;
    }
    .phishvision-news-empty {
        padding: 18px;
        color: #cbd5e1;
        font-size: 0.84rem;
    }
    """

    script = f"""
    <script>
    (function() {{
        const parentWindow = window.parent;
        if (!parentWindow || !parentWindow.document) {{
            return;
        }}

        const bellSelector = {json.dumps(bell_selector)};
        const panelId = 'phishvision-cyber-news-panel';
        const styleId = 'phishvision-cyber-news-style';
        const refreshMs = {refresh_ms};
        const panelHtml = {json.dumps(panel_html)};
        const cssText = {json.dumps(css_text)};

        const parentDocument = parentWindow.document;
        const state = parentWindow.__phishvisionCyberNewsState || (parentWindow.__phishvisionCyberNewsState = {{}});

        const existingPanel = parentDocument.getElementById(panelId);
        if (existingPanel) {{
            existingPanel.remove();
        }}

        const styleNode = parentDocument.getElementById(styleId) || parentDocument.createElement('style');
        styleNode.id = styleId;
        styleNode.textContent = cssText;
        parentDocument.head.appendChild(styleNode);

        const wrapper = parentDocument.createElement('div');
        wrapper.innerHTML = panelHtml;
        const panel = wrapper.firstElementChild;
        parentDocument.body.appendChild(panel);

        const bell = parentDocument.querySelector(bellSelector);
        const closeButton = panel.querySelector('.phishvision-news-close');
        let isOpen = false;

        state.panel = panel;
        state.bell = bell;
        state.refreshMs = refreshMs;

        const positionPanel = () => {{
            if (!state.panel) {{
                return;
            }}
            if (!state.bell) {{
                panel.style.top = '58px';
                panel.style.right = '24px';
                return;
            }}
            const bellRect = state.bell.getBoundingClientRect();
            const panelWidth = Math.min(440, Math.max(320, parentWindow.innerWidth - 32));
            const rightOffset = Math.max(16, parentWindow.innerWidth - bellRect.right - 10);
            panel.style.top = `${{bellRect.bottom + 10}}px`;
            panel.style.right = `${{rightOffset}}px`;
            panel.style.left = 'auto';
            panel.style.width = `min(${{panelWidth}}px, calc(100vw - 32px))`;
        }};

        state.positionPanel = positionPanel;
        state.openPanel = () => {{
            if (!state.panel) {{
                return;
            }}
            positionPanel();
            panel.style.display = 'block';
            requestAnimationFrame(() => panel.classList.add('phishvision-news-open'));
            panel.setAttribute('aria-hidden', 'false');
            isOpen = true;
            if (state.bell) {{
                state.bell.setAttribute('aria-expanded', 'true');
            }}
            state.isOpen = true;
        }};

        state.closePanel = () => {{
            if (!state.panel) {{
                return;
            }}
            panel.classList.remove('phishvision-news-open');
            panel.setAttribute('aria-hidden', 'true');
            panel.style.display = 'none';
            isOpen = false;
            if (state.bell) {{
                state.bell.setAttribute('aria-expanded', 'false');
            }}
            state.isOpen = false;
        }};

        state.togglePanel = (event) => {{
            if (event) {{
                event.preventDefault();
                event.stopPropagation();
            }}
            if (isOpen) {{
                state.closePanel();
            }} else {{
                state.openPanel();
            }}
        }};

        if (state.bell && !state.bell.dataset.phishvisionNewsBound) {{
            state.bell.dataset.phishvisionNewsBound = 'true';
            state.bell.addEventListener('click', state.togglePanel);
            state.bell.setAttribute('role', 'button');
            state.bell.setAttribute('aria-expanded', 'false');
        }}

        if (closeButton && !closeButton.dataset.phishvisionNewsBound) {{
            closeButton.dataset.phishvisionNewsBound = 'true';
            closeButton.addEventListener('click', state.closePanel);
        }}

        if (!state.documentListenerBound) {{
            parentDocument.addEventListener('click', (event) => {{
                if (!state.isOpen || !state.panel) {{
                    return;
                }}
                const target = event.target;
                if (state.panel.contains(target) || (state.bell && state.bell.contains(target))) {{
                    return;
                }}
                state.closePanel();
            }});
            state.documentListenerBound = true;
        }}

        if (!state.resizeListenerBound) {{
            parentWindow.addEventListener('resize', () => {{
                if (state.isOpen) {{
                    positionPanel();
                }}
            }});
            state.resizeListenerBound = true;
        }}

        if (state.isOpen) {{
            state.openPanel();
        }}

        const existingTimer = parentWindow.__phishvisionCyberNewsTimer;
        if (existingTimer) {{
            parentWindow.clearInterval(existingTimer);
        }}

        const refreshTimer = parentWindow.setInterval(() => {{
            if (state.panel && state.panel.getAttribute('aria-hidden') === 'false') {{
                parentWindow.location.reload();
            }}
        }}, refreshMs);
        parentWindow.__phishvisionCyberNewsTimer = refreshTimer;
    }})();
    </script>
    """

    components.html(script, height=0, width=0)