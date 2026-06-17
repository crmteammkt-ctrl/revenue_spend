import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

st.set_page_config(
    page_title="Marketing Performance Dashboard",
    layout="wide"
)

DATA_DIR = Path("parquet_data")

@st.cache_data
def load_data():
    sales_daily = pd.read_parquet(DATA_DIR / "sales_daily.parquet")
    sales_product = pd.read_parquet(DATA_DIR / "sales_product.parquet")
    marketing_daily = pd.read_parquet(DATA_DIR / "marketing_daily.parquet")

    sales_daily["ngay"] = pd.to_datetime(sales_daily["ngay"])
    marketing_daily["ngay"] = pd.to_datetime(marketing_daily["ngay"])

    return sales_daily, sales_product, marketing_daily


sales_daily, sales_product, marketing_daily = load_data()

st.title("📊 Marketing Performance Dashboard")

min_date = min(sales_daily["ngay"].min(), marketing_daily["ngay"].min()).date()
max_date = max(sales_daily["ngay"].max(), marketing_daily["ngay"].max()).date()

f1, f2, f3 = st.columns(3)

with f1:
    date_range = st.date_input(
        "Khoảng thời gian",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

with f2:
    group_by = st.selectbox(
        "Nhóm theo thời gian",
        ["Ngày", "Tuần", "Tháng", "Quý", "Năm"]
    )

with f3:
    selected_channels = st.multiselect(
        "Kênh marketing",
        sorted(marketing_daily["kenh"].dropna().unique())
    )

f4, f5 = st.columns(2)

with f4:
    selected_regions = st.multiselect(
        "Region",
        sorted(sales_daily["region"].dropna().unique())
    )

with f5:
    selected_provinces = st.multiselect(
        "Tỉnh/TP",
        sorted(sales_daily["tinh_tp"].dropna().unique())
    )

# ===== FILTER =====

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

if selected_regions:
    sales_daily = sales_daily[sales_daily["region"].isin(selected_regions)]
    sales_product = sales_product[sales_product["region"].isin(selected_regions)]

if selected_provinces:
    sales_daily = sales_daily[sales_daily["tinh_tp"].isin(selected_provinces)]
    sales_product = sales_product[sales_product["tinh_tp"].isin(selected_provinces)]

if selected_channels:
    marketing_daily = marketing_daily[marketing_daily["kenh"].isin(selected_channels)]

# ===== TIME GROUP =====

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
    gross_revenue=("gross_revenue", "sum"),
    quantity=("quantity", "sum"),
    orders=("orders", "sum")
)

marketing_period = marketing_daily.groupby("period", as_index=False).agg(
    marketing_cost=("marketing_cost", "sum")
)

df = sales_period.merge(marketing_period, on="period", how="left")
df["marketing_cost"] = df["marketing_cost"].fillna(0)

df["roas"] = df["revenue"] / df["marketing_cost"].replace(0, pd.NA)
df["roi"] = (df["revenue"] - df["marketing_cost"]) / df["marketing_cost"].replace(0, pd.NA)

# ===== KPI =====

total_revenue = df["revenue"].sum()
total_cost = df["marketing_cost"].sum()
total_orders = df["orders"].sum()
total_quantity = df["quantity"].sum()

roas = total_revenue / total_cost if total_cost else 0
roi = (total_revenue - total_cost) / total_cost if total_cost else 0
marketing_rate = total_cost / total_revenue if total_revenue else 0
aov = total_revenue / total_orders if total_orders else 0

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Tổng doanh thu", f"{total_revenue:,.0f} đ")
k2.metric("Chi phí marketing", f"{total_cost:,.0f} đ")
k3.metric("ROAS", f"{roas:,.2f}x")
k4.metric("ROI", f"{roi:.0%}")
k5.metric("Marketing / Revenue", f"{marketing_rate:.2%}")

k6, k7, k8 = st.columns(3)

k6.metric("Số hóa đơn", f"{total_orders:,.0f}")
k7.metric("Số lượng bán", f"{total_quantity:,.0f}")
k8.metric("AOV", f"{aov:,.0f} đ")

st.divider()

# ===== CHART 1: REVENUE VS MARKETING COST - 2 Y AXES =====

c1, c2 = st.columns(2)

with c1:
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=df["period"],
            y=df["revenue"],
            name="Doanh thu",
            mode="lines+markers"
        ),
        secondary_y=False
    )

    fig.add_trace(
        go.Bar(
            x=df["period"],
            y=df["marketing_cost"],
            name="Chi phí Marketing",
            opacity=0.35
        ),
        secondary_y=True
    )

    fig.update_layout(
        title="Doanh thu vs Chi phí Marketing",
        hovermode="x unified",
        height=500
    )

    fig.update_yaxes(title_text="Doanh thu", secondary_y=False)
    fig.update_yaxes(title_text="Chi phí Marketing", secondary_y=True)

    st.plotly_chart(fig, use_container_width=True)

with c2:
    fig = px.line(
        df,
        x="period",
        y="roas",
        title="ROAS theo thời gian"
    )
    st.plotly_chart(fig, use_container_width=True)

# ===== MARKETING =====

c3, c4 = st.columns(2)

with c3:
    channel_df = marketing_daily.groupby("kenh", as_index=False).agg(
        marketing_cost=("marketing_cost", "sum")
    ).sort_values("marketing_cost", ascending=False)

    fig = px.pie(
        channel_df,
        names="kenh",
        values="marketing_cost",
        title="Cơ cấu chi phí Marketing theo kênh"
    )
    st.plotly_chart(fig, use_container_width=True)

with c4:
    campaign_df = marketing_daily.groupby("campaign", as_index=False).agg(
        marketing_cost=("marketing_cost", "sum")
    ).sort_values("marketing_cost", ascending=False).head(10)

    fig = px.bar(
        campaign_df,
        x="marketing_cost",
        y="campaign",
        orientation="h",
        title="Top 10 Campaign theo chi phí"
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)

# ===== SALES =====

c5, c6 = st.columns(2)

with c5:
    product_df = sales_product.groupby("ten_hang", as_index=False).agg(
        revenue=("revenue", "sum"),
        quantity=("quantity", "sum")
    ).sort_values("revenue", ascending=False).head(10)

    fig = px.bar(
        product_df,
        x="revenue",
        y="ten_hang",
        orientation="h",
        title="Top 10 sản phẩm theo doanh thu"
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)

with c6:
    region_df = sales_daily.groupby("region", as_index=False).agg(
        revenue=("revenue", "sum")
    ).sort_values("revenue", ascending=False)

    fig = px.bar(
        region_df,
        x="region",
        y="revenue",
        title="Doanh thu theo Region"
    )
    st.plotly_chart(fig, use_container_width=True)

c7, c8 = st.columns(2)

with c7:
    province_df = sales_daily.groupby("tinh_tp", as_index=False).agg(
        revenue=("revenue", "sum")
    ).sort_values("revenue", ascending=False).head(10)

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
    store_df = sales_daily.groupby("diem_mua_hang", as_index=False).agg(
        revenue=("revenue", "sum")
    ).sort_values("revenue", ascending=False).head(10)

    fig = px.bar(
        store_df,
        x="revenue",
        y="diem_mua_hang",
        orientation="h",
        title="Top 10 điểm mua hàng theo doanh thu"
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)