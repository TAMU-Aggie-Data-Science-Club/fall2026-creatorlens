
from datetime import date, timedelta

import streamlit as st
import pandas as pd
import plotly.express as px


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="CreatorLens | YouTube Analytics",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --------------------------------------------------
# CUSTOM STYLING
# --------------------------------------------------

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    .stApp {
        background-color: #0B1020;
        color: #EAF0FF;
        font-family: 'Inter', sans-serif;
    }

    [data-testid="stSidebar"] {
        background-color: #111A2E;
        border-right: 1px solid #263653;
    }

    h1, h2, h3 {
        color: #EAF0FF !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
    }

    [data-testid="stMetric"] {
        background-color: #17243B;
        border: 1px solid #293B5B;
        padding: 18px;
        border-radius: 12px;
    }

    [data-testid="stMetricLabel"] {
        color: #94A3B8;
    }

    [data-testid="stMetricValue"] {
        color: #67B7FF;
    }

    .section-caption {
        color: #8FA9C9;
        font-size: 12px;
        letter-spacing: 2px;
        font-weight: 600;
    }

    hr {
        border-color: #293B5B;
    }

    .stButton button {
        border-radius: 8px;
        background-color: #1D3B66;
        border: 1px solid #3B82F6;
        color: white;
    }

    [data-testid="stRadio"] label {
        color: #D8E5F5;
    }

    [data-testid="stDateInput"] {
        color: #EAF0FF;
    }
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------

with st.sidebar:

    st.markdown("# 🔭 CREATORLENS")
    st.caption("YOUTUBE ANALYTICS PLATFORM")

    st.divider()

    st.caption("NAVIGATION")

    page = st.radio(
        "NAVIGATION",
        [
            "Overview",
            "Creator Analytics",
            "Virality & Trends",
            "ML Predictions",
            "Creator Comparisons",
            "Data Explorer"
        ],
        label_visibility="collapsed"
    )

    st.divider()

    st.caption("REPORTING PERIOD")

    selected_dates = st.date_input(
        "Select date range",
        value=(
            date.today() - timedelta(days=30),
            date.today()
        ),
        format="MM/DD/YYYY"
    )

    st.divider()

    st.caption("PROJECT")
    st.write("CreatorLens · 2026")
    st.caption("YouTube Creator Intelligence")


# --------------------------------------------------
# MAIN HEADER
# --------------------------------------------------

st.markdown(
    "<p class='section-caption'>YOUTUBE DATA & CREATOR INTELLIGENCE</p>",
    unsafe_allow_html=True
)

st.title("CreatorLens")

st.caption(
    "Understanding creator growth, engagement, "
    "and the patterns behind viral content."
)

st.divider()


# --------------------------------------------------
# PAGE CONTENT
# --------------------------------------------------

if page == "Overview":

    st.subheader("Platform Overview")

    st.write(
        "A centralized view of YouTube creator performance "
        "and content trends."
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Creators Analyzed", "—")
    col2.metric("Videos Analyzed", "—")
    col3.metric("Average Engagement", "—")
    col4.metric("Predicted Viral Videos", "—")

    st.divider()

    st.subheader("Platform Performance")

    left, right = st.columns(2)

    with left:
        st.info("Creator growth trends will appear here.")

    with right:
        st.info("Video engagement trends will appear here.")

    st.divider()

    st.subheader("Trending Creators")
    st.info("A ranking of trending creators will appear here.")


elif page == "Creator Analytics":

    st.subheader("Creator Analytics")

    st.write(
        "Explore individual creator profiles, "
        "audience growth, and video performance."
    )

    st.info("Creator search and profile analytics will appear here.")


elif page == "Virality & Trends":

    st.subheader("Virality & Trends")

    st.write(
        "Explore patterns in video performance, "
        "engagement, and content virality."
    )

    st.info("Virality trends and time-series visualizations will appear here.")


elif page == "ML Predictions":

    st.subheader("Machine Learning Predictions")

    st.write(
        "Explore predictive models and machine-learning "
        "insights into creator and video performance."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.info("Model performance and evaluation will appear here.")

    with col2:
        st.info("Prediction results will appear here.")

    st.divider()

    st.subheader("Model Insights")
    st.info("KNN, PCA, and other model visualizations will appear here.")


elif page == "Creator Comparisons":

    st.subheader("Creator Comparisons")

    st.write(
        "Compare creators across engagement, "
        "growth, views, and publishing activity."
    )

    st.info("Creator comparison charts will appear here.")


elif page == "Data Explorer":

    st.subheader("Data Explorer")

    st.write(
        "Explore, filter, and inspect the underlying "
        "YouTube dataset."
    )

    st.info("Dataset tables, filters, and search tools will appear here.")


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "CREATORLENS · YOUTUBE ANALYTICS PLATFORM · 2026"
)
