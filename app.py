import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Exotel Feedback Dashboard", layout="wide")

# --- STREAMLIT SECRETS ---
creds_dict = st.secrets["google_service_account"]
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
client = gspread.authorize(creds)

# --- LOAD DATA FROM GOOGLE SHEET ---
sheet = client.open("Exotel Feedback").worksheet("Ratings")
data = sheet.get_all_records()
df = pd.DataFrame(data)

# --- CLEAN COLUMN HEADERS ---
df.columns = df.columns.astype(str).str.strip()

# --- DEBUG: Show what columns we received ---
# st.sidebar.write("🧾 Detected columns:", df.columns.tolist())

# --- SAFETY CHECK ---
if "Timestamp" not in df.columns or "Rating" not in df.columns:
    st.error("⚠️ 'Timestamp' or 'Rating' column not found. Please check your Google Sheet format.")
    st.stop()

# --- CONVERT TYPES ---
df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')

# --- SIDEBAR FILTERS ---
st.sidebar.title("🔎 Filters")
start_date = st.sidebar.date_input("Start Date", df['Timestamp'].min().date())
end_date = st.sidebar.date_input("End Date", df['Timestamp'].max().date())

# --- FILTER DATA ---
filtered = df[
    (df['Timestamp'].dt.date >= start_date) &
    (df['Timestamp'].dt.date <= end_date)
]

# --- MAIN DASHBOARD ---
st.title("📞 Exotel Feedback Dashboard")

# KPIs
col1, col2 = st.columns(2)
col1.metric("Total Feedback Entries", len(filtered))
col2.metric("Average Rating", round(filtered['Rating'].mean(), 2) if not filtered.empty else "N/A")

# RATING DISTRIBUTION
st.subheader("📊 Rating Distribution")
st.bar_chart(filtered['Rating'].value_counts().sort_index())

# AVERAGE RATING OVER TIME
st.subheader("📈 Average Rating Over Time")
daily_avg = filtered.groupby(filtered['Timestamp'].dt.date)['Rating'].mean()
st.line_chart(daily_avg)

# LOW RATINGS
st.subheader("⚠️ Low Ratings (1 or 2)")
st.dataframe(filtered[filtered['Rating'] <= 2])
