
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
- `portfolio name`: name of the portfolio, offers possibility to process different portfolios

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

<img src="https://github.com/user-attachments/assets/3f845083-367b-46ea-be22-35b88c63d149" alt="image" width="640" />

<img src="https://github.com/user-attachments/assets/d292a687-f0de-45a6-9401-190021d71123" alt="image" width="640" />

<img src="https://github.com/user-attachments/assets/2a29ec1a-c917-46b3-a84c-3f68bf15ed38" alt="image" width="640" />

<img src="https://github.com/user-attachments/assets/2ef363b3-f580-4bb8-a63b-52a0f6e86978" alt="image" width="640" />

<img src="https://github.com/user-attachments/assets/c996b2a1-07b0-43bd-8002-5aa5b7df43a8" alt="image" width="640" />

Slope chart - absolute and relative changes:

<img width="640" alt="image" src="https://github.com/user-attachments/assets/10d75ce8-7e88-4259-8769-570e1d7759a7" />


---

