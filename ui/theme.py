"""
Bloc 7 : Theme — couleurs, variables CSS, injection du style global.
"""
import streamlit as st

# ============================================================================
# COULEURS PROFESSIONNELLES
# ============================================================================
COLORS = {
    "primary": "#1B2A4A",
    "primary_light": "#2A3F6A",
    "accent": "#C9A84C",
    "accent2": "#4A8C8C",
    "surface": "#F7F8FA",
    "surface_dark": "#1A1E2E",
    "text": "#1A1E2E",
    "text_light": "#6B7A8F",
    "text_white": "#F0F2F8",
    "border": "#E2E6EE",
    "positive": "#3A8C6B",
    "negative": "#C95A5A",
    "gradient_primary": "linear-gradient(135deg, #1B2A4A 0%, #2A3F6A 100%)",
    "gradient_accent": "linear-gradient(135deg, #C9A84C 0%, #B8953A 100%)",
}

PIE_COLORS = [COLORS["accent"], COLORS["accent2"], COLORS["primary_light"],
              COLORS["positive"], COLORS["negative"], "#8A7A5A", "#5A6E8A"]


def init_theme_state():
    """Initialise le theme et la langue par defaut dans la session."""
    if "theme" not in st.session_state:
        st.session_state.theme = "dark"
    if "lang" not in st.session_state:
        st.session_state.lang = "FR"


def get_theme() -> dict:
    """Retourne le dictionnaire de couleurs actif (dark/light) selon la session."""
    if st.session_state.get("theme", "dark") == "dark":
        return {
            "bg": "radial-gradient(circle at 15% 0%, #0F1422 0%, #090C15 45%, #060810 100%)",
            "card": "#131927",
            "card_border": "rgba(255,255,255,0.06)",
            "sidebar": "#0B0F1A",
            "text": "#ECEEF4",
            "muted": "#7A88A0",
            "surface": "#1A2235",
            "border": "rgba(255,255,255,0.08)",
        }
    else:
        return {
            "bg": "radial-gradient(circle at 15% 0%, #F0F2F8 0%, #F7F8FA 45%, #FFFFFF 100%)",
            "card": "#FFFFFF",
            "card_border": "#E8EAEF",
            "sidebar": "#FFFFFF",
            "text": "#1A1E2E",
            "muted": "#6B7A8F",
            "surface": "#F5F6FA",
            "border": "#E2E6EE",
        }


def inject_css():
    """Injecte le CSS global de l'application (a appeler une fois dans app.py)."""
    theme = get_theme()
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', -apple-system, sans-serif;
}}

.stApp {{
    background: {theme["bg"]};
    color: {theme["text"]};
}}

.block-container {{
    padding-top: 1.8rem;
    padding-bottom: 2.5rem;
    max-width: 1300px;
}}

[data-testid="stSidebar"] {{
    background: {theme["sidebar"]};
    border-right: 1px solid {theme["border"]};
    padding-top: 1.2rem;
}}

.brand-title {{
    font-size: 1.4rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: {COLORS["accent"]};
}}
.brand-subtitle {{
    color: {theme["muted"]};
    font-size: 0.8rem;
    margin-top: 2px;
    font-weight: 400;
}}
.brand-separator {{
    border: none;
    border-top: 1px solid {theme["border"]};
    margin: 14px 0 16px 0;
}}

.card {{
    background: {theme["card"]};
    border: 1px solid {theme["card_border"]};
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.8rem;
}}
.card-featured {{
    background: {COLORS["gradient_primary"]};
    border: none;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.8rem;
}}
.card-featured .card-title {{
    color: rgba(255,255,255,0.6);
}}
.card-featured .big-number {{
    color: #FFFFFF;
}}
.card-title {{
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: {theme["muted"]};
    font-weight: 600;
    margin-bottom: 4px;
}}
.big-number {{
    font-size: 1.8rem;
    font-weight: 700;
    color: {theme["text"]};
    letter-spacing: -0.02em;
}}
.delta-up {{
    color: {COLORS["positive"]};
    font-size: 0.75rem;
    font-weight: 500;
    margin-top: 4px;
}}
.delta-down {{
    color: {COLORS["negative"]};
    font-size: 0.75rem;
    font-weight: 500;
    margin-top: 4px;
}}
.delta-neutral {{
    color: {theme["muted"]};
    font-size: 0.75rem;
    font-weight: 400;
    margin-top: 4px;
}}

