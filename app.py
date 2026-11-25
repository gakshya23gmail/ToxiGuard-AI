import inspect
import json
import os
import re
import sqlite3
import time
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
import toxiguard_engine

# ---------------------------------------------------------
# 1. PAGE CONFIG & CLEAN SAGE OLIVE / WARM IVORY THEME
# ---------------------------------------------------------
st.set_page_config(
    page_title="ToxiGuard AI | Autonomous Social Moderation",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
DB_PATH = "toxiguard_history.db"

CUSTOM_HTML_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], section.main {
    font-family: 'Inter', sans-serif !important;
    background-color: #F6F5F0 !important;
    color: #1F2933 !important;
}

[data-testid="stHeader"] {
    background-color: rgba(246, 245, 240, 0.92) !important;
}

[data-testid="stSidebar"], section[data-testid="stSidebar"] > div {
    background-color: #ECE9DF !important;
    border-right: 1px solid #D6D1C4 !important;
}

h1, h2, h3, h4, p, label, span, li {
    color: #1F2933;
}

/* Workspace Navigation Radio Styling */
div[data-testid="stSidebar"] div[role="radiogroup"] > label {
    background-color: #F7F5EE !important;
    border: 1px solid #D5CFC0 !important;
    border-radius: 10px !important;
    padding: 9px 12px !important;
    margin-bottom: 6px !important;
    font-weight: 600 !important;
    transition: all 0.15s ease;
}
div[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
    border-color: #4A6332 !important;
    background-color: #E7EDE0 !important;
}

/* Inputs & Selectboxes */
.stTextInput input, .stTextArea textarea, div[data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    color: #1F2933 !important;
    border: 1.5px solid #C8C3B4 !important;
    border-radius: 10px !important;
}

/* Primary Buttons */
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {
    background-color: #4A6332 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: 0.55rem 1.2rem !important;
    box-shadow: 0 3px 10px rgba(74, 99, 50, 0.18) !important;
}
.stButton > button:hover, .stFormSubmitButton > button:hover, .stDownloadButton > button:hover {
    background-color: #374B24 !important;
}
.stButton > button p, .stButton > button span,
.stFormSubmitButton > button p, .stFormSubmitButton > button span,
.stDownloadButton > button p, .stDownloadButton > button span {
    color: #FFFFFF !important;
}

