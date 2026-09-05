-- 2025.04.30. v1
-- ============================================================
-- Problem/reference: aligning sparse, irregular data (stock
-- prices, portfolio holdings) onto a regular calendar - the join
-- types, window functions, and date/time functions needed to fill
-- gaps, get month-end values, and compute rolling averages when
-- source data doesn't arrive on a fixed schedule.
-- ============================================================
-- windows functions
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

 -- generate number series, e.g. when you need a list of years - generate_series works for both numbers and dates
 SELECT generate_series as terms
        FROM generate_series(1,20,1);

-- date_part vs date_trunc: date_part returns a number (e.g. the month as an int),
-- while date_trunc rounds a timestamp down to the given unit and returns a
-- timestamp/date (e.g. date_trunc('month', ts) returns the 1st of that month).

-- ------------------------------------------------------------
-- joins
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

-- ------------------------------------------------------------
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
where date_part('year', c.date) = '2024'
	and pi.ticker in ('NOK', 'AAPL') AND pi.portfolio_name='Portfolio Joshua'
order by c.date, pi.ticker;

-- ------------------------------------------------------------
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
		where (date_part('year', p.date)=date_part('year', c.date) and date_part('month', p.date)=date_part('month', c.date))
			or p.date<=c.date
			order by p.date desc
	) pi on true
where date_part('year', c.date) = '2024'
	and pi.ticker in ('NOK', 'AAPL') AND pi.portfolio_name='Portfolio Joshua'
order by c.date, pi.ticker;


-- ------------------------------------------------------------
-- windows functions


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
-- optional filters, left as toggles for exploration:
--and date_part('year',month_closing_day)='2020'
--and ticker in ('NOK')
;

-- gotcha: the ::decimal cast binds to 3, not to the whole expression,
-- so 2/3::decimal still runs integer division first if 2 and 3 are both
-- ints elsewhere - cast the operand(s) you actually want as decimal.
select 2/3::decimal;

-- ------------------------------------------------------------
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

-- Reference: Cathy Tanimura, "SQL for Data Analysis: Advanced Techniques
-- for Transforming Data into Insights" (O'Reilly, 2021) - tested 2025-01-24.

-- ------------------------------------------------------------
----- time functions

SELECT CURRENT_TIMESTAMP;
SELECT CURRENT_TIMESTAMP + interval '1 month';
SELECT cast (CURRENT_TIMESTAMP as date);
SELECT date_trunc('day',CURRENT_TIMESTAMP);
SELECT date_trunc('year',CURRENT_TIMESTAMP);
SELECT date_trunc('month',CURRENT_TIMESTAMP);
SELECT date_part('hour',CURRENT_TIMESTAMP);

SELECT CURRENT_DATE;
select to_date('2016-03-01', 'YYYY-MM-DD');

SELECT NOW();
SELECT *, 'D' as type FROM generate_series('2025-01-01'::timestamp,'2025-12-31', '1 month');

select make_date(2024,1,1);
SELECT date_part('day',current_timestamp);
SELECT date_part('month',current_timestamp);
SELECT date_part('hour',current_timestamp);
SELECT extract('day' from current_timestamp);
SELECT date_part('minutes',current_timestamp - interval '10 minutes');
SELECT date_part('minutes', age(current_timestamp,current_timestamp - interval '9 minutes'));

SELECT extract('month' from current_timestamp);

SELECT extract('hour' from current_timestamp);

SELECT date_part('year',age(date('2021-07-30'),date('2020-08-01')));
SELECT date('2020-06-01') + interval '7 days' as new_date;
SELECT date('2020-06-01') + 7 as new_date;
SELECT time '05:00' - time '03:00' as time_diff;
select date_trunc('day', CURRENT_DATE - '12 days'::interval)::date;
select date_trunc('week', CURRENT_DATE - '16 days'::interval)::date;
select date_trunc('month', CURRENT_DATE - '0 days'::interval)::date;
select   DATE_TRUNC('month', '2020-01-03'::DATE )::DATE;
SELECT age(date('2021-07-30'),date('2020-06-01')), date_part('year',age(date('2021-07-30'),date('2020-08-01')))
,  date_part('month',age(date('2021-07-30'),date('2020-07-01')));
select age(current_date, '2020-01-01'::date);
SELECT extract('year' from age(date('2021-08-30'),date('2020-07-01'))) * 12 
+ extract('month' from age(date('2021-08-30'),date('2020-07-01'))) * 1 ;

select trunc(5.5);
select floor(5.7);

