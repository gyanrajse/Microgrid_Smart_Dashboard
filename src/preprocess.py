
import pandas as pd
import numpy as np


def preprocess(df: pd.DataFrame, year_filter=None, level_filter=None):
    """
    Cleans and enriches the Salesforce CRM dump.

    Parameters
    ----------
    df           : raw DataFrame from input.csv
    year_filter  : int or None – filter by opened year
    level_filter : "L2 Team" / "L3 Team" / "L4 Team" / None

    Returns
    -------
    df_filtered  : filtered + enriched DataFrame
    df_full      : full enriched DataFrame (no filters applied)
    stale_df     : cases not updated in > 4 days (from filtered set)
    """

    # ── Date parsing ──────────────────────────────────────────────────────────
    for col in ["Date/Time Opened", "Date/Time Closed", "Edit Date"]:
        df[col] = pd.to_datetime(df[col], format="mixed", dayfirst=True, errors="coerce")

    today = pd.Timestamp.today().normalize()

    # ── Level mapping (from CC Team column) ───────────────────────────────────
    def map_level(team):
        t = str(team) if pd.notna(team) else ""
        if "L4" in t:
            return "L4 Team"
        elif "L3" in t:
            return "L3 Team"
        else:
            return "L2 Team"

    df["Level"] = df["CC Team"].apply(map_level)

    # ── Status normalisation ──────────────────────────────────────────────────
    df["Status Category"] = df["Status"].map({
        "Closed":                     "Closed",
        "Cancelled":                  "Closed",
        "Answer Provided to Customer": "Answer Provided",
        "In Progress":                "In Progress",
    }).fillna("Open")

    df["Is Closed"] = df["Status"].isin(["Closed", "Cancelled"])

    # ── Time dimensions ───────────────────────────────────────────────────────
    df["Year"]    = df["Date/Time Opened"].dt.year.astype("Int64")
    df["Month"]   = df["Date/Time Opened"].dt.month.astype("Int64")
    df["Quarter"] = df["Date/Time Opened"].dt.quarter.map(
        {1: "Q1", 2: "Q2", 3: "Q3", 4: "Q4"}
    )
    df["MonthPeriod"] = df["Date/Time Opened"].dt.to_period("M")
    df["Month_Label"] = df["Date/Time Opened"].dt.strftime("%b-%y")

    # ── TAT (Turn-Around Time, days) ──────────────────────────────────────────
    df["TAT_days"] = np.where(
        df["Date/Time Closed"].notna(),
        (df["Date/Time Closed"] - df["Date/Time Opened"]).dt.days,
        np.nan,
    )

    df["TAT Bucket"] = pd.cut(
        df["TAT_days"],
        bins=[-1, 10, 20, 40, 60, 9_999],
        labels=["1-10 Days", "10-20 Days", "20-40 Days", "40-60 Days", ">60 Days"],
    )

    # ── Case Aging ────────────────────────────────────────────────────────────
    df["Age_days"] = (today - df["Date/Time Opened"]).dt.days.clip(lower=0)

    df["Aging Bucket"] = pd.cut(
        df["Age_days"],
        bins=[-1, 2, 10, 30, 60, 9_999],
        labels=["<2 Days", "2-10 Days", "11-30 Days", "31-60 Days", ">60 Days"],
    )

    # ── Closed within 2 weeks ─────────────────────────────────────────────────
    df["Closed in 2 Weeks"] = np.where(
        df["TAT_days"].notna(),
        df["TAT_days"] <= 14,
        False,
    )

    # ── Staleness ─────────────────────────────────────────────────────────────
    df["Days Since Update"] = (today - df["Edit Date"]).dt.days.clip(lower=0)
    df["Stale"] = df["Days Since Update"] > 4

    # ── Priority Score ────────────────────────────────────────────────────────
    # Higher score = needs attention sooner
    df["Priority Score"] = 0.0
    open_mask = ~df["Is Closed"]
    df.loc[open_mask, "Priority Score"] += (
        df.loc[open_mask, "Age_days"] / 10
    ).clip(0, 30)
    df.loc[df["Days Since Update"] > 7,  "Priority Score"] += 15
    df.loc[df["Days Since Update"] > 14, "Priority Score"] += 15

    df["Priority"] = pd.cut(
        df["Priority Score"],
        bins=[-1, 5, 20, 9_999],
        labels=["Low", "Medium", "High"],
    )

    # ── Keep a clean copy of full enriched data ───────────────────────────────
    df_full = df.copy()

    # ── Apply filters ─────────────────────────────────────────────────────────
    df_filtered = df.copy()
    if year_filter:
        df_filtered = df_filtered[df_filtered["Year"] == year_filter]
    if level_filter and level_filter != "All":
        df_filtered = df_filtered[df_filtered["Level"] == level_filter]

    stale_df = (
        df_filtered[df_filtered["Stale"]]
        .sort_values(["Priority Score", "Age_days"], ascending=[False, False])
    )

    return df_filtered, df_full, stale_df