/* Hero Banner */
.hero-banner {
    background: linear-gradient(135deg, #E8EDE0 0%, #F4F2E9 55%, #DFE6D3 100%);
    border: 1px solid #C2CCB4;
    border-radius: 16px;
    padding: 22px 28px;
    margin-bottom: 22px;
    box-shadow: 0 6px 20px rgba(47, 62, 46, 0.07);
}
.hero-badge {
    display: inline-block;
    background: #DCE6CE;
    color: #2E421B !important;
    border: 1px solid #AFC297;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.6px;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.hero-title {
    font-size: 28px;
    font-weight: 800;
    color: #233018 !important;
    margin: 0;
    line-height: 1.2;
}
.hero-sub {
    color: #4B5563 !important;
    font-size: 14px;
    margin-top: 6px;
    margin-bottom: 0;
}

/* KPI Grid */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 22px;
}
.kpi-card {
    background: #FFFFFF;
    border: 1px solid #DDD8CA;
    border-radius: 14px;
    padding: 18px 20px;
    box-shadow: 0 3px 12px rgba(31, 41, 51, 0.04);
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.kpi-card:hover {
    transform: translateY(-2px);
    border-color: #4A6332;
}
.kpi-label {
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.7px;
    color: #5A6572 !important;
}
.kpi-value {
    font-size: 28px;
    font-weight: 800;
    margin: 6px 0 2px 0;
    font-family: 'JetBrains Mono', monospace;
}
.kpi-sub {
    font-size: 12px;
    color: #6B7280 !important;
}

/* Comment Cards */
.comment-card-safe {
    background: #FFFFFF;
    border: 1px solid #DFDAD0;
    border-left: 5px solid #4A6332;
    border-radius: 12px;
    padding: 15px 18px;
    margin-bottom: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
}
.comment-card-toxic {
    background: #FFF6F5;
    border: 1px solid #F5C6C2;
    border-left: 5px solid #DC2626;
    border-radius: 12px;
    padding: 15px 18px;
    margin-bottom: 12px;
    box-shadow: 0 2px 8px rgba(220, 38, 38, 0.05);
}
.comment-author {
    color: #1F2933 !important;
    font-weight: 700;
    font-size: 14px;
}
.comment-date {
    color: #6B7280 !important;
    font-size: 12px;
    font-weight: 500;
}
.comment-body-safe {
    margin: 8px 0 0 0;
    color: #1F2933 !important;
    font-size: 15px;
    line-height: 1.5;
}
.comment-body-toxic {
    margin: 8px 0 4px 0;
    color: #7F1D1D !important;
    font-size: 15px;
    line-height: 1.5;
}
.pill-safe {
    background: #E6F0DC;
    color: #2E4A16 !important;
    border: 1px solid #B5CC9E;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
}
.pill-toxic {
    background: #FEE2E2;
    color: #991B1B !important;
    border: 1px solid #FCA5A5;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
}
.tag-chip {
    display: inline-block;
    background: #FEE2E2;
    color: #991B1B !important;
    border: 1px solid #FECACA;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
    margin-right: 6px;
    margin-top: 6px;
}
.info-panel {
    background: #FFFFFF;
    border: 1px solid #DDD8CA;
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 16px;
}
</style>
"""
st.markdown(CUSTOM_HTML_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. SQLITE AUDIT DATABASE HELPERS
# ---------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS scan_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scanned_at TEXT,
            video_id TEXT,
            video_title TEXT,
            channel_title TEXT,
            total_scanned INTEGER,
            clean_count INTEGER,
            toxic_count INTEGER,
            hidden_live_count INTEGER,
            toxicity_rate REAL,
            mode TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS flagged_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            logged_at TEXT,
            video_id TEXT,
            video_title TEXT,
            author TEXT,
            comment_text TEXT,
            max_score REAL,
            categories TEXT,
            action_taken TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_scan_to_db(video_id, video_title, channel_title, df, mode="Manual Scan"):
    if df.empty:
        return
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = len(df)
    toxic_count = int(df["Flagged"].sum())
    hidden_count = int(df["Actually_Hidden"].sum())
    clean_count = total - toxic_count
    tox_rate = round((toxic_count / total) * 100, 1) if total > 0 else 0.0

    c.execute("""
        INSERT INTO scan_logs (
            scanned_at, video_id, video_title, channel_title,
            total_scanned, clean_count, toxic_count, hidden_live_count, toxicity_rate, mode
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (now_str, video_id, video_title, channel_title, total, clean_count, toxic_count, hidden_count, tox_rate, mode))

    toxic_rows = df[df["Flagged"]]
    for _, r in toxic_rows.iterrows():
        action = "Hidden on YouTube" if r["Actually_Hidden"] else "Flagged Preview"
        c.execute("""
            INSERT INTO flagged_comments (
                logged_at, video_id, video_title, author, comment_text, max_score, categories, action_taken
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (now_str, video_id, video_title, str(r["Author"]), str(r["Comment"]), float(r["Max_Score"]), str(r["Triggered"]), action))

    conn.commit()
    conn.close()

def load_db_tables():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    scans_df = pd.read_sql_query("SELECT * FROM scan_logs ORDER BY id DESC", conn)
    flagged_df = pd.read_sql_query("SELECT * FROM flagged_comments ORDER BY id DESC", conn)
    conn.close()
    return scans_df, flagged_df

init_db()

# ---------------------------------------------------------
# 3. AUTO-DETECT ENGINE CLASS OR FUNCTION (UNCHANGED LOGIC)
# ---------------------------------------------------------
LABELS = ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"]
DEFAULT_THRESHOLDS = {
    "toxic": 0.45,
    "severe_toxic": 0.40,
    "obscene": 0.45,
    "threat": 0.40,
    "insult": 0.45,
    "identity_hate": 0.45,
}

@st.cache_resource
def load_engine():
    for _, obj in inspect.getmembers(toxiguard_engine, inspect.isclass):
        if obj.__module__ == toxiguard_engine.__name__:
            return obj()
    return toxiguard_engine

engine = load_engine()
thresholds = getattr(engine, "thresholds", DEFAULT_THRESHOLDS)

def analyze_text(text: str, custom_threshold: float = 0.45):
    raw = None
    for method_name in ["predict", "analyze", "classify", "moderate", "check_comment", "scan"]:
        if hasattr(engine, method_name) and callable(getattr(engine, method_name)):
            raw = getattr(engine, method_name)(text)
            break

    if raw is None:
        for fn_name, fn_obj in inspect.getmembers(toxiguard_engine, inspect.isfunction):
            if fn_obj.__module__ == toxiguard_engine.__name__ and not fn_name.startswith("_"):
                try:
                    raw = fn_obj(text)
                    break
                except Exception:
                    continue

    if isinstance(raw, dict):
        scores = raw.get("scores") or raw.get("probabilities") or {
            k: float(raw.get(k, 0.0)) for k in LABELS
        }
        clean_scores = {k: float(scores.get(k, 0.0)) for k in LABELS}
        max_score = raw.get("max_score")
        if max_score is None:
            max_score = max(clean_scores.values()) if clean_scores else 0.0
        max_score = float(max_score)

        flagged_cats = [
            k for k, v in clean_scores.items()
            if v >= min(float(thresholds.get(k, custom_threshold)), custom_threshold)
        ]
        is_toxic = (max_score >= custom_threshold) or (len(flagged_cats) > 0)
        if is_toxic and not flagged_cats:
            top_cat = max(clean_scores, key=clean_scores.get)
            flagged_cats = [top_cat]

        return {
            "is_toxic": bool(is_toxic),
            "max_score": max_score,
            "flagged_categories": list(flagged_cats),
            "scores": clean_scores,
        }
    return {
        "is_toxic": False,
        "max_score": 0.0,
        "flagged_categories": [],
        "scores": {k: 0.0 for k in LABELS},
    }

# ---------------------------------------------------------
# 4. DUAL LOCAL + CLOUD MULTI-USER OAUTH 2.0 & PAGINATED SCANNER
# ---------------------------------------------------------
def _get_cloud_oauth_config():
    """Checks if Streamlit Cloud secrets are configured for Web OAuth."""
    try:
        if "google_oauth" in st.secrets:
            cfg = dict(st.secrets["google_oauth"])
            redirect_uri = cfg.pop("redirect_uri", None)
            return {"web": cfg}, redirect_uri
    except Exception:
        pass
    return None, None

def handle_oauth_callback():
    """Handles ?code= redirect when deployed on Streamlit Community Cloud."""
    code = st.query_params.get("code")
    if code and "youtube_creds" not in st.session_state:
        client_config, redirect_uri = _get_cloud_oauth_config()
        if client_config and redirect_uri:
            try:
                flow = Flow.from_client_config(client_config, scopes=SCOPES, redirect_uri=redirect_uri)
                flow.fetch_token(code=code)
                st.session_state["youtube_creds"] = flow.credentials
                st.query_params.clear()
                st.rerun()
            except Exception as err:
                st.sidebar.error(f"OAuth Callback Error: {err}")

handle_oauth_callback()

def get_authenticated_youtube(interactive_login: bool = False):
    """Supports both local desktop OAuth pop-up and cloud web redirect OAuth."""
    creds = st.session_state.get("youtube_creds")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            st.session_state["youtube_creds"] = creds
        elif interactive_login:
            cloud_cfg, redirect_uri = _get_cloud_oauth_config()
            if cloud_cfg and redirect_uri:
                flow = Flow.from_client_config(cloud_cfg, scopes=SCOPES, redirect_uri=redirect_uri)
                auth_url, _ = flow.authorization_url(prompt="select_account", access_type="offline")
                st.sidebar.markdown(f"👉 **[Click here to authorize with Google]({auth_url})**")
                return None
            elif os.path.exists("client_secret.json"):
                with open("client_secret.json", "r", encoding="utf-8") as f:
                    raw_secret = json.load(f)
                if "web" in raw_secret and "redirect_uris" in raw_secret["web"]:
                    r_uri = raw_secret["web"]["redirect_uris"][0]
                    flow = Flow.from_client_config(raw_secret, scopes=SCOPES, redirect_uri=r_uri)
                    auth_url, _ = flow.authorization_url(prompt="select_account", access_type="offline")
                    st.sidebar.markdown(f"👉 **[Click here to authorize with Google]({auth_url})**")
                    return None
                flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
                creds = flow.run_local_server(port=0, prompt="select_account")
                st.session_state["youtube_creds"] = creds
            else:
                st.sidebar.error("Missing 'client_secret.json' (local) or Streamlit Secrets (cloud)!")
                return None
        else:
            return None

    return build("youtube", "v3", credentials=creds)

def get_logged_in_channel_info(youtube_oauth):
    try:
        resp = youtube_oauth.channels().list(part="snippet", mine=True).execute()
        if resp.get("items"):
            ch = resp["items"][0]
            return ch["id"], ch["snippet"]["title"]
    except Exception:
        pass
    return None, None

def hide_comment_on_youtube(youtube_oauth, comment_id: str):
    youtube_oauth.comments().setModerationStatus(
        id=comment_id,
        moderationStatus="heldForReview",
    ).execute()

def extract_video_id(url_or_id: str):
    url_or_id = url_or_id.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url_or_id):
        return url_or_id
    match = re.search(r"(?:v=|\/v\/|embed\/|shorts\/|live\/|youtu\.be\/)([A-Za-z0-9_-]{11})", url_or_id)
    return match.group(1) if match else None

def fetch_and_moderate_youtube(
    api_key: str,
    video_id: str,
    max_results: int = 100,
    custom_threshold: float = 0.45,
    auto_hide_live: bool = False,
):
    youtube_oauth = get_authenticated_youtube(interactive_login=False)
    youtube_read = youtube_oauth if youtube_oauth else build("youtube", "v3", developerKey=api_key)

    video_resp = youtube_read.videos().list(part="snippet,statistics", id=video_id).execute()
    video_title = "Unknown Video"
    channel_title = "Unknown Channel"
    video_channel_id = None
    if video_resp.get("items"):
        snippet = video_resp["items"][0]["snippet"]
        video_title = snippet.get("title", video_title)
        channel_title = snippet.get("channelTitle", channel_title)
        video_channel_id = snippet.get("channelId")

    my_channel_id, _ = get_logged_in_channel_info(youtube_oauth) if youtube_oauth else (None, None)
    is_owner = bool(my_channel_id and video_channel_id and my_channel_id == video_channel_id)

    comments_data = []
  
    statuses_to_fetch = ["published", "heldForReview", "likelySpam"] if (youtube_oauth and is_owner) else ["published"]

    for mod_status in statuses_to_fetch:
        next_page_token = None
        while True:
            remaining = (max_results - len(comments_data)) if max_results > 0 else 100
            if max_results > 0 and remaining <= 0:
                break

            request = youtube_read.commentThreads().list(
                part="snippet,replies",
                videoId=video_id,
                moderationStatus=mod_status,
                maxResults=min(remaining, 100),
                pageToken=next_page_token,
                textFormat="plainText",
                order="time",
            )
            response = request.execute()

            for item in response.get("items", []):
                thread_comments = [item["snippet"]["topLevelComment"]]
                if "replies" in item and "comments" in item["replies"]:
                    thread_comments.extend(item["replies"]["comments"])

                for c_obj in thread_comments:
                    if max_results > 0 and len(comments_data) >= max_results:
                        break

                    comment_id = c_obj["id"]
                    c_snip = c_obj["snippet"]
                    text = c_snip["textDisplay"]
                    author = c_snip["authorDisplayName"]
                    published = c_snip["publishedAt"][:10]

                    res = analyze_text(text, custom_threshold=custom_threshold)
                    already_held = (mod_status == "heldForReview")
                    actually_hidden = already_held
                    hide_error = None

                    if res["is_toxic"] and auto_hide_live and not already_held:
                        if not youtube_oauth:
                            hide_error = "Channel not connected (click Login in sidebar)"
                        elif not is_owner:
                            hide_error = f"Preview only: video belongs to '{channel_title}', not your connected channel"
                        else:
                            try:
                                hide_comment_on_youtube(youtube_oauth, comment_id)
                                actually_hidden = True
                            except Exception as err:
                                hide_error = str(err)

                    comments_data.append({
                        "Comment_ID": comment_id,
                        "Author": author,
                        "Comment": text,
                        "Date": published,
                        "Flagged": res["is_toxic"] or already_held,
                        "Actually_Hidden": actually_hidden,
                        "Hide_Error": hide_error,
                        "Max_Score": round(res["max_score"] * 100, 1),
                        "Triggered": ", ".join(res["flagged_categories"]) if res["flagged_categories"] else ("Held by YouTube" if already_held else "Clean"),
                        **{k: round(v * 100, 1) for k, v in res["scores"].items()},
                    })

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break
    return video_title, channel_title, pd.DataFrame(comments_data), (youtube_oauth is not None)

# ---------------------------------------------------------
# 5. SIDEBAR WORKSPACE NAVIGATION & ACCOUNT CONTROLS
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### 🛡️ ToxiGuard AI")
    st.caption("Autonomous Social Moderation Suite")
    st.markdown("---")

    st.markdown("**🧭 Workspace Interfaces**")
    active_page = st.radio(
        "Select Interface",
        [
            "🎥 Live YouTube Scanner",
            "🤖 Live Auto-Pilot Guard",
            "📊 Audit History & Reports",
            "🧪 Interactive Sandbox & X-Ray",
            "☁️ System & Cloud Status",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("**🔐 YouTube Channel Connection**")
    yt_session = get_authenticated_youtube(interactive_login=False)
    oauth_ready = yt_session is not None

    if oauth_ready:
        _, active_ch_name = get_logged_in_channel_info(yt_session)
        st.success(f"Connected: **{active_ch_name or 'YouTube Channel'}**")
        if st.button("🚪 Logout / Switch Channel", use_container_width=True):
            st.session_state.pop("youtube_creds", None)
            if os.path.exists("token.json"):
                os.remove("token.json")
            st.rerun()
    else:
        st.warning("Channel Disconnected (Scan-Only)")
        if st.button("🔑 Connect YouTube Channel", use_container_width=True):
            yt_conn = get_authenticated_youtube(interactive_login=True)
            if yt_conn:
                st.rerun()

    auto_hide_on_youtube = st.toggle(
        "Auto-Hide Flagged Comments",
        value=oauth_ready,
        help="Automatically hides toxic comments on YouTube when scanning a video from your connected channel.",
    )

    st.markdown("---")
    active_threshold = st.slider(
        "Toxicity Detection Threshold",
        min_value=0.30,
        max_value=0.80,
        value=0.45,
        step=0.05,
        help="Comments scoring at or above this confidence will be flagged and hidden.",
    )

# ---------------------------------------------------------
# 6. HELPER TO RENDER RESULTS DASHBOARD
# ---------------------------------------------------------
def render_scan_results(v_title, c_title, df, elapsed, active_threshold):
    total = len(df)
    toxic_count = int(df["Flagged"].sum())
    hidden_live_count = int(df["Actually_Hidden"].sum())
    clean_count = total - toxic_count
    tox_rate = round((toxic_count / total) * 100, 1)

    st.success(f"Scanned **{total}** comments on **{v_title}** by *{c_title}* in **{elapsed} ms**")
    if hidden_live_count > 0:
        st.warning(
            f"🛡️ **MODERATION EXECUTED:** {hidden_live_count} toxic comment(s) were hidden on YouTube "
            f"and moved to **YouTube Studio → Community → Comments → Held**!"
        )

    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-label">Total Comments Scanned</div>
            <div class="kpi-value" style="color:#1F2933;">{total}</div>
            <div class="kpi-sub">Live YouTube API v3 Stream</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Approved &amp; Published</div>
            <div class="kpi-value" style="color:#3B5226;">{clean_count}</div>
            <div class="kpi-sub">Passed all 6 safety checks</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Quarantined / Hidden</div>
            <div class="kpi-value" style="color:#DC2626;">{toxic_count}</div>
            <div class="kpi-sub">{hidden_live_count} hidden on YouTube</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Channel Toxicity Rate</div>
            <div class="kpi-value" style="color:#B45309;">{tox_rate}%</div>
            <div class="kpi-sub">Threshold: {int(active_threshold*100)}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    categories = ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"]
    avg_scores = [df[c].mean() for c in categories]

    with c1:
        fig_bar = px.bar(
            x=[c.upper() for c in categories],
            y=avg_scores,
            title="Mean Threat Probability Across 6 Categories (%)",
            labels={"x": "Category", "y": "Mean Confidence (%)"},
            color=avg_scores,
            color_continuous_scale=["#6B8E23", "#D97706", "#DC2626"],
        )
        fig_bar.update_layout(
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FAF9F5",
            font_color="#1F2933",
            showlegend=False,
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with c2:
        fig_pie = go.Figure(data=[go.Pie(
            labels=["Approved (Clean)", "Quarantined (Toxic)"],
            values=[clean_count, toxic_count],
            hole=0.55,
            marker_colors=["#4A6332", "#DC2626"],
        )])
        fig_pie.update_layout(
            title="Automated Moderation Split",
            paper_bgcolor="#FFFFFF",
            font_color="#1F2933",
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("### 📋 Comment Moderation Stream")
    filter_mode = st.radio(
        "Filter Stream:",
        ["All Comments", "Quarantined Only (Toxic)", "Approved Only (Safe)"],
        horizontal=True,
    )

    view_df = df
    if filter_mode == "Quarantined Only (Toxic)":
        view_df = df[df["Flagged"]]
    elif filter_mode == "Approved Only (Safe)":
        view_df = df[~df["Flagged"]]

    for _, row in view_df.iterrows():
        clean_author = str(row["Author"]).lstrip("@")
        if row["Flagged"]:
            tags_html = "".join(
                f'<span class="tag-chip">{t.strip().upper()}</span>'
                for t in row["Triggered"].split(",")
            )
            badge_text = (
                f"🚫 HIDDEN ON YOUTUBE ({row['Max_Score']}%)"
                if row["Actually_Hidden"]
                else f"🚫 FLAGGED PREVIEW ({row['Max_Score']}%)"
            )
            err_note = (
                f'<div style="color:#B45309;font-size:12px;margin-top:4px;">⚠️ {row["Hide_Error"]}</div>'
                if row["Hide_Error"]
                else ""
            )
            st.markdown(f"""
            <div class="comment-card-toxic">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span class="comment-author">@{clean_author} <span class="comment-date">• {row['Date']}</span></span>
                    <span class="pill-toxic">{badge_text}</span>
                </div>
                <p class="comment-body-toxic">{row['Comment']}</p>
                <div>{tags_html}</div>
                {err_note}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="comment-card-safe">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span class="comment-author">@{clean_author} <span class="comment-date">• {row['Date']}</span></span>
                    <span class="pill-safe">✅ PUBLISHED ({row['Max_Score']}%)</span>
                </div>
                <p class="comment-body-safe">{row['Comment']}</p>
            </div>
            """, unsafe_allow_html=True)

# =========================================================
# INTERFACE 1: LIVE YOUTUBE SCANNER
# =========================================================
if active_page == "🎥 Live YouTube Scanner":
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-badge">● INTERFACE 01 • ON-DEMAND VIDEO AUDIT</div>
        <h1 class="hero-title">Live YouTube Video Scanner</h1>
        <p class="hero-sub">Paginated multi-label comment scanning with instant YouTube Studio quarantine enforcement.</p>
    </div>
    """, unsafe_allow_html=True)

    col_in1, col_in2, col_in3 = st.columns([2.2, 2.5, 1.1])
    with col_in1:
        api_key = st.text_input(
            "YouTube Data API v3 Key (Optional if Channel Connected)",
            type="password",
            placeholder="Paste AIzaSy... key",
        )
    with col_in2:
        video_url = st.text_input(
            "YouTube Video / Shorts URL",
            value="https://youtu.be/5Zg-4jDPNuI",
            placeholder="Supports watch?v=, shorts/, youtu.be/"
        )
    with col_in3:
        scan_choice = st.selectbox("Scan Limit", [50, 100, 250, 500, "All Comments"], index=1)
        max_comments = 0 if scan_choice == "All Comments" else int(scan_choice)

    if st.button("🚀 Run Live YouTube Scan", type="primary", use_container_width=True):
        vid_id = extract_video_id(video_url)
        has_oauth = "youtube_creds" in st.session_state and st.session_state["youtube_creds"] is not None

        if not api_key and not has_oauth:
            st.error("Please paste your YouTube Data API v3 Key OR click 'Connect YouTube Channel' in the sidebar.")
        elif not vid_id:
            st.error("Could not extract a valid 11-character YouTube Video ID.")
        else:
            with st.spinner("Connecting to YouTube Data API v3 & running 6-head ML inference..."):
                try:
                    t0 = time.time()
                    v_title, c_title, df, _ = fetch_and_moderate_youtube(
                        api_key=api_key,
                        video_id=vid_id,
                        max_results=max_comments,
                        custom_threshold=active_threshold,
                        auto_hide_live=auto_hide_on_youtube,
                    )
                    elapsed = round((time.time() - t0) * 1000)

                    if df.empty:
                        st.warning("No public comments found on this video (or all toxic comments have already been hidden).")
                    else:
                        save_scan_to_db(vid_id, v_title, c_title, df, mode="Manual Scan")
                        render_scan_results(v_title, c_title, df, elapsed, active_threshold)
                except Exception as e:
                    st.error(f"YouTube API Error: {e}")

# =========================================================
# INTERFACE 2: LIVE AUTO-PILOT GUARD (24/7 BACKGROUND MONITOR)
# =========================================================
elif active_page == "🤖 Live Auto-Pilot Guard":
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-badge">● INTERFACE 02 • AUTONOMOUS DAEMON MODE</div>
        <h1 class="hero-title">Live Auto-Pilot Background Guard</h1>
        <p class="hero-sub">Continuous real-time polling loop that catches and hides hate speech seconds after posting.</p>
    </div>
    """, unsafe_allow_html=True)

    if "autopilot_active" not in st.session_state:
        st.session_state.autopilot_active = False
    if "autopilot_cycles" not in st.session_state:
        st.session_state.autopilot_cycles = 0

    col_ap1, col_ap2, col_ap3 = st.columns([2.2, 2.5, 1.3])
    with col_ap1:
        ap_api_key = st.text_input("API Key (Optional if Connected)", type="password", key="ap_key")
    with col_ap2:
        ap_video_url = st.text_input("Target YouTube Video / Livestream URL", value="https://youtu.be/5Zg-4jDPNuI", key="ap_url")
    with col_ap3:
        poll_interval = st.selectbox("Polling Interval", [15, 30, 60], index=1, format_func=lambda x: f"Every {x} sec")

    btn_c1, btn_c2 = st.columns(2)
    with btn_c1:
        if st.button("▶️ Start Auto-Pilot Guard", type="primary", use_container_width=True, disabled=st.session_state.autopilot_active):
            st.session_state.autopilot_active = True
            st.session_state.autopilot_cycles = 0
            st.rerun()
    with btn_c2:
        if st.button("⏹️ Stop Auto-Pilot Guard", use_container_width=True, disabled=not st.session_state.autopilot_active):
            st.session_state.autopilot_active = False
            st.rerun()

    if st.session_state.autopilot_active:
        vid_id = extract_video_id(ap_video_url)
        has_oauth = "youtube_creds" in st.session_state and st.session_state["youtube_creds"] is not None
        if not ap_api_key and not has_oauth:
            st.error("Connect your YouTube Channel in the sidebar or provide an API Key to run Auto-Pilot.")
            st.session_state.autopilot_active = False
        elif not vid_id:
            st.error("Invalid YouTube Video URL.")
            st.session_state.autopilot_active = False
        else:
            st.session_state.autopilot_cycles += 1
            st.info(f"🟢 **AUTO-PILOT ACTIVE** — Cycle **#{st.session_state.autopilot_cycles}** executed at `{datetime.now().strftime('%H:%M:%S')}` (Next sweep in {poll_interval}s)")
            try:
                t0 = time.time()
                v_title, c_title, df, _ = fetch_and_moderate_youtube(
                    api_key=ap_api_key,
                    video_id=vid_id,
                    max_results=50,
                    custom_threshold=active_threshold,
                    auto_hide_live=auto_hide_on_youtube,
                )
                elapsed = round((time.time() - t0) * 1000)
                if not df.empty:
                    save_scan_to_db(vid_id, v_title, c_title, df, mode="Auto-Pilot Guard")
                    render_scan_results(v_title, c_title, df, elapsed, active_threshold)
                else:
                    st.success("Sweep complete — 0 unmoderated comments found.")
            except Exception as err:
                st.error(f"Auto-Pilot Error: {err}")

            time.sleep(poll_interval)
            st.rerun()
    else:
        st.markdown("""
        <div class="info-panel">
            <h4>How Auto-Pilot Guard Works</h4>
            <p>When activated, ToxiGuard continuously polls your video's newest comments at your chosen interval, scores them with the 6-head NLP ensemble, automatically moves flagged hate speech to YouTube's <b>Held for Review</b> queue, and logs every action to your SQLite Audit Database.</p>
        </div>
        """, unsafe_allow_html=True)

# =========================================================
# INTERFACE 3: AUDIT HISTORY & REPORTS (SQLITE DATABASE)
# =========================================================
elif active_page == "📊 Audit History & Reports":
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-badge">● INTERFACE 03 • PERSISTENT SQLITE TELEMETRY</div>
        <h1 class="hero-title">Moderation Audit History &amp; Compliance Reports</h1>
        <p class="hero-sub">Historical scan records, quarantined comment logs, and downloadable CSV audit trails.</p>
    </div>
    """, unsafe_allow_html=True)

    scans_df, flagged_df = load_db_tables()

    if scans_df.empty:
        st.info("No scan logs recorded yet. Run a scan in **Live YouTube Scanner** or **Auto-Pilot Guard** to populate your audit database!")
    else:
        tot_scans = len(scans_df)
        tot_comments = int(scans_df["total_scanned"].sum())
        tot_flagged = int(scans_df["toxic_count"].sum())
        tot_hidden = int(scans_df["hidden_live_count"].sum())

        st.markdown(f"""
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label">Total Audit Runs</div>
                <div class="kpi-value" style="color:#1F2933;">{tot_scans}</div>
                <div class="kpi-sub">Stored in SQLite DB</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Cumulative Scanned</div>
                <div class="kpi-value" style="color:#3B5226;">{tot_comments}</div>
                <div class="kpi-sub">Across all videos</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Total Threats Caught</div>
                <div class="kpi-value" style="color:#DC2626;">{tot_flagged}</div>
                <div class="kpi-sub">Multi-label toxic hits</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Live YouTube Quarantines</div>
                <div class="kpi-value" style="color:#B45309;">{tot_hidden}</div>
                <div class="kpi-sub">Moved to Held for Review</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        dl_c1, dl_c2, dl_c3 = st.columns([1.5, 1.5, 1])
        with dl_c1:
            st.download_button(
                "📥 Download Scan Summary (CSV)",
                data=scans_df.to_csv(index=False).encode("utf-8"),
                file_name="toxiguard_scan_audit.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with dl_c2:
            st.download_button(
                "📥 Download Quarantined Comments (CSV)",
                data=flagged_df.to_csv(index=False).encode("utf-8"),
                file_name="toxiguard_quarantined_comments.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with dl_c3:
            if st.button("🗑️ Clear Audit Logs", use_container_width=True):
                conn = sqlite3.connect(DB_PATH)
                conn.execute("DELETE FROM scan_logs")
                conn.execute("DELETE FROM flagged_comments")
                conn.commit()
                conn.close()
                st.rerun()

        st.markdown("### 🗂️ Scan Execution Ledger")
        st.dataframe(scans_df, use_container_width=True, hide_index=True)

        st.markdown("### 🚨 Quarantined Comment Archive")
        st.dataframe(flagged_df, use_container_width=True, hide_index=True)

# =========================================================
# INTERFACE 4: INTERACTIVE SANDBOX & DEEP X-RAY
# =========================================================
elif active_page == "🧪 Interactive Sandbox & X-Ray":
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-badge">● INTERFACE 04 • REAL-TIME NLP PLAYGROUND</div>
        <h1 class="hero-title">Interactive Social Feed &amp; 6-Axis Probability X-Ray</h1>
        <p class="hero-sub">Test live pre-publish filtering and inspect individual classifier confidence scores.</p>
    </div>
    """, unsafe_allow_html=True)

    sub_t1, sub_t2 = st.tabs(["💬 Interactive Social Feed Demo", "🔬 Single Comment Deep-XRay"])

    with sub_t1:
        st.caption("Have your professor or classmates type comments here during the presentation to see instant quarantine vs. publication.")
        if "demo_feed" not in st.session_state:
            st.session_state.demo_feed = [
                {"user": "Priya_S", "text": "This tutorial explained the concepts so clearly, thank you!", "flagged": False, "score": 2.1, "tags": []},
                {"user": "Troll_99", "text": "You are an absolute idiot, delete this garbage right now!", "flagged": True, "score": 96.4, "tags": ["TOXIC", "INSULT"]},
            ]

        with st.form("live_post_form", clear_on_submit=True):
            c_user, c_msg = st.columns([1, 3])
            with c_user:
                username = st.text_input("Username", value="Guest_Viewer")
            with c_msg:
                new_comment = st.text_input("Post a comment to the live thread...", placeholder="Type a nice or toxic comment to test real-time filtering...")
            submitted = st.form_submit_button("Post Comment", type="primary")

            if submitted and new_comment.strip():
                res = analyze_text(new_comment, custom_threshold=active_threshold)
                st.session_state.demo_feed.insert(0, {
                    "user": username or "Anonymous",
                    "text": new_comment,
                    "flagged": res["is_toxic"],
                    "score": round(res["max_score"] * 100, 1),
                    "tags": [t.upper() for t in res["flagged_categories"]],
                })

        for item in st.session_state.demo_feed:
            clean_user = str(item["user"]).lstrip("@")
            if item["flagged"]:
                tags_html = "".join(f'<span class="tag-chip">{t}</span>' for t in item["tags"])
                st.markdown(f"""
                <div class="comment-card-toxic">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="comment-author">@{clean_user}</span>
                        <span class="pill-toxic">🚫 BLOCKED BEFORE PUBLISH ({item['score']}%)</span>
                    </div>
                    <p class="comment-body-toxic" style="font-style:italic;">[Hidden from public feed] "{item['text']}"</p>
                    <div>{tags_html}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="comment-card-safe">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="comment-author">@{clean_user}</span>
                        <span class="pill-safe">✅ LIVE ON FEED ({item['score']}%)</span>
                    </div>
                    <p class="comment-body-safe">{item['text']}</p>
                </div>
                """, unsafe_allow_html=True)

    with sub_t2:
        sample_text = st.text_area(
            "Enter any sentence to inspect all 6 classifier probabilities:",
            value="I completely disagree with your opinion, though I respect your effort.",
            height=100,
        )
        if st.button("Analyze Probabilities", type="primary"):
            res = analyze_text(sample_text, custom_threshold=active_threshold)
            scores_df = pd.DataFrame({
                "Category": [k.upper() for k in res["scores"].keys()],
                "Probability (%)": [round(v * 100, 2) for v in res["scores"].values()],
                "Threshold (%)": [round(active_threshold * 100, 2) for _ in res["scores"].keys()],
            })

            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=scores_df["Probability (%)"],
                theta=scores_df["Category"],
                fill="toself",
                name="Predicted Risk",
                line_color="#DC2626" if res["is_toxic"] else "#4A6332",
            ))
            fig_radar.add_trace(go.Scatterpolar(
                r=scores_df["Threshold (%)"],
                theta=scores_df["Category"],
                fill="toself",
                name="Safety Threshold",
                line_color="#2563EB",
            ))
            fig_radar.update_layout(
                polar=dict(
                    bgcolor="#FAF9F5",
                    radialaxis=dict(visible=True, range=[0, 100], gridcolor="#D6D1C4"),
                    angularaxis=dict(gridcolor="#D6D1C4"),
                ),
                paper_bgcolor="#FFFFFF",
                font_color="#1F2933",
                title="6-Axis Threat Fingerprint vs. Decision Threshold",
            )
            col_r1, col_r2 = st.columns([1.4, 1])
            with col_r1:
                st.plotly_chart(fig_radar, use_container_width=True)
            with col_r2:
                st.dataframe(scores_df, use_container_width=True, hide_index=True)

