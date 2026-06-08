import yfinance as yf
import pandas as pd
from prophet import Prophet

# 1. Download historical S&P 500 data (^GSPC)
print("Downloading S&P 500 historical data...")
ticker = "^GSPC"
raw_data = yf.download(ticker, start="2021-01-01", end="2026-06-01")

# === UPDATE TO FIX MULTI-INDEX ISSUE ===
# If yfinance generated multi-level columns, flatten them
if isinstance(raw_data.columns, pd.MultiIndex):
    raw_data.columns = raw_data.columns.droplevel(1)
# =======================================

# 2. Data Cleaning and Preparation for Prophet
df_history = raw_data.reset_index()

# Filter and rename columns to fit Prophet format ('ds' for date, 'y' for target value)
df_history = df_history[['Date', 'Close']].rename(columns={'Date': 'ds', 'Close': 'y'})

# Ensure 'y' column is a clean numeric 1D array and remove timezone data from 'ds'
df_history['y'] = pd.to_numeric(df_history['y'].squeeze())
df_history['ds'] = df_history['ds'].dt.tz_localize(None)

# 3. Prophet Model Configuration and Training
print("Training Prophet forecasting model...")
model = Prophet(
    yearly_seasonality=True,  # Critical for capturing financial market cycles (Q4 rallies, etc.)
    weekly_seasonality=False, # Stocks do not trade on weekends; disabling weekly seasonality to reduce noise
    daily_seasonality=False
)
model.fit(df_history)

# 4. Generate Future Timeline for the next 365 days
future = model.make_future_dataframe(periods=365)

# 5. Execute Prediction Pipeline
print("Generating 1-year market forecast...")
forecast = model.predict(future)

# 6. Merge Historical Data and Forecast Components for Tableau
# Including 'trend' and 'yearly' components to build seasonality analytics dashboards
final_df = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper', 'trend', 'yearly']].merge(
    df_history[['ds', 'y']], on='ds', how='left'
)

# Create a data type dimension to easily filter 'Actual' vs 'Forecast' entries in Tableau
final_df['Data_Type'] = final_df['y'].apply(lambda x: 'Actual' if pd.notnull(x) else 'Forecast')

# 7. Export Final Analytical Dataset to CSV
final_df.to_csv("sp500_forecast_tableau.csv", index=False)
print("Success! File 'sp500_forecast_tableau.csv' has been generated and is ready for Tableau ingestion.")
