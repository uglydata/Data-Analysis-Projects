# Data-Analysis-Projects
A collection of demo projects showcasing end-to-end data analysis workflows, including data retrieval, processing, cleaning, shaping, and visualization.

**Tools Used**: 
- **Python**: For data retrieval and automation.
- **PostgreSQL**: For data storage and processing.
- **SQL**: For advanced data manipulation and preparation.
- **MS Excel/CSV**: For data input/output.
- **Power BI**: For dashboard creation and visualization.

## 01-Stock Portfolio Dashboard
[01-Stock-Portfolio-Data-Processing-Dashboards](https://github.com/uglydata/Data-Analysis-Projects/tree/main/01-Stock-Portfolio-Data-Processing-Dashboards)

This project demonstrates the creation of a dashboard for analyzing stock portfolios. Key steps include:

Stock Price Retrieval, Portfolio definition, Visualization:
1. **Portfolio Setup**:
- Define the portfolio in a CSV file.
- Load the portfolio data into PostgreSQL.

2. **Fetch stock prices from Yahoo Finance using Python**.
- Save the data as a CSV file.
- Load the data into a PostgreSQL database.

3. **Data Cleaning and Preparation**:
- Clean and shape the data within the database.
- Prepare the data for Power BI by exporting it as a CSV file.

4. **Data Visualization**:
- Import the prepared data into Power BI.
- Create dashboards and reports, including:
-- Portfolio distribution by sector.
-- Dividend yield analysis.
-- Monthly and yearly performance trends.

## 02-Finance Dashboard
[02-Finance Dashboard](https://github.com/uglydata/Data-Analysis-Projects/tree/main/02-Finance-Dashboard)

This project demonstrates the process of generating, shaping, and visualizing financial data to create insightful dashboards in Power BI. The focus is on analyzing key financial metrics like revenue, costs, profit/loss, and productivity for divisions over a specified period.
High level dashboard w/o detailed project info (separate dashboard).

1. **Prepare Data**:
- MS Excel - Randomly generate finance data

2. **Data Visualization**:
- Load the data into Power BI.
- Create and showcase several dashboard and report variations.

## 03-SQL DEMO
[03-SQL-DEMOs](https://github.com/uglydata/Data-Analysis-Projects/tree/main/03-SQL-Demos)

This project enhances stock portfolio analysis using **advanced SQL techniques**, focusing on **time-series analysis, window functions, and performance optimization**.

**Key Features:**  
- Portfolio Value Analysis: Track year-end and month-end portfolio performance using multiple **SQL approaches (RANK(), LAST_VALUE(), ROW_NUMBER())**.
- Quarter-over-Quarter Returns: Calculate QoQ portfolio returns with **LEAD()**, ensuring accurate **time-based comparisons**.
- Query Performance Optimization: Compare **different SQL techniques to balance speed and readability**.
- Techniques Used: **Window functions (LEAD, LAG, First, Last, Rank etc), subqueries, and multiple SQL methodologies **to analyze portfolio data.
- **Objective**: Demonstrates how to structure and transform stock portfolio data using SQL, replicating similar methodologies used in Power BI in the Stock Portfolio Dashboard project

**Purpose**:
This project demonstrates **data shaping in SQL**, mirroring how portfolio analysis is structured in **Power BI** in the **Stock Portfolio Dashboard** project. It showcases how **SQL can efficiently preprocess and transform stock data** before visualization.


## About
This repository is designed for educational and demonstration purposes, providing a hands-on guide for:
