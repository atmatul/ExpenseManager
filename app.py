import streamlit as st
import os
import pandas as pd

from routes import homePage, insertPage

projectDir = os.path.abspath(os.path.dirname(__file__))
dataDir = os.path.join(projectDir, "data")
seedFile = os.path.join(dataDir, "seed.csv")

# 1. Page Configuration
st.set_page_config(page_title="Expense Manager", layout="wide")

# 2. Initialize Session State (The "Bronze" Table)
if "expenses_df" not in st.session_state:
    st.session_state.expenses_df = pd.read_csv(seedFile)


# 3. Define Pages
def show_home():
    homePage.render()


def show_insert():
    insertPage.render()


# 4. Navigation Logic
pg = st.navigation(
    {
        "Main": [
            st.Page(show_home, title="Home", icon="🏠"),
            st.Page(show_insert, title="Insert", icon="➕"),
        ]
    }
)
pg.run()
