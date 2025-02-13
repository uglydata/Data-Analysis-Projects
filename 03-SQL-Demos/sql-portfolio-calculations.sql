
-- SQL DEMO: Comparing Multiple Approaches to Year-End Portfolio Value Calculation

-- GOAL: Retrieve stock portfolio value at the end of each year using different SQL techniques.

-- TECHNIQUES DEMONSTRATED (6 Approaches):
-- 1. Window Functions (`RANK()`, `LAST_VALUE()`)
-- 2️. Subqueries (Correlated & Non-Correlated)
-- 3️. Optimized Combinations (`DISTINCT ON`, `ROW_NUMBER()`)

-- PERFORMANCE COMPARISON:
-- - Some methods are **fast & efficient**, others are **simpler but slower**.
-- - Each approach highlights **key trade-offs** between speed, readability, and complexity.

-- DEPENDENCY:
-- - Data processed using: 
--  🔗 `https://github.com/uglydata/Data-Analysis-Projects/blob/main/01-Stock-Portfolio-Data-Processing-Dashboards/3_stocks_portfolio_processing.sql`
-- - Results stored in: `temp_portfelis_` (PostgreSQL table)

------------------------------------------------------------------------


------------------------------------------------------------------------
-- Option 1

-- porftolio data -simulate powerbi, with CTE, last value - inefficient sql, see different sql
-- Evaluation: inefficient, NOT RECOMMENDED – Full window scan makes this slow.
-- Execution time: 1.251sec

with portfolio_year_end as(
	select 
		portfolio, 		
		date_part('year', date) as date,
		ticker,
		last_value(portfolio_value) over (
					partition by 
						portfolio
						, ticker
						,date_part('year', date)
					order by 
						date asc
					rows between unbounded preceding and unbounded following) AS value
		, row_number() over (partition by 
						portfolio
						, ticker
						,date_part('year', date)
					order by 
						date asc ) as rownum
	from temp_portfelis_
)
select 
	p.portfolio
	, p.date as date
	, sum(p.value) as value
from portfolio_year_end p
where 1=1
	and rownum=1
group by p.portfolio, p.date
order by p.portfolio, p.date
;


------------------------------------------------------------------------
-- Option 2

-- porftolio data -simulate powerbi, with CTE, values year end, use RANK
-- Evaluation: FASTEST approach, efficient and scalable
-- Execution time: 1.16sec

with portfolio_year_end as (
	select 
		portfolio, 		
		date_part('year', date) as date,
		ticker,
		portfolio_value as value,	
		rank() over (
					partition by 
						portfolio
						, ticker
						,date_part('year', date)
					order by
						date desc) AS rank
	from temp_portfelis_
	where 1=1)
select 
	p.portfolio
	, p.date as date	
	, sum(p.value) as value
from portfolio_year_end p
where 1=1
	and p.rank=1
group by p.portfolio, p.date
order by p.portfolio, p.date
;

--- porftolio data -simulate powerbi, with CTE, values both at the end of year and month
with portfolio_year_end as (
	select 
		portfolio, 		
		date_part('year', date) as date_year,
		date_part('month', date) as date_month,
		ticker,
		portfolio_value as value,
		rank() over (
					partition by 
						portfolio
						, ticker
						,date_part('year', date)
						,date_part('month', date)
					order by
						date desc) AS rank
	from temp_portfelis_
	where 1=1
)
select 
	p.portfolio
	, p.date_year as date_year	
	, p.date_month as date_month
	, sum(p.value) as value
from portfolio_year_end p
where 1=1
	and p.rank=1
group by p.portfolio, p.date_year, p.date_month
order by p.portfolio, p.date_year, p.date_month
;


------------------------------------------------------------------------
-- Option 3

-- porftolio data -simulate powerbi, with subquery and corelated subquery table
-- Evaluation: NOT RECOMMENDED – High execution time due to row-by-row lookup.
-- Execution time: 3.26sec

select 
	t1.portfolio, 		
	date_part('year', t1.date) as date,
	sum(t1.portfolio_value) as value
from temp_portfelis_ t1
where t1.date = (
					select max(t2.date) 
					from temp_portfelis_ t2
					where 1=1
							and date_part('year', t1.date) = date_part('year', t2.date)
							and t1.portfolio = t2.portfolio
							and t1.ticker = t2.ticker
				)
group by t1.portfolio, t1.date
order by t1.portfolio, t1.date
;

------------------------------------------------------------------------
-- Option 4

-- value by year using subquery and windows function - use FIRST_VALUE
-- Evaluation: Moderate speed, a good trade-off
-- Execution time: 1.44sec

