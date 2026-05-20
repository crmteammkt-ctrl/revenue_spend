import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ==================================================
# LOAD DATA
# ==================================================

files = list(
    Path("data").glob("*.parquet")
)

df = pd.concat(
    [
        pd.read_parquet(f)
        for f in files
    ],
    ignore_index=True
)

df["date"] = pd.to_datetime(
    df["date"]
)

# ==================================================
# SIDEBAR
# ==================================================

st.sidebar.title("FILTER")

date_range = st.sidebar.date_input(
    "Date Range",
    [
        df["date"].min(),
        df["date"].max()
    ]
)

campaign_filter = st.sidebar.multiselect(
    "Campaign",
    sorted(df["campaign_name"].dropna().unique())
)

channel_filter = st.sidebar.multiselect(
    "Channel",
    sorted(df["channel"].dropna().unique())
)

splv1_filter = st.sidebar.multiselect(
    "SPLV1",
    sorted(df["splv1"].dropna().unique())
)

group_by = st.sidebar.selectbox(
    "Group By",
    [
        "Day",
        "Week",
        "Month",
        "Quarter",
        "Year"
    ]
)

# ==================================================
# FILTER DATA
# ==================================================

mask = (
    (df["date"] >= pd.to_datetime(date_range[0]))
    &
    (df["date"] <= pd.to_datetime(date_range[1]))
)

filtered = df.loc[mask].copy()

if campaign_filter:
    filtered = filtered[
        filtered["campaign_name"].isin(
            campaign_filter
        )
    ]

if channel_filter:
    filtered = filtered[
        filtered["channel"].isin(
            channel_filter
        )
    ]

if splv1_filter:
    filtered = filtered[
        filtered["splv1"].isin(
            splv1_filter
        )
    ]

# ==================================================
# GROUP TIME
# ==================================================

if group_by == "Day":
    filtered["period"] = filtered["date"]

elif group_by == "Week":
    filtered["period"] = (
        filtered["date"]
        .dt.to_period("W")
        .astype(str)
    )

elif group_by == "Month":
    filtered["period"] = (
        filtered["date"]
        .dt.to_period("M")
        .astype(str)
    )

elif group_by == "Quarter":
    filtered["period"] = (
        filtered["date"]
        .dt.to_period("Q")
        .astype(str)
    )

elif group_by == "Year":
    filtered["period"] = (
        filtered["date"]
        .dt.year
        .astype(str)
    )

# ==================================================
# KPI
# ==================================================

total_revenue = filtered[
    "attributed_revenue"
].sum()

total_spend = filtered[
    "spend"
].sum()

avg_roas = (
    total_revenue / total_spend
    if total_spend != 0
    else 0
)

col1, col2, col3 = st.columns(3)

col1.metric(
    "Revenue",
    f"{total_revenue:,.0f}"
)

col2.metric(
    "Spend",
    f"{total_spend:,.0f}"
)

col3.metric(
    "ROAS",
    f"{avg_roas:.2f}"
)

# ==================================================
# TREND
# ==================================================

trend = (
    filtered.groupby("period")
    .agg(
        revenue=(
            "attributed_revenue",
            "sum"
        ),
        spend=(
            "spend",
            "sum"
        )
    )
    .reset_index()
)

fig = px.line(
    trend,
    x="period",
    y=[
        "revenue",
        "spend"
    ],
    title="Revenue vs Spend"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# ==================================================
# TOP CAMPAIGN
# ==================================================

st.subheader("Top Campaign")

campaign_table = (
    filtered.groupby(
        "campaign_name"
    )
    .agg(
        revenue=(
            "attributed_revenue",
            "sum"
        ),
        spend=(
            "spend",
            "sum"
        ),
        clicks=(
            "clicks",
            "sum"
        )
    )
    .reset_index()
)

campaign_table["roas"] = (
    campaign_table["revenue"]
    / campaign_table["spend"]
)

campaign_table = campaign_table.sort_values(
    "revenue",
    ascending=False
)

st.dataframe(campaign_table)

# ==================================================
# TOP PRODUCT
# ==================================================

st.subheader("Top Product")

product_table = (
    filtered.groupby(
        "splv2"
    )
    .agg(
        revenue=(
            "attributed_revenue",
            "sum"
        ),
        spend=(
            "spend",
            "sum"
        )
    )
    .reset_index()
)

product_table["roas"] = (
    product_table["revenue"]
    / product_table["spend"]
)

product_table = product_table.sort_values(
    "revenue",
    ascending=False
)

st.dataframe(product_table)