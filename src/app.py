
import os
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from preprocess import preprocess

# ══════════════════════════════════════════════════════════════════════════════
# Page config
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Microgrid Adv Support Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ══════════════════════════════════════════════════════════════════════════════
# Styling
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    """
<style>
/* ── global ── */
.block-container { padding-top: 0.8rem !important; }
[data-testid="stSidebar"] { background: #EFEFEF; color: #212121 !important; }
[data-testid="stSidebar"] img { mix-blend-mode: multiply; opacity: 0.92; margin-top: -24px; }
[data-testid="stSidebar"] .microgrid-title { color: #009531 !important; }
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] .stMarkdown { color: #212121 !important; }

/* ── main header ── */
.dash-header {
    background: linear-gradient(90deg, #1B5E20 0%, #2E7D32 100%);
    padding: 14px 22px; border-radius: 8px; margin-bottom: 14px; color: white;
}
.dash-header h2 { margin: 0; font-size: 20px; font-weight: 700; color: white !important; }
.dash-header p  { margin: 3px 0 0; font-size: 12px; color: #C8E6C9; }

/* ── KPI cards ── */
.kpi-row { display: flex; gap: 12px; margin-bottom: 16px; }
.kpi-card {
    flex: 1; background: white; border: 1px solid #E0E0E0;
    border-top: 4px solid #2E7D32; border-radius: 8px;
    padding: 12px 14px; text-align: center;
}
.kpi-val   { font-size: 28px; font-weight: 800; color: #1B5E20; line-height: 1.1; }
.kpi-lbl   { font-size: 10px; color: #757575; text-transform: uppercase;
             letter-spacing: 0.4px; margin-top: 4px; }
.kpi-sub   { font-size: 10px; color: #9E9E9E; margin-top: 2px; }

/* ── section headers ── */
.sec-hdr {
    background: #F1F8E9; border-left: 4px solid #2E7D32;
    padding: 7px 14px; margin: 18px 0 10px;
    border-radius: 0 6px 6px 0; font-weight: 600;
    color: #1B5E20; font-size: 14px;
}

/* ── priority table badges ── */
.badge-High   { background:#FFEBEE; color:#C62828; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600; }
.badge-Medium { background:#FFF8E1; color:#F57F17; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600; }
.badge-Low    { background:#E8F5E9; color:#2E7D32; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600; }
</style>
""",
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════════
# Colour palette
# ══════════════════════════════════════════════════════════════════════════════
C_DARK   = "#154360"
C_MID    = "#2980B9"
C_LIGHT  = "#85C1E9"
C_GREEN  = "#27AE60"
C_AMBER  = "#F39C12"
C_RED    = "#E74C3C"
C_GREY   = "#BDC3C7"

PIE_3    = [C_DARK, C_MID, C_LIGHT]          # L4, L3, L2
PIE_CAT  = [C_GREEN, C_RED, C_GREY, "#9B59B6", "#E67E22"]

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=30, b=20, l=20, r=20),
    font=dict(family="Arial", size=11),
    showlegend=True,
)

# ══════════════════════════════════════════════════════════════════════════════
# Data load
# ══════════════════════════════════════════════════════════════════════════════
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "input.csv")


@st.cache_data
def load_raw():
    return pd.read_csv(DATA_PATH)


raw = load_raw()

# ══════════════════════════════════════════════════════════════════════════════
# Sidebar – filters
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    _logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "schneider_logo.jpeg")
    if os.path.exists(_logo_path):
        st.image(_logo_path, use_container_width=True)
    
    st.markdown("---")
    st.markdown("### Filters")

    # derive available years from raw dates (quick parse)
    _years = (
        pd.to_datetime(raw["Date/Time Opened"], dayfirst=True, errors="coerce")
        .dt.year.dropna().astype(int).unique()
    )
    year_opts = ["All Years"] + [str(y) for y in sorted(_years, reverse=True)]
    sel_year_str = st.selectbox("📅 Year", year_opts, index=0)
    year_filter  = None if sel_year_str == "All Years" else int(sel_year_str)

    level_filter = st.selectbox(
        "🏷️ Support Level", ["All", "L2 Team", "L3 Team", "L4 Team"]
    )

    st.markdown("---")
    st.markdown("#### SLA Aging (days)")
    sla_fresh       = st.number_input("🟡 Fresh ≤",          value=15, min_value=1, step=1)
    sla_approaching = st.number_input("🟠 Approaching SLA ≤", value=30, min_value=1, step=1)
    sla_overdue     = st.number_input("🔴 Overdue >",         value=30, min_value=1, step=1)

    st.markdown("---")
    st.caption("Advanced Support · CRM Analytics")

