import streamlit as st
import numpy as np
import pandas as pd
from models.database import dbManager
from utils import kpis


def render():
    st.header("📊 Financial Analytics Dashboard")

    df = dbManager.con.execute("SELECT * FROM fct_expense").df()
    if df.empty:
        st.warning("No data found. Please upload a CSV or add an entry.")
        return

    # KPI Row
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total Expenses", f"€{df['expend_amount'].sum():,.2f}")
    kpi2.metric("Total Transactions", len(df))
    kpi3.metric(
        "Top Category", df.groupby("parent_category")["expend_amount"].sum().idxmax()
    )

    st.divider()

    # # 4x2 Responsive Grid
    # for row in range(2):
    #     cols = st.columns(4)
    #     for col_idx, col in enumerate(cols):
    #         with col:
    #             st.subheader(f"Metric {row * 4 + col_idx + 1}")
    #             # Placeholder Area Chart
    #             chart_data = pd.DataFrame(np.random.randn(20, 1), columns=["Value"])
    #             st.area_chart(chart_data, height=150)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Spending by Category")
        cat_data = kpis.totalExpensePerCategory(df)
        st.bar_chart(cat_data.set_index("parent_category"))

    with c2:
        st.subheader("Monthly Trend")
        trend_data = kpis.monthlyExpenseTrend(df)
        st.line_chart(trend_data.set_index("month_year_marker")["expend_amount"])
