import streamlit as st
import db

# Page config
st.set_page_config(
    page_title="BugTrack Workspace",
    page_icon="🐛",
    layout="wide",
    initial_sidebar_state="expanded",
)

db.init_db()

# Styling
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Mono:wght@400;600&display=swap');

    :root {
        --bg-1: #f8f5ef;
        --bg-2: #f0ebe1;
        --ink: #1f2a2e;
        --muted: #546168;
        --surface: rgba(255, 255, 255, 0.7);
        --line: #d9d4c8;
        --accent: #0f7b75;
        --open: #0f7b75;
        --progress: #1f6fb4;
        --closed: #6c757d;
        --critical: #bd3f3f;
        --high: #c0692b;
        --medium: #2f7f9f;
        --low: #60717d;
    }

    html, body, [class*="css"] {
        font-family: 'Space Grotesk', sans-serif;
        color: var(--ink);
    }

    .stApp {
        background:
            radial-gradient(circle at 10% 10%, #fff7d8 0%, transparent 32%),
            radial-gradient(circle at 90% 10%, #e3f3f2 0%, transparent 33%),
            linear-gradient(160deg, var(--bg-1) 0%, var(--bg-2) 100%);
        color: var(--ink);
    }

    [data-testid="stHeader"] {
        background: rgba(255, 255, 255, 0);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #17333d 0%, #10242b 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.15);
    }

    [data-testid="stSidebar"] * {
        color: #f4f8f9 !important;
    }

    h1, h2, h3 {
        font-family: 'IBM Plex Mono', monospace !important;
        color: var(--ink) !important;
        letter-spacing: -0.02em;
    }

    .title-hero {
        padding: 1rem 1.2rem;
        border: 1px solid var(--line);
        border-radius: 14px;
        background: linear-gradient(100deg, rgba(15, 123, 117, 0.08) 0%, rgba(220, 124, 58, 0.1) 100%);
        margin-bottom: 1rem;
    }

    .metric-card {
        border: 1px solid var(--line);
        border-radius: 14px;
        background: var(--surface);
        backdrop-filter: blur(6px);
        padding: 0.85rem 1rem;
    }

    .panel {
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 0.7rem;
        background: var(--surface);
        min-height: 520px;
    }

    .bug-card {
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 0.8rem;
        margin-bottom: 0.65rem;
        background: rgba(255, 255, 255, 0.65);
    }

    .bug-title {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.95rem;
        font-weight: 600;
        margin-bottom: 0.2rem;
    }

    .bug-meta {
        font-size: 0.8rem;
        color: var(--muted);
        margin-bottom: 0.45rem;
    }

    .bug-desc {
        font-size: 0.88rem;
        color: var(--ink);
    }

    .badge {
        display: inline-block;
        padding: 0.12rem 0.5rem;
        border-radius: 999px;
        font-size: 0.68rem;
        font-weight: 600;
        font-family: 'IBM Plex Mono', monospace;
        border: 1px solid transparent;
        margin-right: 0.25rem;
    }

    .badge-open { color: var(--open); border-color: var(--open); background: rgba(15, 123, 117, 0.08); }
    .badge-in-progress { color: var(--progress); border-color: var(--progress); background: rgba(31, 111, 180, 0.08); }
    .badge-closed { color: var(--closed); border-color: var(--closed); background: rgba(108, 117, 125, 0.1); }
    .badge-critical { color: var(--critical); border-color: var(--critical); background: rgba(189, 63, 63, 0.08); }
    .badge-high { color: var(--high); border-color: var(--high); background: rgba(192, 105, 43, 0.08); }
    .badge-medium { color: var(--medium); border-color: var(--medium); background: rgba(47, 127, 159, 0.08); }
    .badge-low { color: var(--low); border-color: var(--low); background: rgba(96, 113, 125, 0.1); }

    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea,
    .stSelectbox>div>div>div {
        border: 1px solid var(--line) !important;
        border-radius: 10px !important;
        background: rgba(255, 255, 255, 0.9) !important;
        color: var(--ink) !important;
    }

    .stButton>button {
        border-radius: 10px;
        border: 1px solid transparent;
        background: linear-gradient(160deg, var(--accent), #0a6a64);
        color: #f4fafb;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.85rem;
        font-weight: 600;
        transition: transform 0.16s ease, box-shadow 0.16s ease;
    }

    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 8px 20px rgba(15, 123, 117, 0.2);
    }

    .stForm {
        border: 1px dashed var(--line);
        border-radius: 12px;
        padding: 0.8rem;
        background: rgba(255, 255, 255, 0.4);
    }

    .login-shell {
        max-width: 920px;
        margin: 2rem auto;
        border: 1px solid var(--line);
        border-radius: 20px;
        overflow: hidden;
        display: grid;
        grid-template-columns: 1.2fr 1fr;
        background: rgba(255, 255, 255, 0.78);
    }

    .login-left {
        padding: 2.2rem;
        background:
            radial-gradient(circle at 15% 20%, rgba(15, 123, 117, 0.2), transparent 38%),
            radial-gradient(circle at 80% 70%, rgba(220, 124, 58, 0.2), transparent 40%),
            #f3ede1;
    }

    .login-right {
        padding: 2.2rem;
    }

    @media (max-width: 900px) {
        .login-shell {
            grid-template-columns: 1fr;
        }

        .panel {
            min-height: 360px;
        }
    }
</style>
""",
    unsafe_allow_html=True,
)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "selected_project_id" not in st.session_state:
    st.session_state.selected_project_id = None
if "selected_file_id" not in st.session_state:
    st.session_state.selected_file_id = None

STATUS_OPTIONS = ["Open", "In Progress", "Closed"]
PRIORITY_OPTIONS = ["Critical", "High", "Medium", "Low"]
FILE_TYPES = ["Python", "JavaScript", "TypeScript", "HTML/CSS", "Config", "Docs", "Other"]


def status_badge(status):
    cls = {
        "Open": "open",
        "In Progress": "in-progress",
        "Closed": "closed",
    }.get(status, "open")
    return f"<span class='badge badge-{cls}'>{status}</span>"


def priority_badge(priority):
    cls = (priority or "Medium").lower()
    return f"<span class='badge badge-{cls}'>{priority}</span>"


def ensure_selection(projects, files):
    if projects:
        project_ids = [p["id"] for p in projects]
        if st.session_state.selected_project_id not in project_ids:
            st.session_state.selected_project_id = project_ids[0]
    else:
        st.session_state.selected_project_id = None
        st.session_state.selected_file_id = None
        return

    if files:
        file_ids = [f["id"] for f in files]
        if st.session_state.selected_file_id not in file_ids:
            st.session_state.selected_file_id = file_ids[0]
    else:
        st.session_state.selected_file_id = None


def format_dt(value):
    if not value:
        return "-"
    return value.strftime("%Y-%m-%d %H:%M")


def show_login():
    st.markdown(
        """
        <div class='login-shell'>
            <div class='login-left'>
                <h1 style='margin-top:0;'>BugTrack Workspace</h1>
                <p style='font-size:1.05rem;max-width:38ch;'>
                    Organize quality work in three layers: projects, representative project files,
                    and bug reports linked to each file.
                </p>
                <p style='color:#546168;'>
                    Designed for triage-heavy teams that need context before fixing defects.
                </p>
            </div>
            <div class='login-right'>
        """,
        unsafe_allow_html=True,
    )

    tab_login, tab_register = st.tabs(["Sign In", "Register"])

    with tab_login:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Sign In", key="btn_login"):
            if db.validate_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
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
                st.success("Account created! You can sign in now.")
            else:
                st.error("Username already taken.")

    st.markdown("</div></div>", unsafe_allow_html=True)


def show_sidebar():
    with st.sidebar:
        st.markdown("## BugTrack")
        st.markdown(f"User: **{st.session_state.username}**")
        st.markdown("Projects, files, bugs")
        st.markdown("---")
        if st.button("Refresh Workspace"):
            st.rerun()
        if st.button("Sign Out"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.selected_project_id = None
            st.session_state.selected_file_id = None
            st.rerun()


def render_metrics(projects, files, bugs):
    open_count = sum(1 for b in bugs if b["status"] == "Open")
    progress_count = sum(1 for b in bugs if b["status"] == "In Progress")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"<div class='metric-card'><strong>{len(projects)}</strong><br><span style='color:#546168;'>Projects</span></div>",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"<div class='metric-card'><strong>{len(files)}</strong><br><span style='color:#546168;'>Project Files</span></div>",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"<div class='metric-card'><strong>{len(bugs)}</strong><br><span style='color:#546168;'>Bug Reports</span></div>",
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"<div class='metric-card'><strong>{open_count}</strong> open, <strong>{progress_count}</strong> in progress</div>",
            unsafe_allow_html=True,
        )


def project_panel(projects):
    st.markdown("### 1) Projects")

    if projects:
        for project in projects:
            label = f"{project['name']}  ({project['file_count']} files / {project['bug_count']} bugs)"
            if st.button(label, key=f"project_{project['id']}", use_container_width=True):
                st.session_state.selected_project_id = project["id"]
                st.session_state.selected_file_id = None
                st.rerun()
    else:
        st.info("No projects yet. Create your first project below.")

    with st.form("add_project_form", clear_on_submit=True):
        st.markdown("Add Project")
        project_name = st.text_input("Project name")
        project_desc = st.text_area("Project description", height=80)
        submitted = st.form_submit_button("Create Project")
        if submitted:
            if not project_name.strip():
                st.error("Project name is required.")
            else:
                project_id = db.create_project(project_name.strip(), project_desc.strip(), st.session_state.username)
                st.session_state.selected_project_id = project_id
                st.session_state.selected_file_id = None
                st.rerun()


def file_panel(files):
    st.markdown("### 2) Project Files")
    st.caption("Representative entries only, not actual uploads.")

    if st.session_state.selected_project_id is None:
        st.info("Select or create a project first.")
        return

    if files:
        for project_file in files:
            label = f"{project_file['display_name']}  ({project_file['open_bug_count']} open)"
            if st.button(label, key=f"file_{project_file['id']}", use_container_width=True):
                st.session_state.selected_file_id = project_file["id"]
                st.rerun()
    else:
        st.info("No project files yet. Add one below.")

    with st.form("add_project_file_form", clear_on_submit=True):
        st.markdown("Add Representative File")
        display_name = st.text_input("File display name")
        pseudo_path = st.text_input("Pseudo path", placeholder="src/auth/login.py")
        file_kind = st.selectbox("File type", FILE_TYPES)
        summary = st.text_area("Role in project", height=70)
        submitted = st.form_submit_button("Add File")
        if submitted:
            if not display_name.strip():
                st.error("Display name is required.")
            else:
                file_id = db.create_project_file(
                    st.session_state.selected_project_id,
                    display_name.strip(),
                    pseudo_path.strip(),
                    file_kind,
                    summary.strip(),
                )
                st.session_state.selected_file_id = file_id
                st.rerun()


def bug_panel(projects, files):
    st.markdown("### 3) Bug Reports")

    selected_project = next((p for p in projects if p["id"] == st.session_state.selected_project_id), None)
    selected_file = next((f for f in files if f["id"] == st.session_state.selected_file_id), None)

    if not selected_project:
        st.info("Select a project to work with bug reports.")
        return

    st.markdown(
        f"""
        <div class='title-hero'>
            <div style='font-size:0.8rem;color:#546168;'>Current scope</div>
            <div style='font-family:IBM Plex Mono,monospace;font-size:1rem;'>
                {selected_project['name']} {' / ' + selected_file['display_name'] if selected_file else ''}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not selected_file:
        st.info("Choose a project file to view and create bug reports for that file.")
        return

    col1, col2, col3 = st.columns([2.3, 1, 1])
    with col1:
        search = st.text_input("Search bugs", placeholder="Title, description, steps, reporter")
    with col2:
        status_filter = st.selectbox("Status", ["All"] + STATUS_OPTIONS)
    with col3:
        priority_filter = st.selectbox("Priority", ["All"] + PRIORITY_OPTIONS)

    bugs = db.get_bug_reports(
        project_id=selected_project["id"],
        project_file_id=selected_file["id"],
        status_filter=status_filter,
        priority_filter=priority_filter,
        search_query=search.strip() if search else None,
    )

    with st.expander("Add Bug Report", expanded=False):
        with st.form("add_bug_form", clear_on_submit=True):
            title = st.text_input("Bug title")
            description = st.text_area("Description", height=90)
            c1, c2 = st.columns(2)
            with c1:
                status = st.selectbox("Initial status", STATUS_OPTIONS, key="create_status")
            with c2:
                priority = st.selectbox("Priority", PRIORITY_OPTIONS, index=2, key="create_priority")
            steps = st.text_area("Steps to reproduce", height=80)
            expected = st.text_area("Expected result", height=70)
            actual = st.text_area("Actual result", height=70)
            submitted = st.form_submit_button("Create Bug Report")

            if submitted:
                if not title.strip():
                    st.error("Bug title is required.")
                else:
                    db.create_bug_report(
                        selected_project["id"],
                        selected_file["id"],
                        title.strip(),
                        description.strip(),
                        st.session_state.username,
                        status,
                        priority,
                        steps.strip(),
                        expected.strip(),
                        actual.strip(),
                    )
                    st.rerun()

    st.markdown(
        f"<p style='color:#546168;font-size:0.84rem;'>{len(bugs)} bug report(s) in this file.</p>",
        unsafe_allow_html=True,
    )

    if not bugs:
        st.info("No bug reports found for this file with the current filters.")
        return

    for bug in bugs:
        st.markdown(
            f"""
            <div class='bug-card'>
                <div class='bug-title'>#{bug['id']} {bug['title']}</div>
                <div class='bug-meta'>
                    Reporter: {bug['reporter']} | Created: {format_dt(bug['created_at'])} | Updated: {format_dt(bug['updated_at'])}
                </div>
                <div style='margin-bottom:0.35rem;'>
                    {status_badge(bug['status'])} {priority_badge(bug['priority'])}
                </div>
                <div class='bug-desc'>{bug['description'] or ''}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander(f"Edit / Delete bug #{bug['id']}", expanded=False):
            with st.form(f"edit_bug_{bug['id']}"):
                title = st.text_input("Bug title", value=bug["title"], key=f"title_{bug['id']}")
                description = st.text_area(
                    "Description",
                    value=bug["description"] or "",
                    height=90,
                    key=f"desc_{bug['id']}",
                )
                c1, c2 = st.columns(2)
                with c1:
                    status = st.selectbox(
                        "Status",
                        STATUS_OPTIONS,
                        index=STATUS_OPTIONS.index(bug["status"]) if bug["status"] in STATUS_OPTIONS else 0,
                        key=f"status_{bug['id']}",
                    )
                with c2:
                    priority = st.selectbox(
                        "Priority",
                        PRIORITY_OPTIONS,
                        index=PRIORITY_OPTIONS.index(bug["priority"]) if bug["priority"] in PRIORITY_OPTIONS else 2,
                        key=f"priority_{bug['id']}",
                    )
                steps = st.text_area(
                    "Steps to reproduce",
                    value=bug["steps_to_reproduce"] or "",
                    height=80,
                    key=f"steps_{bug['id']}",
                )
                expected = st.text_area(
                    "Expected result",
                    value=bug["expected_result"] or "",
                    height=70,
                    key=f"exp_{bug['id']}",
                )
                actual = st.text_area(
                    "Actual result",
                    value=bug["actual_result"] or "",
                    height=70,
                    key=f"act_{bug['id']}",
                )

                s1, s2 = st.columns(2)
                with s1:
                    save = st.form_submit_button("Save Changes")
                with s2:
                    delete = st.form_submit_button("Delete Bug")

                if save:
                    if not title.strip():
                        st.error("Bug title is required.")
                    else:
                        db.update_bug_report(
                            bug["id"],
                            title.strip(),
                            description.strip(),
                            status,
                            priority,
                            steps.strip(),
                            expected.strip(),
                            actual.strip(),
                        )
                        st.rerun()

                if delete:
                    db.delete_bug_report(bug["id"])
                    st.rerun()


def show_workspace():
    projects = db.get_projects(st.session_state.username)
    files = db.get_project_files(st.session_state.selected_project_id) if st.session_state.selected_project_id else []
    ensure_selection(projects, files)
    files = db.get_project_files(st.session_state.selected_project_id) if st.session_state.selected_project_id else []
    bugs = (
        db.get_bug_reports(
            project_id=st.session_state.selected_project_id,
            project_file_id=st.session_state.selected_file_id,
        )
        if st.session_state.selected_project_id and st.session_state.selected_file_id
        else []
    )

    st.markdown("<h1 style='margin-bottom:0.2rem;'>BugTrack Workspace</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color:#546168;margin-top:0;'>Projects -> Representative files -> Bug reports</p>",
        unsafe_allow_html=True,
    )
    render_metrics(projects, files, bugs)
    st.markdown("<div style='height:0.7rem;'></div>", unsafe_allow_html=True)

    col_projects, col_files, col_bugs = st.columns([1.15, 1.2, 2.3], gap="large")
    with col_projects:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        project_panel(projects)
        st.markdown("</div>", unsafe_allow_html=True)
    with col_files:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        file_panel(files)
        st.markdown("</div>", unsafe_allow_html=True)
    with col_bugs:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        bug_panel(projects, files)
        st.markdown("</div>", unsafe_allow_html=True)


if not st.session_state.logged_in:
    show_login()
else:
    show_sidebar()
    show_workspace()
