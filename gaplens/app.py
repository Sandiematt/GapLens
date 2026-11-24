"""GapLens entry point: boot DB, theme, login gate, sidebar, role-based navigation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st  # noqa: E402

import config  # noqa: E402
from core import db, seed  # noqa: E402
from ui import loader, profile  # noqa: E402
from ui.flash import show_flash  # noqa: E402
from ui.login import render_faculty_switch_login, render_login  # noqa: E402
from ui.sidebar import render_sidebar  # noqa: E402
from ui.theme import inject_theme  # noqa: E402

st.set_page_config(page_title=f"{config.APP_NAME} · {config.APP_TAGLINE}",
                   page_icon=":material/lens_blur:", layout="wide")

inject_theme()
if not db.DB_PATH.exists():
    loader.run_with_loading_bar(
        f"Initializing {config.APP_NAME}",
        "Setting up database and demo academic records…",
        seed.ensure_seeded,
        done_status="Workspace ready.",
    )
else:
    seed.ensure_seeded()

# role -> [(script, title, icon, url_path)]; add new pages here.
PAGES = {
    "Student": [
        ("views/student_subjects.py", "My Subjects", ":material/grid_view:", "my-subjects"),
        ("views/student_dashboard.py", "Subject Dashboard", ":material/target:", "subject-dashboard"),
    ],
    "Faculty": [
        ("views/faculty_subjects.py", "My Subjects", ":material/grid_view:", "faculty-subjects"),
        ("views/faculty_papers.py", "Papers & Marks", ":material/edit_note:", "papers-marks"),
        ("views/faculty_ese.py", "ESE Scripts", ":material/description:", "ese-scripts"),
        ("views/faculty_resources.py", "Resources", ":material/menu_book:", "resources"),
        ("views/faculty_insights.py", "Class Insights", ":material/monitoring:", "class-insights"),
    ],
}

if not profile.is_authenticated():
    pg = st.navigation(
        [st.Page(render_login, title="Sign in", icon=":material/lock:", url_path="login", default=True)],
        position="hidden",
    )
    pg.run()
elif profile.is_faculty_switch_pending():
    pg = st.navigation(
        [st.Page(render_faculty_switch_login, title="Faculty Sign in", icon=":material/lock:",
                 url_path="faculty-login", default=True)],
        position="hidden",
    )
    pg.run()
else:
    role = profile.current_role()
    pages = [st.Page(script, title=title, icon=icon, url_path=url, default=(i == 0))
             for i, (script, title, icon, url) in enumerate(PAGES[role])]
    pg = st.navigation(pages, position="hidden")
    render_sidebar(pages, role)
    show_flash()
    pg.run()
