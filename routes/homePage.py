import streamlit as st
import numpy as np
import pandas as pd


def render():
    st.header("📊 Financial Analytics Dashboard")

    # KPI Row
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total Spent", f"€{st.session_state.expenses_df['amount'].sum():,.2f}")
    kpi2.metric("Records", len(st.session_state.expenses_df))
    kpi3.metric("Status", "Active")

    st.divider()

    # 4x2 Responsive Grid
    for row in range(2):
        cols = st.columns(4)
        for col_idx, col in enumerate(cols):
            with col:
                st.subheader(f"Metric {row * 4 + col_idx + 1}")
                # Placeholder Area Chart
                chart_data = pd.DataFrame(np.random.randn(20, 1), columns=["Value"])
                st.area_chart(chart_data, height=150)
