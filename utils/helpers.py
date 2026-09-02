"""
Fonctions communes reutilisees par les differentes pages :
style de graphique, cartes metriques, sections d'insights/problemes/chat.
"""
import base64

import streamlit as st

from ui.theme import COLORS, get_theme
from ui.i18n import t

STOPWORDS_PT = {
    "de", "a", "o", "que", "e", "do", "da", "em", "um", "para", "com", "não", "uma", "os",
    "no", "se", "na", "por", "mais", "as", "dos", "como", "mas", "ao", "ele", "das", "seu",
    "sua", "ou", "quando", "muito", "nos", "já", "eu", "também", "só", "pelo", "pela", "até",
    "isso", "ela", "entre", "depois", "sem", "mesmo", "aos", "seus", "quem", "nas", "me",
    "esse", "eles", "você", "essa", "num", "nem", "suas", "meu", "às", "minha", "numa",
    "pelos", "elas", "qual", "nós", "lhe", "deles", "essas", "esses", "pelas", "este",
    "dele", "tu", "te", "vocês", "vos", "lhes", "meus", "minhas", "teu", "tua", "teus",
    "tuas", "nosso", "nossa", "nossos", "nossas", "dela", "delas", "esta", "estes", "estas",
    "aquele", "aquela", "aqueles", "aquelas", "isto", "aquilo", "estou", "está", "estamos",
    "estão", "estive", "esteve", "estivemos", "estiveram", "produto", "recebi", "comprei",
    "para", "pois", "porque", "sobre", "todo", "toda", "todos", "todas", "outro", "outra",
}


def _L(lang, fr, en):
    return fr if lang == "FR" else en


def style_fig(fig, height=280):
    theme = get_theme()
    fig.update_layout(
        template="plotly_dark" if st.session_state.get("theme") == "dark" else "plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=theme["text"], family="Inter, sans-serif"),
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
    )
    grid_color = "rgba(255,255,255,0.05)" if st.session_state.get("theme") == "dark" else "rgba(0,0,0,0.06)"
    fig.update_xaxes(gridcolor=grid_color, zeroline=False)
    fig.update_yaxes(gridcolor=grid_color, zeroline=False)
    return fig


def metric_card(label, value, delta_text=None, delta_up=True, featured=False):
    delta_html = ""
    if delta_text:
        cls = "delta-up" if delta_up else "delta-down"
        delta_html = f'<div class="{cls}">{delta_text}</div>'
    card_class = "card-featured" if featured else "card"
    st.markdown(f"""
    <div class="{card_class}">
        <div class="card-title">{label}</div>
        <div class="big-number">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def missing_data_card(message):
    st.markdown(f'<div class="missing-data-card">{message}</div>', unsafe_allow_html=True)


def generate_avatar_b64():
    svg = f"""
    <svg width="160" height="160" viewBox="0 0 160 160" xmlns="http://www.w3.org/2000/svg">
        <rect width="160" height="160" rx="16" fill="{COLORS['primary']}"/>
        <circle cx="80" cy="65" r="35" fill="{COLORS['accent']}" opacity="0.3"/>
        <circle cx="80" cy="65" r="22" fill="{COLORS['accent']}" opacity="0.6"/>
        <circle cx="80" cy="65" r="12" fill="{COLORS['accent']}"/>
        <rect x="45" y="110" width="70" height="8" rx="4" fill="{COLORS['accent2']}" opacity="0.4"/>
        <rect x="55" y="125" width="50" height="8" rx="4" fill="{COLORS['accent2']}" opacity="0.25"/>
    </svg>
    """
    b64 = base64.b64encode(svg.encode()).decode()
    return f"data:image/svg+xml;base64,{b64}"


def find_review_text_col(df):
    for c in ["review_comment_message", "review_text", "comment", "review_comment"]:
        if c in df.columns:
            return c
    return None


def display_subtabs():
    """Affiche les sous-onglets pour chaque section."""
    return st.tabs([t("sub_main"), t("sub_problems"), t("sub_synthese"), t("sub_chat")])


def display_insights_section(insights, lang):
    """Affiche les insights structures en 4 sections."""
    labels = {
        "ce_qui_sest_passe": "Ce qui s'est passe",
        "pourquoi": "Pourquoi (causes)",
        "attention": "Ce qui merite votre attention",
        "recommandations": "Recommandations"
    }
    en_labels = {
        "ce_qui_sest_passe": "What happened",
        "pourquoi": "Why (causes)",
        "attention": "What needs your attention",
        "recommandations": "Recommendations"
    }
    lbls = en_labels if lang == "EN" else labels

    border_colors = [COLORS["accent"], COLORS["accent2"], COLORS["negative"], COLORS["positive"]]

    col1, col2 = st.columns(2)
    for idx, (key, items) in enumerate(insights.items()):
        if items:
            col = col1 if idx % 2 == 0 else col2
            border_color = border_colors[idx % len(border_colors)]
            with col:
                st.markdown(f"""
                <div class="insight-card" style="border-left-color: {border_color};">
                    <div class="insight-title">{lbls.get(key, key)}</div>
                    <div class="insight-body">{'<br>• '.join(items)}</div>
                </div>
                """, unsafe_allow_html=True)


def display_problems_section(problems, lang):
    """Affiche les problemes detectes."""
    if not problems:
        st.info(t("problems_none"))
        return

    severity_label = {
        "high": t("severity_high"),
        "medium": t("severity_medium"),
        "low": t("severity_low"),
    }

    for p in problems:
        st.markdown(f"""
        <div class="problem-card problem-{p['severity']}">
            <div class="problem-badge problem-badge-{p['severity']}">{severity_label[p['severity']]}</div>
            <div class="problem-title">{p['title']}</div>
            <div class="problem-desc">{p['description']}</div>
            <div class="problem-action"><b>{t('problem_action_label')} :</b> {p['action']}</div>
        </div>
        """, unsafe_allow_html=True)


def display_chat_section(df, lang):
    """Affiche le chat assistant."""
    from core.chat import answer_question

    theme = get_theme()

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    header_col, reset_col = st.columns([4, 1])
    with header_col:
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
            <span class="sonar-dot"></span>
            <span style="font-weight:600; font-size:1rem;">{t("chat_intro")}</span>
            <span style="color:{theme['muted']}; font-size:0.75rem;">({len(st.session_state.chat_history)} messages)</span>
        </div>
        """, unsafe_allow_html=True)
    with reset_col:
        reset_label = "Reinitialiser" if lang == "FR" else "Reset"
        if st.button(reset_label, key="reset_chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

    for role, msg in st.session_state.chat_history:
        if role == "user":
            who = "Vous" if lang == "FR" else "You"
            st.markdown(f"""
            <div class="chat-message chat-user">
                <b style="color:{COLORS['accent']};">{who}</b><br>{msg}
            </div>
            """, unsafe_allow_html=True)
        else:
            who = "Assistant"
            st.markdown(f"""
            <div class="chat-message chat-assistant">
                <b style="color:{COLORS['accent']};">{who}</b><br>{msg}
            </div>
            """, unsafe_allow_html=True)

    q = st.chat_input(t("chat_placeholder"))
    if q:
        st.session_state.chat_history.append(("user", q))
        ans = answer_question(q, df, lang)
        st.session_state.chat_history.append(("assistant", ans))
        st.rerun()
