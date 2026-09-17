import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import datetime
import os
from pymongo import MongoClient
from dotenv import load_dotenv

from scraper import run_sync

load_dotenv()

# ────────────────────────────────────────────────
#  Page config & global CSS
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="Wishnet Dashboard",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<!-- responsive viewport meta injected via streamlit -->
<style>
/* ── Responsive viewport ── */
@viewport { width: device-width; }
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }

.hero {
    background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
    border-radius: 16px;
    padding: 28px 36px;
    margin-bottom: 8px;
}
.hero h1 { color: #fff; font-size: 1.9rem; font-weight: 800; margin: 0 0 4px 0; letter-spacing: -0.5px; }
.hero p  { color: #94a3b8; font-size: 0.92rem; margin: 0; }
.hero-badge {
    background: rgba(56,189,248,0.15); border: 1px solid rgba(56,189,248,0.3);
    color: #38bdf8; font-size: 0.72rem; font-weight: 600; letter-spacing: 0.1em;
    padding: 3px 12px; border-radius: 999px; text-transform: uppercase;
    margin-bottom: 8px; display: inline-block;
}

/* ── Metric grid: 4-col on desktop, 2-col on tablet, 1-col on phone ── */
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 0;
}
@media (max-width: 900px)  { .metrics-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 480px)  { .metrics-grid { grid-template-columns: 1fr; } }

/* ── Section cards stack on mobile ── */
.two-col-grid {
    display: grid;
    grid-template-columns: 3fr 1fr;
    gap: 14px;
}
@media (max-width: 768px) { .two-col-grid { grid-template-columns: 1fr; } }

.half-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
}
@media (max-width: 640px) { .half-grid { grid-template-columns: 1fr; } }

/* ── Session row: 5-col → 2-col on small screens ── */
.session-row-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 8px;
    align-items: start;
    padding: 14px 0;
    border-bottom: 1px solid #1e293b;
}
.session-row-grid:last-child { border-bottom: none; }
@media (max-width: 640px) {
    .session-row-grid {
        grid-template-columns: 1fr 1fr;
        gap: 10px 16px;
    }
}

/* ── Chart containers: allow horizontal scroll on tiny screens ── */
.chart-scroll {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
}

