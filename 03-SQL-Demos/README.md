
# SQL Portfolio Analysis Enhancements - SQL DEMO

## Overview -  SQL utilization

This project enhances stock portfolio analysis using **advanced SQL** techniques, focusing on:

- **Time-Series Analysis**: Tracking portfolio values across monthly, quarterly, and yearly intervals.
- **Window Functions**: Applying `RANK()`, `LAG()`, and `LEAD()` to analyze stock performance.
- **Portfolio Performance Tracking**: Computing stock returns, ranking best/worst performers, and tracking dividends.

Unlike the **Stock Portfolio Dashboard**, which relies on Power BI, this project processes all data **directly in SQL** for efficiency and automation.

## Steps

## SQL Enhancements

The analysis **sql-portfolio-calculations.sql** consists of three main parts:

### 1️⃣ Portfolio Value Calculation
- Computes **monthly stock values** using `LAST_VALUE()`, `MAX()`, and `MIN()`.
- Uses **CTEs** to clean and deduplicate stock price data. Different approaches.

### 2️⃣ Monthly & Quarter-over-Quarter Returns
- Calculates **month-over-month stock performance** using `LAG()`.
- Identifies **top 3 best & worst performers** per month using `RANK()`.

### 3️⃣ Portfolio Holdings & Dividend Tracking
- Joins **stock prices** with portfolio holdings to calculate **total portfolio value**.
- Tracks **dividends earned per stock** using `SUM() OVER(PARTITION BY ticker)`.

---

## Data Sources & Dependencies

### Input Tables:
- **`stock_and_dividends`**: Contains historical stock prices and dividend payouts.
- **`portfolio_info`**: Tracks user portfolios and stock allocations.
- **`calendar`**: Ensures each month is accounted for, even if stock data is missing.

### Expected Outputs:
- Monthly portfolio values per stock.
- Month-over-month stock performance ranking.
- Dividend accumulation per stock & portfolio.

---

## Future Enhancements
- Extend time-series analysis to **quarterly and yearly** intervals.
- Optimize query performance for **large datasets**.
