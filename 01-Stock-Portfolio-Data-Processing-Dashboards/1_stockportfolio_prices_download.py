"""
This script retrieves historical stock price and dividend data for a specified set of tickers 
from Yahoo Finance. The data is processed, merged, and saved as a CSV file for further analysis.

Steps:
1. Fetch historical stock prices and dividends for each ticker.
2. Filter and merge stock and dividend data.
3. Add metadata (e.g., ticker symbol) and format the dataset.
4. Save the combined data to a CSV file.
"""

import yfinance as yf
import pandas as pd

# Input parameters
tickers = {"NLY", "FSK", "PFLT", "DX", "AAPL", "NOK", "ARCC", "SPG", "EPD", "MSFT","EPD", "ABBV", "JNJ", "MO", "PM", "MCD", "AGNC", "LMT", "NVDA", "TSLA", "F", "GOOGL", "T"}  # Set of tickers
start_date = "2020-01-01"
end_date = "2025-01-24"

# Initialize an empty list to store data for all tickers
all_data = []

# Loop through each ticker
for ticker in tickers:
    print(f"\nFetching data for {ticker}...")

    # Fetch stock data
    stock_data = yf.download(ticker, start=start_date, end=end_date)

    # Fetch dividend data
    dividend_data = yf.Ticker(ticker).dividends

    # Filter dividends for the specified period
    dividend_data = dividend_data[(dividend_data.index >= start_date) & (dividend_data.index <= end_date)]

    # Print dividend dates and amounts to the console
    print(f"Dividend Dates and Amounts for {ticker}:")
    for date, amount in dividend_data.items():
        print(f"{date.strftime('%Y-%m-%d')}: {amount:.2f}")

    # Convert dividend_data index to timezone-naive (if it's timezone-aware)
    if dividend_data.index.tz is not None:
        dividend_data.index = dividend_data.index.tz_localize(None)

    # Merge stock data and dividend data
    stock_data = stock_data.merge(
        dividend_data.rename('Dividend Amount'),
        how='left',
        left_index=True,
        right_index=True
    )

    # Fill NaN values in Dividend Amount with 0
    stock_data['Dividend Amount'] = stock_data['Dividend Amount'].fillna(0)

    # Add ticker column
    stock_data['Ticker'] = ticker

    # Reset index to include Date as a column
    stock_data.reset_index(inplace=True)

    # Select and rename columns
    output_data = stock_data[['Date', 'Ticker', 'Close', 'Dividend Amount']]
    output_data.columns = ['Date', 'Ticker', 'Closing Price', 'Dividend Amount']

    # Append to the list
    all_data.append(output_data)

# Combine data for all tickers into a single DataFrame
combined_data = pd.concat(all_data, ignore_index=True)

# Define the output file path
output_file_path = r"stock_prices_and_dividends.csv"

# Save to CSV
combined_data.to_csv(output_file_path, index=False)

print(f"\nDataset saved to '{output_file_path}'.")