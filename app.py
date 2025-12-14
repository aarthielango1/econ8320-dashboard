import streamlit as st
import pandas as pd
import plotly.express as px

# Page setup
st.set_page_config(page_title="US Labor Dashboard", layout="wide")

# Helper function to load data
# We use cache_data so it doesn't reload the CSV every time we interact with a widget
@st.cache_data
def get_data():
  try:
    df = pd.read_csv('bls_data.csv')
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    df.index.name = "Date"
    return df
  except FileNotFoundError:
    st.error(
        "Could not find bls_data.csv. Please run the collection script first.")
    return None

df = get_data()

# --- SIDEBAR CONTROLS ---
st.sidebar.header("Filter Data")

if df is not None:
  # Get min and max dates for the slider
  min_dt = df.index.min().date()
  max_dt = df.index.max().date()

  # Create the date range slider
  selected_range = st.sidebar.slider(
      "Select Date Range:",
      min_value=min_dt,
      max_value=max_dt,
      value=(min_dt, max_dt)  # Default to full range
  )

  # Filter the dataframe based on the slider
  start_date, end_date = selected_range
  mask = (df.index.date >= start_date) & (df.index.date <= end_date)
  filtered_df = df.loc[mask]

  st.title("US Labor Statistics Dashboard")
  st.markdown("Updates monthly with data from the BLS API.")
  st.markdown("---")

  # --- KPI METRICS ---
  # We need to get the latest value and the previous value to show the change.
  # We use ffill() (forward fill) because the Quarterly data (ECI) will be NaN
  # for months that aren't the end of a quarter.
  df_filled = filtered_df.ffill()

  current = df_filled.iloc[-1]
  previous = df_filled.iloc[-2]

  col1, col2, col3, col4 = st.columns(4)

  with col1:
    # Unemployment Rate
    val = current['Unemployment Rate']
    delta = val - previous['Unemployment Rate']
    # Note: delta_color="inverse" makes red mean increase (bad for unemployment)
    st.metric("Unemployment Rate", f"{val}%", f"{delta:.1f}%",
              delta_color="inverse")

  with col2:
    # Total Jobs (Nonfarm)
    val = current['Total Nonfarm Payroll']
    delta = val - previous['Total Nonfarm Payroll']
    st.metric("Total Nonfarm Jobs", f"{int(val):,}k", f"{int(delta)}k")

  with col3:
    # Wages
    val = current['Average Hourly Earnings']
    delta = val - previous['Average Hourly Earnings']
    st.metric("Avg Hourly Earnings", f"${val:.2f}", f"${delta:.2f}")

  with col4:
    # Cost Index (Quarterly)
    val = current['Employment Cost Index']
    delta = val - previous['Employment Cost Index']
    st.metric("Employment Cost Index", f"{val}", f"{delta:.1f}")

  # --- CHARTS AREA ---
  tab1, tab2, tab3 = st.tabs(
      ["📉 Unemployment", "🏭 Jobs Market", "💵 Compensation"])

  with tab1:
    st.subheader("Unemployment Trends")
    # Plotting both the Rate (%) and the absolute Level (people)
    fig = px.line(filtered_df, y=['Unemployment Rate', 'Unemployment Level'],
                  markers=True, title="Rate (%) vs Count (Thousands)")
    st.plotly_chart(fig, use_container_width=True)

  with tab2:
    st.subheader("Labor Demand")
    # Comparing actual jobs vs job openings
    cols = [c for c in ['Total Nonfarm Payroll', 'Job Openings'] if
            c in filtered_df.columns]
    fig = px.line(filtered_df, y=cols, markers=True,
                  title="Total Jobs vs. Job Openings")
    st.plotly_chart(fig, use_container_width=True)

  with tab3:
    st.subheader("Wages & Costs")
    cols = [c for c in ['Average Hourly Earnings', 'Employment Cost Index'] if
            c in filtered_df.columns]
    fig = px.line(filtered_df, y=cols, markers=True,
                  title="Hourly Earnings vs Cost Index")
    st.plotly_chart(fig, use_container_width=True)

  # Footer / Data Table
  with st.expander("See Raw Data"):
    display_df = filtered_df.sort_index(ascending=False).copy()
    display_df.index = display_df.index.date
    st.dataframe(display_df)
