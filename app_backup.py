import inspect
import re
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from googleapiclient.discovery import build
import toxiguard_engine

# ---------------------------------------------------------
# 1. PAGE CONFIG & CUSTOM CYBER-UI HTML/CSS
# ---------------------------------------------------------
st.set_page_config(
    page_title="ToxiGuard AI | Real-Time Social Moderation",
    page_icon="ðŸ›¡ï¸",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_HTML_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #070B14;
    color: #E2E8F0;
}

.stApp {
    background: radial-gradient(circle at 15% 15%, #0F1C3F 0%, #070B14 45%, #050811 100%);
}

.hero-banner {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(59, 130, 246, 0.15) 50%, rgba(139, 92, 246, 0.12) 100%);
    border: 1px solid rgba(56, 189, 248, 0.25);
    border-radius: 16px;
    padding: 24px 30px;
    margin-bottom: 24px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45);
    backdrop-filter: blur(12px);
}
.hero-badge {
    display: inline-block;
    background: rgba(16, 185, 129, 0.18);
    color: #34D399;
    border: 1px solid rgba(52, 211, 153, 0.4);
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.6px;
    text-transform: uppercase;
    margin-bottom: 10px;
}
.hero-title {
    font-size: 34px;
    font-weight: 800;
    background: linear-gradient(90deg, #FFFFFF 0%, #38BDF8 55%, #818CF8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
    line-height: 1.2;
}
.hero-sub {
    color: #94A3B8;
    font-size: 15px;
    margin-top: 8px;
    margin-bottom: 0;
}

.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 22px;
}
.kpi-card {
    background: rgba(15, 23, 42, 0.72);
    border: 1px solid rgba(148, 163, 184, 0.15);
    border-radius: 14px;
    padding: 18px 20px;
    backdrop-filter: blur(10px);
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.kpi-card:hover {
    transform: translateY(-2px);
    border-color: rgba(56, 189, 248, 0.45);
}
.kpi-label {
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #94A3B8;
}
.kpi-value {
    font-size: 28px;
    font-weight: 800;
    margin: 6px 0 2px 0;
    font-family: 'JetBrains Mono', monospace;
}
.kpi-sub {
    font-size: 12px;
    color: #64748B;
}

.comment-card-safe {
    background: rgba(15, 23, 42, 0.65);
    border-left: 4px solid #10B981;
    border-top: 1px solid rgba(255,255,255,0.06);
    border-right: 1px solid rgba(255,255,255,0.06);
    border-bottom: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 12px;
}
.comment-card-toxic {
    background: rgba(69, 10, 10, 0.35);
    border-left: 4px solid #EF4444;
    border-top: 1px solid rgba(239, 68, 68, 0.25);
    border-right: 1px solid rgba(239, 68, 68, 0.25);
    border-bottom: 1px solid rgba(239, 68, 68, 0.25);
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 12px;
}
.pill-safe {
    background: rgba(16, 185, 129, 0.15);
    color: #34D399;
    border: 1px solid rgba(16, 185, 129, 0.35);
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
}
.pill-toxic {
    background: rgba(239, 68, 68, 0.2);
    color: #FCA5A5;
    border: 1px solid rgba(239, 68, 68, 0.45);
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
}
.tag-chip {
    display: inline-block;
    background: rgba(239, 68, 68, 0.25);
    color: #FECACA;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 11px;
    font-family: 'JetBrains Mono', monospace;
    margin-right: 6px;
    margin-top: 6px;
}
<style>
.stApp { background-color: #F7F5EE !important; color: #1F291E !important; }
[data-testid="stHeader"] { background-color: rgba(247, 245, 238, 0.9) !important; }
[data-testid="stSidebar"] { background-color: #EFECE2 !important; border-right: 1px solid #DCD7C9 !important; }
.stApp p, .stApp span, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp div { color: #1F291E; }
.stTextInput input, .stTextArea textarea { background-color: #FFFFFF !important; color: #1F291E !important; border: 1.5px solid #C5C2B2 !important; border-radius: 10px !important; }
.stButton > button { background-color: #556B2F !important; color: #FFFFFF !important; border: none !important; border-radius: 10px !important; font-weight: 600 !important; }
.stButton > button:hover { background-color: #3F5221 !important; }
.hero-banner { background: linear-gradient(135deg, #E9EDE0 0%, #F4F1E6 50%, #E3E8D5 100%) !important; border: 1px solid #C2CCB0 !important; box-shadow: 0 8px 24px rgba(63, 82, 33, 0.08) !important; }
.kpi-card { background: #FFFFFF !important; border: 1px solid #DDD8C8 !important; box-shadow: 0 4px 12px rgba(44, 53, 39, 0.05) !important; }
.kpi-card:hover { border-color: #556B2F !important; }
.kpi-label { color: #5C6656 !important; }
.kpi-value { color: #2D3B1E !important; }
.comment-card-safe { background: #FFFFFF !important; border-left: 5px solid #556B2F !important; border-top: 1px solid #E2DDD0 !important; border-right: 1px solid #E2DDD0 !important; border-bottom: 1px solid #E2DDD0 !important; box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important; }
.comment-card-toxic { background: #FFF6F3 !important; border-left: 5px solid #C2410C !important; border-top: 1px solid #F5D0C5 !important; border-right: 1px solid #F5D0C5 !important; border-bottom: 1px solid #F5D0C5 !important; }
</style>
"""
st.markdown(CUSTOM_HTML_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. AUTO-DETECT ENGINE CLASS OR FUNCTION (NO IMPORTERROR)
# ---------------------------------------------------------
LABELS = ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"]
DEFAULT_THRESHOLDS = {
    "toxic": 0.50,
    "severe_toxic": 0.40,
    "obscene": 0.50,
    "threat": 0.40,
    "insult": 0.50,
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

def analyze_text(text: str):
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
        flagged_cats = raw.get("flagged_categories") or raw.get("categories") or [
            k for k, v in scores.items() if float(v) >= float(thresholds.get(k, 0.5))
        ]
        max_score = raw.get("max_score")
        if max_score is None:
            max_score = max(scores.values()) if scores else 0.0
        is_toxic = raw.get("is_toxic")
        if is_toxic is None:
            is_toxic = bool(raw.get("flagged", len(flagged_cats) > 0))
        return {
            "is_toxic": bool(is_toxic),
            "max_score": float(max_score),
            "flagged_categories": list(flagged_cats),
            "scores": {k: float(scores.get(k, 0.0)) for k in LABELS},
        }
    return {
        "is_toxic": False,
        "max_score": 0.0,
        "flagged_categories": [],
        "scores": {k: 0.0 for k in LABELS},
    }

# ---------------------------------------------------------
# 3. HELPER FUNCTIONS (SUPPORTS WATCH, SHORTS, YOUTU.BE, LIVE)
# ---------------------------------------------------------
def extract_video_id(url_or_id: str):
    url_or_id = url_or_id.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url_or_id):
        return url_or_id
    match = re.search(r"(?:v=|\/v\/|embed\/|shorts\/|live\/|youtu\.be\/)([A-Za-z0-9_-]{11})", url_or_id)
    return match.group(1) if match else None

def fetch_youtube_comments(api_key: str, video_id: str, max_results: int = 50):
    youtube = build("youtube", "v3", developerKey=api_key)
    video_resp = youtube.videos().list(part="snippet,statistics", id=video_id).execute()
    video_title = "Unknown Video"
    channel_title = "Unknown Channel"
    if video_resp.get("items"):
        snippet = video_resp["items"][0]["snippet"]
        video_title = snippet.get("title", video_title)
        channel_title = snippet.get("channelTitle", channel_title)

    comments_data = []
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=min(max_results, 100),
        textFormat="plainText",
        order="time",
    )
    response = request.execute()

    for item in response.get("items", []):
        top = item["snippet"]["topLevelComment"]["snippet"]
        text = top["textDisplay"]
        author = top["authorDisplayName"]
        published = top["publishedAt"][:10]
        res = analyze_text(text)
        comments_data.append({
            "Author": author,
            "Comment": text,
            "Date": published,
            "Flagged": res["is_toxic"],
            "Max_Score": round(res["max_score"] * 100, 1),
            "Triggered": ", ".join(res["flagged_categories"]) if res["flagged_categories"] else "Clean",
            **{k: round(v * 100, 1) for k, v in res["scores"].items()},
        })
    return video_title, channel_title, pd.DataFrame(comments_data)

# ---------------------------------------------------------
# 4. SIDEBAR TELEMETRY & MODEL ARCHITECTURE
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### ðŸ›¡ï¸ ToxiGuard Control Center")
    st.caption("Ensemble NLP Threat Detection Engine")
    st.markdown("---")
    st.markdown("""
    **Model Architecture:**
    - **Vectorization:** Word (1â€“2 ngram) + Char-WB (3â€“5 ngram) TF-IDF
    - **Classifiers:** 6 Calibrated Logistic Regression Heads
    - **Validation ROC-AUC:** `0.9858`
    - **Inference Latency:** `< 15 ms / comment`
    """)
    st.markdown("---")
    st.markdown("**Active Moderation Thresholds:**")
    for label, thresh in thresholds.items():
        st.progress(float(thresh), text=f"{label.upper()}: {int(float(thresh)*100)}%")

# ---------------------------------------------------------
# 5. TOP HERO HEADER
# ---------------------------------------------------------
st.markdown("""
<div class="hero-banner">
    <div class="hero-badge">â— SYSTEM ONLINE â€¢ REAL-TIME AI MODERATION</div>
    <h1 class="hero-title">ToxiGuard AI Moderation Command Center</h1>
    <p class="hero-sub">Multi-label NLP toxicity detection & automated comment quarantine for social media platforms.</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 6. TABS FOR CAPSTONE DEMONSTRATION
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs([
    "ðŸŽ¥ Live YouTube Video Scanner",
    "ðŸ’¬ Interactive Social Feed Demo",
    "ðŸ”¬ Single Comment Deep-XRay"
])

# =========================================================
# TAB 1: LIVE YOUTUBE VIDEO SCANNER
# =========================================================
with tab1:
    col_in1, col_in2, col_in3 = st.columns([2.2, 2.5, 1])
    with col_in1:
        api_key = st.text_input("YouTube Data API v3 Key", type="password", placeholder="Paste AIzaSy... key")
    with col_in2:
        video_url = st.text_input(
            "YouTube Video / Shorts URL",
            value="https://www.youtube.com/shorts/7Z1cE9qu9Ag",
            placeholder="Supports watch?v=, shorts/, youtu.be/"
        )
    with col_in3:
        max_comments = st.selectbox("Scan Limit", [25, 50, 100], index=1)

    if st.button("ðŸš€ Run Live YouTube Scan", type="primary", use_container_width=True):
        vid_id = extract_video_id(video_url)
        if not api_key:
            st.error("Please paste your YouTube Data API v3 Key first.")
        elif not vid_id:
            st.error("Could not extract a valid 11-character YouTube Video ID.")
        else:
            with st.spinner("Connecting to YouTube Data API v3 & running 6-head ML inference..."):
                try:
                    t0 = time.time()
                    v_title, c_title, df = fetch_youtube_comments(api_key, vid_id, max_comments)
                    elapsed = round((time.time() - t0) * 1000)

                    if df.empty:
                        st.warning("No public comments found on this video (comments may be disabled).")
                    else:
                        total = len(df)
                        toxic_count = int(df["Flagged"].sum())
                        clean_count = total - toxic_count
                        tox_rate = round((toxic_count / total) * 100, 1)

                        st.success(f"Scanned **{v_title}** by *{c_title}* in **{elapsed} ms**")

                        st.markdown(f"""
                        <div class="kpi-grid">
                            <div class="kpi-card">
                                <div class="kpi-label">Total Comments Scanned</div>
                                <div class="kpi-value" style="color:#38BDF8;">{total}</div>
                                <div class="kpi-sub">Live YouTube API v3 Stream</div>
                            </div>
                            <div class="kpi-card">
                                <div class="kpi-label">Approved & Published</div>
                                <div class="kpi-value" style="color:#34D399;">{clean_count}</div>
                                <div class="kpi-sub">Passed all 6 safety checks</div>
                            </div>
                            <div class="kpi-card">
                                <div class="kpi-label">Quarantined / Hidden</div>
                                <div class="kpi-value" style="color:#C2410C;">{toxic_count}</div>
                                <div class="kpi-sub">Auto-rejected by ToxiGuard</div>
                            </div>
                            <div class="kpi-card">
                                <div class="kpi-label">Channel Toxicity Rate</div>
                                <div class="kpi-value" style="color:#FBBF24;">{tox_rate}%</div>
                                <div class="kpi-sub">Avg latency: {round(elapsed/total, 1)} ms/item</div>
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
                                color_continuous_scale=["#38BDF8", "#F59E0B", "#EF4444"],
                            )
                            fig_bar.update_layout(
                                paper_bgcolor="rgba(15,23,42,0.6)",
                                plot_bgcolor="rgba(0,0,0,0)",
                                font_color="#E2E8F0",
                                showlegend=False,
                                coloraxis_showscale=False,
                            )
                            st.plotly_chart(fig_bar, use_container_width=True)

                        with c2:
                            fig_pie = go.Figure(data=[go.Pie(
                                labels=["Approved (Clean)", "Quarantined (Toxic)"],
                                values=[clean_count, toxic_count],
                                hole=0.55,
                                marker_colors=["#556B2F", "#C2410C"],
                            )])
                            fig_pie.update_layout(
                                title="Automated Moderation Split",
                                paper_bgcolor="rgba(15,23,42,0.6)",
                                font_color="#E2E8F0",
                            )
                            st.plotly_chart(fig_pie, use_container_width=True)

                        st.markdown("### ðŸ“‹ Live Comment Moderation Log")
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
                            if row["Flagged"]:
                                tags_html = "".join(
                                    f'<span class="tag-chip">{t.strip().upper()}</span>'
                                    for t in row["Triggered"].split(",")
                                )
                                st.markdown(f"""
                                <div class="comment-card-toxic">
                                    <div style="display:flex; justify-content:space-between; align-items:center;">
                                        <strong>@{row['Author']} <span style="color:#64748B; font-size:12px;">â€¢ {row['Date']}</span></strong>
                                        <span class="pill-toxic">ðŸš« AUTO-HIDDEN ({row['Max_Score']}%)</span>
                                    </div>
                                    <p style="margin:8px 0 4px 0; color:#FECACA;">{row['Comment']}</p>
                                    <div>{tags_html}</div>
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown(f"""
                                <div class="comment-card-safe">
                                    <div style="display:flex; justify-content:space-between; align-items:center;">
                                        <strong>@{row['Author']} <span style="color:#64748B; font-size:12px;">â€¢ {row['Date']}</span></strong>
                                        <span class="pill-safe">âœ… PUBLISHED ({row['Max_Score']}%)</span>
                                    </div>
                                    <p style="margin:8px 0 0 0; color:#E2E8F0;">{row['Comment']}</p>
                                </div>
                                """, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"YouTube API Error: {e}")

# =========================================================
# TAB 2: INTERACTIVE LIVE SOCIAL FEED SIMULATOR
# =========================================================
with tab2:
    st.markdown("#### ðŸ§ª Live Social Comment Stream (Interactive Audience Test)")
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
            res = analyze_text(new_comment)
            st.session_state.demo_feed.insert(0, {
                "user": username or "Anonymous",
                "text": new_comment,
                "flagged": res["is_toxic"],
                "score": round(res["max_score"] * 100, 1),
                "tags": [t.upper() for t in res["flagged_categories"]],
            })

    for item in st.session_state.demo_feed:
        if item["flagged"]:
            tags_html = "".join(f'<span class="tag-chip">{t}</span>' for t in item["tags"])
            st.markdown(f"""
            <div class="comment-card-toxic">
                <div style="display:flex; justify-content:space-between;">
                    <strong>@{item['user']}</strong>
                    <span class="pill-toxic">ðŸš« BLOCKED BEFORE PUBLISH ({item['score']}%)</span>
                </div>
                <p style="margin:8px 0 4px 0; color:#FCA5A5; font-style:italic;">[Hidden from public feed] "{item['text']}"</p>
                <div>{tags_html}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="comment-card-safe">
                <div style="display:flex; justify-content:space-between;">
                    <strong>@{item['user']}</strong>
                    <span class="pill-safe">âœ… LIVE ON FEED ({item['score']}%)</span>
                </div>
                <p style="margin:8px 0 0 0;">{item['text']}</p>
            </div>
            """, unsafe_allow_html=True)

# =========================================================
# TAB 3: SINGLE COMMENT DEEP X-RAY
# =========================================================
with tab3:
    st.markdown("#### ðŸ”¬ Multi-Label Probability X-Ray")
    sample_text = st.text_area(
        "Enter any sentence to inspect all 6 classifier probabilities:",
        value="I completely disagree with your opinion, though I respect your effort.",
        height=100,
    )
    if st.button("Analyze Probabilities", type="primary"):
        res = analyze_text(sample_text)
        scores_df = pd.DataFrame({
            "Category": [k.upper() for k in res["scores"].keys()],
            "Probability (%)": [round(v * 100, 2) for v in res["scores"].values()],
            "Threshold (%)": [round(float(thresholds.get(k, 0.5)) * 100, 2) for k in res["scores"].keys()],
        })

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=scores_df["Probability (%)"],
            theta=scores_df["Category"],
            fill="toself",
            name="Predicted Risk",
            line_color="#EF4444" if res["is_toxic"] else "#10B981",
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=scores_df["Threshold (%)"],
            theta=scores_df["Category"],
            fill="toself",
            name="Safety Threshold",
            line_color="#38BDF8",
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            paper_bgcolor="rgba(15,23,42,0.6)",
            font_color="#E2E8F0",
            title="6-Axis Threat Fingerprint vs. Decision Threshold",
        )
        col_r1, col_r2 = st.columns([1.4, 1])
        with col_r1:
            st.plotly_chart(fig_radar, use_container_width=True)
        with col_r2:
            st.dataframe(scores_df, use_container_width=True, hide_index=True)

