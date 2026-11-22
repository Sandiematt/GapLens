"""Gold theme: design tokens and the one global stylesheet.

Pages never write their own CSS; extend ``CSS`` here instead.
"""
from __future__ import annotations

import streamlit as st

CREAM, CARD, MUTED, BORDER = "#FFFBEB", "#FFFFFF", "#FBF4E8", "#F1E4C3"
TEXT, TEXT2 = "#1E1B3A", "#5B5876"

GOLD = {50: "#FFFBEB", 100: "#FEF3C7", 200: "#FDE68A", 300: "#FCD34D", 400: "#FBBF24",
        500: "#F59E0B", 600: "#D97706", 700: "#B45309", 800: "#92400E", 900: "#78350F",
        950: "#3B2A06"}

# name -> (soft, main, text)
SHADES = {
    "lemon": ("#FEFCE8", "#FDE047", "#713F12"),
    "sunflower": ("#FEF9C3", "#FACC15", "#6B3A10"),
    "honey": ("#FEF3C7", "#FBBF24", "#78350F"),
    "amber": ("#FFF4DE", "#F59E0B", "#92400E"),
    "marigold": ("#FFEFD1", "#F4A300", "#7C3A06"),
    "mustard": ("#FBF3D0", "#CA8A04", "#6B4A04"),
    "oldgold": ("#F6EAD3", "#B7791F", "#5E3A0B"),
    "bronze": ("#F3E8D8", "#A16207", "#5C3A08"),
    "champagne": ("#FBF4E8", "#F7E7CE", "#6B4E2E"),
}
SHADE_ORDER = list(SHADES)

GRAD_HERO = "linear-gradient(120deg,#E0A21F 0%,#F6C445 55%,#FFE7A3 100%)"
GRAD_CHAMPAGNE = "linear-gradient(135deg,#FFFBEB 0%,#F7E7CE 100%)"
GRAD_DEEP = "linear-gradient(135deg,#92400E 0%,#A16207 100%)"

# status pill name -> (background, text)
PILLS = {
    "ok": ("#DCFCE7", "#15803D"), "on-track": ("#DCFCE7", "#15803D"),
    "stretch": ("#FFF4DE", "#92400E"),
    "at-risk": ("#FEE2E2", "#B91C1C"), "concept-gap": ("#FEE2E2", "#B91C1C"),
    "out-of-reach": ("#7F1D1D", "#FFFFFF"),
    "not-attempted": ("#F1F1F4", "#4B5563"),
    "silly-flagged": ("#F3E8D8", "#7C4A1E"),
    "silly-loss": ("#F9E3DC", "#9F4A3C"),
    "time-pressure": ("#FFF4DE", "#B45309"),
    "gold": ("#FEF3C7", "#92400E"),
    "muted": ("#F1F1F4", "#4B5563"),
}

CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap');
:root {{
  --cream:{CREAM}; --card:{CARD}; --muted:{MUTED}; --border:{BORDER};
  --text:{TEXT}; --text2:{TEXT2};
  --gold-50:{GOLD[50]}; --gold-100:{GOLD[100]}; --gold-700:{GOLD[700]};
  --gold-800:{GOLD[800]}; --gold-900:{GOLD[900]}; --gold-950:{GOLD[950]};
  --shadow:0 8px 24px rgba(146,64,14,0.10);
  --grad-deep:{GRAD_DEEP};
}}
html, body, .stApp, [data-testid="stSidebar"], button, input, textarea, select {{
  font-family:'Plus Jakarta Sans', system-ui, sans-serif !important;
}}
.stApp {{ background:var(--cream); color:var(--text); }}
[data-testid="stHeader"] {{ background:transparent; }}
.block-container {{ padding-top:2rem; max-width:1280px; }}
h1,h2,h3,h4 {{ color:var(--text); letter-spacing:-0.02em; }}
.gl-num, [data-testid="stMetricValue"] {{ font-variant-numeric:tabular-nums; }}