with periods AS (

		SELECT 'D'::text AS periodgroup,
       generate_series(
           date_trunc('day', CURRENT_DATE - '12 days'::interval)::date,
           date_trunc('day', CURRENT_DATE)::date,
           '1 day'::interval
       ) AS start_date
			UNION ALL
			SELECT 'W'::text AS periodgroup,
			       generate_series(
			           date_trunc('week', CURRENT_DATE - '84 days'::interval)::date,
			           date_trunc('week', CURRENT_DATE)::date,
			           '7 days'::interval
			       ) AS start_date
			UNION ALL
			SELECT 'M'::text AS periodgroup,
			       generate_series(
			           date_trunc('month', CURRENT_DATE - '2 years'::interval)::date,
			           date_trunc('month', CURRENT_DATE)::date,
			           '1 month'::interval
			       ) AS start_date
			UNION ALL
			SELECT 'Q'::text AS periodgroup,
			       generate_series(
			           date_trunc('quarter', CURRENT_DATE - '3 years'::interval)::date,
			           date_trunc('quarter', CURRENT_DATE)::date,
			           '3 months'::interval
			       ) AS start_date

        )
select p.*
from periods p
;

select generate_series('2016-03-01'::date,  '2016-03-15'::date,'1 day'::interval) as date;


with dimdate as (
	 		select generate_series(
			           date_trunc('year', CURRENT_DATE - interval '1 year')::date,
			           date_trunc('year', CURRENT_DATE)::date,
			           '1 day'::interval) as date
		   )
select 
	*
	, count(*) over () as totaldaycount
	, lead(date) over (order by date) daynext
	, lead(date, 2) over (order by date
			) dayafternext
	, last_value(date) over (order by date
			rows between current row and 2 following) dayafternext
from dimdate
;
-- ------------------------------------------------------------
-- text functions
-- ------------------------------------------------------------

SELECT (string_to_array('pirmais otras', ' '))[1] as name;
SELECT unnest(string_to_array('pirmais otras', ' ')) as name;
SELECT substring('abcdc', 1, 1);

-- reference: common string functions
-- LENGTH(string)                    - length of a string
-- SUBSTRING(string FROM s FOR n)    - extracts part of a string
-- LEFT(string, n) / RIGHT(string,n) - first/last n characters
-- TRIM(BOTH 'x' FROM string)        - removes leading/trailing characters
-- REPLACE(string, old, new)         - replaces text
-- POSITION(substring IN string)     - position of a substring
-- UPPER(string) / LOWER(string)     - changes case
-- CONCAT(string1, string2, ...)     - concatenates strings
-- STRING_AGG(column, delimiter)     - aggregates rows into one string
SELECT LENGTH('PostgreSQL');                                -- 10
SELECT SUBSTRING('PostgreSQL' FROM 1 FOR 4);                -- 'Post'
SELECT LEFT('PostgreSQL', 4);                               -- 'Post'
SELECT RIGHT('PostgreSQL', 4);                               -- 'SQL'
SELECT TRIM(BOTH 'x' FROM 'xxxHelloWorldxxx');              -- 'HelloWorld'
SELECT REPLACE('Hello World', 'World', 'PostgreSQL');       -- 'Hello PostgreSQL'
SELECT POSITION('SQL' IN 'PostgreSQL');                     -- 8
SELECT UPPER('postgresql');                                 -- 'POSTGRESQL'
SELECT LOWER('POSTGRESQL');                                 -- 'postgresql'
SELECT CONCAT('Postgre', 'SQL');                            -- 'PostgreSQL'
SELECT STRING_AGG(first_name, ', ') FROM xxxx;              -- 'Alice, Bob, Charlie'

-- RPAD(text, target_length, fill) pads `text` on the right up to
-- target_length using `fill`; handy for generating ASCII patterns.
-- Oracle equivalent of generate_series: SELECT LEVEL AS n FROM dual CONNECT BY LEVEL <= 10;
SELECT  (n * 2) - 1 as step, RPAD('* ', (n * 2) - 1, '* ') AS pattern
FROM generate_series(1,5,1) as n
ORDER BY n DESC;

-- ------------------------------------------------------------
-- prime numbers calc
WITH numbers AS (
    SELECT generate_series(1,1000,1) AS num       
),
primes AS (
    SELECT num  FROM numbers n
    WHERE num > 1 
    AND NOT EXISTS (
        SELECT 1
        FROM numbers f
        WHERE f.num BETWEEN 2 AND FLOOR(SQRT(n.num))  
            AND MOD(n.num, f.num) = 0
    )
)
SELECT STRING_AGG(cast (p.num as text), '&' ORDER BY p.num) AS result
FROM primes p;


