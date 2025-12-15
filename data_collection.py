import requests
import json
import pandas as pd
from datetime import datetime

SERIES_MAPPING = {
  "CES0000000001": "Total Nonfarm Payroll",  # Monthly
  "LNS14000000": "Unemployment Rate",  # Rate (%) - Corrected ID for Rate
  "LNS13000000": "Unemployment Level",  # Level (Count) - Corrected ID for Count
  "CIU1010000000000A": "Employment Cost Index",  # Quarterly
  "CES0500000003": "Average Hourly Earnings",  # Monthly
  "JTS00000000JOL": "Job Openings"  # Monthly
}

def fetch_bls_data():
  headers = {'Content-type': 'application/json'}

  current_year = datetime.now().year
  start_year = current_year - 6

  data = json.dumps({
    "seriesid": list(SERIES_MAPPING.keys()),
    "startyear": str(start_year),
    "endyear": str(current_year),
    "registrationkey": "6d64f86af5594dea912cbf909bd4ecc4"
  })

  print(f"Fetching data from BLS API for years {start_year}-{current_year}...")

  try:
    p = requests.post('https://api.bls.gov/publicAPI/v2/timeseries/data/',
                      data=data, headers=headers)
    json_data = json.loads(p.text)
  except Exception as e:
    print(f"API Request failed: {e}")
    return

  records = []
  if 'Results' not in json_data:
    print("Error: No results found. Check API key or Series IDs.")
    print(json_data)
    return

  for series in json_data['Results']['series']:
    series_id = series['seriesID']
    for item in series['data']:
      records.append({
        'series_id': series_id,
        'year': item['year'],
        'period': item['period'],
        'value': item['value']
      })

  df = pd.DataFrame(records)

  # --- FIXED DATE PARSING FOR QUARTERLY DATA ---
  def parse_period(period):
    if 'M' in period:
      return period.replace('M', '')
    elif 'Q' in period:
      # Map Quarters to the last month of the quarter (Mar, Jun, Sep, Dec)
      # This aligns Quarterly data with Monthly data reasonably well
      q_map = {'Q01': '03', 'Q02': '06', 'Q03': '09', 'Q04': '12'}
      return q_map.get(period, '01')
    return '01'

  df['month'] = df['period'].apply(parse_period)

  df['date'] = pd.to_datetime(df['year'] + '-' + df['month'] + '-01')
  df['value'] = pd.to_numeric(df['value'])

  # Pivot
  df_pivot = df.pivot_table(index='date', columns='series_id', values='value',
                            aggfunc='last')

  # Rename columns
  df_pivot.rename(columns=SERIES_MAPPING, inplace=True)
  df_pivot.sort_index(inplace=True)

  print("Data fetched and cleaned successfully.")
  print(df_pivot.tail())

  df_pivot.to_csv('bls_data.csv')
  print("Data saved to bls_data.csv")


if __name__ == "__main__":
  fetch_bls_data()