# =========================================================
# INTERFACE 5: SYSTEM & CLOUD STATUS
# =========================================================
elif active_page == "☁️ System & Cloud Status":
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-badge">● INTERFACE 05 • ARCHITECTURE &amp; TELEMETRY</div>
        <h1 class="hero-title">System Architecture &amp; Deployment Telemetry</h1>
        <p class="hero-sub">Model specifications, active session security status, and cloud deployment readiness.</p>
    </div>
    """, unsafe_allow_html=True)

    c_sys1, c_sys2 = st.columns(2)
    with c_sys1:
        st.markdown("""
        <div class="info-panel">
            <h4>🧠 NLP Ensemble Pipeline</h4>
            <ul>
                <li><b>Feature Extraction:</b> Dual Word (1–2 n-gram) + Subword Char-WB (3–5 n-gram) TF-IDF</li>
                <li><b>Classification Heads:</b> 6 Calibrated Logistic Regression Classifiers</li>
                <li><b>Labels:</b> Toxic, Severe Toxic, Obscene, Threat, Insult, Identity Hate</li>
                <li><b>Benchmark ROC-AUC:</b> <code>0.9858</code></li>
                <li><b>Inference Latency:</b> <code>&lt; 15 ms / comment</code></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with c_sys2:
        cloud_cfg, _ = _get_cloud_oauth_config()
        env_mode = "Streamlit Cloud (st.secrets Web OAuth)" if cloud_cfg else "Local Host (client_secret.json OAuth)"
        st.markdown(f"""
        <div class="info-panel">
            <h4>🛡️ Security &amp; Runtime Status</h4>
            <ul>
                <li><b>Execution Environment:</b> <code>{env_mode}</code></li>
                <li><b>YouTube OAuth Scope:</b> <code>youtube.force-ssl</code></li>
                <li><b>Session Isolation:</b> Per-user browser <code>st.session_state</code></li>
                <li><b>Audit Database:</b> SQLite (<code>{DB_PATH}</code>)</li>
                <li><b>Moderation Action:</b> <code>setModerationStatus("heldForReview")</code></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)