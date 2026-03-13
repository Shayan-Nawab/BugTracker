import streamlit as st
import db

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="BugTrack",
    page_icon="🐛",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styling ───────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Dark sidebar */
    [data-testid="stSidebar"] {
        background-color: #0f1117;
        border-right: 1px solid #1e2130;
    }
    [data-testid="stSidebar"] * {
        color: #c9d1d9 !important;
    }

    /* Main background */
    .stApp { background-color: #0d1117; color: #c9d1d9; }

    /* Cards */
    .bug-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 10px;
        transition: border-color 0.2s;
    }
    .bug-card:hover { border-color: #58a6ff; }

    .bug-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 15px;
        font-weight: 600;
        color: #58a6ff;
        margin-bottom: 4px;
    }
    .bug-meta {
        font-size: 12px;
        color: #8b949e;
        margin-bottom: 6px;
    }
    .bug-desc { font-size: 13px; color: #c9d1d9; }

    /* Badges */
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
        margin-right: 6px;
    }
    .badge-open    { background:#1f3a1f; color:#3fb950; border:1px solid #238636; }
    .badge-closed  { background:#1f2937; color:#8b949e; border:1px solid #30363d; }
    .badge-in-progress { background:#1e2d40; color:#58a6ff; border:1px solid #1f6feb; }
    .badge-critical { background:#3d1a1a; color:#f85149; border:1px solid #da3633; }
    .badge-high    { background:#2d1f0e; color:#e3b341; border:1px solid #9e6a03; }
    .badge-medium  { background:#1e2d40; color:#58a6ff; border:1px solid #1f6feb; }
    .badge-low     { background:#1f2937; color:#8b949e; border:1px solid #30363d; }

    /* Headings */
    h1, h2, h3 { font-family: 'JetBrains Mono', monospace !important; color: #e6edf3 !important; }

    /* Inputs */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea,
    .stSelectbox>div>div>div {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        color: #c9d1d9 !important;
        border-radius: 6px !important;
    }

    /* Buttons */
    .stButton>button {
        background-color: #238636;
        color: white;
        border: none;
        border-radius: 6px;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        padding: 6px 16px;
        transition: background-color 0.2s;
    }
    .stButton>button:hover { background-color: #2ea043; }

    /* Login card */
    .login-wrap {
        max-width: 400px;
        margin: 60px auto;
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 40px;
    }

    /* Divider */
    hr { border-color: #21262d; }

    /* Bug ID chip */
    .bug-id {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        color: #8b949e;
    }

    /* Success / error */
    .stSuccess { background-color: #1f3a1f !important; }
    .stError   { background-color: #3d1a1a !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "page" not in st.session_state:
    st.session_state.page = "bugs"
if "edit_bug_id" not in st.session_state:
    st.session_state.edit_bug_id = None

# ── Helpers ───────────────────────────────────────────────────────────────────

STATUS_OPTIONS   = ["Open", "In Progress", "Closed"]
PRIORITY_OPTIONS = ["Critical", "High", "Medium", "Low"]
CATEGORY_OPTIONS = ["Logic", "UI", "Performance", "Security", "Crash", "Data", "Other"]

def status_badge(status):
    cls = {"Open": "open", "Closed": "closed", "In Progress": "in-progress"}.get(status, "open")
    return f'<span class="badge badge-{cls}">{status}</span>'

def priority_badge(priority):
    cls = priority.lower() if priority else "medium"
    return f'<span class="badge badge-{cls}">{priority}</span>'

# ── Login / Register page ─────────────────────────────────────────────────────

def show_login():
    st.markdown('<div class="login-wrap">', unsafe_allow_html=True)
    st.markdown("## 🐛 BugTrack")
    st.markdown("---")

    tab_login, tab_register = st.tabs(["Sign In", "Register"])

    with tab_login:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Sign In", key="btn_login"):
            if db.validate_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid username or password.")

    with tab_register:
        new_user = st.text_input("Choose a username", key="reg_user")
        new_pass = st.text_input("Choose a password", type="password", key="reg_pass")
        new_pass2 = st.text_input("Confirm password", type="password", key="reg_pass2")
        if st.button("Create Account", key="btn_register"):
            if not new_user or not new_pass:
                st.error("Username and password are required.")
            elif new_pass != new_pass2:
                st.error("Passwords do not match.")
            elif db.create_user(new_user, new_pass):
                st.success("Account created! You can now sign in.")
            else:
                st.error("Username already taken.")

    st.markdown('</div>', unsafe_allow_html=True)

# ── Bug list page ─────────────────────────────────────────────────────────────

def show_bugs():
    st.markdown("# 🐛 Bug Tracker")
    st.markdown("---")

    # Filters
    col1, col2, col3, col4 = st.columns([3, 1.5, 1.5, 1])
    with col1:
        search = st.text_input("🔍 Search", placeholder="Title, description, reporter, category…")
    with col2:
        status_f = st.selectbox("Status", ["All"] + STATUS_OPTIONS)
    with col3:
        priority_f = st.selectbox("Priority", ["All"] + PRIORITY_OPTIONS)
    with col4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("＋ New Bug"):
            st.session_state.page = "new_bug"
            st.rerun()

    bugs = db.get_all_bugs(
        status_filter=status_f,
        priority_filter=priority_f,
        search_query=search if search else None,
    )

    st.markdown(f"<p style='color:#8b949e;font-size:13px;'>{len(bugs)} bug(s) found</p>", unsafe_allow_html=True)

    if not bugs:
        st.markdown("<p style='color:#8b949e;margin-top:40px;text-align:center;'>No bugs match your filters.</p>", unsafe_allow_html=True)
        return

    for bug in bugs:
        with st.container():
            st.markdown(f"""
            <div class="bug-card">
                <div class="bug-title">#{bug['id']} — {bug['title']}</div>
                <div class="bug-meta">
                    Reported by <strong>{bug['reporter']}</strong>
                    &nbsp;·&nbsp; Found: {bug['found_date'] or '—'}
                    &nbsp;·&nbsp; Fixed: {bug['fixed_date'] or '—'}
                    &nbsp;·&nbsp; Artifact: <code>{bug['artifact'] or '—'}</code>
                </div>
                <div style="margin-bottom:6px;">
                    {status_badge(bug['status'])}
                    {priority_badge(bug['priority'])}
                    {'<span class="badge badge-low">' + bug['category'] + '</span>' if bug['category'] else ''}
                </div>
                <div class="bug-desc">{bug['description'] or ''}</div>
            </div>
            """, unsafe_allow_html=True)

            col_edit, col_del, _ = st.columns([1, 1, 8])
            with col_edit:
                if st.button("Edit", key=f"edit_{bug['id']}"):
                    st.session_state.edit_bug_id = bug['id']
                    st.session_state.page = "edit_bug"
                    st.rerun()
            with col_del:
                if st.button("Delete", key=f"del_{bug['id']}"):
                    db.delete_bug(bug['id'])
                    st.rerun()

# ── Bug form (shared by new + edit) ──────────────────────────────────────────

def show_bug_form(existing=None):
    is_edit = existing is not None
    st.markdown(f"# {'✏️ Edit Bug' if is_edit else '＋ New Bug'}")
    st.markdown("---")

    if st.button("← Back to bugs"):
        st.session_state.page = "bugs"
        st.session_state.edit_bug_id = None
        st.rerun()

    with st.form("bug_form"):
        col1, col2 = st.columns(2)

        with col1:
            title = st.text_input("Title *", value=existing['title'] if is_edit else "")
            reporter = st.text_input(
                "Reporter *",
                value=existing['reporter'] if is_edit else st.session_state.username,
                disabled=is_edit,
            )
            status = st.selectbox(
                "Status",
                STATUS_OPTIONS,
                index=STATUS_OPTIONS.index(existing['status']) if is_edit else 0,
            )
            priority = st.selectbox(
                "Priority",
                PRIORITY_OPTIONS,
                index=PRIORITY_OPTIONS.index(existing['priority']) if is_edit and existing['priority'] in PRIORITY_OPTIONS else 2,
            )

        with col2:
            category = st.selectbox(
                "Category",
                CATEGORY_OPTIONS,
                index=CATEGORY_OPTIONS.index(existing['category']) if is_edit and existing['category'] in CATEGORY_OPTIONS else 0,
            )
            artifact = st.text_input("Artifact / Source file", value=existing['artifact'] if is_edit else "")
            found_date = st.date_input(
                "Found date",
                value=existing['found_date'] if is_edit and existing['found_date'] else None,
            )
            fixed_date = st.date_input(
                "Fixed date (optional)",
                value=existing['fixed_date'] if is_edit and existing['fixed_date'] else None,
            )

        description = st.text_area("Description", value=existing['description'] if is_edit else "", height=120)
        notes = st.text_area("Additional notes", value=existing['notes'] if is_edit else "", height=80)

        submitted = st.form_submit_button("Save Bug" if is_edit else "Create Bug")

        if submitted:
            if not title:
                st.error("Title is required.")
                return
            if fixed_date and found_date and fixed_date < found_date:
                st.error("Fixed date cannot be earlier than found date.")
                return

            if is_edit:
                db.update_bug(
                    existing['id'], title, description, status, priority,
                    category, artifact, found_date, fixed_date, notes
                )
                st.success("Bug updated.")
            else:
                bug_id = db.create_bug(
                    title, description, reporter, status, priority,
                    category, artifact, found_date, fixed_date, notes
                )
                st.success(f"Bug #{bug_id} created.")

            st.session_state.page = "bugs"
            st.session_state.edit_bug_id = None
            st.rerun()

# ── Sidebar ───────────────────────────────────────────────────────────────────

def show_sidebar():
    with st.sidebar:
        st.markdown(f"### 🐛 BugTrack")
        st.markdown(f"Signed in as **{st.session_state.username}**")
        st.markdown("---")
        if st.button("📋  All Bugs"):
            st.session_state.page = "bugs"
            st.rerun()
        if st.button("＋  New Bug"):
            st.session_state.page = "new_bug"
            st.rerun()
        st.markdown("---")
        if st.button("Sign Out"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.page = "bugs"
            st.rerun()

# ── Router ────────────────────────────────────────────────────────────────────

if not st.session_state.logged_in:
    show_login()
else:
    show_sidebar()

    if st.session_state.page == "bugs":
        show_bugs()
    elif st.session_state.page == "new_bug":
        show_bug_form()
    elif st.session_state.page == "edit_bug":
        bug = db.get_bug_by_id(st.session_state.edit_bug_id)
        if bug:
            show_bug_form(existing=bug)
        else:
            st.error("Bug not found.")
            st.session_state.page = "bugs"
            st.rerun()