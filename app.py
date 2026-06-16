import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Marketing Performance Dashboard",
    layout="wide"
)

DATA_DIR = Path("data")

@st.cache_data
def read_parquet(name):
    return pd.read_parquet(DATA_DIR / f"{name}.parquet")

sales_daily = read_parquet("sales_daily")
sales_product = read_parquet("sales_product")
sales_region = read_parquet("sales_region")
sales_province = read_parquet("sales_province")
sales_store = read_parquet("sales_store")

marketing_daily = read_parquet("marketing_daily")
marketing_channel = read_parquet("marketing_channel")
marketing_campaign = read_parquet("marketing_campaign")

sales_daily["ngay"] = pd.to_datetime(sales_daily["ngay"])
marketing_daily["ngay"] = pd.to_datetime(marketing_daily["ngay"])

st.title("📊 Marketing Performance Dashboard")

min_date = min(sales_daily["ngay"].min(), marketing_daily["ngay"].min()).date()
max_date = max(sales_daily["ngay"].max(), marketing_daily["ngay"].max()).date()

c1, c2 = st.columns(2)

with c1:
    date_range = st.date_input(
        "Khoảng thời gian",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

with c2:
    group_by = st.selectbox(
        "Nhóm theo thời gian",
        ["Ngày", "Tuần", "Tháng", "Quý", "Năm"]
    )

if len(date_range) == 2:
    start_date = pd.Timestamp(date_range[0])
    end_date = pd.Timestamp(date_range[1])

    sales_daily = sales_daily[
        (sales_daily["ngay"] >= start_date) &
        (sales_daily["ngay"] <= end_date)
    ]

    marketing_daily = marketing_daily[
        (marketing_daily["ngay"] >= start_date) &
        (marketing_daily["ngay"] <= end_date)
    ]

def add_period(df):
    df = df.copy()

    if group_by == "Ngày":
        df["period"] = df["ngay"]
    elif group_by == "Tuần":
        df["period"] = df["ngay"].dt.to_period("W").dt.start_time
    elif group_by == "Tháng":
        df["period"] = df["ngay"].dt.to_period("M").dt.start_time
    elif group_by == "Quý":
        df["period"] = df["ngay"].dt.to_period("Q").dt.start_time
    else:
        df["period"] = df["ngay"].dt.to_period("Y").dt.start_time

    return df

sales_daily = add_period(sales_daily)
marketing_daily = add_period(marketing_daily)

sales_period = sales_daily.groupby("period", as_index=False).agg(
    revenue=("revenue", "sum"),
    orders=("orders", "sum"),
    quantity=("quantity", "sum")
)

marketing_period = marketing_daily.groupby("period", as_index=False).agg(
    marketing_cost=("marketing_cost", "sum")
)

df = sales_period.merge(marketing_period, on="period", how="left")
df["marketing_cost"] = df["marketing_cost"].fillna(0)

total_revenue = df["revenue"].sum()
total_cost = df["marketing_cost"].sum()
total_orders = df["orders"].sum()
total_quantity = df["quantity"].sum()

roas = total_revenue / total_cost if total_cost else 0
roi = (total_revenue - total_cost) / total_cost if total_cost else 0
marketing_rate = total_cost / total_revenue if total_revenue else 0

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Tổng doanh thu", f"{total_revenue:,.0f} đ")
k2.metric("Chi phí marketing", f"{total_cost:,.0f} đ")
k3.metric("ROAS", f"{roas:,.2f}x")
k4.metric("ROI", f"{roi:.0%}")
k5.metric("Marketing / Revenue", f"{marketing_rate:.2%}")

k6, k7, k8 = st.columns(3)

k6.metric("Số hóa đơn", f"{total_orders:,.0f}")
k7.metric("Số lượng bán", f"{total_quantity:,.0f}")
k8.metric("AOV", f"{total_revenue / total_orders:,.0f} đ" if total_orders else "0 đ")

st.divider()

c1, c2 = st.columns(2)

with c1:
    fig = px.line(
        df,
        x="period",
        y="revenue",
        title="Doanh thu theo thời gian"
    )
    st.plotly_chart(fig, use_container_width=True)

with c2:
    df["roas"] = df["revenue"] / df["marketing_cost"].replace(0, pd.NA)
    fig = px.line(
        df,
        x="period",
        y="roas",
        title="ROAS theo thời gian"
    )
    st.plotly_chart(fig, use_container_width=True)

c3, c4 = st.columns(2)

with c3:
    fig = px.pie(
        marketing_channel,
        names="kenh",
        values="marketing_cost",
        title="Cơ cấu chi phí Marketing theo kênh"
    )
    st.plotly_chart(fig, use_container_width=True)

with c4:
    top_campaign = marketing_campaign.sort_values(
        "marketing_cost",
        ascending=False
    ).head(10)

    fig = px.bar(
        top_campaign,
        x="marketing_cost",
        y="campaign",
        orientation="h",
        title="Top 10 Campaign theo chi phí"
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)

c5, c6 = st.columns(2)

with c5:
    top_product = sales_product.sort_values(
        "revenue",
        ascending=False
    ).head(10)

    fig = px.bar(
        top_product,
        x="revenue",
        y="ten_hang",
        orientation="h",
        title="Top 10 sản phẩm theo doanh thu"
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)

with c6:
    region_df = sales_region.sort_values("revenue", ascending=False)

    fig = px.bar(
        region_df,
        x="region",
        y="revenue",
        title="Doanh thu theo Region"
    )
    st.plotly_chart(fig, use_container_width=True)

c7, c8 = st.columns(2)

with c7:
    province_df = sales_province.sort_values(
        "revenue",
        ascending=False
    ).head(10)

    fig = px.bar(
        province_df,
        x="revenue",
        y="tinh_tp",
        orientation="h",
        title="Top 10 tỉnh/thành theo doanh thu"
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)

with c8:
    store_df = sales_store.sort_values(
        "revenue",
        ascending=False
    ).head(10)

    fig = px.bar(
        store_df,
        x="revenue",
        y="diem_mua_hang",
        orientation="h",
        title="Top 10 điểm mua hàng theo doanh thu"
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)