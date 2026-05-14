import streamlit as st
import os

from models.database import dbManager
from routes import homePage, insertPage

projectDir = os.path.abspath(os.path.dirname(__file__))
dataDir = os.path.join(projectDir, "data")

# 1. Page Configuration
st.set_page_config(page_title="Expense Manager", layout="wide")

# 2. Initialize Database (Singleton - runs only once on first app load)
# This ensures DB schema is created and seed data is loaded
_ = dbManager

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

