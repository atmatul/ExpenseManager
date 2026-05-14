# import streamlit as st
# import pandas as pd


# def render():
#     st.header("📥 Data Entry")
#     st.info("Choose between manual entry or bulk CSV upload to update your records.")

#     # UI Split: Manual (Left) | CSV (Right)
#     col_manual, col_csv = st.columns([1.2, 1], gap="large")

#     with col_manual:
#         st.subheader("Manual Entry")
#         with st.form("manual_entry_form", clear_on_submit=True):
#             desc = st.text_input("Description")
#             date = st.date_input("Date")
#             amt = st.number_input("Amount", min_value=0.0, step=0.01)
#             f_acc = st.selectbox("From Account", ["Cash", "Bank", "Credit Card"])
#             t_acc = st.selectbox(
#                 "To Account", ["Groceries", "Rent", "Utilities", "Entertainment"]
#             )

#             if st.form_submit_button("Add Expense"):
#                 new_row = pd.DataFrame(
#                     [
#                         {
#                             "Description": desc,
#                             "Date": date,
#                             "Amount": amt,
#                             "From Account": f_acc,
#                             "To Account": t_acc,
#                         }
#                     ]
#                 )
#                 st.session_state.expenses_df = pd.concat(
#                     [st.session_state.expenses_df, new_row], ignore_index=True
#                 )
#                 st.success("Entry Saved!")

#     with col_csv:
#         st.subheader("Bulk CSV Upload")
#         uploaded_file = st.file_uploader("Upload .csv file", type=["csv"])

#         if uploaded_file is not None:
#             try:
#                 # CSV Parser Logic
#                 df_upload = pd.read_csv(uploaded_file)

#                 # Validation: Ensure columns match our schema
#                 required_cols = [
#                     "Description",
#                     "Date",
#                     "Amount",
#                     "From Account",
#                     "To Account",
#                 ]
#                 if all(col in df_upload.columns for col in required_cols):
#                     if st.button("Merge CSV Data"):
#                         st.session_state.expenses_df = pd.concat(
#                             [st.session_state.expenses_df, df_upload[required_cols]],
#                             ignore_index=True,
#                         )
#                         st.success(f"Imported {len(df_upload)} records successfully!")
#                 else:
#                     st.error(f"CSV must contain: {required_cols}")
#             except Exception as e:
#                 st.error(f"Error parsing CSV: {e}")

#     # Footer: Live Data Preview
#     st.divider()
#     st.subheader("Current Session Data")
#     st.dataframe(st.session_state.expenses_df, use_container_width=True)


import streamlit as st
import pandas as pd
from models.database import dbManager, InsertRowObject, InsertFileObject
from utils.logger import get_logger

logger = get_logger(__name__)

opCategory = [
    "transportation",
    "grocery",
    "food",
    "cigga",
    "green",
    "mobile",
    "relocation",
    "personal",
    "entertainment",
    "home",
]

opAccounts = ["n26", "wise", "deutsche_bank", "cash"]
opTowardsCategory = ["home", "atul", "khushboo"]


def render():
    st.header("📥 Data Entry")
    col_manual, col_csv = st.columns(2)

    with col_manual:
        st.subheader("Manual Entry")
        with st.form("entry_form"):
            desc = st.text_input("Description")
            date = st.date_input("Date")
            amt = st.number_input("Amount", min_value=0.0)
            f_category = st.selectbox("Category", options=opCategory)
            f_acc = st.selectbox("From Account", options=opAccounts)
            t_acc = st.selectbox("Towards Category", options=opTowardsCategory)

            if st.form_submit_button("Submit"):
                logger.info("User submitted manual entry form.")
                row_dict = {
                    "Description": desc,
                    "Date": str(date),
                    "Amount": amt,
                    "Category": f_category,
                    "From Account": f_acc,
                    "To Account": t_acc,
                }
                obj = InsertRowObject(row_dict)
                if dbManager.insertExpenseRow(obj):
                    st.success("Record Added!")
                else:
                    st.error("Validation Failed or Duplicate Entry.")

    with col_csv:
        st.subheader("Bulk Upload")
        file = st.file_uploader("Upload CSV", type=["csv"])
        if file:
            logger.info(f"File uploaded: {file.name} ({file.size} bytes)")
            df = pd.read_csv(file)
            obj = InsertFileObject(dfExpenses=df)
            obj.filename = file.name
            count = dbManager.insertExpenseFile(obj)
            if count > 0:
                st.success(f"Imported {count} rows!")
            else:
                st.error("Import failed check file integrity.")
