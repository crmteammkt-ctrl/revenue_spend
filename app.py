import streamlit as st
import pandas as pd
import plotly.express as px

# =========================
# PAGE
# =========================
st.set_page_config(
    page_title="Revenue Dashboard",
    layout="wide"
)

st.title("Revenue Dashboard")

# =========================
# LOAD DATA
# =========================
df = pd.read_parquet(
    "data/ads_vs_sales_2026-03.parquet"
)

# convert date
df["date"] = pd.to_datetime(df["date"])

# =========================
# SIDEBAR
# =========================
st.sidebar.header("Filter")

# Date filter
date_range = st.sidebar.date_input(
    "Date Range",
    value=(
        df["date"].min().date(),
        df["date"].max().date()
    )
)

start_date = pd.to_datetime(date_range[0])
end_date = pd.to_datetime(date_range[1])

# Filter dataframe
filtered_df = df[
    (df["date"] >= start_date) &
    (df["date"] <= end_date)
].copy()

# =========================
# KPI
# =========================
col1, col2, col3 = st.columns(3)

col1.metric(
    "Revenue",
    f"{filtered_df['revenue'].sum():,.0f}"
)

col2.metric(
    "Spend",
    f"{filtered_df['spend'].sum():,.0f}"
)

roas = (
    filtered_df["revenue"].sum() /
    filtered_df["spend"].sum()
    if filtered_df["spend"].sum() != 0
    else 0
)

col3.metric(
    "ROAS",
    f"{roas:.2f}"
)

# =========================
# CHART
# =========================
fig = px.line(
    filtered_df,
    x="date",
    y=["revenue", "spend"],
    title="Revenue vs Spend"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# =========================
# DATA TABLE
# =========================
st.subheader("Dataset")

st.dataframe(
    filtered_df,
    use_container_width=True
)