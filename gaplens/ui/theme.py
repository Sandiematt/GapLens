"""Editorial Mint & Charcoal theme: design tokens and the one global stylesheet.

Pages never write their own CSS; extend ``CSS`` here instead.
"""
from __future__ import annotations

import streamlit as st

# Core palette tokens (matching the reference dashboard: pale mint canvas,
# deep charcoal slate chrome, coral-salmon & fresh mint-green accents).
SLATE = "#262833"
SLATE_DARK = "#1D1F28"
SLATE_MID = "#343746"
CORAL = "#F27D65"
CORAL_DARK = "#E0664D"
CORAL_SOFT = "#FDECE8"
GREEN = "#8FE089"
GREEN_TEXT = "#43A854"
GREEN_SOFT = "#E7F8E6"

# Preserved public token names so existing views & components stay compatible.
CREAM, CARD, MUTED, BORDER = "#EBF6F4", "#FFFFFF", "#F3FAF8", "#D7E8E4"
TEXT, TEXT2 = "#262833", "#64697D"

GOLD = {50: "#F3FAF8", 100: "#E4F3F0", 200: "#CBE5DF", 300: "#A8D5CC", 400: "#8FE089",
        500: "#F27D65", 600: "#E0664D", 700: "#262833", 800: "#262833", 900: "#1D1F28",
        950: "#181A22"}

# name -> (soft, main, text)
SHADES = {
    "lemon": ("#E7F8E6", "#8FE089", "#25642F"),
    "sunflower": ("#FDECE8", "#F27D65", "#A8412C"),
    "honey": ("#EAF5F3", "#62B6A8", "#1F5B52"),
    "amber": ("#FFF3E6", "#F4A261", "#9A4B16"),
    "marigold": ("#EEF0F6", "#4A4E69", "#262833"),
    "mustard": ("#E7F8E6", "#58B957", "#235E2A"),
    "oldgold": ("#FDECE8", "#E0664D", "#8F3623"),
    "bronze": ("#EAEDF3", "#343746", "#262833"),
    "champagne": ("#F3FAF8", "#D7E8E4", "#3B4A48"),
}
SHADE_ORDER = list(SHADES)

GRAD_HERO = "linear-gradient(120deg,#262833 0%,#343848 100%)"
GRAD_CHAMPAGNE = "linear-gradient(135deg,#F4FAF9 0%,#EBF6F4 100%)"
GRAD_DEEP = "linear-gradient(135deg,#262833 0%,#343746 100%)"

# status pill name -> (background, text)
PILLS = {
    "ok": ("#E3F7E2", "#277A35"), "on-track": ("#E3F7E2", "#277A35"),
    "stretch": ("#FFF2E2", "#B45309"),
    "at-risk": ("#FDE8E4", "#C8432B"), "concept-gap": ("#FDE8E4", "#C8432B"),
    "out-of-reach": ("#262833", "#FFFFFF"),
    "not-attempted": ("#ECEFF3", "#4B5563"),
    "silly-flagged": ("#F4EEE8", "#7C4A1E"),
    "silly-loss": ("#FDECE8", "#B84934"),
    "time-pressure": ("#FFF2E2", "#B45309"),
    "gold": ("#E5F3F0", "#262833"),
    "coral": ("#FDECE8", "#C8432B"),
    "slate": ("#262833", "#FFFFFF"),
    "muted": ("#EEF2F4", "#565D70"),
}

CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
:root {{
  --cream:{CREAM}; --card:{CARD}; --muted:{MUTED}; --border:{BORDER};
  --text:{TEXT}; --text2:{TEXT2};
  --slate:{SLATE}; --slate-dark:{SLATE_DARK}; --slate-mid:{SLATE_MID};
  --coral:{CORAL}; --coral-dark:{CORAL_DARK}; --coral-soft:{CORAL_SOFT};
  --green:{GREEN}; --green-text:{GREEN_TEXT}; --green-soft:{GREEN_SOFT};
  --gold-50:{GOLD[50]}; --gold-100:{GOLD[100]}; --gold-700:{GOLD[700]};
  --gold-800:{GOLD[800]}; --gold-900:{GOLD[900]}; --gold-950:{GOLD[950]};
  --shadow:0 4px 16px rgba(38,40,51,0.06);
  --shadow-sm:0 2px 10px rgba(38,40,51,0.05);
  --grad-deep:{GRAD_DEEP};
  --font-display:'Barlow Condensed', 'Plus Jakarta Sans', system-ui, sans-serif;
  --font-body:'Plus Jakarta Sans', system-ui, sans-serif;
}}
html, body, .stApp, [data-testid="stSidebar"], button, input, textarea, select {{
  font-family:var(--font-body) !important;
}}
.stApp {{ background:var(--cream); color:var(--text); }}
[data-testid="stHeader"] {{ background:transparent; }}
.block-container {{ padding-top:1rem; padding-bottom:2.5rem; max-width:1320px; }}
h1,h2,h3,h4 {{ color:var(--text); letter-spacing:-0.015em; }}
.gl-num, [data-testid="stMetricValue"] {{ font-variant-numeric:tabular-nums; }}

/* ===================== DARK CHARCOAL SIDEBAR ===================== */
[data-testid="stSidebar"] {{
  background:var(--slate) !important;
  border-right:1px solid rgba(255,255,255,0.06) !important;
  color:#E6E9F2;
}}
[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] button {{
  color:#CBD0DF !important;
}}
[data-testid="stSidebarContent"] {{ display:flex; flex-direction:column; }}
[data-testid="stSidebarUserContent"] {{ flex:1; display:flex; flex-direction:column; padding-top:1.1rem; }}
[data-testid="stSidebarUserContent"] > div {{ flex:1; display:flex; flex-direction:column; }}
[data-testid="stSidebarUserContent"] > div > [data-testid="stVerticalBlock"] {{ flex:1; }}
[data-testid="stLayoutWrapper"]:has(> .st-key-sidebar_footer) {{ margin-top:auto; }}
.st-key-sidebar_footer {{
  background:var(--slate-dark);
  border:1px solid rgba(255,255,255,0.08);
  border-radius:12px;
  padding:14px;
}}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {{
  border-radius:8px;
  height:44px;
  color:#C4C9D9 !important;
  font-weight:500;
  border-left:3px solid transparent;
  padding-left:10px;
  transition:background .15s ease, color .15s ease;
}}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] p {{
  color:#C4C9D9 !important;
  font-family:var(--font-display) !important;
  font-size:15px !important;
  letter-spacing:0.06em;
  text-transform:uppercase;
}}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] span[data-testid="stIconMaterial"],
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] svg {{
  color:var(--coral) !important;
}}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover {{
  background:rgba(255,255,255,0.06);
  color:#FFFFFF !important;
}}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover p {{ color:#FFFFFF !important; }}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] {{
  background:rgba(242,125,101,0.14);
  border-left:3px solid var(--coral);
  color:#FFFFFF !important;
  font-weight:600;
}}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] p {{
  color:#FFFFFF !important;
  font-weight:600;
}}
.gl-brand {{ display:flex; align-items:center; gap:12px; padding:4px 4px 12px;
  border-bottom:1px solid rgba(255,255,255,0.08); margin-bottom:4px; }}
