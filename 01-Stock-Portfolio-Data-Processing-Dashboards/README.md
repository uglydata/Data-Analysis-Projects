
# Data Analysis Project - Portfolio Dashboard

## Overview

This project focuses on the following tasks:

1. Stock Price Retrieval:
- Fetch stock prices from Yahoo Finance using Python.
- Save the data as a CSV file.
- Load the data into a PostgreSQL database.

2. Portfolio Setup:
- Define the portfolio in a CSV file.
- Load the portfolio data into PostgreSQL.

3. Data Cleaning and Preparation:
- Clean and shape the data within the database.
- Prepare the data for Power BI by exporting it as a CSV file.

4. Data Visualization:
- Load the cleaned data into Power BI.
- Create and showcase several dashboard and report variations.

## Steps


### 1. Prepare Portfolio CSV

Create a CSV file named `portfolio.csv` with the following columns:
- `date`: The date of the portfolio record.
- `ticker`: Stock ticker symbol (e.g., AAPL).
- `shares`: Number of shares held.
- `porftolio name`: name of the portfolio, offers possibility to process different portfolios

File:
**0_portfolio_setup.csv**

### 2. Download Stock Prices

Follow:
**1_stockportfolio_prices_download.py**

Define stock tickers and period for which stock prices should be retrieved

Fetch daily stock prices and dividends for selected tickers (e.g., AAPL, MSFT, GOOGL) using the Yahoo Finance API. 
Save the data as 
**`**2_stock_prices_and_dividends.csv**`.**

#### Example:
```
Date,Ticker,Shares,Name,Portfolio_name
2020-01-03,NOK,16000,Nokia,Portfolio Joshua
2020-01-03,AAPL,320,Apple Inc,Portfolio Joshua
2020-01-03,PM,500,Philip Morris International,Portfolio Joshua
2020-01-03,MCD,200,McDonald’s Corporation,Portfolio Joshua
2022-02-01,F,350,Ford,Portfolio Jessica
2022-02-01,JNJ,160,Johnson & Johnson,Portfolio Jessica
2022-02-01,T,4200,ATT,Portfolio Jessica
2022-02-01,PM,200,Philip Morris International,Por
```

### 3. Load Data into PostgreSQL

Data to load into DB:
**2_stock_prices_and_dividends.csv**

Tables used: 
```stock_prices```, ```portfolio``` 

Follow: 
**3_stocks_portfolio_processing.sql**

### 4. SQL for Portfolio Analysis

Goal: to combine portfolio and stock price data to calculate:
- **Portfolio Value**: `shares * closing_price`
- **Received Dividends**: `shares * dividend_amount`

Output: prepared CSV (``4_data_import_into_powerbi.csv```) for importing into Power BI

### 5. Visualize in Power BI

File to import:
**4_data_import_into_powerbi.csv**

1. **Import CSV Results**: process/shape/clean data, like add sector.
2. **Create Visualizations**:
    - portfolio dashboard - several options, default themes used
    - reports

Examples:

<img width="638" alt="image-39" src="https://github.com/user-attachments/assets/37441760-d5e2-4a01-92bd-7db8e673f471" />

<img width="638" alt="image-40" src="https://github.com/user-attachments/assets/77daf803-7a22-4a8c-ad33-6704bc1e432f" />

<img width="638" alt="image-42" src="https://github.com/user-attachments/assets/92d682e8-9798-4a9e-86a7-12d829712b0e" />

<img width="638" alt="image-45" src="https://github.com/user-attachments/assets/32c40058-0928-4e34-b68f-328e67f93475" />

<img width="638" alt="image" src="https://github.com/user-attachments/assets/c191bf99-0863-4a4f-9077-f7006346db16" />



---

