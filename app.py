import os
import html
import uuid
import base64
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

import streamlit as st
import pymysql
from pymysql.cursors import DictCursor

BASE_DIR = Path(__file__).resolve().parent

st.set_page_config(
    page_title="NativeFrames 🌿",
    page_icon=str(BASE_DIR / "static/images/nativeframes-logo.jpg"),
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Configuration
# -----------------------------
# Local XAMPP defaults are preserved. For cloud deployment, values can be
# supplied through environment variables OR Streamlit secrets.
def setting(name, default=""):
    value = os.getenv(name, "")
    if value:
        return value
    try:
        if name in st.secrets:
            return str(st.secrets[name])
        section = st.secrets.get("nativeframes", {})
        short = name.replace("NATIVEFRAMES_", "").lower()
        if short in section:
            return str(section[short])
    except Exception:
        pass
    return default

DATABASE_URL = setting("NATIVEFRAMES_DATABASE_URL", "").strip()
if DATABASE_URL:
    parsed = urlparse(DATABASE_URL)
    DB_HOST = parsed.hostname or "localhost"
    DB_PORT = parsed.port or 3306
    DB_USER = parsed.username or "root"
    DB_PASSWORD = parsed.password or ""
    DB_NAME = (parsed.path or "/nativeframes").lstrip("/") or "nativeframes"
else:
    DB_HOST = setting("NATIVEFRAMES_DB_HOST", "sql.freedb.tech")
    DB_PORT = int(setting("NATIVEFRAMES_DB_PORT", "3306"))
    DB_USER = setting("NATIVEFRAMES_DB_USER", "u_vKlaXU")
    DB_PASSWORD = setting("NATIVEFRAMES_DB_PASSWORD", "H5oodL9UHMHc")
    DB_NAME = setting("NATIVEFRAMES_DB_NAME", "freedb_nHmfR453")

AUTO_CREATE_DB = setting(
    "NATIVEFRAMES_DB_AUTO_CREATE",
    "true" if DB_HOST in ("localhost", "127.0.0.1") else "false"
).lower() in ("1", "true", "yes", "on")

UPLOAD_ROOT = Path(
    setting("NATIVEFRAMES_UPLOAD_DIR", str(BASE_DIR / "static" / "uploads"))
).expanduser()

ADMIN_USERNAME = setting("NATIVEFRAMES_ADMIN_USERNAME", "nativeframes")
ADMIN_PASSWORD = setting("NATIVEFRAMES_ADMIN_PASSWORD", "nativeframes@24")

UPLOAD_DIR = UPLOAD_ROOT
PHOTO_DIR = UPLOAD_DIR / "photos"
VIDEO_DIR = UPLOAD_DIR / "videos"
FILE_DIR = UPLOAD_DIR / "files"
for folder in (PHOTO_DIR, VIDEO_DIR, FILE_DIR):
    folder.mkdir(parents=True, exist_ok=True)

# -----------------------------
# Styling
# -----------------------------
def load_css():
    css_path = BASE_DIR / "static/css/style.css"
    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )

def load_js():
    js_path = BASE_DIR / "static/js/app.js"
    if js_path.exists():
        st.markdown(
            f"<script>{js_path.read_text(encoding='utf-8')}</script>",
            unsafe_allow_html=True,
        )

load_css()

# -----------------------------
# Session state
# -----------------------------
defaults = {
    "screen": "welcome",
    "viewer_name": "",
    "viewer_mobile": "",
    "admin_logged": False,
    "theme": "midnight",
    "leaf_effect": True,
    "db_error": "",
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# -----------------------------
# Database
# -----------------------------
def server_connection():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        cursorclass=DictCursor,
        autocommit=True,
    )

def db_connection():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=DictCursor,
        autocommit=True,
    )

