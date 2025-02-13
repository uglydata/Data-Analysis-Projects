
# SQL Portfolio Analysis Enhancements - SQL DEMO

## Overview -  SQL utilization

This project enhances stock portfolio analysis using **advanced SQL** techniques, focusing on time-series analysis, window functions, and performance optimization. These SQL scripts aim to provide:

- **Portfolio Value Analysis**: Monthly and yearly tracking of stock portfolio value. Demonstrate different approaches.
- **Rolling Averages & Volatility**: Trends in stock prices over time.
- **Investment Duration Tracking**: Measuring how long stocks are held and their performance.
- **Dividend Analysis**: Cumulative and yearly dividends earned per stock.

- Project is based on the data from the 1st project in this demo repo about Stock Portfolio Dashboard- data is shaped using SQL, not Power BI like it is mostly done in the 1st demo project.

## Steps

### SQL Enhancements

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

See [sql-portfolio-calculations.sql](https://github.com/uglydata/Data-Analysis-Projects/blob/main/03-SQL-Demos/sql-portfolio-calculations.sql)

*Dependency*:
[Executed SQL - preparation of raw data](https://github.com/uglydata/Data-Analysis-Projects/blob/main/01-Stock-Portfolio-Data-Processing-Dashboards/3_stocks_portfolio_processing.sql)
