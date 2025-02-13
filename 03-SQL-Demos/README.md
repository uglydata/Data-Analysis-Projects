
# SQL Portfolio Analysis Enhancements - SQL DEMO

## Overview

This project extends the stock portfolio analysis by incorporating time-series calculations for enhanced financial insights. These SQL scripts aim to provide:

- **Portfolio Value Analysis**: Monthly and yearly tracking of stock portfolio value. Demonstrate different approaches.
- **Rolling Averages & Volatility**: Trends in stock prices over time.
- **Investment Duration Tracking**: Measuring how long stocks are held and their performance.
- **Dividend Analysis**: Cumulative and yearly dividends earned per stock.

## Steps

###New SQL Enhancements

1️.Portfolio Value & Performance Tracking

**Goal: Track portfolio value at year-end and month-end to analyze growth trends.**
Key SQL Concepts: RANK(), WINDOW FUNCTIONS, PARTITION BY
Insights: Compare different portfolios, detect high-growth stocks, and identify trends over years.

2️.Rolling 3-Month Stock Price Averages

**Goal: Smooth out stock price fluctuations using a 3-month rolling average.**
Key SQL Concepts: AVG() OVER (ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)
Insights: Identify short-term trends and detect sudden price movements.

3️.Holding Duration & Profitability - TimeSeries

**Goal: Measure how long stocks were held and calculate the percentage price change - quarter over quarter.**
Key SQL Concepts: LEAD(), LAG(), DATEDIFF(), % Change Calculation
Insights: Optimize investment decisions by understanding stock holding duration vs. profitability.

4️.Cumulative Dividends by Portfolio

**Goal: Track total dividends received per portfolio/ticker over time.**
Key SQL Concepts: SUM() OVER (ORDER BY time), PARTITION BY ticker
Insights: Identify high-dividend stocks and analyze dividend growth trends.
