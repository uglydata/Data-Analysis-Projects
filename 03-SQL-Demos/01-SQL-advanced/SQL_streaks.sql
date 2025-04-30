-- streaks misc
/*

General Algorithm Steps for Streak Calculation
1. Base CTE:
	Select necessary columns.
	Use LAG() to look at previous row’s value.
	Define a break flag (1 = streak break, 0 = continue streak) based on your condition.

2. Streak ID CTE:
	Use SUM(break_flag) OVER (ORDER BY id/season) to assign a streak ID for each group of continuous rows.
	Streak Analysis CTE (optional):
	Calculate count of rows per streak (COUNT(*) OVER (PARTITION BY streak_id)).
	Calculate aggregations (min, max, etc.) if needed.

3. Final Selection:
	Filter to keep only streaks that meet your minimum length (e.g., at least 3 or 10 rows).

	Variants
	RowID/Delta Method:
	When IDs are perfectly sequential, use id - ROW_NUMBER() trick to create streaks by constant delta.
	
	Sliding Window Method:
	Instead of cumulative sums, use a moving window (ROWS BETWEEN n PRECEDING AND CURRENT ROW) to check conditions across limited rows.


*/
----------------------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------
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

-- misc sql training 24.03.2025.
-- calc streaks
-- query nba players with at least 10 seasons with 20pts+
-- NBA Players - Streaks of 20+ Points per Season

-- option 1
with lagged as (select 
	player_name
	, pts
	, season
	, lag(pts) over (partition by player_name order by season) prev_season_points
from player_seasons 
)
, streaked as (select 
	player_name
	, season
	, pts
	, prev_season_points
	, case when pts>20 and prev_season_points>20 then 0 else 1 end as streak_break
from lagged
where 1=1
--	and lower(player_name) like '%harden%'
)
, streaks as (
select 
	player_name
	, season
	, pts
	, prev_season_points
	, streak_break
	, sum(case when streak_break=1 then 1 else 0 end) over (partition by player_name order by season) as streakid
	, sum(streak_break) over (partition by player_name order by season) as streak_id
from streaked	
where 1=1
	
	)
select 
	player_name
	, max(pts), min(pts), max(season), min(season), max(season) - min(season) + 1 as numb_of_seasons
from streaks
where 1=1
--	and lower(player_name) like '%harden%'
group by player_name, streakid	
-- zach wilson approach:
--having max(pts)>20	and  max(season) - min(season) + 1 > 10
-- or simpler imho
having count(season)>10
order by 1	
;

-- option 2
with lagged as (select 
	player_name
	, pts
	, season
	, case when pts>20 and lag(pts) over (partition by player_name order by season)>20 then 0 else 1 end as streak_br
from player_seasons 
)
, streaked as (select 
	player_name
	, season
	, pts
	, streak_br
	, sum(case when streak_br=0 then 1 else 0 end) over (partition by player_name order by season rows between 9 preceding and current row) as last10
from lagged
where 1=1
)
select 
	player_name, max(pts), min(pts), max(season), min(season), max(season) - min(season) + 1 as numb_of_seasons
from streaked
	where 1=1
	and last10>=10
--	and lower(player_name) like '%harden%'
group by player_name
order by 1
;


--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
-- NBA Players - 2nd Highest Points in Season, 3-Year Streak
-- give me the player who got the 2nd highest pts in every season for at least 3 seasons in row
with ranked as (
	select 	
		player_name
		, pts
		, season
		, rank() over (partition by season order by pts desc) ranked
	from player_seasons 	
)
, rank2d as (
select * from ranked
where 1=1 
and ranked=2
)
, rrr as (
select 
	*
	, lag(player_name, 1) over (order by season) as prev2nd
	, lag(player_name, 2) over (order by season) as prev3rdd
from rank2d
)
, results as (
select player_name, min(season), max(season) 
from rrr
where 1=1
	and player_name=prev2nd and player_name=prev3rdd
--	and lower(player_name) like '%harden%'
group by 1
--order by season
)
select * 
from results 
--order by season


----------------------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------
-- Stadium Visits - Streaks of High Attendance (People > 100)

-- Create table
CREATE TABLE stadium (
    id INT PRIMARY KEY,
    visit_date DATE,
    people INT)
delete from stadium where 1=1
-- Insert rows
INSERT INTO stadium (id, visit_date, people) VALUES
(1, '2017-01-01', 10),
(2, '2017-01-02', 109),
(3, '2017-01-03', 150),
(4, '2017-01-04', 99),
(5, '2017-01-05', 145 ),
(6, '2017-01-06', 1455),
(7, '2017-01-07', 200),
(8, '2017-01-08', 300),
(9, '2017-01-09', 40),
(10, '2017-01-10', 500),
(11, '2017-01-11', 20),
(12, '2017-01-12', 182),
(13, '2017-01-13', 177),
(14, '2017-01-14', 400)

---

-- identify valid rows
-- check if sequental is valid -if yes, do not change id, if no-add up-change streak id
-- count rows in streak id
-- return only count>2

-- option 1
with aaa as (
    select    
            s1.id as id, 
            s1.visit_date
        , s1.people as l0    
        , case when (s1.people<100 or lag(s1.people,1) over (order by s1.id) < 100 ) 
            or (s1.people<100 and lag(s1.people,1) over (order by s1.id) is null) 
            then 1 else 0 end as isvalidid        
    from stadium s1
    where 1=1
)
, streaks as (
    select 
        *
        ,  SUM(CASE WHEN isvalidid=1 THEN 1 ELSE 0 END)
                OVER (ORDER BY id) as streakid 
    from aaa
)
, streakscount as (
select 
    id, visit_date, l0 as people, streakid
    , count(id) over (partition by streakid) as strc
from streaks 
)
select 
    id, visit_date, people , streakid, strc
from streakscount
where 1=1
--    and strc >2
order by id asc
;

-- improved version->2nd cte is better, more efficient

-- identify valid rows
-- check if sequental is valid -if yes, do not change id, if no-add up-change streak id
-- count rows in streak id
-- return only count>2

-- option 2

WITH base AS (
    SELECT    
        id, 
        visit_date,
        people,
        CASE             WHEN people < 100 OR COALESCE(LAG(people) OVER (ORDER BY id), 0) < 100 
            THEN 1             ELSE 0         END AS break_flag
    FROM stadium
),
streaks AS (
    SELECT 
        *,
        SUM(break_flag) OVER (ORDER BY id) AS streak_id
    FROM base
),
streak_counts AS (
    SELECT 
        id, 
        visit_date, 
        people, 
        streak_id,
        COUNT(*) OVER (PARTITION BY streak_id) AS streak_length
    FROM streaks
)
SELECT 
    id, 
    visit_date, 
    people
	, streak_id, streak_length
FROM streak_counts
WHERE 1=1
	--and streak_length >= 3
ORDER BY id;

-- option 3: rowid
-- usable only if id are definetily 1 by 1 in order

 with base as (SELECT 
        *
        , row_number() OVER (ORDER BY id) AS rn
		, id - row_number() OVER (ORDER BY id) as delta
    FROM stadium
	where 1=1
		and people>100)
select a.* from (select *
	, count(id) over (partition by delta) as n
from 	base ) as a
where 1=1
	and a.n>2
order by id
;

-- option 4: rowid 
-- usable only if id are definetily 1 by 1 in order

 with base as (SELECT 
        *
        , row_number() OVER (ORDER BY id) AS rn
		, id - row_number() OVER (ORDER BY id) as delta
    FROM stadium
	where 1=1
		and people>100)
select * 
from base where delta in (select delta from 	base group by delta having count(delta)>2) 
order by id
;