select 
	portfolio
	, date_year
	, sum(value) as portfolio_value
from(	
	select 
		distinct
		portfolio, 	
		date_part('year', date) as date_year,
		ticker,		 
		first_value(portfolio_value) over (
					partition by 
						portfolio
						,ticker
						,date_part('year', date)						
					order by
						date desc
					) AS value
	from temp_portfelis_	
	)
group by portfolio, date_year
order by portfolio, date_year
;

------------------------------------------------------------------------
-- Option 5

-- value by year using subquery and windows function - use row number
-- Evaluation: Best execution time so far
-- Execution time: top execution 1.112sec

select 
	portfolio
	, date_year
	, sum(value) as portfolio_value
from(	
	select 		
		portfolio, 	
		date_part('year', date) as date_year,
		ticker,		 
		portfolio_value as value,
		row_number() over (
					partition by 
						portfolio
						,ticker
						,date_part('year', date)						
					order by
						date desc
					) AS rownum
	from temp_portfelis_
	where 1=1	
	)
where rownum=1	
group by portfolio, date_year
order by portfolio, date_year
;

------------------------------------------------------------------------
-- Option 6

-- value by year using subquery and distinct on
-- Evaluation: Fast and reliable.
-- Execution time: top execution 1.3sec

select 
	portfolio
	, date_year
	, sum(value) as portfolio_value
from(	
	select 
		distinct on (portfolio, ticker, date_part('year', date))
		portfolio, 	
		date_part('year', date) as date_year,
		ticker,		 
		portfolio_value as value
		, date
	from temp_portfelis_
	where 1=1
	order by portfolio, ticker, date_part('year', date), date desc
	)
where 1=1	
group by  portfolio, date_year
order by  portfolio, date_year
;


------------------------------------------------------------------------
-- different SQLs - data quality checks, statistics and misc insights.


-- received dividends by portfolio, ticker, cumulative
select 
	ticker, 
	portfolio,
	 date_part('year',date),
	sum(received_dividends) as dividendsreiceived
	, sum(sum(received_dividends)) over (order by ticker, date_part('year',date)) as recordcount_running
from temp_portfelis_
	where ticker = 'AAPL'
group by 1, 2, 3
order by 2
;


--- porftolio data -simulate powerbi, with CTE, values year and month end, 3 month average
-- Year-End, Month-End, and 3-Month Rolling Average

with portfolio_year_end as (
	select 
		portfolio, 		
		date_part('year', date) as date,
		date_part('month', date) as datemonth,
		ticker,
		portfolio_value as value,	
		rank() over (
					partition by 
						portfolio
						, ticker
						,date_part('year', date)
						,date_part('month', date)
					order by
						date desc) AS rank
		
	from temp_portfelis_
	where 1=1)
, aggregated_portfolio as (
		select 
			p.portfolio
			, p.date as date	
			, p.datemonth as month
			, sum(p.value) as value
		from portfolio_year_end p
		where 1=1
			and p.rank=1
		group by 1,2,3
		)
select 
	ap.*
	, avg(ap.value) over (partition by ap.portfolio
				order by  ap.date, ap.month
				rows between 2 preceding and current row) as value_3month_avg
from 	aggregated_portfolio ap
;


----------------------------------------------------------------------------------------
-- use time series, return porftolio returns % quarter on quarter

with calendar as (    
    select generate_series('2019-01-01'::timestamp, '2025-12-31', '1 day')::date as date
),
portfolio_values as (   
     select distinct on (p.portfolio, date_trunc('quarter', p.date)) 
        p.portfolio,
        date_trunc('quarter', p.date) as quarter_start,
        p.portfolio_value as quarter_value
    from temp_portfelis_ p
    order by p.portfolio, DATE_TRUNC('quarter', p.date), p.date
),
quarterly_returns as (
    select 
        pv.portfolio,
        extract(year from pv.quarter_start) as year,
        extract(quarter from pv.quarter_start) as quarter,
        pv.quarter_value as value_at_start,
        lead(pv.quarter_value) over (partition by pv.portfolio order by pv.quarter_start) AS value_at_end
		, ROUND(
					(
						lead(pv.quarter_value) over (partition by pv.portfolio order by pv.quarter_start) 
						- pv.quarter_value
					) 
					/ 
					nullif(pv.quarter_value, 0) * 100
					, 2
				) as return_pct
    from portfolio_values pv
)
select 
	qr.* 
	, sum(qr.value_at_start) over (partition by qr.portfolio, qr.year order by qr.year, qr.quarter) as portfolio_yearly_cumulative_value
from quarterly_returns qr
order by 
	qr.portfolio, qr.year, qr.quarter
;


