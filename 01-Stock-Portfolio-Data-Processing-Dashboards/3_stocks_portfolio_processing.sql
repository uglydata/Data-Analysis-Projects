-- stock price loading into
/*

drop table stock_and_dividends;
delete from stock_and_dividends;

CREATE TABLE stock_and_dividends (
    date DATE,
    ticker VARCHAR(10),
    closing_price NUMERIC(10, 2),
    dividend_amount NUMERIC(10, 2)
);


\copy stock_and_dividends (date, ticker, closing_price, dividend_amount) FROM '2_stock_prices_and_dividends.csv' WITH CSV HEADER;
drop table portfolio_info;

delete from portfolio_info;

CREATE TABLE portfolio_info (
    date DATE NOT NULL,          -- Date of the portfolio entry
    ticker VARCHAR(10) NOT NULL, -- Stock ticker symbol (e.g., AAPL, NOK)
    shares INT NOT NULL,         -- Number of shares held
	name VARCHAR(50) NOT NULL, -- Stock ticker symbol (e.g., AAPL, NOK)
	portfolio_name VARCHAR(50) NOT NULL,
    PRIMARY KEY (date, ticker,portfolio_name)   -- Composite primary key to ensure uniqueness
);
\copy portfolio_info (date, ticker, shares, name, portfolio_name) FROM '0_portfolio_setup.csv' WITH CSV HEADER;
*/

/*
select * from stock_and_dividends WHERE ticker = 'AGNC' and EXTRACT(YEAR FROM DATE) = 2025;
select * from portfolio_info WHERE ticker = 'AAPL';

select pi.*, sd.* from portfolio_info pi join stock_and_dividends sd on sd.ticker=pi.ticker where pi.ticker='AAPL' ORDER BY sd.date desc;
*/

-- save output in csv "4_data_import_into_powerbi.csv" - for import into powerbi

-- returns value of portfolio and received dividends for portfolios positions

WITH calendar AS (
    -- Generate a series of dates for the calendar
    SELECT generate_series('2019-01-01'::timestamp, '2025-12-31', '1 day')::date AS date
),
portfolio_extended AS (
    -- Combine calendar with portfolio_info and stock_and_dividends
    SELECT
        c.date,
        p.ticker,
        COALESCE(p.shares, 0) AS shares,
        s.closing_price,
        s.dividend_amount -- Include dividends
		, p.name
		, p.portfolio_name as portfolio
    FROM
        calendar c
    LEFT JOIN LATERAL (
        SELECT *
        FROM portfolio_info p
        WHERE p.date <= c.date
        ORDER BY p.date DESC
    ) p ON true -- Always join for each ticker
    LEFT JOIN stock_and_dividends s
    ON c.date = s.date AND p.ticker = s.ticker
),
filled_prices AS (
    -- Forward-fill `closing_price` for each ticker
    SELECT
        date,
        ticker,
        shares,
        COALESCE(
            closing_price,
            -- Subquery to retrieve the most recent non-NULL price
            (
                SELECT closing_price
                FROM portfolio_extended sub
                WHERE sub.ticker = main.ticker AND sub.date < main.date
                AND sub.closing_price IS NOT NULL
                ORDER BY sub.date DESC
                LIMIT 1
            )
        ) AS filled_closing_price,
        dividend_amount
		, name
		, portfolio
    FROM
        portfolio_extended main
)
SELECT
    date,
    ticker,
    shares,
    filled_closing_price AS closing_price,
    shares * filled_closing_price AS portfolio_value,
    CASE 
        WHEN dividend_amount IS NOT NULL THEN shares * dividend_amount
        ELSE 0
    END AS received_dividends -- Calculate received dividends
	, name
	, portfolio
FROM
    filled_prices
WHERE ticker IS NOT NULL
ORDER BY ticker, date;