/* sidebar */
[data-testid="stSidebar"] {{ background:var(--card); border-right:1px solid var(--border); }}
[data-testid="stSidebarContent"] {{ display:flex; flex-direction:column; }}
[data-testid="stSidebarUserContent"] {{ flex:1; display:flex; flex-direction:column; padding-top:1.2rem; }}
[data-testid="stSidebarUserContent"] > div {{ flex:1; display:flex; flex-direction:column; }}
[data-testid="stSidebarUserContent"] > div > [data-testid="stVerticalBlock"] {{ flex:1; }}
[data-testid="stLayoutWrapper"]:has(> .st-key-sidebar_footer) {{ margin-top:auto; }}
.st-key-sidebar_footer {{ background:var(--gold-50); border:1px solid var(--border);
  border-radius:14px; padding:14px; }}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {{ border-radius:10px; height:44px;
  color:var(--text2); font-weight:500; }}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] {{
  background:var(--gold-100); color:var(--gold-900); font-weight:600; }}
.gl-brand {{ display:flex; align-items:center; gap:12px; padding:4px 4px 0; }}
.gl-brand-badge {{ width:44px; height:44px; border-radius:14px; display:flex; align-items:center;
  justify-content:center; background:linear-gradient(135deg,#E0A21F 0%,#F6C445 55%,#FFE7A3 100%);
  box-shadow:0 6px 16px rgba(146,64,14,0.10); color:var(--gold-950); }}
.gl-brand-name {{ font-weight:700; font-size:18px; letter-spacing:-0.025em; line-height:1.2; color:var(--text); }}
.gl-brand-tag {{ font-size:12px; color:var(--text2); line-height:1.3; }}
.gl-label {{ font-size:12px; font-weight:600; letter-spacing:.05em; text-transform:uppercase;
  color:var(--text2); margin:4px 0 6px; }}
.gl-profile {{ display:flex; align-items:center; gap:10px; }}
.gl-avatar {{ width:30px; height:30px; border-radius:999px; display:flex; align-items:center;
  justify-content:center; font-size:12px; font-weight:700; flex-shrink:0; }}
.gl-profile-name {{ font-size:13px; font-weight:600; line-height:1.3; color:var(--text); }}
.gl-profile-sub {{ font-size:12px; color:var(--text2); line-height:1.3; }}

/* cards: bordered containers */
[class*="st-key-card_"], [class*="st-key-subjcard_"] {{ background:var(--card); border:none !important;
  border-radius:20px; box-shadow:var(--shadow); }}
[class*="st-key-subjcard_"] {{ padding:0 !important; gap:0 !important; overflow:hidden; }}
[class*="st-key-subjact_"] {{ margin:0 22px 22px; padding-top:16px; border-top:1px solid #EFE6D2; width:auto !important; }}

/* html components */
.gl-title {{ font-size:28px; font-weight:700; letter-spacing:-0.025em; line-height:1.2; color:var(--text); margin:0; }}
.gl-subtitle {{ font-size:15px; color:var(--text2); margin:4px 0 0; }}
.gl-header {{ display:flex; justify-content:space-between; align-items:center; gap:16px; flex-wrap:wrap; margin-bottom:20px; }}
.gl-chips {{ display:flex; gap:8px; flex-wrap:wrap; }}
.gl-pill {{ display:inline-block; border-radius:999px; padding:5px 14px; font-size:13px; font-weight:600; line-height:1.4; }}
.gl-chip {{ display:inline-block; border-radius:999px; padding:5px 12px; font-size:12px; font-weight:600; }}
.gl-kpi {{ background:var(--card); border-radius:20px; box-shadow:var(--shadow); padding:18px 20px; }}
.gl-kpi-label {{ font-size:12px; color:var(--text2); font-weight:600; letter-spacing:.04em; text-transform:uppercase; }}
.gl-kpi-value {{ font-size:30px; font-weight:700; color:var(--text); font-variant-numeric:tabular-nums; line-height:1.2; }}
.gl-kpi-sub {{ font-size:12px; color:var(--text2); }}
.gl-hero {{ background:{GRAD_HERO}; color:{GOLD[950]}; border-radius:20px; padding:24px 28px; box-shadow:var(--shadow); }}
.gl-hero h2 {{ color:{GOLD[950]}; margin:0 0 4px; font-size:24px; }}
.gl-hero p {{ margin:0; font-size:14px; }}
.gl-section {{ background:var(--card); border-radius:20px; box-shadow:var(--shadow); padding:20px 22px; margin-bottom:16px; }}
.gl-section h3 {{ font-size:18px; font-weight:700; margin:0 0 8px; }}
.gl-section p, .gl-section li {{ font-size:14px; color:var(--text2); }}
.gl-callout {{ display:flex; gap:12px; align-items:flex-start; background:{GRAD_CHAMPAGNE};
  border:1px solid var(--border); border-radius:14px; padding:16px; font-size:14px; color:var(--text); margin-top:8px; }}
.gl-file {{ display:flex; gap:12px; align-items:center; background:{GRAD_CHAMPAGNE}; border:2px dashed #B7791F;
  border-radius:14px; padding:12px 14px; margin-bottom:8px; }}
.gl-file-icon {{ width:36px; height:36px; border-radius:10px; background:#fff; display:flex; align-items:center;
  justify-content:center; color:{GOLD[800]}; font-size:18px; flex:none; }}
.gl-file b {{ display:block; font-size:14px; color:var(--text); word-break:break-all; }}
.gl-file span {{ font-size:12px; color:var(--text2); }}
.gl-soon {{ background:var(--card); border-radius:20px; box-shadow:var(--shadow); padding:36px 28px; text-align:center; }}
.gl-soon-icon {{ width:56px; height:56px; border-radius:16px; margin:0 auto 14px; display:flex;
  align-items:center; justify-content:center; background:{GRAD_HERO}; color:{GOLD[950]}; font-size:26px; }}
.gl-soon h3 {{ margin:0 0 6px; font-size:18px; }}
.gl-soon p {{ margin:0; color:var(--text2); font-size:14px; }}

/* goal tab */
.gl-hero-row {{ display:flex; justify-content:space-between; align-items:center; gap:20px; flex-wrap:wrap; }}
.gl-hero-eyebrow {{ font-size:12px; font-weight:700; letter-spacing:.06em; text-transform:uppercase; margin-bottom:6px; }}
.gl-targets {{ display:flex; gap:12px; flex-wrap:wrap; }}
.gl-target-card {{ background:#fff; color:{GOLD[950]}; border-radius:14px; padding:10px 16px; min-width:110px; }}
.gl-target-card small {{ display:block; font-size:11px; font-weight:700; letter-spacing:.04em; text-transform:uppercase; color:var(--text2); }}
.gl-target-card b {{ font-size:26px; font-variant-numeric:tabular-nums; }}
.gl-target-card span {{ font-size:12px; color:var(--text2); }}
.gl-rule {{ display:flex; gap:10px; align-items:center; margin:6px 0; font-size:12px; color:var(--text2); }}
.gl-formula {{ background:{GRAD_CHAMPAGNE}; border:1px solid var(--border); border-radius:14px; padding:12px 14px;
  font-size:14px; font-weight:600; color:var(--text); margin-bottom:10px; }}
.gl-eyebrow {{ font-size:12px; font-weight:700; letter-spacing:.04em; text-transform:uppercase; color:var(--text2); margin:12px 0 4px; }}

/* subject card */
.gl-banner {{ display:flex; justify-content:space-between; align-items:center; padding:22px; }}
.gl-banner-code {{ font-size:12px; font-weight:600; letter-spacing:.1em; text-transform:uppercase; }}
.gl-banner-name {{ font-size:22px; font-weight:700; letter-spacing:-0.025em; }}
.gl-banner-icon {{ width:48px; height:48px; border-radius:14px; background:#fff; display:flex;
  align-items:center; justify-content:center; font-size:22px; }}
.gl-card-body {{ padding:22px 22px 4px; display:flex; flex-direction:column; gap:18px; }}
.gl-row {{ display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap; }}
.gl-fac-avatar {{ width:34px; height:34px; border-radius:999px; background:#FBF3D0; color:#6B4A04;
  display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:700; }}
.gl-meta {{ font-size:12px; color:var(--text2); }}
.gl-split-labels {{ display:flex; justify-content:space-between; font-size:13px; font-weight:600; margin-bottom:8px; }}
.gl-bar {{ display:flex; height:10px; border-radius:999px; overflow:hidden; gap:3px; }}
.gl-topics {{ display:flex; flex-wrap:wrap; gap:8px; }}
.gl-enrolled {{ display:flex; align-items:center; justify-content:center; gap:8px; height:42px;
  background:#DCFCE7; color:#15803D; border-radius:10px; padding:0 16px; font-size:14px; font-weight:600; }}

/* controls */
.stButton > button, .stFormSubmitButton > button, [data-testid="stBaseButton-secondary"] {{
  border-radius:10px; font-weight:600; border:1px solid {GOLD[700]}; color:{GOLD[800]}; background:#fff; min-height:42px; }}
.stButton > button:hover {{ border-color:{GOLD[800]}; color:{GOLD[900]}; background:var(--gold-50); }}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primaryFormSubmit"],
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"] {{
  background:var(--grad-deep); color:#fff; border:none; box-shadow:0 6px 16px rgba(146,64,14,0.10); }}
.stButton > button[kind="primary"] p, [data-testid="stBaseButton-primary"] p {{ color:#fff; }}
[data-baseweb="input"], [data-baseweb="select"] > div, [data-baseweb="base-input"] {{
  background:var(--gold-50) !important; border-radius:10px !important; border-color:var(--border) !important; }}
[data-testid="stNumberInput"] input, [data-testid="stTextInput"] input {{ font-weight:600; color:var(--text); }}
[data-testid="stButtonGroup"] {{ width:100%; }}
[data-testid="stButtonGroup"] [role="radiogroup"] {{ background:#fff; border:1px solid var(--border);
  border-radius:10px; padding:4px; width:100%; display:flex; gap:4px; }}
[data-testid="stButtonGroup"] button[data-variant="segmented_control"] {{ flex:1 1 0; min-width:0; padding:0 6px; white-space:nowrap; border:none; border-radius:8px;
  background:transparent; color:var(--text2); font-weight:600; min-height:34px; }}
[data-testid="stButtonGroup"] button[data-variant="segmented_control"][aria-checked="true"] {{
  background:var(--grad-deep); color:#fff; }}
[data-testid="stButtonGroup"] button[data-variant="segmented_control"][aria-checked="true"] p {{ color:#fff; }}
.stButton > button {{ white-space:nowrap; padding:0 8px; width:100%; }}
[class*="st-key-enrolled_"] button {{ background:#DCFCE7 !important; color:#15803D !important; border:none !important; opacity:1 !important; }}
[class*="st-key-enrolled_"] button p {{ color:#15803D !important; }}
.stTabs [data-baseweb="tab-highlight"] {{ background:{GOLD[700]}; }}
.stTabs [aria-selected="true"] {{ color:{GOLD[800]}; font-weight:600; }}
[data-testid="stFileUploaderDropzone"] {{ border:2px dashed #B7791F; background:var(--muted); border-radius:14px; }}
[data-testid="stExpander"] {{ border:1px solid var(--border); border-radius:14px; background:#fff; }}
[data-testid="stAlert"] {{ border-radius:14px; }}
/* CIA analysis (SAN-124) */
.gl-tile {{ display:flex; align-items:center; gap:12px; border-radius:14px; padding:14px 16px; }}
.gl-tile-icon {{ width:38px; height:38px; border-radius:999px; background:#fff; display:flex;
  align-items:center; justify-content:center; font-size:17px; font-weight:700; flex-shrink:0; }}
.gl-tile-label {{ font-size:12px; color:var(--text2); font-weight:600; }}
.gl-tile-value {{ font-size:22px; font-weight:700; color:var(--text); font-variant-numeric:tabular-nums; line-height:1.2; }}
.gl-tile-unit {{ font-size:13px; font-weight:500; color:var(--text2); margin-left:4px; }}
.gl-tile > div:last-child {{ min-width:0; }}
.gl-tile-label, .gl-tile-value {{ white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
@media (max-width:1200px) {{ .gl-tile-icon {{ display:none; }} .gl-tile {{ padding:12px; }} }}
.gl-warn {{ display:flex; gap:12px; align-items:flex-start; background:#FFF4DE; border:1px solid #F4A300;
  border-radius:14px; padding:14px 16px; font-size:13px; color:var(--text); margin:14px 0 4px; }}
.gl-warn-icon {{ color:{GOLD[700]}; font-size:18px; line-height:1.2; }}
.gl-warn-title {{ font-weight:700; color:{GOLD[700]}; font-size:14px; margin-bottom:2px; }}
.gl-table-wrap {{ border:1px solid var(--border); border-radius:14px; overflow-x:auto; margin:14px 0 6px; }}
.gl-table {{ width:100%; border-collapse:collapse; font-size:14px; font-variant-numeric:tabular-nums; }}
.gl-table th {{ background:var(--muted); color:var(--text2); font-size:12px; font-weight:600;
  text-transform:uppercase; letter-spacing:.04em; text-align:left; padding:10px 14px; border:none; }}
.gl-table td {{ padding:10px 14px; border:none; border-top:1px solid #EFE6D2; color:var(--text); }}
.gl-table .gl-q {{ font-weight:700; }}
.gl-table .gl-muted {{ color:var(--text2); }}
.gl-table .gl-you {{ font-weight:700; color:{GOLD[800]}; }}
.gl-table .gl-pill {{ font-size:12px; padding:3px 10px; }}
.gl-gain {{ font-size:12px; font-weight:700; color:#15803D; }}
.gl-tip-title {{ font-size:15px; font-weight:700; color:var(--text); margin:10px 0 6px; }}
.gl-tip-text {{ font-size:13px; color:var(--text2); line-height:1.5; margin:0 0 8px; }}
[class*="st-key-tip_"] {{ background:var(--card); border:none !important; border-radius:20px;
  box-shadow:var(--shadow); border-top:4px solid #F7E7CE !important; }}
[class*="st-key-tip_concept-gap"] {{ border-top-color:#DC2626 !important; }}
[class*="st-key-tip_time-pressure"] {{ border-top-color:#F59E0B !important; }}
[class*="st-key-tip_silly-loss"] {{ border-top-color:#D9826B !important; }}
[class*="st-key-tip_silly-flagged"] {{ border-top-color:#A16207 !important; }}
[class*="st-key-tip_not-attempted"] {{ border-top-color:#4B5563 !important; }}
[class*="st-key-tip_"] [data-testid="stCheckbox"] {{ border-top:1px solid #EFE6D2; padding-top:10px; }}
[class*="st-key-tip_"] [data-testid="stCheckbox"] p {{ font-size:13px; }}
.gl-rank {{ display:flex; gap:12px; align-items:center; }}
.gl-rank-n {{ width:40px; height:40px; border-radius:999px; background:#FEE2E2; color:#B91C1C; display:flex;
  align-items:center; justify-content:center; font-weight:700; font-size:15px; }}
.gl-rank-title {{ font-size:18px; font-weight:700; color:var(--text); }}
.gl-rank-lost {{ font-size:14px; color:var(--text); margin:14px 0 8px; font-variant-numeric:tabular-nums; }}
.gl-bar {{ height:10px; border-radius:999px; background:#F1F1F4; overflow:hidden; }}
.gl-bar > div {{ height:100%; border-radius:999px; }}
.gl-eyebrow2 {{ font-size:12px; font-weight:700; letter-spacing:.06em; text-transform:uppercase;
  color:var(--text2); margin:14px 0 8px; }}
.gl-res {{ display:flex; align-items:center; gap:12px; border:1px solid var(--border); border-radius:14px;
  padding:12px 14px; margin-bottom:10px; background:#fff; text-decoration:none !important; }}
.gl-res.gl-auto {{ background:var(--muted); border-color:transparent; }}
.gl-res-title {{ font-size:14px; font-weight:600; color:var(--text); margin-bottom:6px; }}
.gl-res-meta {{ display:flex; gap:6px; flex-wrap:wrap; }}
.gl-res-meta .gl-pill {{ font-size:12px; padding:2px 10px; }}
.gl-res-go {{ margin-left:auto; color:var(--gold-800); font-size:16px; }}
.gl-res-body {{ flex:1; min-width:0; }}
.gl-rule-note {{ background:#FBF4E8; border:1px solid var(--border); border-radius:14px; padding:12px 14px;
  font-size:13px; color:var(--gold-800); margin:8px 0 14px; }}
.gl-section-head {{ display:flex; justify-content:space-between; align-items:baseline; gap:12px;
  flex-wrap:wrap; margin:22px 0 10px; }}
.gl-section-head .gl-section-title {{ font-size:18px; font-weight:700; color:var(--text); letter-spacing:-0.02em; }}
.gl-section-head span {{ font-size:12px; color:var(--text2); }}
"""


def inject_theme() -> None:
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)
