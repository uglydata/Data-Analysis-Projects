## SQL DEMO - Portfolio Analysis - Summary

This project processes stock portfolio data **entirely in SQL**, focusing on **time-series analysis, stock performance tracking, and portfolio valuation**.

### **SQL Breakdown - 3 Key Parts**

The analysis **sql-portfolio-calculations.sql** consists of three main parts:

#### **Portfolio Value Calculation (6 Approaches)**  
- Cleans stock price data using **CTEs** to remove duplicates.  
- Determines **monthly closing prices** using `LAST_VALUE()`, `MAX()`, and `MIN()`.  
- Demonstrates **6 different approaches**, including **window functions, subqueries, and optimized techniques (`DISTINCT ON`, `ROW_NUMBER()`)**.
- Computes **monthly stock values** using `LAST_VALUE()`, `MAX()`, and `MIN()`.
- Uses **CTEs** to clean and deduplicate stock price data. Different approaches.

#### **Monthly & Quarter-over-Quarter Returns**
- Calculates **month-over-month stock performance** using `LAG()`.
- Identifies **top 3 best & worst performers** per month using `RANK()`.

<img src="https://github.com/user-attachments/assets/ec675885-1948-4fdb-89c2-f8bb58819471" alt="image" width="640" />

#### **Portfolio Holdings & Dividend Tracking**  
- Joins stock data with **portfolio allocations** to calculate **total portfolio value**.  
- Aggregates **dividends earned** per stock using `SUM() OVER()`.  

<img src="https://github.com/user-attachments/assets/73e5ed18-68a4-4843-b56f-52cb6bc2f5b5" alt="image" width="640"/>

Portfolio value at the end of the month, last 3 months average value:

Dividends received per ticker, cumulative, average last 3 months:

<img src="https://github.com/user-attachments/assets/0968136f-4083-4b0a-a6a9-591e6a502534" alt="image" width="640"/>

Quarter over quarter returns:

<img src="https://github.com/user-attachments/assets/4bd0a83a-1fa6-4b61-a1a6-c7da2e7f9086" alt="image" width="640"/>

This project **mirrors data transformations** done in Power BI but executes them **entirely in SQL** for efficiency and automation.


### Data Sources & Dependencies

#### Input Tables:
- **`stock_and_dividends`**: Contains historical stock prices and dividend payouts.
- **`portfolio_info`**: Tracks user portfolios and stock allocations.
- **`calendar`**: Ensures each month is accounted for, even if stock data is missing.

Data Source: https://github.com/uglydata/Data-Analysis-Projects/blob/main/01-Stock-Portfolio-Data-Processing-Dashboards/1_stockportfolio_prices_download.py

#### Expected Outputs:
- Monthly portfolio values per stock.
- Month-over-month stock performance ranking.
- Dividend accumulation per stock & portfolio.

---

#### Future Enhancements
- Extend time-series analysis to **quarterly and yearly** intervals.
- Optimize query performance for **large datasets**.