.gl-brand-badge {{
  width:38px; height:38px; border-radius:999px; display:flex; align-items:center;
  justify-content:center; background:var(--slate-dark);
  border:2px solid var(--coral); color:var(--coral); flex-shrink:0;
}}
.gl-brand-name {{
  font-family:var(--font-display); font-weight:700; font-size:21px;
  letter-spacing:0.06em; line-height:1.1; color:#FFFFFF; text-transform:uppercase;
}}
.gl-brand-tag {{ font-size:11px; color:#8E94A8; line-height:1.3; margin-top:1px; }}
.gl-label {{
  font-family:var(--font-display); font-size:12px; font-weight:600;
  letter-spacing:.10em; text-transform:uppercase; color:var(--text2); margin:4px 0 6px;
}}
[data-testid="stSidebar"] .gl-label {{ color:#8B91A6; }}
.gl-label.gl-label-gap {{ margin-top:18px; }}
.gl-profile {{ display:flex; align-items:center; gap:10px; margin-top:6px; }}
.gl-avatar {{
  width:32px; height:32px; border-radius:999px; display:flex; align-items:center;
  justify-content:center; font-size:12px; font-weight:700; flex-shrink:0;
  background:var(--coral); color:#262833;
}}
.gl-profile-name {{ font-size:13px; font-weight:600; line-height:1.3; color:#FFFFFF; }}
.gl-profile-sub {{ font-size:11px; color:#9BA1B4; line-height:1.3; }}
.gl-side-year {{
  text-align:center; font-family:var(--font-display); font-size:11px;
  letter-spacing:0.12em; color:#6D7285; margin-top:12px;
}}

/* Sidebar form controls: crisp white boxes with black text */
[data-testid="stSidebar"] [data-baseweb="select"],
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-baseweb="input"],
[data-testid="stSidebar"] [data-baseweb="base-input"] {{
  background:#FFFFFF !important;
  background-color:#FFFFFF !important;
  border-color:#D5E4E0 !important;
  color:#111827 !important;
}}
[data-testid="stSidebar"] [data-baseweb="select"] > div > div,
[data-testid="stSidebar"] [data-baseweb="select"] > div > div > div,
[data-testid="stSidebar"] [data-baseweb="select"] input,
[data-testid="stSidebar"] [data-baseweb="input"] > div,
[data-testid="stSidebar"] [data-baseweb="base-input"] > div,
[data-testid="stSidebar"] [data-baseweb="base-input"] input {{
  background:transparent !important;
  background-color:transparent !important;
  color:#111827 !important;
  -webkit-text-fill-color:#111827 !important;
}}
[data-testid="stSidebar"] [data-baseweb="select"] span,
[data-testid="stSidebar"] [data-baseweb="select"] div,
[data-testid="stSidebar"] [data-baseweb="select"] svg,
[data-testid="stSidebar"] input {{
  color:#111827 !important;
  -webkit-text-fill-color:#111827 !important;
}}
[data-testid="stSidebar"] [data-baseweb="select"]:hover > div {{
  border-color:var(--coral) !important;
}}
/* Dropdown menu popover (mounted at document root) */
[data-baseweb="popover"] [role="listbox"],
[data-baseweb="popover"] ul[data-baseweb="menu"] {{
  background:#FFFFFF !important;
  border:1px solid var(--border) !important;
  border-radius:10px !important;
  box-shadow:0 10px 28px rgba(38,40,51,0.14) !important;
}}
[data-baseweb="popover"] [role="option"],
[data-baseweb="popover"] ul[data-baseweb="menu"] li {{
  color:var(--slate) !important;
  background:#FFFFFF !important;
  font-size:13px !important;
  font-weight:500 !important;
}}
[data-baseweb="popover"] [role="option"]:hover,
[data-baseweb="popover"] [role="option"][aria-selected="true"],
[data-baseweb="popover"] ul[data-baseweb="menu"] li:hover {{
  background:#EBF6F4 !important;
  color:var(--slate) !important;
  font-weight:600 !important;
}}
[data-testid="stSidebar"] label, [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{
  color:#A6ACC0 !important;
}}
[data-testid="stSidebar"] [data-testid="stButtonGroup"] [role="radiogroup"] {{
  background:#2B2E3C; border:1px solid rgba(255,255,255,0.10);
}}
[data-testid="stSidebar"] [data-testid="stButtonGroup"] button[data-variant="segmented_control"] {{
  color:#B8BECE;
}}
[data-testid="stSidebar"] [data-testid="stButtonGroup"] button[data-variant="segmented_control"][aria-checked="true"] {{
  background:var(--coral); color:#FFFFFF;
}}
[data-testid="stSidebar"] [data-testid="stExpander"] {{
  background:#262833; border:1px solid rgba(255,255,255,0.10); border-radius:10px; margin-top:8px;
}}
[data-testid="stSidebar"] [data-testid="stExpander"] summary,
[data-testid="stSidebar"] [data-testid="stExpander"] summary p,
[data-testid="stSidebar"] [data-testid="stExpander"] summary svg {{
  color:#D7DBE7 !important;
}}
[data-testid="stSidebar"] .stButton > button {{
  background:#2E3140; color:#E6E9F2; border:1px solid rgba(255,255,255,0.15);
}}
[data-testid="stSidebar"] .stButton > button:hover {{
  background:#383C4F; color:#FFFFFF; border-color:var(--coral);
}}
[data-testid="stSidebar"] .stFormSubmitButton > button[kind="primaryFormSubmit"],
[data-testid="stSidebar"] .stButton > button[kind="primary"] {{
  background:var(--coral); color:#FFFFFF; border:none;
}}

/* ===================== HOME PAGE REFERENCE SHELL ===================== */
.st-key-home_topbar {{
  background:#FFFFFF !important;
  border-radius:10px !important;
  padding:10px 20px !important;
  box-shadow:var(--shadow-sm) !important;
  border:1px solid #DFECE9 !important;
  margin-bottom:18px !important;
}}
.st-key-home_topbar > [data-testid="stVerticalBlock"] {{
  gap:0 !important;
}}
.st-key-home_topbar [data-testid="stTextInput"] [data-baseweb="input"],
.st-key-home_topbar [data-testid="stTextInput"] [data-baseweb="base-input"],
.st-key-home_topbar [data-testid="stSelectbox"] [data-baseweb="select"] > div {{
  background:#EAF4F2 !important;
  border-radius:999px !important;
  border:1px solid #D5E7E3 !important;
  min-height:36px !important;
}}
.st-key-home_topbar [data-testid="stSelectbox"] [data-baseweb="select"] input,
.st-key-home_topbar [data-testid="stSelectbox"] [data-baseweb="select"] span,
.st-key-home_topbar [data-testid="stTextInput"] input {{
  background:transparent !important;
  font-size:13px !important;
  font-weight:500 !important;
  color:var(--slate) !important;
}}
.st-key-home_topbar [data-testid="stTextInput"] input::placeholder,
.st-key-home_topbar [data-testid="stSelectbox"] [data-baseweb="select"] [aria-placeholder] {{
  color:#6A7B78 !important;
}}
.st-key-home_topbar [data-testid="stPopover"] > button {{
  min-height:36px !important;
  height:36px !important;
  border-radius:999px !important;
  border:1px solid #DCEBE8 !important;
  background:#F4FAF9 !important;
  color:var(--slate) !important;
  padding:0 10px !important;
  font-family:var(--font-display) !important;
  font-size:14px !important;
  font-weight:700 !important;
}}
.st-key-home_topbar [data-testid="stPopover"] > button:hover {{
  border-color:var(--coral) !important;
  background:var(--coral-soft) !important;
  color:var(--slate) !important;
}}
.st-key-home_notif_unread [data-testid="stPopover"] > button {{
  background:var(--coral-soft) !important;
  border-color:var(--coral) !important;
  color:var(--coral-dark) !important;
}}
.st-key-home_notif_unread [data-testid="stPopover"] > button span[data-testid="stIconMaterial"] {{
  color:var(--coral-dark) !important;
}}
.gl-notif-item {{
  display:flex; gap:10px; align-items:flex-start;
  padding:10px 12px; border-radius:8px; background:#F6FBFA;
  border:1px solid #DFECE9; border-left:3px solid var(--coral);
  margin-bottom:8px;
}}
.gl-notif-item.gl-notif-info {{ border-left-color:var(--slate); }}
.gl-notif-item.gl-notif-ok {{ border-left-color:var(--green-text); }}
.gl-notif-title {{ font-size:13px; font-weight:700; color:var(--slate); line-height:1.25; }}
.gl-notif-body {{ font-size:12px; color:var(--text2); line-height:1.4; margin-top:2px; }}
.gl-search-banner {{
  display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap;
  background:#FFFFFF; border:1px solid #D5E7E3; border-left:4px solid var(--coral);
  border-radius:10px; padding:10px 16px; margin-bottom:14px; font-size:13px; color:var(--slate);
  box-shadow:var(--shadow-sm);
}}
.gl-topbar {{
  background:#FFFFFF;
  border-radius:10px;
  padding:13px 22px;
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:16px;
  flex-wrap:wrap;
  box-shadow:var(--shadow-sm);
  border:1px solid #DFECE9;
  margin-bottom:18px;
}}
.gl-topbar-left {{ display:flex; align-items:center; gap:12px; }}
.gl-topbar-logo {{
  width:36px; height:36px; flex-shrink:0; display:flex; align-items:center; justify-content:center;
}}
.gl-topbar-word {{
  font-family:var(--font-display);
  font-size:22px;
  font-weight:700;
  letter-spacing:0.06em;
  color:var(--slate);
  text-transform:uppercase;
  line-height:1;
}}
.gl-topbar-right {{ display:flex; align-items:center; gap:16px; flex-wrap:wrap; }}
.gl-search-pill {{
  display:flex; align-items:center; background:#EAF4F2; border-radius:999px;
  overflow:hidden; height:32px; min-width:190px; border:1px solid #D9EAE6;
}}
.gl-search-text {{
  flex:1; padding:0 12px; font-size:12px; color:#6A7B78; white-space:nowrap;
}}
.gl-search-btn {{
  width:34px; height:32px; background:#B8CCC8; display:flex; align-items:center;
  justify-content:center; color:var(--slate);
}}
.gl-top-icon {{
  position:relative; display:inline-flex; align-items:center; justify-content:center;
  width:30px; height:30px; color:var(--slate);
}}
.gl-top-badge {{
  position:absolute; top:-2px; right:-3px; min-width:16px; height:16px;
  border-radius:999px; background:var(--coral); color:#FFFFFF;
  font-size:9px; font-weight:700; display:flex; align-items:center;
  justify-content:center; padding:0 4px; border:1.5px solid #FFFFFF;
}}
.gl-top-user {{ display:flex; align-items:center; justify-content:flex-end; gap:10px; padding-left:4px; }}
.gl-top-avatar {{
  width:36px; height:36px; border-radius:999px; background:var(--coral);
  display:flex; align-items:center; justify-content:center; overflow:hidden;
  flex-shrink:0;
}}
.gl-top-uname {{
  font-family:var(--font-display); font-size:15px; font-weight:700;
  letter-spacing:0.05em; color:var(--slate); text-transform:uppercase; line-height:1.1;
}}
.gl-top-uroll {{ font-size:11px; color:var(--text2); line-height:1.2; }}

.gl-crumb-row {{
  display:flex; justify-content:space-between; align-items:center;
  gap:16px; flex-wrap:wrap; margin:0 0 16px;
}}
.gl-crumb-left {{ display:flex; align-items:baseline; gap:18px; flex-wrap:wrap; }}
.gl-crumb-title {{
  font-family:var(--font-display); font-size:28px; font-weight:700;
  letter-spacing:0.04em; color:var(--slate); text-transform:uppercase;
  margin:0; line-height:1;
}}
.gl-crumb-path {{
  display:inline-flex; align-items:center; gap:6px;
  font-family:var(--font-display); font-size:13px; font-weight:600;
  letter-spacing:0.07em; color:#5A6174; text-transform:uppercase;
}}

/* Reference 4-column KPI cards */
.gl-ref-kpi {{
  background:#FFFFFF;
  border-radius:10px;
  overflow:hidden;
  box-shadow:var(--shadow);
  border:1px solid #DFECE9;
  height:100%;
}}
.gl-ref-kpi-head {{
  background:var(--slate);
  color:#FFFFFF;
  padding:8px 16px;
  font-family:var(--font-display);
  font-size:13px;
  font-weight:600;
  letter-spacing:0.08em;
  text-transform:uppercase;
  line-height:1.2;
}}
.gl-ref-kpi-body {{
  padding:16px 18px 15px;
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:12px;
}}
.gl-ref-kpi-val {{
  font-family:var(--font-display);
  font-size:32px;
  font-weight:700;
  color:var(--slate);
  line-height:1.05;
  font-variant-numeric:tabular-nums;
}}
.gl-ref-kpi-foot {{
  margin-top:9px;
  font-family:var(--font-display);
  font-size:12px;
  font-weight:600;
  letter-spacing:0.05em;
  text-transform:uppercase;
  color:#6A7084;
  white-space:nowrap;
  overflow:hidden;
  text-overflow:ellipsis;
}}
.gl-delta-up {{ color:var(--green-text); margin-right:5px; font-weight:700; }}
.gl-delta-down {{ color:var(--coral); margin-right:5px; font-weight:700; }}
.gl-ref-kpi-icon {{
  width:46px; height:46px; border-radius:999px;
  display:flex; align-items:center; justify-content:center; flex-shrink:0;
}}
.gl-icon-dark {{ background:var(--slate); color:#FFFFFF; }}
.gl-icon-green {{ background:var(--green); color:#FFFFFF; }}
.gl-icon-coral {{ background:var(--coral); color:#FFFFFF; }}

/* Reference stacked mini cards (Row 2 left) */
.gl-mini-stack {{ display:flex; flex-direction:column; gap:14px; height:100%; }}
.gl-mini-card {{
  background:#FFFFFF;
  border-radius:10px;
  padding:18px 20px;
  box-shadow:var(--shadow);
  border:1px solid #DFECE9;
  position:relative;
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:14px;
  min-height:122px;
}}
.gl-mini-dots {{
  position:absolute; top:10px; right:14px; display:flex; gap:3px;
}}
.gl-mini-dots span {{
  width:4px; height:4px; border-radius:999px; background:var(--green); display:block;
}}
.gl-mini-title {{
  font-family:var(--font-display); font-size:17px; font-weight:700;
  letter-spacing:0.05em; color:var(--slate); text-transform:uppercase; line-height:1.15;
}}
.gl-mini-sub {{
  font-size:12px; color:var(--text2); margin-top:6px; line-height:1.4;
}}
.gl-mini-metric {{
  font-family:var(--font-display); font-size:14px; font-weight:700;
  letter-spacing:0.04em; text-transform:uppercase; margin-top:4px;
}}
.gl-mini-icon {{
  width:46px; height:46px; display:flex; align-items:center; justify-content:center; flex-shrink:0;
}}

/* Reference line chart panel (Row 2 right) */
.st-key-card_home_line {{
  background:#FFFFFF !important;
  border:1px solid #DFECE9 !important;
  border-radius:10px !important;
  box-shadow:var(--shadow) !important;
  padding:14px 18px 6px !important;
}}
.gl-panel-label {{
  font-family:var(--font-display); font-size:14px; font-weight:700;
  letter-spacing:0.07em; color:var(--slate); text-transform:uppercase;
  display:flex; justify-content:space-between; align-items:center;
}}
.gl-panel-label span {{
  font-family:var(--font-body); font-size:11px; font-weight:600;
  color:var(--green-text); letter-spacing:0.02em; text-transform:none;
}}

/* Reference bottom-left coral-topped action card (Row 3 left) */
.st-key-card_home_action {{
  background:#FFFFFF !important;
  border:1px solid #DFECE9 !important;
  border-radius:10px !important;
  box-shadow:var(--shadow) !important;
  padding:0 !important;
  gap:0 !important;
  overflow:hidden;
}}
.gl-action-top {{
  background:var(--coral);
  height:38px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  padding:0 18px;
  color:#FFFFFF;
  font-family:var(--font-display);
  font-size:13px;
  font-weight:600;
  letter-spacing:0.08em;
  text-transform:uppercase;
}}
.gl-action-body {{
  padding:22px 20px 10px;
  display:flex;
  flex-direction:column;
  align-items:center;
  text-align:center;
}}
.gl-action-circle {{
  width:104px; height:104px; border-radius:999px;
  background:var(--slate);
  display:flex; align-items:center; justify-content:center;
  color:#FFFFFF;
  margin-bottom:14px;
  box-shadow:0 8px 20px rgba(38,40,51,0.16);
}}
.gl-action-title {{
  font-family:var(--font-display); font-size:21px; font-weight:700;
  letter-spacing:0.06em; color:var(--slate); text-transform:uppercase;
}}
.gl-action-sub {{
  font-size:12px; color:var(--text2); margin-top:4px; line-height:1.4;
}}
.st-key-home_action_btn {{
  padding:8px 20px 18px;
}}

/* Reference bottom-right mint-green bar chart card (Row 3 right) */
.st-key-card_home_bars {{
  background:var(--green) !important;
  border:1px solid #7FD179 !important;
  border-radius:10px !important;
  box-shadow:var(--shadow) !important;
  padding:0 !important;
  gap:0 !important;
  overflow:hidden;
}}
.gl-green-head {{
  background:var(--slate);
  color:#FFFFFF;
  height:38px;
  padding:0 18px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  font-family:var(--font-display);
  font-size:13px;
  font-weight:600;
  letter-spacing:0.08em;
  text-transform:uppercase;
}}
.gl-green-head span {{
  color:var(--green); font-size:12px; letter-spacing:0.05em;
}}
.st-key-card_home_bars .stPlotlyChart {{
  padding:4px 12px 6px;
}}
.st-key-card_home_bars > [data-testid="stVerticalBlock"],
.st-key-card_home_action > [data-testid="stVerticalBlock"],
.st-key-card_home_line > [data-testid="stVerticalBlock"] {{
  gap:0.25rem !important;
}}
.st-key-card_home_bars > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"],
.st-key-card_home_action > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"] {{
  margin:0 !important;
}}

/* ===================== CARDS & SHARED COMPONENTS ===================== */
[class*="st-key-card_"], [class*="st-key-subjcard_"] {{
  background:var(--card);
  border:1px solid #DFECE9 !important;
  border-radius:12px;
  box-shadow:var(--shadow);
}}
[class*="st-key-subjcard_"] {{ padding:0 !important; gap:0 !important; overflow:hidden; }}
[class*="st-key-subjact_"] {{
  margin:0 20px 20px; padding-top:14px; border-top:1px solid var(--border); width:auto !important;
}}

/* html components */
.gl-title {{ font-family:var(--font-display); font-size:28px; font-weight:700; letter-spacing:0.03em;
  text-transform:uppercase; line-height:1.15; color:var(--text); margin:0; }}
.gl-subtitle {{ font-size:14px; color:var(--text2); margin:4px 0 0; }}
.gl-header {{ display:flex; justify-content:space-between; align-items:flex-start; gap:16px; flex-wrap:wrap; margin-bottom:20px; }}
.gl-chips {{ display:flex; gap:8px; flex-wrap:wrap; }}
.gl-pill {{ display:inline-block; border-radius:999px; padding:4px 12px; font-size:12px; font-weight:600; line-height:1.4; }}
.gl-chip {{ display:inline-block; border-radius:999px; padding:4px 11px; font-size:12px; font-weight:600; }}
.gl-kpi {{ background:var(--card); border-radius:12px; border:1px solid #DFECE9; box-shadow:var(--shadow); padding:18px 20px; }}
.gl-kpi-label {{ font-family:var(--font-display); font-size:12px; color:var(--text2); font-weight:600; letter-spacing:.06em; text-transform:uppercase; }}
.gl-kpi-value {{ font-family:var(--font-display); font-size:30px; font-weight:700; color:var(--text); font-variant-numeric:tabular-nums; line-height:1.2; }}
.gl-kpi-sub {{ font-size:12px; color:var(--text2); }}
.gl-kpi-pill {{ margin:8px 0 6px; }}
.gl-card-head {{ margin:0 0 4px; }}
.gl-card-head-row {{ display:flex; justify-content:space-between; align-items:baseline; gap:12px; }}
.gl-card-title {{ font-size:17px; font-weight:700; line-height:1.35; letter-spacing:-0.015em; color:var(--text); }}
.gl-card-aside {{ flex-shrink:0; }}
.gl-card-sub {{ font-size:13px; color:var(--text2); margin:4px 0 0; line-height:1.5; }}
.gl-figure {{ font-family:var(--font-display); font-size:32px; font-weight:700; color:var(--text); font-variant-numeric:tabular-nums;
  line-height:1.2; margin:6px 0 8px; }}
.gl-figure-aside {{ font-size:14px; font-weight:600; color:var(--text2); }}
.gl-chart-title {{ font-size:14px; font-weight:700; color:var(--text); }}
.gl-chart-aside {{ font-weight:500; color:var(--text2); }}
.gl-empty {{ display:flex; gap:12px; align-items:flex-start; border:2px dashed var(--border);
  background:var(--muted); border-radius:12px; padding:14px 16px; }}
.gl-empty-icon {{ width:32px; height:32px; border-radius:10px; background:#fff; display:flex; align-items:center;
  justify-content:center; font-size:16px; flex-shrink:0; }}
.gl-empty-title {{ font-size:14px; font-weight:600; color:var(--text); }}
.gl-empty-text {{ font-size:13px; color:var(--text2); line-height:1.5; margin-top:2px; }}
.gl-hero {{ background:{GRAD_HERO}; color:#FFFFFF; border-radius:12px; padding:24px 28px; box-shadow:var(--shadow); }}
.gl-hero h2 {{ color:#FFFFFF; margin:0 0 4px; font-size:24px; }}
.gl-hero p {{ margin:0; font-size:14px; color:#D5DAE6; }}
.gl-section {{ background:var(--card); border:1px solid #DFECE9; border-radius:12px; box-shadow:var(--shadow); padding:20px 22px; margin-bottom:16px; }}
.gl-section .gl-card-head {{ margin-bottom:8px; }}
.gl-section p, .gl-section li {{ font-size:14px; color:var(--text2); }}
.gl-callout {{ display:flex; gap:12px; align-items:flex-start; background:#FFFFFF;
  border:1px solid var(--border); border-left:4px solid var(--coral); border-radius:10px;
  padding:14px 16px; font-size:13px; color:var(--text); margin-top:12px; box-shadow:var(--shadow-sm); }}
.gl-file {{ display:flex; gap:12px; align-items:center; background:{GRAD_CHAMPAGNE}; border:2px dashed var(--coral);
  border-radius:12px; padding:12px 14px; margin-bottom:8px; }}
.gl-file-icon {{ width:36px; height:36px; border-radius:10px; background:#fff; display:flex; align-items:center;
  justify-content:center; color:var(--coral); font-size:18px; flex:none; }}
.gl-file b {{ display:block; font-size:14px; color:var(--text); word-break:break-all; }}
.gl-file span {{ font-size:12px; color:var(--text2); }}
.gl-soon {{ background:var(--card); border:1px solid #DFECE9; border-radius:12px; box-shadow:var(--shadow); padding:36px 28px; text-align:center; }}
.gl-soon-icon {{ width:56px; height:56px; border-radius:14px; margin:0 auto 14px; display:flex;
  align-items:center; justify-content:center; background:var(--slate); color:var(--coral); font-size:26px; }}
.gl-soon h3 {{ margin:0 0 6px; font-size:18px; }}
.gl-soon p {{ margin:0; color:var(--text2); font-size:14px; }}

/* goal tab */
.gl-hero-row {{ display:flex; justify-content:space-between; align-items:center; gap:20px; flex-wrap:wrap; }}
.gl-hero-eyebrow {{ font-family:var(--font-display); font-size:13px; font-weight:600; letter-spacing:.08em; text-transform:uppercase; color:var(--green); margin-bottom:6px; }}
.gl-targets {{ display:flex; gap:12px; flex-wrap:wrap; }}
.gl-target-card {{ background:#fff; color:var(--slate); border-radius:10px; padding:10px 16px; min-width:110px; }}
.gl-target-card small {{ display:block; font-size:11px; font-weight:700; letter-spacing:.04em; text-transform:uppercase; color:var(--text2); }}
.gl-target-card b {{ font-family:var(--font-display); font-size:28px; font-variant-numeric:tabular-nums; }}
.gl-target-card span {{ font-size:12px; color:var(--text2); }}
.gl-rule {{ display:flex; gap:10px; align-items:center; margin:6px 0; font-size:12px; color:var(--text2); }}
.gl-formula {{ background:{GRAD_CHAMPAGNE}; border:1px solid var(--border); border-radius:10px; padding:12px 14px;
  font-size:14px; font-weight:600; color:var(--text); margin-bottom:10px; }}
.gl-formula-note {{ display:block; font-weight:400; font-size:12px; margin-top:2px; }}
.gl-formula.gl-formula-fail {{ background:#FDE8E4; border-color:#F8CFC7; color:#B91C1C; }}
.gl-eyebrow {{ font-family:var(--font-display); font-size:13px; font-weight:700; letter-spacing:.06em; text-transform:uppercase; color:var(--text2); margin:12px 0 4px; }}

/* subject card (redesigned to match reference dark-slate & coral header cards) */
.gl-banner {{ display:flex; justify-content:space-between; align-items:center; padding:16px 20px; min-height:74px; }}
.gl-banner-hero {{ background:var(--slate) !important; color:#FFFFFF !important; border-bottom:3px solid var(--green); }}
.gl-banner-deep {{ background:var(--slate) !important; color:#FFFFFF !important; border-bottom:3px solid var(--coral); }}
.gl-banner-code {{ font-family:var(--font-display); font-size:12px; font-weight:600; letter-spacing:.10em; text-transform:uppercase; color:#C4CBDC !important; }}
.gl-banner-name {{ font-family:var(--font-display); font-size:23px; font-weight:700; letter-spacing:0.03em; text-transform:uppercase; color:#FFFFFF !important; line-height:1.15; margin-top:2px; }}
.gl-banner-icon {{ width:42px; height:42px; border-radius:999px; background:rgba(255,255,255,0.10); display:flex;
  align-items:center; justify-content:center; font-size:18px; color:var(--green); flex-shrink:0; }}
.gl-banner-deep .gl-banner-icon {{ color:var(--coral); }}
.gl-card-body {{ padding:18px 20px 6px; display:flex; flex-direction:column; gap:14px; }}
.gl-row {{ display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap; }}
.gl-fac-avatar {{ width:34px; height:34px; border-radius:999px; background:var(--coral-soft); color:var(--coral-dark);
  display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:700; }}
.gl-meta {{ font-size:12px; color:var(--text2); }}
.gl-fac {{ display:flex; align-items:center; gap:10px; }}
.gl-fac-name {{ font-size:14px; font-weight:600; color:var(--slate); }}
.gl-split-cia {{ color:var(--slate); }}
.gl-split-ese {{ color:var(--coral-dark); }}
.gl-pill-row {{ display:flex; gap:6px; flex-wrap:wrap; margin-top:8px; }}
.gl-split-labels {{ display:flex; justify-content:space-between; font-size:12px; font-weight:600; margin-bottom:6px; }}
.gl-bar {{ display:flex; height:8px; border-radius:999px; overflow:hidden; gap:3px; background:#EAF2F0; }}
.gl-bar > div {{ height:100%; border-radius:999px; }}
.gl-topics {{ display:flex; flex-wrap:wrap; gap:6px; }}
.gl-enrolled {{ display:flex; align-items:center; justify-content:center; gap:8px; height:40px;
  background:var(--green-soft); color:var(--green-text); border-radius:8px; padding:0 14px; font-size:13px; font-weight:600; }}

/* controls */
.stButton > button, .stFormSubmitButton > button, [data-testid="stBaseButton-secondary"] {{
  border-radius:8px; font-weight:600; border:1px solid #C5D9D5; color:var(--slate); background:#FFFFFF; min-height:40px;
  transition:all .15s ease;
}}
.stButton > button:hover {{ border-color:var(--slate); color:var(--slate); background:var(--muted); }}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primaryFormSubmit"],
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"] {{
  background:var(--slate); color:#FFFFFF; border:none; box-shadow:0 4px 12px rgba(38,40,51,0.14);
}}
.stButton > button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover {{
  background:var(--coral); color:#FFFFFF;
}}
.stButton > button[kind="primary"] p, [data-testid="stBaseButton-primary"] p {{ color:#FFFFFF; }}
[data-testid="stMain"] [data-baseweb="input"],
[data-testid="stMain"] [data-baseweb="select"] > div,
[data-testid="stMain"] [data-baseweb="base-input"] {{
  background:var(--muted) !important; border-radius:8px !important; border-color:var(--border) !important;
}}
[data-testid="stMain"] [data-testid="stNumberInput"] input,
[data-testid="stMain"] [data-testid="stTextInput"] input {{ font-weight:600; color:var(--text); }}
[data-testid="stButtonGroup"] {{ width:100%; }}
[data-testid="stButtonGroup"] [role="radiogroup"] {{ background:#fff; border:1px solid var(--border);
  border-radius:8px; padding:4px; width:100%; display:flex; gap:4px; }}
[data-testid="stButtonGroup"] button[data-variant="segmented_control"] {{ flex:1 1 0; min-width:0; padding:0 6px; white-space:nowrap; border:none; border-radius:6px;
  background:transparent; color:var(--text2); font-weight:600; min-height:34px; }}
[data-testid="stButtonGroup"] button[data-variant="segmented_control"][aria-checked="true"] {{
  background:var(--slate); color:#fff; }}
[data-testid="stButtonGroup"] button[data-variant="segmented_control"][aria-checked="true"] p {{ color:#fff; }}
.stButton > button {{ white-space:nowrap; padding:0 10px; width:100%; }}
[class*="st-key-enrolled_"] button {{ background:var(--green-soft) !important; color:#277A35 !important; border:1px solid #C2EBC0 !important; opacity:1 !important; }}
[class*="st-key-enrolled_"] button p {{ color:#277A35 !important; }}
.stTabs [data-baseweb="tab-highlight"] {{ background:var(--coral); }}
.stTabs [aria-selected="true"] {{ color:var(--slate); font-weight:700; }}
[data-testid="stFileUploaderDropzone"] {{ border:2px dashed #9ABCB5; background:var(--muted); border-radius:12px; }}
[data-testid="stExpander"] {{ border:1px solid var(--border); border-radius:10px; background:#fff; }}
[data-testid="stAlert"] {{ border-radius:10px; }}

/* CIA analysis & other views */
.gl-tile {{ display:flex; align-items:center; gap:12px; border-radius:10px; padding:14px 16px; }}
.gl-tile-icon {{ width:38px; height:38px; border-radius:999px; background:#fff; display:flex;
  align-items:center; justify-content:center; font-size:17px; font-weight:700; flex-shrink:0; }}
.gl-tile-label {{ font-size:12px; color:var(--text2); font-weight:600; }}
.gl-tile-value {{ font-family:var(--font-display); font-size:24px; font-weight:700; color:var(--text); font-variant-numeric:tabular-nums; line-height:1.2; }}
.gl-tile-unit {{ font-size:13px; font-weight:500; color:var(--text2); margin-left:4px; }}
.gl-tile > div:last-child {{ min-width:0; }}
.gl-tile-label, .gl-tile-value {{ white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
@media (max-width:1200px) {{ .gl-tile-icon {{ display:none; }} .gl-tile {{ padding:12px; }} }}
.gl-warn {{ display:flex; gap:12px; align-items:flex-start; background:#FFF2E2; border:1px solid #F4A261;
  border-radius:10px; padding:14px 16px; font-size:13px; color:var(--text); margin:14px 0 4px; }}
.gl-warn-icon {{ color:#B45309; font-size:18px; line-height:1.2; }}
.gl-warn-title {{ font-weight:700; color:#9A4B16; font-size:14px; margin-bottom:2px; }}
.gl-table-wrap {{ border:1px solid var(--border); border-radius:10px; overflow-x:auto; margin:14px 0 6px; }}
.gl-table {{ width:100%; border-collapse:collapse; font-size:14px; font-variant-numeric:tabular-nums; }}
.gl-table th {{ background:var(--slate); color:#FFFFFF; font-family:var(--font-display); font-size:13px; font-weight:600;
  text-transform:uppercase; letter-spacing:.06em; text-align:left; padding:10px 14px; border:none; }}
.gl-table td {{ padding:10px 14px; border:none; border-top:1px solid #E5EFECE6; color:var(--text); }}
.gl-table .gl-q {{ font-weight:700; }}
.gl-table th.gl-num-col, .gl-table td.gl-num-col {{ text-align:right; }}
.gl-table .gl-muted {{ color:var(--text2); }}
.gl-table .gl-you {{ font-weight:700; color:var(--coral-dark); }}
.gl-table .gl-pill {{ font-size:12px; padding:3px 10px; }}
.gl-gain {{ font-size:12px; font-weight:700; color:var(--green-text); }}
.gl-tip-title {{ font-size:15px; font-weight:700; color:var(--text); margin:10px 0 6px; }}
.gl-tip-text {{ font-size:13px; color:var(--text2); line-height:1.5; margin:0 0 8px; }}
[class*="st-key-tip_"] {{ background:var(--card); border:1px solid #DFECE9 !important; border-radius:12px;
  box-shadow:var(--shadow); border-top:4px solid var(--border) !important; }}
[class*="st-key-tip_concept-gap"] {{ border-top-color:#E0523B !important; }}
[class*="st-key-tip_time-pressure"] {{ border-top-color:#F4A261 !important; }}
[class*="st-key-tip_silly-loss"] {{ border-top-color:var(--coral) !important; }}
[class*="st-key-tip_silly-flagged"] {{ border-top-color:var(--slate) !important; }}
[class*="st-key-tip_not-attempted"] {{ border-top-color:#64697D !important; }}
[class*="st-key-tip_"] [data-testid="stCheckbox"] {{ border-top:1px solid var(--border); padding-top:10px; }}
[class*="st-key-tip_"] [data-testid="stCheckbox"] p {{ font-size:13px; }}
.gl-rank {{ display:flex; gap:12px; align-items:center; }}
.gl-rank-n {{ width:40px; height:40px; border-radius:999px; background:var(--coral-soft); color:var(--coral-dark); display:flex;
  align-items:center; justify-content:center; font-weight:700; font-size:15px; }}
.gl-rank-title {{ font-size:18px; font-weight:700; color:var(--text); }}
.gl-rank-lost {{ font-size:14px; color:var(--text); margin:14px 0 8px; font-variant-numeric:tabular-nums; }}
.gl-rank-gap {{ margin-top:12px; }}
.gl-eyebrow2 {{ font-family:var(--font-display); font-size:13px; font-weight:700; letter-spacing:.06em; text-transform:uppercase;
  color:var(--text2); margin:14px 0 8px; }}
.gl-res {{ display:flex; align-items:center; gap:12px; border:1px solid var(--border); border-radius:10px;
  padding:12px 14px; margin-bottom:10px; background:#fff; text-decoration:none !important; }}
.gl-res.gl-auto {{ background:var(--muted); border-color:transparent; }}
.gl-res-list {{ display:flex; flex-direction:column; }}
.gl-res-list .gl-res:last-child {{ margin-bottom:0; }}
.gl-res-icon {{ font-size:18px; width:28px; text-align:center; flex-shrink:0; }}
.gl-res-title {{ display:block; font-size:14px; font-weight:600; color:var(--text); margin-bottom:6px;
  overflow-wrap:anywhere; }}
.gl-res-meta {{ display:flex; gap:6px; flex-wrap:wrap; }}
.gl-res-meta .gl-pill {{ font-size:12px; padding:2px 10px; }}
.gl-res-go {{ margin-left:auto; color:var(--coral-dark); font-size:16px; flex-shrink:0; }}
.gl-res-body {{ display:block; flex:1; min-width:0; }}
.gl-rule-note {{ background:var(--muted); border:1px solid var(--border); border-radius:10px; padding:12px 14px;
  font-size:13px; color:var(--slate); margin:8px 0 14px; }}
.gl-section-head {{ display:flex; justify-content:space-between; align-items:baseline; gap:12px;
  flex-wrap:wrap; margin:22px 0 12px; }}
.gl-section-head .gl-section-title {{ font-family:var(--font-display); font-size:21px; font-weight:700; color:var(--slate); letter-spacing:0.05em; text-transform:uppercase; }}
.gl-section-head span {{ font-family:var(--font-display); font-size:13px; font-weight:600; letter-spacing:0.05em; text-transform:uppercase; color:var(--text2); }}
.gl-tab-head {{ margin:8px 0 14px; }}
.gl-tab-head .gl-section-title {{ font-family:var(--font-display); font-size:22px; font-weight:700; color:var(--text); letter-spacing:0.03em; text-transform:uppercase; line-height:1.25; }}
.gl-tab-sub {{ font-size:13px; color:var(--text2); margin:4px 0 0; }}

/* --- layout polish ------------------------------------------------------------ */
[data-testid="stToolbarActions"], [data-testid="stAppDeployButton"], [data-testid="stMainMenu"],
[data-testid="stDecoration"] {{ display:none !important; }}
[data-testid="stHeader"] {{ pointer-events:none; }}
[data-testid="stHeader"] button, [data-testid="stHeader"] a {{ pointer-events:auto; }}
h1.gl-title, h1.gl-title * {{ font-size:28px !important; font-weight:700; line-height:1.15; padding:0; }}
.gl-header {{ align-items:flex-start; }}
.gl-header .gl-chips {{ padding-top:6px; }}
[data-testid="stColumn"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"]:only-child:has(> [class*="st-key-card_"]),
[data-testid="stColumn"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"]:only-child:has(> [class*="st-key-tip_"]),
[data-testid="stColumn"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"]:only-child:has(> [class*="st-key-subjcard_"]) {{
  flex:1 1 auto; display:flex; flex-direction:column; }}
[data-testid="stColumn"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"]:only-child > [class*="st-key-card_"],
[data-testid="stColumn"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"]:only-child > [class*="st-key-tip_"],
[data-testid="stColumn"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"]:only-child > [class*="st-key-subjcard_"] {{
  flex:1 1 auto; }}
[class*="st-key-tip_"] > [data-testid="stElementContainer"]:has([data-testid="stCheckbox"]) {{ margin-top:auto; }}
[class*="st-key-subjcard_"] > [data-testid="stLayoutWrapper"]:has(> [class*="st-key-subjact_"]),
[class*="st-key-subjcard_"] > [class*="st-key-subjact_"] {{ margin-top:auto; }}
[data-testid="stMarkdownContainer"]:has(> [class*="gl-"]:last-child) {{ margin-bottom:0 !important; }}
.stPlotlyChart .main-svg {{ background:transparent !important; }}
.stPlotlyChart .modebar-group {{ background:transparent !important; }}
.st-key-card_ese_score {{ background:{GRAD_HERO} !important; }}
.st-key-card_ese_score .gl-kpi-label, .st-key-card_ese_score .gl-figure,
.st-key-card_ese_score [data-testid="stCaptionContainer"] {{ color:#FFFFFF; }}
[data-testid="stCheckbox"] label {{ align-items:flex-start; }}
[data-testid="stCheckbox"] label p, [data-testid="stCheckbox"] label div {{ white-space:normal !important;
  overflow:visible !important; text-overflow:clip !important; }}
.st-key-ese_actions .stButton > button {{ padding:0 16px; }}
.gl-field-label {{ font-size:14px; color:var(--text); margin-bottom:8px; line-height:1.6; }}
.gl-field-value {{ height:40px; display:flex; align-items:center; padding:0 12px; border-radius:8px;
  background:var(--muted); border:1px solid var(--border); color:var(--text2); font-size:14px; }}
.gl-table-scroll {{ max-height:420px; overflow-y:auto; }}
.gl-table-scroll thead th {{ position:sticky; top:0; z-index:1; }}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"]) {{ background:#FFFFFF;
  border:1px solid var(--border); border-left:4px solid var(--slate); border-radius:10px; }}
[data-testid="stAlertContentInfo"], [data-testid="stAlertContentInfo"] p {{ color:var(--text); }}
[data-testid="stAlertContentInfo"] code {{ background:var(--muted); color:var(--coral-dark); }}
.gl-card-head + div, [data-testid="stCaptionContainer"] p {{ line-height:1.5; }}

/* ===================== LOGIN PORTAL ===================== */
.st-key-login_topbar {{
  background:#FFFFFF !important;
  border-radius:10px !important;
  padding:10px 20px !important;
  box-shadow:var(--shadow-sm) !important;
  border:1px solid #DFECE9 !important;
  margin-bottom:20px !important;
}}
.st-key-login_topbar > [data-testid="stVerticalBlock"] {{
  gap:0 !important;
}}
.st-key-login_topbar [data-testid="stButtonGroup"] [role="radiogroup"] {{
  background:#EAF4F2 !important;
  border:1px solid #D5E7E3 !important;
  border-radius:999px !important;
  padding:4px !important;
}}
.st-key-login_topbar [data-testid="stButtonGroup"] button[data-variant="segmented_control"] {{
  border-radius:999px !important;
  min-height:36px !important;
  font-family:var(--font-display) !important;
  font-size:14px !important;
  font-weight:700 !important;
  letter-spacing:0.06em !important;
  text-transform:uppercase !important;
  color:var(--slate) !important;
}}
.st-key-login_topbar [data-testid="stButtonGroup"] button[data-variant="segmented_control"][aria-checked="true"] {{
  background:var(--slate) !important;
  color:#FFFFFF !important;
  box-shadow:0 3px 10px rgba(38,40,51,0.16) !important;
}}
.st-key-login_topbar [data-testid="stButtonGroup"] button[data-variant="segmented_control"][aria-checked="true"] p {{
  color:#FFFFFF !important;
}}
.st-key-card_login {{
  background:#FFFFFF !important;
  border:1px solid #DFECE9 !important;
  border-radius:12px !important;
  box-shadow:var(--shadow) !important;
  padding:0 !important;
  gap:0 !important;
  overflow:hidden !important;
}}
.st-key-card_login > [data-testid="stVerticalBlock"] {{
  gap:0 !important;
}}
.gl-login-head {{
  background:var(--slate);
  color:#FFFFFF;
  padding:18px 24px;
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:14px;
}}
.gl-login-head-student {{ border-bottom:3px solid var(--green); }}
.gl-login-head-faculty {{ border-bottom:3px solid var(--coral); }}
.gl-login-eyebrow {{
  font-family:var(--font-display);
  font-size:12px;
  font-weight:600;
  letter-spacing:0.10em;
  text-transform:uppercase;
  color:#B9C0D4;
}}
.gl-login-title {{
  font-family:var(--font-display);
  font-size:26px;
  font-weight:700;
  letter-spacing:0.04em;
  text-transform:uppercase;
  color:#FFFFFF;
  line-height:1.1;
  margin-top:2px;
}}
.gl-login-badge {{
  width:44px;
  height:44px;
  border-radius:999px;
  display:flex;
  align-items:center;
  justify-content:center;
  flex-shrink:0;
}}
.gl-login-badge-student {{ background:var(--green); color:var(--slate); }}
.gl-login-badge-faculty {{ background:var(--coral); color:#FFFFFF; }}
.st-key-login_form_body {{
  padding:20px 24px 22px !important;
}}
.gl-login-desc {{
  font-size:13px;
  color:var(--text2);
  line-height:1.5;
  margin:0 0 12px;
}}
.gl-login-note {{
  background:#F3FAF8;
  border:1px solid #D7E8E4;
  border-radius:8px;
  padding:10px 12px;
  font-size:12px;
  color:var(--text2);
  line-height:1.45;
  margin-top:12px;
}}
.gl-login-note b {{ color:var(--slate); }}
.gl-login-footer {{
  text-align:center;
  font-family:var(--font-display);
  font-size:12px;
  letter-spacing:0.12em;
  color:#6D7285;
  text-transform:uppercase;
  margin-top:26px;
}}
.gl-role-badge {{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:8px;
  background:#262833;
  border:1px solid rgba(255,255,255,0.10);
  border-radius:8px;
  padding:8px 10px;
  margin-bottom:10px;
}}
.gl-role-badge-text {{
  font-family:var(--font-display);
  font-size:14px;
  font-weight:700;
  letter-spacing:0.06em;
  text-transform:uppercase;
  color:#FFFFFF;
}}
.gl-role-dot {{
  width:8px;
  height:8px;
  border-radius:999px;
  display:inline-block;
  margin-right:7px;
}}
.gl-role-user {{
  font-size:11px;
  color:#9BA1B4;
}}

/* ===================== LOADING BARS & BUSY INDICATOR ===================== */
@keyframes gl-loading-slide {{
  0% {{ background-position:0% 50%; }}
  100% {{ background-position:200% 50%; }}
}}
@keyframes gl-pulse-dot {{
  0%, 100% {{ opacity:1; transform:scale(1); }}
  50% {{ opacity:0.45; transform:scale(0.8); }}
}}
/* Automatic top-of-screen animated loading bar whenever Streamlit is running */
body:has([data-testid="stStatusWidget"])::before {{
  content:"";
  position:fixed;
  top:0;
  left:0;
  width:100%;
  height:4px;
  z-index:999999;
  background:linear-gradient(90deg, var(--slate) 0%, var(--coral) 35%, var(--green) 65%, var(--slate) 100%);
  background-size:200% 100%;
  animation:gl-loading-slide 1.1s linear infinite;
  pointer-events:none;
}}
[data-testid="stStatusWidget"] {{
  background:var(--slate) !important;
  color:#FFFFFF !important;
  border:1px solid rgba(242,125,101,0.45) !important;
  border-radius:999px !important;
  padding:4px 12px !important;
  box-shadow:0 6px 18px rgba(38,40,51,0.18) !important;
}}
[data-testid="stStatusWidget"] label,
[data-testid="stStatusWidget"] span,
[data-testid="stStatusWidget"] button {{
  color:#FFFFFF !important;
  font-family:var(--font-display) !important;
  font-size:13px !important;
  letter-spacing:0.06em !important;
  text-transform:uppercase !important;
}}
[data-testid="stStatusWidget"] svg {{
  color:var(--coral) !important;
}}
/* Branded st.progress bar */
[data-testid="stProgress"] > div > div > div {{
  background:#DCECE8 !important;
  border-radius:999px !important;
  height:10px !important;
  overflow:hidden !important;
}}
[data-testid="stProgress"] > div > div > div > div {{
  background:linear-gradient(90deg, var(--slate) 0%, var(--coral) 55%, var(--green) 100%) !important;
  border-radius:999px !important;
  transition:width 0.22s ease !important;
}}
/* Branded inline loading card */
.gl-loader-card {{
  background:#F4FAF8;
  border:1px solid #CFE3DE;
  border-left:4px solid var(--coral);
  border-radius:10px;
  padding:12px 14px 10px;
  margin:10px 0 6px;
  box-shadow:var(--shadow-sm);
}}
.gl-loader-row {{
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:10px;
}}
.gl-loader-title {{
  display:inline-flex;
  align-items:center;
  gap:8px;
  font-family:var(--font-display);
  font-size:15px;
  font-weight:700;
  letter-spacing:0.06em;
  text-transform:uppercase;
  color:var(--slate);
}}
.gl-loader-pulse {{
  width:8px;
  height:8px;
  border-radius:999px;
  background:var(--coral);
  display:inline-block;
  animation:gl-pulse-dot 0.9s ease-in-out infinite;
}}
.gl-loader-pct {{
  font-family:var(--font-display);
  font-size:15px;
  font-weight:700;
  color:var(--coral-dark);
  font-variant-numeric:tabular-nums;
}}
.gl-loader-status {{
  font-size:12px;
  color:var(--text2);
  margin-top:3px;
}}
"""

HIDE_SIDEBAR_CSS = """
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {
  display:none !important;
}
"""


def inject_theme() -> None:
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


def hide_sidebar() -> None:
    st.markdown(f"<style>{HIDE_SIDEBAR_CSS}</style>", unsafe_allow_html=True)
