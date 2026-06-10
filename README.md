# Microgrid Advanced Support Dashboard ⚡

An interactive analytics dashboard for Schneider Electric's **Microgrid Advanced Support team**. It ingests a raw CRM export from Salesforce and produces a live, filterable visual dashboard — tracking case volumes, resolution times, SLA compliance, and team efficiency across L2, L3, and L4 support tiers.

---

## Table of Contents

1. [What Problem Does It Solve?](#what-problem-does-it-solve)
2. [Dashboard Overview](#dashboard-overview)
3. [How to Run](#how-to-run)
4. [Updating Data](#updating-data)
5. [Project Structure](#project-structure)
6. [Code Walkthrough](#code-walkthrough)
7. [Key Business Logic](#key-business-logic)
8. [Tech Stack](#tech-stack)
9. [Deploying Online](#deploying-online)

---

## What Problem Does It Solve?

The Advanced Support team manages cases across L2, L3, and L4 tiers spanning multiple countries (NAM & IEC regions). Without this tool, understanding how many cases are open, which are overdue, and how the team is performing over time means manually navigating raw Salesforce exports. This dashboard makes that instant and visual — with live filters and no IT setup needed.

---

## Dashboard Overview

### KPI Strip *(top of the page)*
Five headline numbers — countries covered, total cases, cases closed, average turn-around time, and pending cases. Updates live with sidebar filters.

### Section 1 — Cases Volume, Resolution & Efficiency

| Chart | What it shows |
|---|---|
| **Monthly Case Volume** | Line chart of cases opened vs closed per month |
| **Pending Cases by Level** | Donut chart splitting pending cases across L2/L3/L4 |
| **Case Resolution by Level** | Pie chart of which tier is closing what share |
| **TAT Distribution** | Horizontal bar chart of resolution time buckets (1–10d, 10–20d, etc.) |
| **Quarterly 2-Week Closure Rate** | % of cases resolved within 14 days, tracked per quarter |

### Section 2 — L2 Team Deep-Dive

| Chart | What it shows |
|---|---|
| **Overall Case Volume – L2** | Bar chart: received, closed, answered, in-progress |
| **Case Status – Latest Month** | Status breakdown for cases opened in the most recent month |
| **Category Breakdown** | Donut of case types (Troubleshooting, Install/Setup, Digital Tool, etc.) |
| **Volume by Country** | Top 10 countries by case count |
| **Closed Cases Ageing** | How old closed L2 cases were at resolution |
| **Monthly Volume Trend – L2** | Created vs resolved per month for L2 only |

### Section 3 — Priority Queue

A live sortable table of all **open/in-progress cases**, ranked by Priority Score. Each row shows age, days since last update, and an SLA status flag:

- 🟡 **Fresh** — within the Fresh threshold
- 🟠 **Approaching SLA** — nearing the limit
- 🔴 **Overdue** — past the overdue threshold

All three thresholds are configurable from the sidebar.

---

## How to Run

### Prerequisites
Python 3.8 or higher.

### 1. Install dependencies
```bash
pip install streamlit pandas plotly numpy
```

### 2. Add your data
Place your Salesforce CRM export (CSV) at:
```
data/input.csv
```

### 3. Launch
```bash
streamlit run src/app.py
```

Opens automatically in your browser at `http://localhost:8501`.

---

## Updating Data

No code changes needed. Replace `data/input.csv` with a fresh Salesforce export and rerun the app — all charts update automatically.

**Expected columns** (standard Salesforce export):

```
Case Number, Subject, Status, CC Team, POC Country, Category,
Date/Time Opened, Date/Time Closed, Edit Date
```

---

## Project Structure

```
Microgrid_Smart_Dashboard/
│
├── data/
│   ├── input.csv                  ← Salesforce CRM export (your data)
│   └── schneider_logo.jpeg
│
├── src/
│   ├── app.py                     ← Main app: UI layout, charts, filters
│   └── preprocess.py              ← Data cleaning and feature engineering
│
└── README.md
```

---

## Code Walkthrough

The app is split into two files with clear responsibilities.

---

### `src/preprocess.py` — Data Pipeline

This file contains a single function `preprocess(df, year_filter, level_filter)` that takes the raw CSV and returns three DataFrames:

| Return value | What it contains |
|---|---|
| `df` | Filtered and enriched data (respects year + level filters) |
| `df_full` | Full enriched data with no filters applied (used for cross-level charts) |
| `stale_df` | Subset of filtered open cases that haven't been updated in >4 days |

**What it does step by step:**

```
1. Date parsing
   ─ Converts Date/Time Opened, Date/Time Closed, Edit Date to proper datetime objects
   ─ Handles mixed date formats (dayfirst=True for DD/MM/YYYY)

2. Level mapping
   ─ Reads the "CC Team" column and maps to L2 / L3 / L4
   ─ Rule: "L4" in name → L4 Team, "L3" → L3 Team, else → L2 Team

3. Status normalisation
   ─ Groups raw Salesforce statuses into 4 clean categories:
     Closed, Answer Provided, In Progress, Open

4. Time dimensions
   ─ Extracts Year, Month, Quarter, MonthPeriod from the opened date
   ─ Used to power the monthly and quarterly charts

5. TAT (Turn-Around Time)
   ─ TAT_days = Date Closed − Date Opened (only for closed cases)
   ─ Bucketed into: 1-10d, 10-20d, 20-40d, 40-60d, >60d

6. Case Aging
   ─ Age_days = Today − Date Opened (for all cases)
   ─ Bucketed into: <2d, 2-10d, 11-30d, 31-60d, >60d

7. "Closed in 2 Weeks" flag
   ─ Boolean: True if TAT_days ≤ 14

8. Staleness
   ─ Days Since Update = Today − Edit Date
   ─ Stale = True if Days Since Update > 4

9. Priority Score
   ─ Numeric score for open cases used to rank the Priority Queue
   ─ +Age_days/10 (capped at 30) for age
   ─ +15 if not updated in >7 days
   ─ +15 more if not updated in >14 days
   ─ Labelled: Low / Medium / High
```

---

### `src/app.py` — Dashboard UI

This file handles everything the user sees. It's structured in sequential blocks:

```
1. Page config & CSS
   ─ Sets up the Streamlit page (title, layout, icon)
   ─ Injects custom CSS for the header, KPI cards, section headers,
     priority badges, sidebar styling, and logo blending

2. Colour palette & chart defaults
   ─ Defines a shared set of hex colours and a base chart layout
     (transparent backgrounds, consistent font/margins)
   ─ Keeps all charts visually consistent without repeating settings

3. Data load
   ─ Reads input.csv once and caches it (@st.cache_data)
   ─ Caching means the file is only read on first load, not on every
     user interaction — keeps the app fast

4. Sidebar
   ─ Renders the Schneider logo + MICROGRID title
   ─ Year selectbox (derived from actual dates in the data)
   ─ Support Level selectbox (L2 / L3 / L4 / All)
   ─ SLA Aging thresholds (Fresh / Approaching / Overdue — all configurable)

5. Preprocessing call
   ─ Calls preprocess() with the selected filters
   ─ Also derives the L2-only subset (df_l2) from df_full

6. KPI row
   ─ Calculates 5 headline metrics from the filtered DataFrame
   ─ Renders them as styled HTML cards in a 5-column grid

7. Charts — Rows 1–4
   ─ Each chart is a self-contained Plotly figure
   ─ Figures are placed in st.columns() for side-by-side layout
   ─ All use the shared base_layout() helper for consistent styling

8. Priority Queue
   ─ Filters to open/in-progress cases
   ─ Fills in missing Age_days for cases where the field wasn't computed
   ─ Sorts by Priority Score (highest first), then Age_days
   ─ Renders as a Streamlit dataframe with column formatting
   ─ tat_flag() assigns the SLA emoji label based on configurable thresholds
```

---

## Key Business Logic

| Rule | Detail |
|---|---|
| **Level assignment** | Based on `CC Team` field — anything without "L3" or "L4" defaults to L2 |
| **TAT** | Only computed for closed cases; open cases use Age_days instead |
| **Priority Score** | Combines case age and update staleness into a single urgency number |
| **SLA flags** | Fresh / Approaching / Overdue thresholds are user-configurable at runtime |
| **Stale threshold** | Hard-coded at >4 days since last CRM edit |
| **Category grouping** | Small slices (<3% of total) are merged into "Others" in the L2 category donut |

---

## Tech Stack

| Tool | Version | Role |
|---|---|---|
| [Python](https://python.org) | 3.8+ | Core language |
| [Streamlit](https://streamlit.io) | Latest | Web UI — no HTML/JS needed |
| [Plotly](https://plotly.com/python) | Latest | Interactive charts |
| [Pandas](https://pandas.pydata.org) | Latest | Data wrangling |
| [NumPy](https://numpy.org) | Latest | Numeric operations |

---

## Deploying Online

The app can be hosted for free on [Streamlit Community Cloud](https://streamlit.io/cloud):

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) and log in with GitHub
3. Select this repo → set main file path to `src/app.py`
4. Click **Deploy** — a shareable URL is generated automatically

> **Data privacy note:** If `input.csv` contains sensitive customer data, use a **private** GitHub repo. Streamlit Community Cloud supports private repos on free accounts.

The **Deploy** button in the top-right of the running app is a shortcut to this same flow.


## Run the app

python3 -m streamlit run src/app.py

---

*Built for Schneider Electric · Microgrid Advanced Support · CRM Analytics*