def setup_database():
    try:
        if AUTO_CREATE_DB:
            conn = server_connection()
            with conn.cursor() as cur:
                cur.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            conn.close()

        conn = db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS viewers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(120) NOT NULL,
                    mobile VARCHAR(30) NULL,
                    login_count INT NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_login DATETIME NULL,
                    INDEX idx_viewer_name (name)
                ) ENGINE=InnoDB
            """)
            # Upgrade databases created by earlier NativeFrames versions.
            try:
                cur.execute("ALTER TABLE viewers MODIFY mobile VARCHAR(30) NULL")
            except Exception:
                pass
            try:
                cur.execute("ALTER TABLE viewers DROP INDEX uq_viewer_mobile")
            except Exception:
                pass
            try:
                cur.execute("ALTER TABLE viewers ADD INDEX idx_viewer_name (name)")
            except Exception:
                pass

            cur.execute("""
                CREATE TABLE IF NOT EXISTS viewer_logins (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    viewer_id INT NOT NULL,
                    login_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    ip_address VARCHAR(80) NULL,
                    user_agent VARCHAR(255) NULL,
                    CONSTRAINT fk_login_viewer
                        FOREIGN KEY (viewer_id) REFERENCES viewers(id)
                        ON DELETE CASCADE
                ) ENGINE=InnoDB
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS media (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    media_type ENUM('photo','video','text') NOT NULL,
                    file_name VARCHAR(255) NULL,
                    title VARCHAR(255) NOT NULL,
                    description TEXT NULL,
                    is_favorite TINYINT(1) NOT NULL DEFAULT 0,
                    is_deleted TINYINT(1) NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS admin_profile (
                    id INT PRIMARY KEY,
                    name VARCHAR(150) DEFAULT 'NativeFrames',
                    username VARCHAR(120) DEFAULT 'nativeframes',
                    dob DATE NULL,
                    mobile VARCHAR(40) NULL,
                    email VARCHAR(180) NULL,
                    location VARCHAR(180) NULL,
                    occupation VARCHAR(180) NULL,
                    about TEXT NULL,
                    profile_photo VARCHAR(255) NULL
                ) ENGINE=InnoDB
            """)
            cur.execute("""
                INSERT INTO admin_profile (id, name, username)
                VALUES (1, 'NativeFrames', 'nativeframes')
                ON DUPLICATE KEY UPDATE username = VALUES(username)
            """)
        conn.close()
        return True
    except Exception as exc:
        st.session_state.db_error = str(exc)
        return False

def query(sql, params=()):
    conn = db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.close()

def execute(sql, params=()):
    conn = db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.lastrowid
    finally:
        conn.close()

db_ok = setup_database()

# -----------------------------
# Helpers
# -----------------------------
def esc(value):
    return html.escape(str(value or ""))

def logo_html(size=82):
    """Return the logo as an embedded data URI so it works reliably in Streamlit."""
    logo_path = BASE_DIR / "static" / "images" / "nativeframes-logo.jpg"
    if logo_path.exists():
        encoded = base64.b64encode(logo_path.read_bytes()).decode("ascii")
        return (
            f'<img class="nf-logo nf-logo-{size}" '
            f'src="data:image/jpeg;base64,{encoded}" '
            f'alt="NativeFrames logo">'
        )
    return '<div class="nf-logo-fallback">NF</div>'

def page_title(title, subtitle=""):
    st.markdown(
        f"""
        <div class="page-heading">
            <div>
                <h1>{esc(title)}</h1>
                <p>{esc(subtitle)}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def leaves():
    if not st.session_state.leaf_effect:
        return
    st.markdown(
        """
        <div class="leaf-layer" aria-hidden="true">
            <span>🍃</span><span>🍂</span><span>🍃</span>
            <span>🍃</span><span>🍂</span><span>🍃</span>
            <span>🍂</span><span>🍃</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

def show_db_warning():
    if not db_ok:
        st.error(
            "MySQL connection failed. Check your NativeFrames database settings. "
            f"Details: {st.session_state.db_error}"
        )

def mask_mobile(mobile):
    mobile = str(mobile or "")
    if len(mobile) <= 4:
        return "*" * len(mobile)
    return "*" * (len(mobile) - 4) + mobile[-4:]

def save_upload(uploaded_file, media_type):
    ext = Path(uploaded_file.name).suffix.lower()
    safe_name = f"{uuid.uuid4().hex}{ext}"
    if media_type == "photo":
        destination = PHOTO_DIR / safe_name
    elif media_type == "video":
        destination = VIDEO_DIR / safe_name
    else:
        destination = FILE_DIR / safe_name
    destination.write_bytes(uploaded_file.getbuffer())
    return safe_name

def media_path(row):
    if not row["file_name"]:
        return None
    if row["media_type"] == "photo":
        return PHOTO_DIR / row["file_name"]
    if row["media_type"] == "video":
        return VIDEO_DIR / row["file_name"]
    return FILE_DIR / row["file_name"]

# -----------------------------
# Welcome / sign in
# -----------------------------
def welcome_screen():
    leaves()
    st.markdown(
        f"""
        <div class="welcome-wrap">
            <div class="welcome-card">
                {logo_html(130)}
                <div class="brand-name">NativeFrames <span>📷</span></div>
                <div class="brand-line">PROMOTIONS &nbsp;|&nbsp; BRAND FILMS &nbsp;|&nbsp; SOCIAL CONTENT</div>
                <p class="welcome-copy">
                    Capture. Preserve. Relive.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        if st.button("Continue to NativeFrames  →", use_container_width=True):
            st.session_state.screen = "signin"
            st.rerun()

def signin_screen():
    leaves()
    c1, c2, c3 = st.columns([1, 1.25, 1])
    with c2:
        st.markdown(
            f"""
            <div class="signin-head">
                {logo_html(92)}
                <h1>Welcome to NativeFrames 📷</h1>
                <p>Enter your name to view the gallery.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        tab_viewer, tab_admin = st.tabs(["Viewer Sign In", "Admin Sign In"])

        with tab_viewer:
            with st.form("viewer_login"):
                name = st.text_input("Name", placeholder="Enter your name")
                submitted = st.form_submit_button("Enter Gallery", use_container_width=True)
            if submitted:
                if not db_ok:
                    st.error("Database is not available.")
                elif not name.strip():
                    st.warning("Please enter your name.")
                else:
                    existing = query(
                        "SELECT * FROM viewers WHERE name=%s ORDER BY id LIMIT 1",
                        (name.strip(),)
                    )
                    if existing:
                        viewer_id = existing[0]["id"]
                        execute(
                            "UPDATE viewers SET login_count=login_count+1, "
                            "last_login=NOW() WHERE id=%s",
                            (viewer_id,),
                        )
                    else:
                        viewer_id = execute(
                            "INSERT INTO viewers (name,login_count,last_login) "
                            "VALUES (%s,1,NOW())",
                            (name.strip(),),
                        )
                    execute(
                        "INSERT INTO viewer_logins (viewer_id) VALUES (%s)",
                        (viewer_id,),
                    )
                    st.session_state.viewer_name = name.strip()
                    st.session_state.viewer_mobile = ""
                    st.session_state.screen = "viewer"
                    st.rerun()

        with tab_admin:
            with st.form("admin_login"):
                username = st.text_input("Username", value="", placeholder="Admin username")
                password = st.text_input("Password", type="password", placeholder="Admin password")
                submitted = st.form_submit_button("Open Admin Panel", use_container_width=True)
            if submitted:
                if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                    st.session_state.admin_logged = True
                    st.session_state.screen = "admin"
                    st.rerun()
                else:
                    st.error("Invalid admin username or password.")

        if st.button("← Back", use_container_width=True):
            st.session_state.screen = "welcome"
            st.rerun()

# -----------------------------
# Admin
# -----------------------------
def admin_sidebar():
    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-brand">
                {logo_html(62)}
                <div>
                    <b>NativeFrames 📷</b>
                    <small>Admin Studio</small>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        choices = {
            "🏠 Dashboard": "dashboard",
            "➕ Create / Upload": "upload",
            "📷 Media Library": "media",
            "⭐ Favorites": "favorites",
            "👥 Viewers & Analytics": "viewers",
            "👤 My Profile": "profile",
            "⚙️ Settings": "settings",
            "🗑️ Trash": "trash",
        }
        for label, value in choices.items():
            if st.button(label, use_container_width=True, key=f"nav_{value}"):
                st.session_state.admin_page = value
                st.rerun()
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.admin_logged = False
            st.session_state.screen = "signin"
            st.rerun()

def admin_dashboard():
    page_title("Admin Dashboard", "Your NativeFrames control center")
    rows = query("SELECT * FROM media WHERE is_deleted=0 ORDER BY created_at DESC")
    viewers = query("SELECT COUNT(*) AS c FROM viewers")[0]["c"]
    logins = query("SELECT COUNT(*) AS c FROM viewer_logins")[0]["c"]
    favourites = query(
        "SELECT COUNT(*) AS c FROM media WHERE is_deleted=0 AND is_favorite=1"
    )[0]["c"]

    a, b, c, d = st.columns(4)
    a.metric("Published Items", len(rows))
    b.metric("Viewers", viewers)
    c.metric("Total Logins", logins)
    d.metric("Favorites", favourites)

    st.markdown("### Recent NativeFrames")
    if not rows:
        st.info("No media uploaded yet. Use Create / Upload to add your first memory.")
        return

    for row in rows[:6]:
        left, right = st.columns([1.25, 1])
        with left:
            p = media_path(row)
            if row["media_type"] == "photo" and p and p.exists():
                st.image(str(p), use_container_width=True)
            elif row["media_type"] == "video" and p and p.exists():
                st.video(str(p))
            else:
                st.markdown(
                    f'<div class="text-memory">{esc(row["description"])}</div>',
                    unsafe_allow_html=True,
                )
        with right:
            st.markdown(
                f"""
                <div class="side-story">
                    <span class="type-pill">{esc(row["media_type"].upper())}</span>
                    <h3>{esc(row["title"])}</h3>
                    <p>{esc(row["description"])}</p>
                    <small>{esc(row["created_at"])}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )

def upload_page():
    page_title("Create / Upload", "Add a photo, video, or text memory")
    media_type = st.radio(
        "Content type",
        ["Photo", "Video", "Text"],
        horizontal=True,
    )

    with st.form("create_media", clear_on_submit=True):
        title = st.text_input("Title", placeholder="Example: Sunset Memories")
        description = st.text_area(
            "Text / Story",
            placeholder="Write the text that should appear beside the photo or video...",
            height=130,
        )

        uploaded = None
        if media_type in ("Photo", "Video"):
            accepted = ["jpg", "jpeg", "png", "webp"] if media_type == "Photo" else ["mp4", "mov", "webm", "mkv"]
            uploaded = st.file_uploader(
                f"Upload {media_type}",
                type=accepted,
            )

        favourite = st.checkbox("Add to Favorites")
        submitted = st.form_submit_button("Publish to NativeFrames", use_container_width=True)

    if submitted:
        if not title.strip():
            st.warning("Please enter a title.")
            return
        if media_type in ("Photo", "Video") and uploaded is None:
            st.warning(f"Please upload a {media_type.lower()}.")
            return

        file_name = None
        db_type = media_type.lower()
        if uploaded is not None:
            file_name = save_upload(uploaded, db_type)

        execute(
            "INSERT INTO media (media_type,file_name,title,description,is_favorite) "
            "VALUES (%s,%s,%s,%s,%s)",
            (db_type, file_name, title.strip(), description.strip(), int(favourite)),
        )
        st.success("Published successfully.")
        st.rerun()

def media_library(filter_fav=False):
    title = "Favorites" if filter_fav else "Media Library"
    page_title(title, "Manage published NativeFrames content")
    sql = "SELECT * FROM media WHERE is_deleted=0"
    params = ()
    if filter_fav:
        sql += " AND is_favorite=1"
    sql += " ORDER BY created_at DESC"
    rows = query(sql, params)

    if not rows:
        st.info("Nothing to display.")
        return

    for row in rows:
        c1, c2, c3 = st.columns([1.05, 1.25, 0.55])
        with c1:
            p = media_path(row)
            if row["media_type"] == "photo" and p and p.exists():
                st.image(str(p), use_container_width=True)
            elif row["media_type"] == "video" and p and p.exists():
                st.video(str(p))
            else:
                st.markdown(
                    f'<div class="text-memory">{esc(row["description"])}</div>',
                    unsafe_allow_html=True,
                )
        with c2:
            fav = "★ Favorite" if row["is_favorite"] else "☆ Favorite"
            st.markdown(
                f"""
                <div class="side-story">
                    <span class="type-pill">{esc(row["media_type"].upper())}</span>
                    <h3>{esc(row["title"])}</h3>
                    <p>{esc(row["description"])}</p>
                    <small>{esc(row["created_at"])}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(fav, key=f"fav_{row['id']}"):
                execute(
                    "UPDATE media SET is_favorite=NOT is_favorite WHERE id=%s",
                    (row["id"],),
                )
                st.rerun()
        with c3:
            if st.button("🗑️ Trash", key=f"trash_{row['id']}"):
                execute(
                    "UPDATE media SET is_deleted=1 WHERE id=%s",
                    (row["id"],),
                )
                st.rerun()
        st.divider()

def trash_page():
    page_title("Trash", "Restore deleted content or permanently remove it")
    rows = query("SELECT * FROM media WHERE is_deleted=1 ORDER BY created_at DESC")
    if not rows:
        st.success("Trash is empty.")
        return

    for row in rows:
        a, b = st.columns([2.5, 1])
        with a:
            st.markdown(
                f"**{esc(row['title'])}** · `{esc(row['media_type'])}`  \n"
                f"{esc(row['description'])}"
            )
        with b:
            if st.button("↩️ Restore", key=f"restore_{row['id']}"):
                execute("UPDATE media SET is_deleted=0 WHERE id=%s", (row["id"],))
                st.rerun()
            if st.button("❌ Delete Permanently", key=f"perm_{row['id']}"):
                p = media_path(row)
                if p and p.exists():
                    p.unlink(missing_ok=True)
                execute("DELETE FROM media WHERE id=%s", (row["id"],))
                st.rerun()
        st.divider()

def viewers_page():
    page_title("Viewers & Analytics", "See who entered NativeFrames and how often")
    total_viewers = query("SELECT COUNT(*) AS c FROM viewers")[0]["c"]
    total_logins = query("SELECT COUNT(*) AS c FROM viewer_logins")[0]["c"]
    today = query(
        "SELECT COUNT(*) AS c FROM viewer_logins WHERE DATE(login_time)=CURDATE()"
    )[0]["c"]

    a, b, c = st.columns(3)
    a.metric("Total Viewers", total_viewers)
    b.metric("Total Logins", total_logins)
    c.metric("Today's Logins", today)

    rows = query("""
        SELECT id, name, login_count, created_at, last_login
        FROM viewers
        ORDER BY last_login DESC
    """)

    st.markdown("### Viewer list")
    if rows:
        for row in rows:
            st.markdown(
                f"""
                <div class="viewer-row">
                    <div>
                        <b>{esc(row["name"])}</b>
                    </div>
                    <div>Logins: <b>{row["login_count"]}</b></div>
                    <div>Last: {esc(row["last_login"])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No viewer has signed in yet.")

def profile_page():
    page_title("My Profile", "Manage the NativeFrames administrator profile")
    row = query("SELECT * FROM admin_profile WHERE id=1")[0]

    with st.form("profile_form"):
        name = st.text_input("Name", value=row["name"] or "")
        username = st.text_input("Username", value=row["username"] or "")
        dob = st.date_input("Date of Birth", value=row["dob"] or datetime(2000, 1, 1))
        mobile = st.text_input("Mobile Number", value=row["mobile"] or "")
        email = st.text_input("Email", value=row["email"] or "")
        location = st.text_input("Location", value=row["location"] or "")
        occupation = st.text_input("Occupation", value=row["occupation"] or "")
        about = st.text_area("About Me", value=row["about"] or "", height=120)
        profile_photo = st.file_uploader(
            "Profile Photo",
            type=["jpg", "jpeg", "png", "webp"],
        )
        save = st.form_submit_button("Save Profile", use_container_width=True)

    if save:
        photo_name = row["profile_photo"]
        if profile_photo is not None:
            ext = Path(profile_photo.name).suffix.lower()
            photo_name = f"profile_{uuid.uuid4().hex}{ext}"
            destination = FILE_DIR / photo_name
            destination.write_bytes(profile_photo.getbuffer())

        execute("""
            UPDATE admin_profile
            SET name=%s, username=%s, dob=%s, mobile=%s, email=%s,
                location=%s, occupation=%s, about=%s, profile_photo=%s
            WHERE id=1
        """, (
            name.strip(), username.strip(), dob, mobile.strip(), email.strip(),
            location.strip(), occupation.strip(), about.strip(), photo_name
        ))
        st.success("Profile saved.")
        st.rerun()

    st.markdown("### Profile preview")
    st.markdown(
        f"""
        <div class="profile-card">
            {logo_html(86)}
            <div>
                <h2>{esc(name)} 🌿</h2>
                <p>{esc(about)}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def settings_page():
    page_title("Settings", "Personalize the NativeFrames experience")
    theme = st.selectbox(
        "Theme",
        ["midnight", "camera", "cinema", "nature", "forest", "aurora", "minimal"],
        index=["midnight", "camera", "cinema", "nature", "forest", "aurora", "minimal"].index(st.session_state.theme),
    )
    leaves_on = st.toggle("Leaf animation", value=st.session_state.leaf_effect)
    if st.button("Apply Settings", use_container_width=True):
        st.session_state.theme = theme
        st.session_state.leaf_effect = leaves_on
        st.success("Settings applied.")
        st.rerun()

    st.markdown(
        """
        <div class="settings-note">
            <b>Theme ideas</b>
            <p>Nature = warm botanical style · Midnight = cinematic dark style ·
            Minimal = clean gallery style.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

def admin_page():
    if not st.session_state.admin_logged:
        st.session_state.screen = "signin"
        st.rerun()

    admin_sidebar()
    if "admin_page" not in st.session_state:
        st.session_state.admin_page = "dashboard"

    leaves()
    page = st.session_state.admin_page
    if page == "dashboard":
        admin_dashboard()
    elif page == "upload":
        upload_page()
    elif page == "media":
        media_library()
    elif page == "favorites":
        media_library(filter_fav=True)
    elif page == "viewers":
        viewers_page()
    elif page == "profile":
        profile_page()
    elif page == "settings":
        settings_page()
    elif page == "trash":
        trash_page()

# -----------------------------
# Viewer
# -----------------------------
def viewer_page():
    leaves()
    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-brand">
                {logo_html(58)}
                <div>
                    <b>NativeFrames 🌿</b>
                    <small>Viewer Gallery</small>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🏠 Gallery", use_container_width=True):
            st.rerun()
        theme = st.selectbox(
            "Theme",
            ["midnight", "camera", "cinema", "nature", "forest", "aurora", "minimal"],
            index=["midnight", "camera", "cinema", "nature", "forest", "aurora", "minimal"].index(st.session_state.theme),
        )
        st.session_state.theme = theme
        st.session_state.leaf_effect = st.toggle(
            "🍃 Leaves", value=st.session_state.leaf_effect
        )
        st.divider()
        st.caption(f"Viewer: {st.session_state.viewer_name}")
        if st.button("🚪 Exit Gallery", use_container_width=True):
            st.session_state.viewer_name = ""
            st.session_state.viewer_mobile = ""
            st.session_state.screen = "signin"
            st.rerun()

    page_title(
        "NativeFrames Gallery",
        f"Welcome, {st.session_state.viewer_name} · Capture. Preserve. Relive.",
    )

    filter_type = st.selectbox(
        "Browse",
        ["All", "Photos", "Videos", "Stories", "Favorites"],
    )

    conditions = ["is_deleted=0"]
    params = []
    if filter_type == "Photos":
        conditions.append("media_type='photo'")
    elif filter_type == "Videos":
        conditions.append("media_type='video'")
    elif filter_type == "Stories":
        conditions.append("media_type='text'")
    elif filter_type == "Favorites":
        conditions.append("is_favorite=1")

    rows = query(
        "SELECT * FROM media WHERE " + " AND ".join(conditions) +
        " ORDER BY created_at DESC",
        tuple(params),
    )

    if not rows:
        st.info("The gallery is waiting for its first NativeFrame.")
        return

    for row in rows:
        left, right = st.columns([1.35, 1])
        with left:
            p = media_path(row)
            if row["media_type"] == "photo" and p and p.exists():
                st.image(str(p), use_container_width=True)
            elif row["media_type"] == "video" and p and p.exists():
                st.video(str(p))
            else:
                st.markdown(
                    f'<div class="text-memory viewer-memory">{esc(row["description"])}</div>',
                    unsafe_allow_html=True,
                )
        with right:
            st.markdown(
                f"""
                <div class="viewer-story">
                    <span class="type-pill">{esc(row["media_type"].upper())}</span>
                    <h2>{esc(row["title"])}</h2>
                    <p>{esc(row["description"])}</p>
                    <small>{esc(row["created_at"])}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.divider()

# -----------------------------
# Run
# -----------------------------
THEMES = {
    "midnight": {
        "bg": "radial-gradient(circle at 18% 8%, rgba(208,167,90,.18), transparent 28%), radial-gradient(circle at 82% 78%, rgba(58,78,72,.25), transparent 30%), linear-gradient(135deg, #07090a 0%, #111514 48%, #202722 100%)",
        "surface": "rgba(23,28,26,.92)", "text": "#f7f3ea", "muted": "#b9b7ae",
        "accent": "#d0a75a", "accent_soft": "rgba(208,167,90,.16)",
        "border": "rgba(255,255,255,.10)", "sidebar": "rgba(10,13,12,.98)",
    },
    "camera": {
        "bg": "radial-gradient(circle at 50% 40%, rgba(67,73,77,.18), transparent 35%), linear-gradient(135deg, #050607 0%, #111315 52%, #1b1d1f 100%)",
        "surface": "rgba(22,24,27,.94)", "text": "#f3f3f1", "muted": "#a8aaad",
        "accent": "#d5a957", "accent_soft": "rgba(213,169,87,.15)",
        "border": "rgba(255,255,255,.11)", "sidebar": "rgba(7,8,9,.98)",
    },
    "cinema": {
        "bg": "radial-gradient(ellipse at 50% 0%, rgba(173,124,44,.20), transparent 35%), linear-gradient(180deg, #080706 0%, #18120b 55%, #0a0908 100%)",
        "surface": "rgba(27,22,16,.94)", "text": "#f8f1df", "muted": "#c0b49d",
        "accent": "#d6a84f", "accent_soft": "rgba(214,168,79,.17)",
        "border": "rgba(214,168,79,.18)", "sidebar": "rgba(12,10,8,.98)",
    },
    "nature": {
        "bg": "linear-gradient(135deg, #f5f2ea 0%, #e6eadc 52%, #dce3d1 100%)",
        "surface": "rgba(255,255,255,.84)", "text": "#1b1d1a", "muted": "#5e625a",
        "accent": "#a87d32", "accent_soft": "rgba(168,125,50,.14)",
        "border": "rgba(112,121,88,.22)", "sidebar": "rgba(239,243,232,.96)",
    },
    "forest": {
        "bg": "radial-gradient(circle at 15% 15%, rgba(119,144,91,.22), transparent 30%), linear-gradient(135deg, #08110d 0%, #102018 55%, #172c20 100%)",
        "surface": "rgba(18,32,24,.92)", "text": "#edf3e9", "muted": "#b2c0b1",
        "accent": "#b6a15b", "accent_soft": "rgba(182,161,91,.15)",
        "border": "rgba(182,205,174,.12)", "sidebar": "rgba(7,15,11,.98)",
    },
    "aurora": {
        "bg": "radial-gradient(circle at 15% 25%, rgba(67,121,126,.25), transparent 30%), radial-gradient(circle at 85% 70%, rgba(112,74,136,.25), transparent 30%), linear-gradient(135deg, #090b12, #151324 52%, #10171a)",
        "surface": "rgba(24,24,38,.90)", "text": "#f4f2fa", "muted": "#b9b5c7",
        "accent": "#c4a9e8", "accent_soft": "rgba(196,169,232,.15)",
        "border": "rgba(196,169,232,.13)", "sidebar": "rgba(10,10,18,.98)",
    },
    "minimal": {
        "bg": "#f7f7f5", "surface": "#ffffff", "text": "#20221f", "muted": "#666a63",
        "accent": "#8f6b2f", "accent_soft": "rgba(143,107,47,.10)",
        "border": "rgba(32,34,31,.12)", "sidebar": "#ffffff",
    },
}

theme = THEMES.get(st.session_state.theme, THEMES["midnight"])
st.markdown(
    f"""
    <style>
      :root {{
        --nf-bg: {theme["bg"]};
        --nf-surface: {theme["surface"]};
        --nf-text: {theme["text"]};
        --nf-muted: {theme["muted"]};
        --nf-accent: {theme["accent"]};
        --nf-accent-soft: {theme["accent_soft"]};
        --nf-border: {theme["border"]};
        --nf-sidebar: {theme["sidebar"]};
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

if st.session_state.screen == "welcome":
    welcome_screen()
elif st.session_state.screen == "signin":
    show_db_warning()
    signin_screen()
elif st.session_state.screen == "admin":
    show_db_warning()
    admin_page()
elif st.session_state.screen == "viewer":
    show_db_warning()
    viewer_page()

load_js()
