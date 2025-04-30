/*
All SQL Joins with Brief Descriptions

INNER JOIN – Returns only matching rows from both tables.

LEFT JOIN (LEFT OUTER JOIN) – Returns all rows from the left table, with matching rows from the right table (or NULL if no match).

RIGHT JOIN (RIGHT OUTER JOIN) – Returns all rows from the right table, with matching rows from the left table (or NULL if no match).

FULL JOIN (FULL OUTER JOIN) – Returns all rows from both tables; unmatched rows get NULLs.

CROSS JOIN – Returns the Cartesian product of both tables (all possible combinations).
-- alternative - join on 1=1, same as cross join

SELF JOIN – Joins a table with itself.

NATURAL JOIN – Joins tables using columns with the same name and data type.

LATERAL JOIN – Allows the right-side subquery to reference columns from the left table; useful for row-by-row calculations.
*/

  
/*

ALL WINDOWS functions explained

FUNCTION() OVER (
    [PARTITION BY column]
    [ORDER BY column]
    [ROWS/RANGE BETWEEN ...]
)


List of Window Functions
Aggregate Functions:

	SUM(), AVG(), MIN(), MAX(), COUNT()

Ranking Functions:

	ROW_NUMBER() → Unique rank, no ties.
	RANK() → Same rank for ties, gaps in ranking.
	DENSE_RANK() → Same rank for ties, no gaps.
	NTILE(N) → Distributes rows into N equal groups.
	PERCENT_RANK() OVER (    [PARTITION BY column]   - calculates the relative rank of a row as a percentage of the total number of rows.
	

Analytic Functions:

	LAG() → Gets previous row’s value.
	LEAD() → Gets next row’s value.
	FIRST_VALUE() → First value in the window.
	LAST_VALUE() → Last value in the window.
	NTH_VALUE(N) → N-th row value in the window.


Row Specification (ROWS / RANGE)
	ROWS → Based on physical row position.
	RANGE → Based on value range in ORDER BY.

Common options:

	ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW  
	ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING  
	RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING  

*/

/*

PERCENTILE_CONT() is an ordered-set aggregate function in PostgreSQL.

🔹 Function Type
Ordered-Set Aggregate Function
Computes a Continuous (Interpolated) Percentile Value

🔹 Explanation
PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY mag)
PERCENTILE_CONT(x) → Computes the continuous percentile for fraction x (e.g., 0.25 for the 25th percentile).
WITHIN GROUP (ORDER BY mag) → Defines how the values are sorted before percentile calculation.

*/

/*
STATISTICAL FUNCTIONS
stddev_pop(mag) - STANDART deviation for all population
stddev_samp(mag)  - STANDART deviation for sample,  n-1 minus observatiosn, parasti looooti tuvu
*/

 -- generate number series, like sometimes you need years -generate series is both for numbers, dates etc
 SELECT generate_series as terms 
        FROM generate_series(1,20,1)

date_part and date_trunc - date part returns number, bet date trunc - noīsina uz leju, piem, timestime tips, iedod month, atgriezīs 1.dienu mēnesī
date trunc atgriež datumu


----------------------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------
--- inner join or simply join and with left join
-- all clear
with calendar AS (
    -- Generate a series of dates for the calendar
    SELECT generate_series('2019-01-01'::timestamp, '2025-12-31', '1 month')::date AS date
)
select 
	c.*
	, pi.*
from calendar c
left join portfolio_info pi
	on date_part('year', pi.date)=date_part('year', c.date) and date_part('month', pi.date)=date_part('month', c.date)
order by c.date, pi.ticker	

---------------------------------------------------------v
---------------------------------------------------------v
---------------------------------------------------------v
---------------------------------------------------------v
-- cartesian join - all values vs all values
with calendar AS (
    -- Generate a series of dates for the calendar
    SELECT generate_series('2019-01-01'::timestamp, '2025-12-31', '1 month')::date AS date
)
select 
	c.*
	, pi.*
from calendar c
cross join portfolio_info pi
	
where 1=1
	and date_part('year', c.date) = '2024'	
	and pi.ticker in ('NOK', 'AAPL') AND pi.portfolio_name='Portfolio Joshua'
order by c.date, pi.ticker	

---------------------------------------------------------v
---------------------------------------------------------v
---------------------------------------------------------v
---------------------------------------------------------v
-- lateral join - from left side rows generate right side even if not present
with calendar AS (
    -- Generate a series of dates for the calendar
    SELECT generate_series('2019-01-01'::timestamp, '2025-12-31', '1 month')::date AS date
)
select 
	c.*
	, pi.*
from calendar c
join lateral (
		select 
			p.* 
		from  portfolio_info p
		where 1=1
			and 
				(
					(date_part('year', p.date)=date_part('year', c.date) and date_part('month', p.date)=date_part('month', c.date))
					or p.date<=c.date
				
				)
			order by p.date desc
	) pi on true
where 1=1
	and date_part('year', c.date) = '2024'	
	and pi.ticker in ('NOK', '--AAPL') AND pi.portfolio_name='Portfolio Joshua'
order by c.date, pi.ticker	


---------------------------------------------------------v
---------------------------------------------------------v
-- WINDOWS functions


with calendar AS (
    -- Generate a series of dates for the calendar
    SELECT generate_series('2019-01-01'::timestamp, '2025-12-31', '1 month')::date AS date
)
, deduped_prices as(

	select 
	p.ticker
	
	, first_value(date) over (partition by ticker, date_part('year', date), date_part('month', date) order by date desc
		ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as month_closing_day
	
	, max(date) over (partition by ticker, date_part('year', date),date_part('month', date) ) as month_closing_day2
	
	, last_value(closing_price) over (partition by ticker,date_part('year', date), date_part('month', date) order by date asc 
		ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as month_closing_price
	
	, MAX(closing_price) OVER (PARTITION BY ticker, date_part('year', date), date_part('month', date)) AS month_max_price
	
	, MIN(closing_price) OVER (PARTITION BY ticker, date_part('year', date), date_part('month', date)) AS month_min_price
	
	, sum(dividend_amount) over (partition by ticker, date_part('year', date), date_part('month', date)) as dividends_month
	
	, row_number() over (
				partition by
				ticker, date_part('year', date), date_part('month', date)
				order by date desc
			) as row_num
from stock_and_dividends p
where 1=1
	
--limit 50
)

	select 
	ticker
	, month_closing_day
--	, month_closing_day2
	, month_closing_price
	, month_max_price
	, month_min_price
	, dividends_month
	,  round(AVG(month_closing_price) 
		OVER (PARTITION BY ticker
			 order by month_closing_day
		rows between 1 preceding and current row), 2) AS month_3avgprice
from
deduped_prices
where row_num =1
--and date_part('year',month_closing_day)='2020'
--and ticker in ('NOK')

select 2/3::decimal 
---------------------------------------------------------v
---------------------------------------------------------v
-- WINDOWS functions - details


---------------------------------------------------------------------
-- execution order
/*
Table 8-1. SQL query order of evaluation
1 FROM
including JOINs and their ON clauses
2 WHERE
3 GROUP BY
including aggregations
4 HAVING
5 Window functions
6 SELECT
7 DISTINCT
8 UNION
9 ORDER BY
10 LIMIT and OFFSET
*/
