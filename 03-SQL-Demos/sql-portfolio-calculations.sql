-- PART 1

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

----------------------------------------------------------------------------------------
-- PART 2

-- different SQLs - data quality checks, statistics and misc insights.
-- received dividends by portfolio, ticker, cumulative, average for portfolio dividends last 3 years
select 
--	ticker, 
	portfolio,
	 date_part('year',date),
	sum(received_dividends) as dividendsreiceived
	, sum(sum(received_dividends)) over (partition by partition order by date_part('year',date)) as recordcount_running
	, avg(sum(received_dividends)) over (partition by portfolio order by date_part('year',date)
		rows between 2 preceding and current row) as dividends_avg_last_3month
from temp_portfelis_
	where --		and ticker = 'AAPL'
		and portfolio like '%Home'
		and  date_part('year',date)<>2025
group by 1, 2
order by 2
;

----------------------------------------------------------------------------------------
--- porftolio data -simulate powerbi, with CTE, provide porftolio values year and month end and last 3 month average
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


----------------------------------------------------------------------------------------
-- PART 3

/*
Query calculates monthly portfolio values using timeseries data.
Tables Used: calendar, stock_and_dividends, portfolio_info

Approach:
	Excludes duplicates from stock prices.
	Retrieves monthly closing prices using window functions.
	Computes portfolio values and dividends for each stock.
	Uses CTEs, window functions, and LEFT JOINs to align stock data with portfolio holdings.
*/

with calendar as (
    select generate_series('2019-01-01'::timestamp, '2025-12-31', '1 month')::date as date
)
-- monthly prices 
, deduped_prices as (
    select 
      p.ticker
    , last_value(date) over (partition by ticker, date_part('year', date), date_part('month', date) order by date asc
      rows between unbounded preceding and unbounded following) as month_closing_day
    , max(date) over (partition by ticker, date_part('year', date), date_part('month', date)) as month_closing_day2
    , last_value(closing_price) over (partition by ticker, date_part('year', date), date_part('month', date) order by date asc
      rows between unbounded preceding and unbounded following) as month_closing_price
    , max(closing_price) over (partition by ticker, date_part('year', date), date_part('month', date)) as month_max_price
    , min(closing_price) over (partition by ticker, date_part('year', date), date_part('month', date)) as month_min_price
    , sum(dividend_amount) over (partition by ticker, date_part('year', date), date_part('month', date)) as dividends_month
    , row_number() over (
        partition by ticker, date_part('year', date), date_part('month', date)
        order by date desc
      ) as row_num
    from stock_and_dividends p
    where 1=1
)
-deduped prices
, stock_monthly_prices as (
    select 
      ticker
    , month_closing_day
    , month_closing_day2
    , month_closing_price
    , month_max_price
    , month_min_price
    , dividends_month
    from deduped_prices
    where row_num = 1
)
--calculate monthly value, max during month, min during month
select  
      c.date as date
    , pi.ticker
    , pi.shares
    , smp.month_closing_price as closing_price
    , (pi.shares * smp.month_closing_price) as portfolio_value
    , (pi.shares * smp.dividends_month) as received_dividends
    , pi.name as name
    , pi.portfolio_name as portfolio
    , (pi.shares * smp.month_max_price) as portfolio_value_max
    , (pi.shares * smp.month_min_price) as portfolio_value_min
from calendar c
left join portfolio_info pi on 
    (
      (date_part('year', pi.date) = date_part('year', c.date)
        and date_part('month', pi.date) = date_part('month', c.date))
      or (pi.date <= c.date)
    )
left join stock_monthly_prices smp 
    on date_part('year', smp.month_closing_day) = date_part('year', c.date)
    and date_part('month', smp.month_closing_day) = date_part('month', c.date)
    and smp.ticker = pi.ticker
where 1=1
  and pi.ticker = 'NOK'
  and pi.portfolio_name = 'PortfolioHome'
order by 1, 2;

----------------------------------------------------------------------------------------------------------------------------------

--Calculate monthly returns for each stock ticker.
--Identify top 3 best-performing and worst-performing stocks per month.
--Future improvement: Extend to quarterly and yearly time-series analysis.
--Techniques Used: CTE  to structure data, Window functions (lag(), rank(), sum() over()) for ranking and performance tracking.
--Time-series joins using a generated calendar.


with calendar as (
   
   select generate_series('2019-01-01'::timestamp, '2025-12-31', '1 month')::date as date
)
-- daily prices- get closing price on monthly basis
, deduped_prices as (
    select 
      p.ticker
    , first_value(date) over (partition by ticker, date_part('year', date), date_part('month', date) order by date desc
      rows between unbounded preceding and unbounded following) as month_closing_day
    , last_value(closing_price) over (partition by ticker, date_part('year', date), date_part('month', date) order by date asc 
      rows between unbounded preceding and unbounded following) as month_closing_price
    , max(closing_price) over (partition by ticker, date_part('year', date), date_part('month', date)) as month_max_price
    , min(closing_price) over (partition by ticker, date_part('year', date), date_part('month', date)) as month_min_price
    , sum(dividend_amount) over (partition by ticker, date_part('year', date), date_part('month', date)) as dividends_month
    , row_number() over (
        partition by ticker, date_part('year', date), date_part('month', date)
        order by date desc
      ) as row_num
    from stock_and_dividends p
    where 1=1
)
-- deduplicated monthly based stock price table
, stock_monthly_prices as (
    select 
      ticker
    , month_closing_day	
    , month_closing_price
    , month_max_price
    , month_min_price
    , lag(month_closing_price) over (
        partition by ticker
        order by month_closing_day
      ) as m_closing_price_prev
    from deduped_prices
    where row_num = 1
)
-- calculate rank for each of the ticker on monthly basis -return top 3 and worst 3
, portfolio_ranked as (
    select  
      c.date as date
    , smp.*
    , smp.month_closing_price - smp.m_closing_price_prev as mom_return
    , round(100 * (smp.month_closing_price - smp.m_closing_price_prev) / nullif(smp.m_closing_price_prev, 0), 2) as mom_perc
    , rank() over (partition by c.date order by ((smp.month_closing_price - smp.m_closing_price_prev) / nullif(smp.m_closing_price_prev, 0)) desc) as rank_best
    , rank() over (partition by c.date order by ((smp.month_closing_price - smp.m_closing_price_prev) / nullif(smp.m_closing_price_prev, 0)) asc) as rank_worst
    from calendar c
    left join stock_monthly_prices smp on 
        date_part('year', smp.month_closing_day) = date_part('year', c.date)
        and date_part('month', smp.month_closing_day) = date_part('month', c.date)
    where 1=1
      and date_part('year', c.date) = '2024'
)
-- return top 3 and worst 3 tickers by performance on monthly basis, for each ticker give number of times ticker has been worst or best case category
select 
      *
    , case 
        when rank_best < 4 then 'top 3 performing'
        when rank_worst < 4 then 'worst 3 performing'
        else '' 
      end as category
    , sum(
        case when rank_best < 4 then 1 else 0 end
      ) over (partition by ticker) as top_performing_count	
    , sum(
        case when rank_worst < 4 then 1 else 0 end
      ) over (partition by ticker) as worst_performing_count	
from portfolio_ranked 
where 1=1
  and (rank_worst < 4 or rank_best < 4)
order by date, rank_best, rank_worst;