# ══════════════════════════════════════════════════════════════════════════════
# Preprocess
# ══════════════════════════════════════════════════════════════════════════════
df, df_full, stale_df = preprocess(
    raw.copy(),
    year_filter=year_filter,
    level_filter=level_filter if level_filter != "All" else None,
)

# L2 sub-set (always from full, then year-filtered)
df_l2 = df_full[df_full["Level"] == "L2 Team"].copy()
if year_filter:
    df_l2 = df_l2[df_l2["Year"] == year_filter]

# ══════════════════════════════════════════════════════════════════════════════
# Header
# ══════════════════════════════════════════════════════════════════════════════
period_label = sel_year_str
st.markdown(
    f"""
<div class="dash-header">
  <h2>Microgrid Adv Support – Performance Overview </h2>
  <p>Cases Volume · Resolution · Adv Team Operational Efficiency</p>
</div>
""",
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════════
# KPI row
# ══════════════════════════════════════════════════════════════════════════════
total      = len(df)
closed     = int(df["Is Closed"].sum())
countries  = int(df["POC Country"].nunique())
avg_tat    = round(df["TAT_days"].dropna().mean(), 1) if df["TAT_days"].dropna().shape[0] else 0
pending    = int((~df["Is Closed"]).sum())
answer_pct = round(
    df[df["Status"] == "Answer Provided to Customer"].shape[0] / total * 100
    if total else 0, 1
)

kpis = [
    (countries,        "Countries Covered",    "NAM & IEC"),
    (f"{total}",       "Total Cases",          f"{period_label}"),
    (closed,           "Cases Closed",         "Handled by Adv Team"),
    (f"{avg_tat} d",   "Avg. TAT",             "Closed cases"),
    (pending,          "Pending / In-Progress","Active cases"),
]

cols = st.columns(len(kpis))
for col, (val, lbl, sub) in zip(cols, kpis):
    col.markdown(
        f"""<div class="kpi-card">
              <div class="kpi-val">{val}</div>
              <div class="kpi-lbl">{lbl}</div>
              <div class="kpi-sub">{sub}</div>
            </div>""",
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# Helper – compact plotly layout
# ══════════════════════════════════════════════════════════════════════════════
def base_layout(**kwargs):
    d = dict(**CHART_LAYOUT)
    d.update(kwargs)
    return d


# ══════════════════════════════════════════════════════════════════════════════
# ROW 1  ─  Monthly Volume (wide)  +  Pending by Level (narrow)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="sec-hdr">📈 Cases Volume, Resolution and Adv Team Operational Efficiency</div>', unsafe_allow_html=True)

r1c1, r1c2 = st.columns([2, 1])

# ── Monthly Volume line chart ──────────────────────────────────────────────
with r1c1:
    st.markdown("**Monthly Case Volume**")

    # Created per month
    created_m = (
        df_full.assign(Period=df_full["Date/Time Opened"].dt.to_period("M"))
        .groupby("Period").size().reset_index(name="Open Cases")
    )
    if year_filter:
        created_m = created_m[created_m["Period"].dt.year == year_filter]

    # Closed per month (by close date)
    closed_src = df_full[df_full["Date/Time Closed"].notna()].copy()
    closed_m = (
        closed_src.assign(Period=closed_src["Date/Time Closed"].dt.to_period("M"))
        .groupby("Period").size().reset_index(name="Closed Cases")
    )
    if year_filter:
        closed_m = closed_m[closed_m["Period"].dt.year == year_filter]

    monthly = (
        created_m.merge(closed_m, on="Period", how="outer")
        .fillna(0)
        .sort_values("Period")
    )
    monthly["Period_dt"]  = monthly["Period"].dt.to_timestamp()
    monthly["Period_str"] = monthly["Period_dt"].dt.strftime("%b-%y")
    monthly["Open Cases"]   = monthly["Open Cases"].astype(int)
    monthly["Closed Cases"] = monthly["Closed Cases"].astype(int)

    fig_monthly = go.Figure()
    for series, color, dash, tpos in [
        ("Open Cases",   C_MID,   "solid", "top center"),
        ("Closed Cases", C_GREEN, "dot",   "bottom center"),
    ]:
        fig_monthly.add_trace(go.Scatter(
            x=monthly["Period_str"], y=monthly[series],
            mode="lines+markers+text",
            name=series,
            line=dict(color=color, width=2.5, dash=dash),
            marker=dict(size=7),
            text=monthly[series],
            textposition=tpos,
            textfont=dict(size=9),
            cliponaxis=False,
        ))

    fig_monthly.update_layout(
        **base_layout(height=300, legend=dict(orientation="h", y=1.12, x=0.5, xanchor="center")),
        xaxis=dict(tickangle=-45, showgrid=False, nticks=12),
        yaxis=dict(showgrid=True, gridcolor="#F0F0F0", automargin=True),
    )
    st.plotly_chart(fig_monthly, use_container_width=True)

# ── Pending by Level pie ───────────────────────────────────────────────────
with r1c2:
    st.markdown("**Pending Cases by Level**")

    pending_df = df[~df["Is Closed"]]
    level_pending = pending_df["Level"].value_counts().reset_index()
    level_pending.columns = ["Level", "Count"]

    total_pending = level_pending["Count"].sum()
    fig_pend = px.pie(
        level_pending, names="Level", values="Count",
        color_discrete_sequence=PIE_3,
        hole=0.35,
    )
    fig_pend.update_traces(
        textinfo="percent+label",
        textfont_size=11,
    )
    fig_pend.update_layout(
        **base_layout(height=280, showlegend=False),
        title=dict(text=f"<b>{total_pending} Cases</b>", x=0.5, font_size=12),
    )
    st.plotly_chart(fig_pend, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# ROW 2  ─  Resolution by Level  |  TAT Distribution  |  Q Closure %
# ══════════════════════════════════════════════════════════════════════════════
r2c1, r2c2, r2c3 = st.columns(3)

# ── Case Resolution by Level (pie) ────────────────────────────────────────
with r2c1:
    st.markdown("**Case Resolution by Level**")

    res_df = df[df["Is Closed"]]["Level"].value_counts().reset_index()
    res_df.columns = ["Level", "Count"]

    fig_res = px.pie(
        res_df, names="Level", values="Count",
        color_discrete_sequence=PIE_3,
        hole=0.0,
    )
    fig_res.update_traces(textinfo="percent+label", textfont_size=11)
    fig_res.update_layout(**base_layout(height=270, showlegend=False))
    st.plotly_chart(fig_res, use_container_width=True)

# ── TAT Distribution horizontal bar ───────────────────────────────────────
with r2c2:
    st.markdown("**Cases Turn Around Time – Days**")

    tat_order = ["1-10 Days", "10-20 Days", "20-40 Days", "40-60 Days", ">60 Days"]
    tat_counts = (
        df["TAT Bucket"].value_counts()
        .reindex(tat_order, fill_value=0)
        .reset_index()
    )
    tat_counts.columns = ["TAT Bucket", "No of Cases"]

    fig_tat = px.bar(
        tat_counts, y="TAT Bucket", x="No of Cases",
        orientation="h",
        text="No of Cases",
        color_discrete_sequence=[C_LIGHT],
    )
    fig_tat.update_traces(textposition="outside", cliponaxis=False)
    fig_tat.update_layout(
        **base_layout(height=270),
        xaxis=dict(showgrid=True, gridcolor="#F0F0F0", automargin=True),
        yaxis=dict(categoryorder="array", categoryarray=tat_order[::-1]),
    )
    st.plotly_chart(fig_tat, use_container_width=True)

# ── Case closure within 2 weeks (line, by quarter) ────────────────────────
with r2c3:
    st.markdown("**Case Closure within 2 Weeks**")

    closed_src2 = df[df["Is Closed"] & df["TAT_days"].notna()].copy()
    q_total = closed_src2.groupby("Quarter").size().rename("Total")
    q_2wk   = closed_src2[closed_src2["Closed in 2 Weeks"]].groupby("Quarter").size().rename("Within2Wks")
    q_merge = pd.concat([q_total, q_2wk], axis=1).fillna(0)
    q_merge["Pct"] = (q_merge["Within2Wks"] / q_merge["Total"] * 100).round(1)
    q_merge = q_merge.reset_index()
    q_order = ["Q1", "Q2", "Q3", "Q4"]
    q_merge = q_merge[q_merge["Quarter"].isin(q_order)]

    fig_q = go.Figure(go.Scatter(
        x=q_merge["Quarter"], y=q_merge["Pct"],
        mode="lines+markers+text",
        line=dict(color=C_GREEN, width=2.5),
        marker=dict(size=8),
        text=[f"{v}%" for v in q_merge["Pct"]],
        textposition="top center",
        textfont=dict(size=11),
        fill="tozeroy",
        fillcolor="rgba(39,174,96,0.08)",
    ))
    fig_q.update_layout(
        **base_layout(height=270),
        yaxis=dict(range=[0, 105], ticksuffix="%", showgrid=True, gridcolor="#F0F0F0"),
        xaxis=dict(categoryorder="array", categoryarray=q_order),
    )
    st.plotly_chart(fig_q, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# L2 SECTION
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="sec-hdr">🔵 L2 Team – Detailed View</div>', unsafe_allow_html=True)

# Determine the "current" month label for the status chart
if len(df_l2):
    latest_period = df_l2["MonthPeriod"].dropna().max()
    latest_label  = latest_period.strftime("%B %Y") if pd.notna(latest_period) else "Latest Month"
    df_l2_latest  = df_l2[df_l2["MonthPeriod"] == latest_period]
else:
    latest_label = "—"
    df_l2_latest = df_l2.copy()

r3c1, r3c2, r3c3 = st.columns(3)

# ── L2 Overall Case Volume (bar) ──────────────────────────────────────────
with r3c1:
    st.markdown("**Overall Case Volume – L2**")

    l2_total    = len(df_l2)
    l2_closed   = int(df_l2["Is Closed"].sum())
    l2_answer   = int((df_l2["Status"] == "Answer Provided to Customer").sum())
    l2_progress = int((df_l2["Status"] == "In Progress").sum())

    vol_df = pd.DataFrame({
        "Category": ["Total\nReceived", "Closed\n(inc. backlog)", "Answer\nProvided", "In Progress\n(inc. backlog)"],
        "Count":    [l2_total, l2_closed, l2_answer, l2_progress],
    })
    fig_vol = px.bar(
        vol_df, x="Category", y="Count",
        text="Count",
        color_discrete_sequence=[C_MID],
    )
    fig_vol.update_traces(textposition="outside", textfont_size=12, cliponaxis=False)
    fig_vol.update_layout(
        **base_layout(height=270),
        xaxis_title="",
        yaxis=dict(showgrid=True, gridcolor="#F0F0F0", automargin=True),
    )
    st.plotly_chart(fig_vol, use_container_width=True)

# ── L2 Case Status for latest month ──────────────────────────────────────
with r3c2:
    st.markdown(f"**Case Status by L2** (Opened in {latest_label})")

    status_map = {
        "Closed":                      "Closed",
        "Cancelled":                   "Closed",
        "Answer Provided to Customer": "Answer Provided",
        "In Progress":                 "In Progress",
    }
    l2_latest_status = (
        df_l2_latest["Status"].map(status_map).fillna("Open")
        .value_counts().reset_index()
    )
    l2_latest_status.columns = ["Status", "Count"]

    status_colors = {
        "Closed":          C_GREEN,
        "In Progress":     C_GREY,
        "Answer Provided": C_MID,
        "Open":            C_AMBER,
    }
    l2_latest_status["Color"] = l2_latest_status["Status"].map(status_colors).fillna(C_GREY)

    fig_stat = px.bar(
        l2_latest_status,
        y="Status", x="Count",
        orientation="h",
        text="Count",
        color="Status",
        color_discrete_map=status_colors,
    )
    fig_stat.update_traces(textposition="outside", cliponaxis=False)
    fig_stat.update_layout(
        **base_layout(height=270, showlegend=False),
        xaxis=dict(showgrid=True, gridcolor="#F0F0F0", automargin=True),
    )
    st.plotly_chart(fig_stat, use_container_width=True)

# ── L2 Category donut ─────────────────────────────────────────────────────
with r3c3:
    st.markdown("**Received Cases Category – L2**")

    # Clean category labels
    def clean_cat(c):
        c = str(c).replace("*", "").strip()
        if c.lower() == "nan" or c == "":  return None
        if "Digital" in c:      return "Digital Tool Support"
        if "Install" in c:      return "Install / Setup Support"
        if "Troubleshoot" in c: return "Troubleshooting"
        return c

    cat_df = df_l2.copy()
    cat_df["Category Clean"] = cat_df["Category"].apply(clean_cat)
    cat_df = cat_df[cat_df["Category Clean"].notna()]

    cat_counts = cat_df["Category Clean"].value_counts().reset_index()
    cat_counts.columns = ["Category", "Count"]

    # Merge slices under 3% of total into "Others"
    total_cat = cat_counts["Count"].sum()
    cat_counts["Category"] = cat_counts.apply(
        lambda r: r["Category"] if r["Count"] / total_cat >= 0.03 else "Others", axis=1
    )
    cat_counts = cat_counts.groupby("Category", as_index=False)["Count"].sum()
    cat_counts = cat_counts.sort_values("Count", ascending=False)

    fig_cat = px.pie(
        cat_counts, names="Category", values="Count",
        color_discrete_sequence=PIE_CAT,
        hole=0.4,
    )
    fig_cat.update_traces(
        textinfo="percent+label",
        textfont_size=11,
        insidetextorientation="radial",
    )
    fig_cat.update_layout(**base_layout(height=270, showlegend=False))
    st.plotly_chart(fig_cat, use_container_width=True)


# ── Row 4 ─────────────────────────────────────────────────────────────────
r4c1, r4c2, r4c3 = st.columns(3)

# ── L2 Volume by Country ──────────────────────────────────────────────────
with r4c1:
    st.markdown("**Case Volume by Country – L2**")

    country_df = (
        df_l2["POC Country"].value_counts()
        .head(10).reset_index()
    )
    country_df.columns = ["Country", "Cases"]

    fig_cty = px.bar(
        country_df, x="Cases", y="Country",
        orientation="h",
        text="Cases",
        color="Cases",
        color_continuous_scale=["#D6EAF8", C_DARK],
    )
    fig_cty.update_traces(textposition="outside", cliponaxis=False)
    fig_cty.update_layout(
        **base_layout(height=280),
        yaxis=dict(categoryorder="total ascending"),
        coloraxis_showscale=False,
        xaxis=dict(showgrid=True, gridcolor="#F0F0F0", automargin=True),
    )
    st.plotly_chart(fig_cty, use_container_width=True)

# ── L2 Closed Cases Aging ─────────────────────────────────────────────────
with r4c2:
    st.markdown("**Closed Cases Ageing – L2**")

    l2_closed_df = df_l2[df_l2["Is Closed"] & df_l2["TAT_days"].notna()].copy()
    age_order = ["<2 Days", "2-10 Days", "11-30 Days", "31-60 Days", ">60 Days"]
    age_counts = (
        l2_closed_df["Aging Bucket"].value_counts()
        .reindex(age_order, fill_value=0)
        .reset_index()
    )
    age_counts.columns = ["Bucket", "Count"]

    fig_age = px.bar(
        age_counts, x="Bucket", y="Count",
        text="Count",
        color_discrete_sequence=[C_LIGHT],
        category_orders={"Bucket": age_order},
    )
    fig_age.update_traces(textposition="outside", cliponaxis=False)
    fig_age.update_layout(
        **base_layout(height=280),
        xaxis_title="",
        yaxis=dict(showgrid=True, gridcolor="#F0F0F0", automargin=True),
    )
    st.plotly_chart(fig_age, use_container_width=True)

# ── L2 Monthly Volume trend ───────────────────────────────────────────────
with r4c3:
    st.markdown("**Monthly Case Volume – L2**")

    l2_created = (
        df_l2.assign(Period=df_l2["Date/Time Opened"].dt.to_period("M"))
        .groupby("Period").size().reset_index(name="Created")
    )
    l2_resolved = (
        df_l2[df_l2["Date/Time Closed"].notna()]
        .assign(Period=lambda x: x["Date/Time Closed"].dt.to_period("M"))
        .groupby("Period").size().reset_index(name="Resolved")
    )
    l2_monthly = (
        l2_created.merge(l2_resolved, on="Period", how="outer")
        .fillna(0).sort_values("Period")
    )
    l2_monthly["Period_dt"]  = l2_monthly["Period"].dt.to_timestamp()
    l2_monthly["Period_str"] = l2_monthly["Period_dt"].dt.strftime("%b-%y")
    l2_monthly["Created"]    = l2_monthly["Created"].astype(int)
    l2_monthly["Resolved"]   = l2_monthly["Resolved"].astype(int)

    fig_l2m = go.Figure()
    for series, color, dash, tpos in [
        ("Created",  C_MID,   "solid", "top center"),
        ("Resolved", C_GREEN, "dot",   "bottom center"),
    ]:
        fig_l2m.add_trace(go.Scatter(
            x=l2_monthly["Period_str"], y=l2_monthly[series],
            mode="lines+markers+text",
            name=series,
            line=dict(color=color, width=2.5, dash=dash),
            marker=dict(size=7),
            text=l2_monthly[series],
            textposition=tpos,
            textfont=dict(size=9),
            cliponaxis=False,
        ))

    fig_l2m.update_layout(
        **base_layout(height=300, legend=dict(orientation="h", y=1.12, x=0.5, xanchor="center")),
        xaxis=dict(tickangle=-45, showgrid=False, nticks=12),
        yaxis=dict(showgrid=True, gridcolor="#F0F0F0", automargin=True),
    )
    st.plotly_chart(fig_l2m, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PRIORITY QUEUE  ─  stale / urgent cases
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="sec-hdr">🚨 Priority Queue – Cases Needing Immediate Attention</div>', unsafe_allow_html=True)

# TAT SLA colouring
def tat_flag(days):
    if pd.isna(days):
        return "⏳ Open"
    if days <= sla_fresh:
        return "🟡 Fresh"
    if days <= sla_approaching:
        return "🟠 Approaching SLA"
    if days > sla_overdue:
        return "🔴 Overdue"
    return "🟠 Approaching SLA"

# Build display table from stale + in-progress cases
queue_df = df[~df["Is Closed"]].copy()

# Fallback: if Age_days is missing, derive from Date/Time Opened (only when no close date)
_today = pd.Timestamp.today().normalize()
_null_age = queue_df["Age_days"].isna() & queue_df["Date/Time Opened"].notna() & queue_df["Date/Time Closed"].isna()
if _null_age.any():
    queue_df.loc[_null_age, "Age_days"] = (
        _today - queue_df.loc[_null_age, "Date/Time Opened"]
    ).dt.days.clip(lower=0)

queue_df = queue_df.sort_values(["Priority Score", "Age_days"], ascending=[False, False])

display_cols = {
    "Case Number":       "Case #",
    "Subject":           "Subject",
    "CC Team":           "Team",
    "Status":            "Status",
    "Level":             "Level",
    "POC Country":       "Country",
    "Age_days":          "Age (d)",
    "Days Since Update": "Last Upd (d)",
    "Priority":          "Priority",
}

q_show = queue_df[[c for c in display_cols if c in queue_df.columns]].rename(columns=display_cols)

# SLA based on age (open cases have no TAT)
q_show["SLA Status"] = q_show["Age (d)"].apply(tat_flag)

st.dataframe(
    q_show,
    use_container_width=True,
    height=340,
    hide_index=True,
    column_config={
        "Subject":    st.column_config.TextColumn(width="large"),
        "Age (d)":    st.column_config.NumberColumn(format="%d d"),
        "Last Upd (d)": st.column_config.NumberColumn(format="%d d"),
        "SLA Status": st.column_config.TextColumn(width="medium"),
    },
)

st.caption(
    f"Showing {len(q_show)} open/in-progress cases · "
    f"Sorted by Priority Score (highest first) · "
    f"SLA thresholds: 🟡 Fresh ≤{sla_fresh}d · 🟠 Approaching ≤{sla_approaching}d · 🔴 Overdue >{sla_overdue}d"
)