/* ── Hero shrinks on mobile ── */
@media (max-width: 600px) {
    .hero { padding: 20px 18px; }
    .hero h1 { font-size: 1.35rem; }
    .metric-value { font-size: 1.4rem; }
    .section-card { padding: 16px; }
}
.metric-card {
    background: linear-gradient(145deg, #1e293b, #0f172a);
    border: 1px solid #334155; border-radius: 14px;
    padding: 20px 22px; height: 100%;
}
.metric-card.highlight {
    background: linear-gradient(135deg, #1e3a5f 0%, #0c2340 100%);
    border-color: #38bdf8; box-shadow: 0 0 24px rgba(56,189,248,0.12);
}
.metric-card.green {
    background: linear-gradient(135deg, #0d2b1f 0%, #071a12 100%);
    border-color: #34d399; box-shadow: 0 0 24px rgba(52,211,153,0.10);
}
.metric-card.violet {
    background: linear-gradient(135deg, #1e1b4b 0%, #0f0c29 100%);
    border-color: #a78bfa; box-shadow: 0 0 24px rgba(167,139,250,0.10);
}
.metric-label {
    color: #64748b; font-size: 0.7rem; font-weight: 600;
    letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 8px;
}
.metric-value { color: #f1f5f9; font-size: 1.8rem; font-weight: 700; letter-spacing: -0.5px; line-height: 1; }
.metric-card.highlight .metric-value { color: #38bdf8; }
.metric-card.green   .metric-value   { color: #34d399; }
.metric-card.violet  .metric-value   { color: #a78bfa; }
.metric-sub { color: #475569; font-size: 0.7rem; margin-top: 6px; }

.section-card {
    background: #1e293b; border: 1px solid #334155;
    border-radius: 14px; padding: 22px; margin-bottom: 0;
}
.section-title { color: #e2e8f0; font-size: 0.95rem; font-weight: 700; margin: 0 0 2px 0; }
.section-sub   { color: #64748b; font-size: 0.76rem; margin: 0 0 16px 0; }

/* Session row in day view */
.session-row {
    display: grid; grid-template-columns: 1fr 1fr 1fr 1fr 1fr;
    gap: 8px; align-items: center;
    padding: 12px 0; border-bottom: 1px solid #1e293b;
}
.session-row:last-child { border-bottom: none; }
.session-label { color: #64748b; font-size: 0.68rem; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; }
.session-val   { color: #e2e8f0; font-size: 0.85rem; font-weight: 600; }
.badge-active  { background: rgba(52,211,153,0.15); color: #34d399; border: 1px solid rgba(52,211,153,0.35); font-size: 0.65rem; font-weight: 700; padding: 2px 8px; border-radius: 999px; }
.badge-done    { background: rgba(100,116,139,0.15); color: #94a3b8; border: 1px solid #334155; font-size: 0.65rem; font-weight: 700; padding: 2px 8px; border-radius: 999px; }

.stButton > button {
    background: linear-gradient(135deg, #0ea5e9, #6366f1) !important;
    color: white !important; border: none !important; border-radius: 10px !important;
    padding: 10px 22px !important; font-weight: 600 !important; font-size: 0.86rem !important;
    transition: all 0.2s ease !important; box-shadow: 0 4px 15px rgba(14,165,233,0.25) !important;
}
.stButton > button:hover { transform: translateY(-1px) !important; box-shadow: 0 8px 25px rgba(14,165,233,0.4) !important; }

hr { border-color: #1e293b !important; margin: 18px 0 !important; }
.stAlert { border-radius: 10px !important; }

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    background: #0f172a; border-radius: 10px; padding: 4px; gap: 4px; border: 1px solid #334155;
}
.stTabs [data-baseweb="tab"] {
    background: transparent; border-radius: 8px; color: #64748b;
    font-weight: 600; font-size: 0.85rem; padding: 8px 20px;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #0ea5e9, #6366f1) !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
#  DB
# ────────────────────────────────────────────────
@st.cache_resource
def get_db():
    uri = os.environ.get("MONGODB_URI")
    db_name = os.environ.get("MONGODB_DB")
    if not uri or not db_name:
        st.error("MongoDB URI and DB name must be set in .env"); st.stop()
    return MongoClient(uri)[db_name]

db        = get_db()
usage_col = db["usage"]
logs_col  = db["logs"]

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

# ────────────────────────────────────────────────
#  Helpers
# ────────────────────────────────────────────────
def fmt_mb(mb: float) -> str:
    if mb >= 1024**2: return f"{mb/1024**2:.2f} TB"
    if mb >= 1024:    return f"{mb/1024:.2f} GB"
    return f"{mb:.2f} MB"

def ist_bounds(start_date, end_date):
    s = datetime.datetime.combine(start_date, datetime.time.min, tzinfo=IST).astimezone(datetime.timezone.utc)
    e = datetime.datetime.combine(end_date,   datetime.time.max, tzinfo=IST).astimezone(datetime.timezone.utc)
    return s, e

def fmt_dt(d):
    if not d: return "—"
    return (d + datetime.timedelta(hours=5, minutes=30)).strftime("%d %b %Y, %I:%M %p")

def fmt_time(d):
    if not d: return "—"
    return (d + datetime.timedelta(hours=5, minutes=30)).strftime("%I:%M %p")

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#94a3b8", size=12),
    margin=dict(l=0, r=0, t=10, b=0),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                font=dict(size=11), bgcolor="rgba(0,0,0,0)", borderwidth=0),
    xaxis=dict(gridcolor="#1e293b", linecolor="#334155", tickfont=dict(size=10)),
    yaxis=dict(gridcolor="#1e293b", linecolor="#334155", zeroline=False),
    hovermode="x unified",
)
DL_COLOR  = "#38bdf8"
UL_COLOR  = "#a78bfa"
TOT_COLOR = "#34d399"

# ────────────────────────────────────────────────
#  DB Queries
# ────────────────────────────────────────────────
@st.cache_data(ttl=60)
def fetch_all_time():
    rows = list(usage_col.aggregate([
        {"$group": {"_id": None, "downloadMB": {"$sum": "$downloadMB"},
                    "uploadMB": {"$sum": "$uploadMB"}, "sessions": {"$sum": 1}}}
    ]))
    return rows[0] if rows else {}

@st.cache_data(ttl=60)
def fetch_range(start, end):
    match = {"loginTime": {"$gte": start, "$lte": end}}
    summary = list(usage_col.aggregate([
        {"$match": match},
        {"$group": {"_id": None, "downloadMB": {"$sum": "$downloadMB"},
                    "uploadMB": {"$sum": "$uploadMB"}, "sessions": {"$sum": 1},
                    "earliestLogin": {"$min": "$loginTime"}, "latestLogin": {"$max": "$loginTime"}}}
    ]))
    daily = list(usage_col.aggregate([
        {"$match": match},
        {"$project": {
            "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$loginTime", "timezone": "Asia/Kolkata"}},
            "downloadMB": 1, "uploadMB": 1
        }},
        {"$group": {"_id": "$date", "downloadMB": {"$sum": "$downloadMB"}, "uploadMB": {"$sum": "$uploadMB"}}},
        {"$sort": {"_id": 1}}
    ]))
    return summary[0] if summary else {}, daily

@st.cache_data(ttl=30)
def fetch_day_sessions(day: datetime.date):
    """Fetch all individual sessions for a given IST day."""
    start, end = ist_bounds(day, day)
    sessions = list(usage_col.find(
        {"loginTime": {"$gte": start, "$lte": end}},
        sort=[("loginTime", -1)]
    ))
    return sessions

@st.cache_data(ttl=30)
def fetch_latest_session_day():
    """Return the IST date of the most recent session stored."""
    doc = usage_col.find_one({}, sort=[("loginTime", -1)])
    if not doc: return datetime.datetime.now(IST).date()
    ist_dt = doc["loginTime"].replace(tzinfo=datetime.timezone.utc) + datetime.timedelta(hours=5, minutes=30)
    return ist_dt.date()

@st.cache_data(ttl=60)
def fetch_sync_logs(limit=5):
    return list(logs_col.find(
        {"status": {"$in": ["success", "error"]}},
        sort=[("startedAt", -1)], limit=limit
    ))

@st.cache_data(ttl=60)
def fetch_raw_sessions(limit=1000):
    """Fetch recent raw sessions directly from the collection."""
    docs = list(usage_col.find({}, sort=[("loginTime", -1)], limit=limit))
    return docs

@st.cache_data(ttl=300)
def fetch_db_date_bounds():
    """Return (earliest_date_ist, latest_date_ist) stored in the DB."""
    earliest_doc = usage_col.find_one({}, sort=[("loginTime",  1)], projection={"loginTime": 1})
    latest_doc   = usage_col.find_one({}, sort=[("loginTime", -1)], projection={"loginTime": 1})
    if not earliest_doc or not latest_doc:
        today = datetime.datetime.now(IST).date()
        return today, today
    def to_ist_date(d):
        return (d.replace(tzinfo=datetime.timezone.utc) + datetime.timedelta(hours=5, minutes=30)).date()
    return to_ist_date(earliest_doc["loginTime"]), to_ist_date(latest_doc["loginTime"])

@st.cache_data(ttl=60)
def fetch_annual(year: int):
    """Monthly aggregation for a given IST year."""
    # Build UTC bounds for Jan 1 00:00 IST → Dec 31 23:59:59 IST
    start = datetime.datetime(year, 1, 1, 0, 0, 0, tzinfo=IST).astimezone(datetime.timezone.utc)
    end   = datetime.datetime(year, 12, 31, 23, 59, 59, tzinfo=IST).astimezone(datetime.timezone.utc)
    match = {"loginTime": {"$gte": start, "$lte": end}}

    summary = list(usage_col.aggregate([
        {"$match": match},
        {"$group": {"_id": None,
                    "downloadMB": {"$sum": "$downloadMB"},
                    "uploadMB":   {"$sum": "$uploadMB"},
                    "sessions":   {"$sum": 1}}}
    ]))

    monthly = list(usage_col.aggregate([
        {"$match": match},
        {"$project": {
            "month": {"$dateToString": {"format": "%Y-%m", "date": "$loginTime", "timezone": "Asia/Kolkata"}},
            "downloadMB": 1, "uploadMB": 1
        }},
        {"$group": {"_id": "$month",
                    "downloadMB": {"$sum": "$downloadMB"},
                    "uploadMB":   {"$sum": "$uploadMB"},
                    "sessions":   {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]))
    return summary[0] if summary else {}, monthly

# ────────────────────────────────────────────────
#  Chart helpers
# ────────────────────────────────────────────────
def area_chart(daily_data):
    df = pd.DataFrame(daily_data).rename(columns={"_id": "date"})
    df["date"] = pd.to_datetime(df["date"])  # Fixes Plotly categorical bug
    df["downloadGB"] = df["downloadMB"] / 1024
    df["uploadGB"]   = df["uploadMB"]   / 1024
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["date"], y=df["downloadGB"], name="Download GB",
        fill="tozeroy", line=dict(color=DL_COLOR, width=2), fillcolor="rgba(56,189,248,0.15)",
        hovertemplate="<b>%{x|%d %b %Y}</b><br>Download: %{y:.2f} GB<extra></extra>"))
    fig.add_trace(go.Scatter(x=df["date"], y=df["uploadGB"], name="Upload GB",
        fill="tozeroy", line=dict(color=UL_COLOR, width=2), fillcolor="rgba(167,139,250,0.15)",
        hovertemplate="<b>%{x|%d %b %Y}</b><br>Upload: %{y:.2f} GB<extra></extra>"))
    fig.update_layout(**PLOTLY_LAYOUT, height=300)
    return fig

def bar_chart(daily_data):
    df = pd.DataFrame(daily_data).rename(columns={"_id": "date"})
    df["date"] = pd.to_datetime(df["date"])  # Fixes Plotly categorical bug
    df["downloadGB"] = df["downloadMB"] / 1024
    df["uploadGB"]   = df["uploadMB"]   / 1024
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["date"], y=df["downloadGB"], name="Download GB",
        marker_color=DL_COLOR, opacity=0.85,
        hovertemplate="<b>%{x|%d %b %Y}</b><br>Download: %{y:.2f} GB<extra></extra>"))
    fig.add_trace(go.Bar(x=df["date"], y=df["uploadGB"], name="Upload GB",
        marker_color=UL_COLOR, opacity=0.85,
        hovertemplate="<b>%{x|%d %b %Y}</b><br>Upload: %{y:.2f} GB<extra></extra>"))
    fig.update_layout(**PLOTLY_LAYOUT, height=300, barmode="group")
    return fig

def donut_chart(dl_mb, ul_mb):
    total_gb = (dl_mb + ul_mb) / 1024
    fig = go.Figure(go.Pie(
        labels=["Download", "Upload"], values=[dl_mb, ul_mb], hole=0.68,
        marker=dict(colors=[DL_COLOR, UL_COLOR], line=dict(color="#0f172a", width=2)),
        textinfo="percent", textfont=dict(size=12, color="#e2e8f0"),
        hovertemplate="<b>%{label}</b><br>%{value:.0f} MB (%{percent})<extra></extra>"
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5,
                    font=dict(size=11, color="#94a3b8"), bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=0, r=0, t=0, b=0), height=230,
        annotations=[dict(text=f"<b>{total_gb:.1f} GB</b><br><span style='font-size:10px'>total</span>",
                          x=0.5, y=0.5, font=dict(size=14, color="#e2e8f0"), showarrow=False)]
    )
    return fig

def session_timeline_chart(sessions):
    """Horizontal bar chart showing each session's time span for a given day."""
    if not sessions:
        return go.Figure()

    rows = []
    for s in sessions:
        login = s.get("loginTime")
        logout = s.get("logoutTime")
        if not login: continue
        login_ist  = login.replace(tzinfo=datetime.timezone.utc) + datetime.timedelta(hours=5, minutes=30)
        logout_ist = (logout.replace(tzinfo=datetime.timezone.utc) + datetime.timedelta(hours=5, minutes=30)) if logout else datetime.datetime.now(IST)
        duration_h = (logout_ist - login_ist).total_seconds() / 3600
        rows.append({
            "IP": s.get("ipAddress", "?"),
            "Login": login_ist.strftime("%H:%M"),
            "Logout": logout_ist.strftime("%H:%M") if s.get("logoutTime") else "Active",
            "Start": login_ist,
            "End": logout_ist,
            "DL": s.get("downloadMB", 0),
            "UL": s.get("uploadMB", 0),
            "Active": not bool(s.get("logoutTime")),
        })

    if not rows: return go.Figure()

    fig = go.Figure()
    for i, r in enumerate(rows):
        color = TOT_COLOR if r["Active"] else DL_COLOR
        tip = (f"<b>Session {i+1}</b><br>"
               f"Login: {r['Login']} → Logout: {r['Logout']}<br>"
               f"↓ {fmt_mb(r['DL'])} · ↑ {fmt_mb(r['UL'])}<extra></extra>")
        fig.add_trace(go.Bar(
            x=[(r["End"] - r["Start"]).total_seconds() / 3600],
            y=[f"S{i+1} · {r['Login']}"],
            base=[(r["Start"] - r["Start"].replace(hour=0, minute=0, second=0)).total_seconds() / 3600],
            orientation="h",
            marker_color=color, opacity=0.85,
            name="Active" if r["Active"] else "Ended",
            hovertemplate=tip,
            showlegend=False,
            width=0.5,
        ))

    # Exclude xaxis/yaxis/hovermode from spread to avoid duplicate kwarg error
    base = {k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("hovermode", "xaxis", "yaxis")}
    fig.update_layout(
        **base,
        hovermode="y unified",
        height=max(120, len(rows) * 52),
        barmode="overlay",
        xaxis=dict(
            title="Hour of day (IST)", gridcolor="#1e293b",
            linecolor="#334155", tickfont=dict(size=10),
            tickvals=list(range(0, 25, 2)),
            ticktext=[f"{h:02d}:00" for h in range(0, 25, 2)]
        ),
        yaxis=dict(gridcolor="#1e293b", linecolor="#334155", autorange="reversed"),
    )
    return fig

def monthly_area_chart(monthly_data):
    df = pd.DataFrame(monthly_data).rename(columns={"_id": "month"})
    df["downloadGB"] = df["downloadMB"] / 1024
    df["uploadGB"]   = df["uploadMB"]   / 1024
    MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    df["label"] = df["month"].apply(lambda m: MONTHS[int(m.split("-")[1]) - 1] + " '" + m.split("-")[0][2:])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["label"], y=df["downloadGB"], name="Download GB",
        fill="tozeroy", line=dict(color=DL_COLOR, width=2.5), fillcolor="rgba(56,189,248,0.18)",
        hovertemplate="<b>%{x}</b><br>Download: %{y:.2f} GB<extra></extra>"))
    fig.add_trace(go.Scatter(x=df["label"], y=df["uploadGB"], name="Upload GB",
        fill="tozeroy", line=dict(color=UL_COLOR, width=2.5), fillcolor="rgba(167,139,250,0.18)",
        hovertemplate="<b>%{x}</b><br>Upload: %{y:.2f} GB<extra></extra>"))
    fig.update_layout(**PLOTLY_LAYOUT, height=320)
    return fig

def monthly_bar_chart(monthly_data):
    df = pd.DataFrame(monthly_data).rename(columns={"_id": "month"})
    df["downloadGB"] = df["downloadMB"] / 1024
    df["uploadGB"]   = df["uploadMB"]   / 1024
    df["totalGB"]    = df["downloadGB"] + df["uploadGB"]
    MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    df["label"] = df["month"].apply(lambda m: MONTHS[int(m.split("-")[1]) - 1])
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["label"], y=df["downloadGB"], name="Download GB",
        marker_color=DL_COLOR, opacity=0.88,
        hovertemplate="<b>%{x}</b><br>Download: %{y:.2f} GB<extra></extra>"))
    fig.add_trace(go.Bar(x=df["label"], y=df["uploadGB"], name="Upload GB",
        marker_color=UL_COLOR, opacity=0.88,
        hovertemplate="<b>%{x}</b><br>Upload: %{y:.2f} GB<extra></extra>"))
    fig.update_layout(**PLOTLY_LAYOUT, height=320, barmode="group")
    return fig

def metric_card(col, label, value, sub="", style=""):
    col.markdown(f"""
    <div class="metric-card {style}">
      <div class="metric-label">{label}</div>
      <div class="metric-value">{value}</div>
      <div class="metric-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
#  Hero
# ────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div>
    <div class="hero-badge">📡 ISP Analytics</div>
    <h1>Wishnet Usage Dashboard</h1>
    <p>Long-term history collected from your Wishnet portal · stored in MongoDB</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
#  Top bar: Sync button
# ────────────────────────────────────────────────
today_ist = datetime.datetime.now(IST).date()

scol1, scol2 = st.columns([1, 5])
with scol1:
    do_sync = st.button("↻  Sync Now", use_container_width=True)
with scol2:
    msg_placeholder = st.empty()

if do_sync:
    with st.spinner("Connecting to Wishnet & syncing data…"):
        try:
            res = run_sync()
            fetch_all_time.clear(); fetch_range.clear()
            fetch_day_sessions.clear(); fetch_latest_session_day.clear(); fetch_sync_logs.clear()
            msg_placeholder.success(
                f"✅ Sync complete — **{res['recordsInserted']}** new · "
                f"**{res['recordsUpdated']}** updated · **{res['duplicates']}** already present"
            )
        except Exception as e:
            msg_placeholder.error(f"❌ Sync failed: {e}")

st.markdown("<hr/>", unsafe_allow_html=True)

# ────────────────────────────────────────────────
#  All-time metric strip
# ────────────────────────────────────────────────
all_time = fetch_all_time()
all_dl   = all_time.get("downloadMB", 0)
all_ul   = all_time.get("uploadMB",   0)
all_tot  = all_dl + all_ul
all_sess = all_time.get("sessions", 0)

def metrics_row(cards):
    """Render a responsive 4-col metric grid from a list of (label, value, sub, style) tuples."""
    inner = ""
    for label, value, sub, style in cards:
        inner += f'<div class="metric-card {style}"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-sub">{sub}</div></div>'
    st.markdown(f'<div class="metrics-grid">{inner}</div>', unsafe_allow_html=True)

metrics_row([
    ("All-Time Total",    fmt_mb(all_tot),  f"↓ {fmt_mb(all_dl)} · ↑ {fmt_mb(all_ul)}", "highlight"),
    ("All-Time Download", fmt_mb(all_dl),   "total ever downloaded", ""),
    ("All-Time Upload",   fmt_mb(all_ul),   "total ever uploaded", "violet"),
    ("Sessions Stored",   str(all_sess),    "in MongoDB", "green"),
])

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# ────────────────────────────────────────────────
#  TABS
# ────────────────────────────────────────────────
tab_range, tab_day, tab_year, tab_data = st.tabs(["📅  Range View", "🔍  Day View", "📆  Year View", "🗄️  Raw Data"])

# ══════════════════════════════════════════════
#  TAB 1 — RANGE VIEW
# ══════════════════════════════════════════════
with tab_range:
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    # Fetch bounds from DB so user can't pick dates outside available data
    earliest_date, latest_date = fetch_db_date_bounds()
    month_start = max(today_ist.replace(day=1), earliest_date)

    fc1, fc2, fc3 = st.columns([2, 2, 3])
    with fc1:
        start_date = st.date_input(
            "📅 From",
            value=month_start,
            min_value=earliest_date,
            max_value=latest_date,
            key="range_from",
            help=f"Earliest available data: {earliest_date.strftime('%d %b %Y')}"
        )
    with fc2:
        end_date = st.date_input(
            "📅 To",
            value=min(today_ist, latest_date),
            min_value=earliest_date,
            max_value=latest_date,
            key="range_to",
            help=f"Latest available data: {latest_date.strftime('%d %b %Y')}"
        )
    with fc3:
        st.markdown(f"""
        <div style="padding-top:22px;color:#64748b;font-size:0.75rem">
          📦 Data available from
          <span style="color:#38bdf8;font-weight:600">{earliest_date.strftime('%d %b %Y')}</span>
          to
          <span style="color:#38bdf8;font-weight:600">{latest_date.strftime('%d %b %Y')}</span>
        </div>""", unsafe_allow_html=True)

    start_utc, end_utc = ist_bounds(start_date, end_date)
    selected, daily = fetch_range(start_utc, end_utc)

    sel_dl   = selected.get("downloadMB", 0)
    sel_ul   = selected.get("uploadMB",   0)
    sel_tot  = sel_dl + sel_ul
    sel_sess = selected.get("sessions", 0)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    metrics_row([
        ("Range Download", fmt_mb(sel_dl),  f"of {fmt_mb(sel_tot)} combined", ""),
        ("Range Upload",   fmt_mb(sel_ul),  f"{(sel_ul/sel_tot*100):.1f}% of range total" if sel_tot else "—", "violet"),
        ("Range Total",    fmt_mb(sel_tot), f"across {sel_sess} sessions", "green"),
        ("Sessions",       str(sel_sess),   f"{len(daily)} active days", ""),
    ])

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    if not daily:
        st.info("No usage data for this range. Try syncing or widening the date range.")
    else:
        ch1, ch2 = st.columns([3, 1])
        with ch1:
            st.markdown('<div class="section-card"><p class="section-title">Daily Traffic</p><p class="section-sub">GB transferred per day in the selected range</p>', unsafe_allow_html=True)
            st.plotly_chart(area_chart(daily), use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)
        with ch2:
            st.markdown('<div class="section-card"><p class="section-title">Breakdown</p><p class="section-sub">Download vs Upload split</p>', unsafe_allow_html=True)
            if sel_tot > 0:
                st.plotly_chart(donut_chart(sel_dl, sel_ul), use_container_width=True, config={"displayModeBar": False})
            else:
                st.markdown("<p style='color:#64748b;font-size:0.8rem'>No data</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        st.markdown('<div class="section-card"><p class="section-title">Download vs Upload – Daily Comparison</p><p class="section-sub">Side-by-side view to spot heavy usage days</p>', unsafe_allow_html=True)
        st.plotly_chart(bar_chart(daily), use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        info_col, log_col = st.columns(2)
        earliest = selected.get("earliestLogin")
        latest   = selected.get("latestLogin")

        with info_col:
            st.markdown(f"""
            <div class="section-card">
              <p class="section-title">Range Details</p>
              <p class="section-sub">Session boundaries & averages in selected period</p>
              <div style="display:grid;gap:14px">
                <div><div class="metric-label">Earliest Session</div>
                  <div style="color:#e2e8f0;font-size:0.9rem;font-weight:600">{fmt_dt(earliest)}</div></div>
                <div><div class="metric-label">Latest Session</div>
                  <div style="color:#e2e8f0;font-size:0.9rem;font-weight:600">{fmt_dt(latest)}</div></div>
                <div><div class="metric-label">Avg. Daily Download</div>
                  <div style="color:{DL_COLOR};font-size:0.9rem;font-weight:600">{fmt_mb(sel_dl / max(len(daily),1))}</div></div>
                <div><div class="metric-label">Avg. Daily Upload</div>
                  <div style="color:{UL_COLOR};font-size:0.9rem;font-weight:600">{fmt_mb(sel_ul / max(len(daily),1))}</div></div>
              </div>
            </div>""", unsafe_allow_html=True)

        with log_col:
            logs = fetch_sync_logs()
            st.markdown('<div class="section-card"><p class="section-title">Recent Sync History</p><p class="section-sub">Last 5 sync operations</p>', unsafe_allow_html=True)
            if logs:
                for l in logs:
                    status      = l.get("status", "?")
                    started     = l.get("startedAt")
                    started_ist = (started + datetime.timedelta(hours=5, minutes=30)).strftime("%d %b, %I:%M %p") if started else "—"
                    icon        = "✅" if status == "success" else "❌"
                    found       = l.get("recordsFound", 0)
                    ins         = l.get("recordsInserted", 0)
                    err         = l.get("error") or ""
                    detail      = f"{found} found · {ins} new" if status == "success" else err[:55]
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid #1e293b">
                      <span style="font-size:1.1rem">{icon}</span>
                      <div>
                        <div style="color:#e2e8f0;font-size:0.8rem;font-weight:600">{started_ist}</div>
                        <div style="color:#64748b;font-size:0.73rem">{detail}</div>
                      </div>
                    </div>""", unsafe_allow_html=True)
            else:
                st.markdown("<p style='color:#64748b;font-size:0.8rem'>No sync history yet.</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  TAB 2 — DAY VIEW
# ══════════════════════════════════════════════
with tab_day:
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Default to the most recent session's day
    default_day = fetch_latest_session_day()

    dcol1, dcol2 = st.columns([2, 4])
    with dcol1:
        chosen_day = st.date_input(
            "📅 Select a day",
            value=default_day,
            max_value=today_ist,
            key="day_picker",
            help="Defaults to the day of your most recent stored session."
        )
    with dcol2:
        st.markdown(f"""
        <div style="padding-top:10px">
          <span style="color:#64748b;font-size:0.78rem">Showing sessions for</span>
          <span style="color:#38bdf8;font-weight:700;font-size:1.05rem;margin-left:8px">
            {chosen_day.strftime("%A, %d %B %Y")}
          </span>
          {"<span style='margin-left:10px;background:rgba(52,211,153,0.15);color:#34d399;border:1px solid rgba(52,211,153,0.35);font-size:0.68rem;font-weight:700;padding:2px 10px;border-radius:999px'>TODAY</span>" if chosen_day == today_ist else ""}
          {"<span style='margin-left:10px;background:rgba(56,189,248,0.15);color:#38bdf8;border:1px solid rgba(56,189,248,0.3);font-size:0.68rem;font-weight:700;padding:2px 10px;border-radius:999px'>MOST RECENT</span>" if chosen_day == default_day and chosen_day != today_ist else ""}
        </div>""", unsafe_allow_html=True)

    sessions = fetch_day_sessions(chosen_day)

    if not sessions:
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        st.info(f"No sessions found on **{chosen_day.strftime('%d %b %Y')}**. Try a different day or sync first.")
    else:
        # Day-level aggregates
        day_dl   = sum(s.get("downloadMB", 0) for s in sessions)
        day_ul   = sum(s.get("uploadMB",   0) for s in sessions)
        day_tot  = day_dl + day_ul
        n_active = sum(1 for s in sessions if not s.get("logoutTime"))

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        metrics_row([
            ("Day Download",    fmt_mb(day_dl),  f"{(day_dl/day_tot*100):.1f}% of day total" if day_tot else "—", ""),
            ("Day Upload",      fmt_mb(day_ul),  f"{(day_ul/day_tot*100):.1f}% of day total" if day_tot else "—", "violet"),
            ("Day Total",       fmt_mb(day_tot), f"across {len(sessions)} session(s)", "green"),
            ("Active Sessions", str(n_active),   "currently open" if n_active else "all sessions ended",
             "highlight" if n_active else ""),
        ])

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # Timeline chart + donut
        tl_col, dn_col = st.columns([3, 1])
        with tl_col:
            st.markdown('<div class="section-card"><p class="section-title">Session Timeline</p><p class="section-sub">When each session was active throughout the day (IST)</p>', unsafe_allow_html=True)
            st.plotly_chart(session_timeline_chart(sessions), use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)
        with dn_col:
            st.markdown('<div class="section-card"><p class="section-title">Day Split</p><p class="section-sub">Download vs Upload for the day</p>', unsafe_allow_html=True)
            if day_tot > 0:
                st.plotly_chart(donut_chart(day_dl, day_ul), use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        # Per-session detail table
        st.markdown('<div class="section-card"><p class="section-title">Session Details</p><p class="section-sub">Each individual session logged on this day</p>', unsafe_allow_html=True)

        for i, s in enumerate(sessions):
            login_raw  = s.get("loginTime")
            logout_raw = s.get("logoutTime")
            is_active  = not bool(logout_raw)

            login_ist  = login_raw.replace(tzinfo=datetime.timezone.utc) + datetime.timedelta(hours=5, minutes=30) if login_raw else None
            logout_ist = logout_raw.replace(tzinfo=datetime.timezone.utc) + datetime.timedelta(hours=5, minutes=30) if logout_raw else None

            dur_secs = s.get("sessionSeconds", 0)
            if dur_secs >= 3600:
                dur_str = f"{dur_secs//3600}h {(dur_secs%3600)//60}m"
            elif dur_secs >= 60:
                dur_str = f"{dur_secs//60}m"
            else:
                dur_str = f"{dur_secs}s" if dur_secs else "—"

            badge = '<span class="badge-active">● Active</span>' if is_active else '<span class="badge-done">Ended</span>'
            login_str  = login_ist.strftime("%I:%M:%S %p")  if login_ist  else "—"
            logout_str = logout_ist.strftime("%I:%M:%S %p") if logout_ist else "Still Active"

            st.markdown(f"""
            <div class="session-row-grid">
              <div>
                <div class="session-label">Session {i+1} &nbsp; {badge}</div>
                <div class="session-val" style="color:{TOT_COLOR if is_active else '#e2e8f0'}">{s.get('planName','—')}</div>
              </div>
              <div>
                <div class="session-label">Login → Logout</div>
                <div class="session-val" style="font-size:0.78rem">{login_str} → {logout_str}</div>
              </div>
              <div>
                <div class="session-label">Duration</div>
                <div class="session-val">{dur_str}</div>
              </div>
              <div>
                <div class="session-label">↓ Download</div>
                <div class="session-val" style="color:{DL_COLOR}">{fmt_mb(s.get('downloadMB',0))}</div>
              </div>
              <div>
                <div class="session-label">↑ Upload</div>
                <div class="session-val" style="color:{UL_COLOR}">{fmt_mb(s.get('uploadMB',0))}</div>
              </div>
            </div>""", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  TAB 3 — YEAR VIEW
# ══════════════════════════════════════════════
with tab_year:
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Determine available year range from DB
    earliest_date, latest_date = fetch_db_date_bounds()
    min_year = earliest_date.year
    max_year = latest_date.year
    available_years = list(range(max_year, min_year - 1, -1))  # newest first

    yc1, yc2 = st.columns([1, 3])
    with yc1:
        selected_year = st.selectbox(
            "📆 Select Year",
            options=available_years,
            index=0,
            key="year_picker",
            help=f"Data available from {earliest_date.strftime('%b %Y')} to {latest_date.strftime('%b %Y')}"
        )
    with yc2:
        is_current_year = (selected_year == max_year)
        is_first_year   = (selected_year == min_year)
        note = ""
        if is_current_year and is_first_year:
            note = f"Only year with data · {earliest_date.strftime('%d %b')} → {latest_date.strftime('%d %b %Y')}"
        elif is_current_year:
            note = f"Current year · data up to {latest_date.strftime('%d %b %Y')}"
        elif is_first_year:
            note = f"First year of data · starting {earliest_date.strftime('%d %b %Y')}"
        st.markdown(f"""
        <div style="padding-top:14px">
          <span style="color:#38bdf8;font-weight:800;font-size:2rem;letter-spacing:-1px">{selected_year}</span>
          {"<span style='margin-left:12px;background:rgba(52,211,153,0.15);color:#34d399;border:1px solid rgba(52,211,153,0.35);font-size:0.68rem;font-weight:700;padding:2px 10px;border-radius:999px'>CURRENT YEAR</span>" if is_current_year else ""}
          {"<span style='margin-left:12px;background:rgba(167,139,250,0.15);color:#a78bfa;border:1px solid rgba(167,139,250,0.3);font-size:0.68rem;font-weight:700;padding:2px 10px;border-radius:999px'>FIRST YEAR</span>" if is_first_year and not is_current_year else ""}
          <div style="color:#64748b;font-size:0.78rem;margin-top:4px">{note}</div>
        </div>""", unsafe_allow_html=True)

    year_summary, monthly = fetch_annual(selected_year)

    if not monthly:
        st.info(f"No data found for **{selected_year}**. Try syncing first.")
    else:
        yr_dl   = year_summary.get("downloadMB", 0)
        yr_ul   = year_summary.get("uploadMB",   0)
        yr_tot  = yr_dl + yr_ul
        yr_sess = year_summary.get("sessions", 0)
        n_months = len(monthly)

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        metrics_row([
            ("Annual Download",  fmt_mb(yr_dl),   f"{(yr_dl/yr_tot*100):.1f}% of total" if yr_tot else "—", ""),
            ("Annual Upload",    fmt_mb(yr_ul),   f"{(yr_ul/yr_tot*100):.1f}% of total" if yr_tot else "—", "violet"),
            ("Annual Total",     fmt_mb(yr_tot),  f"across {n_months} month(s)", "highlight"),
            ("Sessions",         str(yr_sess),    f"avg {yr_sess//n_months if n_months else 0}/month", "green"),
        ])

        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

        # Monthly area chart + donut
        ya1, ya2 = st.columns([3, 1])
        with ya1:
            st.markdown('<div class="section-card"><p class="section-title">Monthly Traffic</p><p class="section-sub">GB transferred per month across the selected year</p>', unsafe_allow_html=True)
            st.plotly_chart(monthly_area_chart(monthly), use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)
        with ya2:
            st.markdown('<div class="section-card"><p class="section-title">Annual Split</p><p class="section-sub">Download vs Upload for the year</p>', unsafe_allow_html=True)
            if yr_tot > 0:
                st.plotly_chart(donut_chart(yr_dl, yr_ul), use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        # Monthly bar chart
        st.markdown('<div class="section-card"><p class="section-title">Download vs Upload – Monthly Comparison</p><p class="section-sub">Side-by-side monthly breakdown to spot heavy months</p>', unsafe_allow_html=True)
        st.plotly_chart(monthly_bar_chart(monthly), use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        # Month-by-month table
        MONTH_NAMES = ["January","February","March","April","May","June",
                       "July","August","September","October","November","December"]

        st.markdown('<div class="section-card"><p class="section-title">Month-by-Month Breakdown</p><p class="section-sub">Detailed figures for every month in the selected year</p>', unsafe_allow_html=True)

        # Header row
        st.markdown("""
        <div class="session-row-grid" style="border-bottom:2px solid #334155">
          <div class="metric-label">Month</div>
          <div class="metric-label">↓ Download</div>
          <div class="metric-label">↑ Upload</div>
          <div class="metric-label">Combined</div>
          <div class="metric-label">Sessions</div>
        </div>""", unsafe_allow_html=True)

        for row in monthly:
            month_key = row["_id"]   # "YYYY-MM"
            m_num = int(month_key.split("-")[1])
            m_name = MONTH_NAMES[m_num - 1]
            dl  = row.get("downloadMB", 0)
            ul  = row.get("uploadMB",   0)
            tot = dl + ul
            ses = row.get("sessions", 0)
            pct = f"{(dl/tot*100):.0f}% DL" if tot else ""
            is_peak = (tot == max(r.get("downloadMB",0)+r.get("uploadMB",0) for r in monthly))
            peak_badge = "<span style='background:rgba(251,191,36,0.15);color:#fbbf24;border:1px solid rgba(251,191,36,0.3);font-size:0.62rem;font-weight:700;padding:1px 7px;border-radius:999px;margin-left:6px'>PEAK</span>" if is_peak else ""
            st.markdown(f"""
            <div class="session-row-grid">
              <div>
                <div class="session-val">{m_name}{peak_badge}</div>
                <div class="metric-label">{month_key}</div>
              </div>
              <div><div class="session-val" style="color:{DL_COLOR}">{fmt_mb(dl)}</div></div>
              <div><div class="session-val" style="color:{UL_COLOR}">{fmt_mb(ul)}</div></div>
              <div>
                <div class="session-val">{fmt_mb(tot)}</div>
                <div class="metric-label">{pct}</div>
              </div>
              <div><div class="session-val">{ses}</div></div>
            </div>""", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  TAB 4 — RAW DATA
# ══════════════════════════════════════════════
with tab_data:
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    raw_docs = fetch_raw_sessions(1000)

    if not raw_docs:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.info("No records found in database.")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        # ── Safe datetime helper (avoids tz-naive crash) ───
        def to_ist_str(val):
            if val is None: return "—"
            try:
                if hasattr(val, "tzinfo") and val.tzinfo is None:
                    val = val.replace(tzinfo=datetime.timezone.utc)
                return val.astimezone(IST).strftime("%d %b %Y  %I:%M %p")
            except Exception:
                return str(val)

        def fmt_duration(secs):
            if not secs: return "—"
            h, rem = divmod(int(secs), 3600)
            m = rem // 60
            if h: return f"{h}h {m:02d}m"
            return f"{m}m" if m else "<1m"

        # ── Build rows ─────────────────────────────────────
        all_rows = []
        for doc in raw_docs:
            dl  = round(doc.get("downloadMB",  0), 2)
            ul  = round(doc.get("uploadMB",    0), 2)
            all_rows.append({
                "Plan":         doc.get("planName", "—"),
                "Login (IST)":  to_ist_str(doc.get("loginTime")),
                "Logout (IST)": to_ist_str(doc.get("logoutTime")),
                "Duration":     fmt_duration(doc.get("sessionSeconds", 0)),
                "Download (MB)": dl,
                "Upload (MB)":  ul,
                "Total (MB)":   round(dl + ul, 2),
            })

        df_all = pd.DataFrame(all_rows)

        # ── Header + controls ──────────────────────────────
        st.markdown('<div class="section-card">', unsafe_allow_html=True)

        hc1, hc2 = st.columns([3, 1])
        with hc1:
            st.markdown('<p class="section-title">Session Records</p>'
                        '<p class="section-sub">All stored sessions from MongoDB · newest first</p>',
                        unsafe_allow_html=True)
        with hc2:
            st.markdown(
                f"<div style='padding-top:8px;text-align:right;"
                f"color:#38bdf8;font-size:0.95rem;font-weight:700'>"
                f"{len(raw_docs):,} sessions</div>",
                unsafe_allow_html=True
            )

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

        cc1, cc2 = st.columns([3, 1])
        with cc1:
            search_q = st.text_input(
                "", placeholder="🔍  Filter by plan, date, or any value…",
                key="raw_search", label_visibility="collapsed"
            )
        with cc2:
            per_page = st.selectbox(
                "Rows to show", [25, 50, 100, 250, "All"],
                index=0, key="raw_per_page"
            )

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # ── Filter ─────────────────────────────────────────
        df_view = df_all.copy()
        if search_q:
            mask = df_view.apply(
                lambda col: col.astype(str).str.contains(search_q, case=False, na=False)
            ).any(axis=1)
            df_view = df_view[mask]

        total_filtered = len(df_view)

        if per_page != "All":
            df_view = df_view.head(int(per_page))

        max_tot = float(df_view["Total (MB)"].max()) if not df_view.empty else 1.0

        # ── Dataframe with rich column config ──────────────
        st.dataframe(
            df_view,
            use_container_width=True,
            hide_index=True,
            height=min(52 * (len(df_view) + 1) + 4, 600),
            column_config={
                "Plan": st.column_config.TextColumn(
                    "📋 Plan", width="small"
                ),
                "Login (IST)": st.column_config.TextColumn(
                    "🔓 Login (IST)", width="medium"
                ),
                "Logout (IST)": st.column_config.TextColumn(
                    "🔒 Logout (IST)", width="medium"
                ),
                "Duration": st.column_config.TextColumn(
                    "⏱ Duration", width="small"
                ),
                "Download (MB)": st.column_config.NumberColumn(
                    "⬇ Download", format="%.2f MB", width="small"
                ),
                "Upload (MB)": st.column_config.NumberColumn(
                    "⬆ Upload", format="%.2f MB", width="small"
                ),
                "Total (MB)": st.column_config.ProgressColumn(
                    "📊 Total Usage",
                    format="%.0f MB",
                    min_value=0,
                    max_value=max_tot,
                    width="medium",
                ),
            }
        )

        # ── Footer count ───────────────────────────────────
        shown = len(df_view)
        if per_page != "All" and total_filtered > shown:
            st.markdown(
                f"<div style='color:#64748b;font-size:0.75rem;padding:6px 2px'>"
                f"Showing <b style='color:#94a3b8'>{shown:,}</b> of "
                f"<b style='color:#94a3b8'>{total_filtered:,}</b> matching sessions"
                f"{'  ·  increase row count to see more' if total_filtered > shown else ''}."
                f"</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div style='color:#64748b;font-size:0.75rem;padding:6px 2px'>"
                f"Showing all <b style='color:#94a3b8'>{shown:,}</b>"
                f"{' matching' if search_q else ''} sessions.</div>",
                unsafe_allow_html=True
            )

        st.markdown("</div>", unsafe_allow_html=True)