.nav-label {{
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: {theme["muted"]};
    font-weight: 600;
    padding: 0 8px 8px 8px;
}}
.stRadio > div {{
    flex-direction: column;
    gap: 2px;
}}
.stRadio > div > label {{
    padding: 8px 12px !important;
    border-radius: 8px !important;
    margin-bottom: 1px;
    font-weight: 500 !important;
    color: {theme["muted"]} !important;
}}
.stRadio > div > label:has(input:checked) {{
    background: rgba(201, 168, 76, 0.12) !important;
}}
.stRadio > div > label:has(input:checked) p {{
    color: {COLORS["accent"]} !important;
    font-weight: 600 !important;
}}

.filter-section {{
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: {theme["muted"]};
    font-weight: 600;
    margin: 12px 0 8px 0;
}}

.stButton > button {{
    background: {COLORS["gradient_accent"]};
    color: #FFFFFF !important;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.82rem;
    padding: 8px 16px;
    width: 100%;
}}
.stButton > button:hover {{
    opacity: 0.9;
}}

.data-note {{
    color: {theme["muted"]};
    font-size: 0.7rem;
    font-style: italic;
    margin-top: -6px;
    margin-bottom: 12px;
}}

.page-title {{
    font-size: 1.8rem;
    font-weight: 700;
    color: {theme["text"]};
    letter-spacing: -0.02em;
}}
.page-subtitle {{
    color: {theme["muted"]};
    font-size: 0.9rem;
    margin-bottom: 16px;
}}
.section-header {{
    font-size: 1rem;
    font-weight: 600;
    color: {theme["text"]};
    margin: 12px 0 10px 0;
}}

.insight-card {{
    background: {theme["card"]};
    border: 1px solid {theme["card_border"]};
    border-left: 3px solid {COLORS["accent"]};
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
}}
.insight-title {{
    font-weight: 600;
    font-size: 0.85rem;
    color: {theme["text"]};
}}
.insight-body {{
    font-size: 0.8rem;
    color: {theme["muted"]};
    margin-top: 2px;
    line-height: 1.4;
}}

.problem-card {{
    background: {theme["card"]};
    border: 1px solid {theme["card_border"]};
    border-left: 4px solid {theme["border"]};
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
}}
.problem-high {{ border-left-color: {COLORS["negative"]}; }}
.problem-medium {{ border-left-color: {COLORS["accent"]}; }}
.problem-low {{ border-left-color: {COLORS["positive"]}; }}
.problem-badge {{
    display: inline-block;
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 20px;
    margin-bottom: 6px;
}}
.problem-badge-high {{ background: rgba(201,90,90,0.15); color: {COLORS["negative"]}; }}
.problem-badge-medium {{ background: rgba(201,168,76,0.15); color: {COLORS["accent"]}; }}
.problem-badge-low {{ background: rgba(58,140,107,0.15); color: {COLORS["positive"]}; }}
.problem-title {{
    font-weight: 700;
    font-size: 0.95rem;
    color: {theme["text"]};
    margin-bottom: 4px;
}}
.problem-desc {{
    font-size: 0.85rem;
    color: {theme["muted"]};
    margin-bottom: 6px;
    line-height: 1.4;
}}
.problem-action {{
    font-size: 0.82rem;
    color: {theme["text"]};
    background: {theme["surface"]};
    padding: 8px 10px;
    border-radius: 6px;
    line-height: 1.4;
}}

.missing-data-card {{
    background: {theme["card"]};
    border: 1px dashed {theme["card_border"]};
    border-radius: 10px;
    padding: 16px 18px;
    color: {theme["muted"]};
    font-size: 0.85rem;
    line-height: 1.5;
}}

.chat-message {{
    padding: 10px 14px;
    border-radius: 10px;
    margin-bottom: 6px;
    font-size: 0.85rem;
    line-height: 1.5;
}}
.chat-user {{
    background: {theme["surface"]};
    border: 1px solid {theme["card_border"]};
}}
.chat-assistant {{
    background: rgba(201, 168, 76, 0.08);
    border: 1px solid rgba(201, 168, 76, 0.15);
}}

#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}

.sonar-avatar-wrap {{
    border-radius: 14px;
    padding: 16px;
    background: {theme["card"]};
    border: 1px solid {theme["card_border"]};
    text-align: center;
}}
.sonar-avatar-img {{
    width: 100%;
    max-width: 160px;
    border-radius: 10px;
}}
.sonar-avatar-name {{
    font-weight: 700;
    font-size: 0.9rem;
    margin-top: 6px;
    color: {theme["text"]};
}}
.sonar-avatar-role {{
    color: {theme["muted"]};
    font-size: 0.75rem;
}}
.sonar-dot {{
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: {COLORS["positive"]};
    margin-right: 6px;
}}

.sub-tabs {{
    margin-bottom: 12px;
}}
</style>
""", unsafe_allow_html=True)
