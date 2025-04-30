--2025.04.30. v1
/*
    Example of recursion usage - use CTE and 'recursive'
    
    2 examples: 
        a. organizational hierarchy
        b. fibonacci
*/
----------------------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------
-- Example 1: Organizational hierarchy - employees and managers
/*
 
+----------------+---------+
| Column Name    | Type    | 
+----------------+---------+
| employee_id    | int     |
| employee_name  | varchar |
| manager_id     | int     |
| salary         | int     |
| department     | varchar |
+----------------+----------+
-- Create table
drop table employees
CREATE TABLE employees (
    employee_id INT PRIMARY KEY,
    employee_name varchar,
	manager_id int,
	salary int,
	department varchar)

delete from employees where 1=1

-- Insert rows
INSERT INTO employees (employee_id, employee_name, manager_id ,salary ,department) VALUES
(1, 'Alice', null, 12000, 'Executuve'),
(2, 'Bob', 1, 11000, 'Sales'),
(3, 'Charlie', 1, 10000, 'Engineering'),
(4, 'David', 2, 75000, 'Sales'),
(5, 'Eva', 2, 7600, 'Sales'),
(6, 'Frank', 3, 9000, 'Engineering'),
(7, 'Grace', 3, 8500, 'Engineering'),
(8, 'Hank', 4, 6000, 'Sales'),
(9, 'Ivy', 6, 7000, 'Engineering'),
(10, 'Judy', 6, 7000, 'Engineering'),
(11, 'Ivy1', 9, 1000, 'Engineering'),
(12, 'Ivy2', 9, 3000, 'Engineering'),
(13, 'Ivy3', 9, 2000, 'Engineering')

Goal:
Write a solution to analyze the organizational hierarchy and answer the following:

Hierarchy Levels: 
	For each employee, determine their level in the organization (CEO is level 1, employees reporting directly to the CEO are level 2, and so on).

Team Size: 
	For each employee who is a manager, count the total number of employees under them (direct and indirect reports).

Salary Budget: 
	For each manager, calculate the total salary budget they control (sum of salaries of all employees under them, including indirect reports, plus their own salary).

*/

-- option 1
with recursive levels as (
    -- calc levels - ceo 1, next level: 2, .., etc
    select 
        1 as level, 
        employee_id, 
        employee_name, 
        manager_id, 
        salary, 
        department
    from employees
    where manager_id is null

    union all

    -- recursion: find employees reporting to previous level
    select
        d.level + 1,
        e.employee_id,
        e.employee_name,
        e.manager_id,
        e.salary,
        e.department
    from employees e
    	join levels d on e.manager_id = d.employee_id
),
hierarchy as (
    -- build employee-manager relationships
    select 
        manager_id,
        employee_id,
        salary
    from employees
    where manager_id is not null
),
teams as (
    -- recursive expansion: all subordinates under each manager - each manager id for every subordinate
    select 
        manager_id,
        employee_id,
        salary
    from hierarchy

    union all

    select 
        h.manager_id,
        e.employee_id,
        e.salary
    from hierarchy h
    	join teams e on h.employee_id = e.manager_id
)
, results as (
select 
    d.employee_id,
    d.employee_name,
--    d.department,
    d.level,
    coalesce(count(t.employee_id), 0) as team_size,
    d.salary + coalesce(sum(t.salary), 0) as budget
from levels d
	left join teams t on d.employee_id = t.manager_id
group by 
    d.employee_id, 
    d.employee_name, 
--    d.department, 
    d.level, 
    d.salary
order by 
    d.level asc, 
    budget desc, 
    d.employee_name asc
)
select * from results
--select * from teams order by 1, 2


---------------------------------------------------------------------
-- just teams- every's manager each subordinate -direct or indirect

with recursive managers as (
	select employee_id, employee_name, manager_id, salary, department from employees where manager_id is not null
	union all
	select e.employee_id, e.employee_name, m.manager_id, e.salary, e.department
	from employees e
		join managers m on m.employee_id = e.manager_id
)
select * 
, count(employee_id) over (partition by manager_id) as subordinates
, sum(salary) over (partition by manager_id) as budget -- without manager's salary - should add
from managers
where 1=1
--	and employee_id=4
order by manager_id
;


-----------------------------------------------------------------------
-- option 2
WITH RECURSIVE level_cte AS (
	--levels
	SELECT employee_id, manager_id, 1 AS level, salary 
	FROM Employees
	UNION ALL
	SELECT a.employee_id, b.manager_id, level + 1, a.salary
	FROM level_cte a
	JOIN Employees b on b.employee_id = a.manager_id
	)
,    employee_with_level AS (
	SELECT 
		a.employee_id, a.employee_name, a.salary, b.level 
			FROM Employees a, 
				(SELECT employee_id, level 
				FROM level_cte  
				WHERE manager_id IS NULL) b 
				WHERE a.employee_id = b.employee_id
)
, results as (
SELECT 
	a.employee_id, a.employee_name, a.level, COALESCE(b.team_size, 0) AS team_size,
    a.salary + COALESCE(b.budget, 0) AS budget
FROM employee_with_level a
	LEFT JOIN 
			(
					SELECT manager_id AS employee_id, COUNT(*) AS team_size, SUM(salary) AS budget 
						FROM level_cte 
						WHERE manager_id IS NOT NULL 
					GROUP BY manager_id
			) b	ON a.employee_id = b.employee_id
ORDER BY 
	level,
	budget DESC, 
	employee_name
)
--select * from results
select * from level_cte
;

-----------------------------------------------------------------------
-- option 3: close to option 1, different implementation
WITH  recursive cte AS (
  SELECT e.employee_id , e.employee_name, COALESCE(e.manager_id, 0) AS manager_id , e.salary, 1 AS lvl
	FROM Employees e
  	WHERE e.manager_id IS NULL
  UNION ALL
  SELECT e.employee_id , e.employee_name, e.manager_id , e.salary, c.lvl+1 AS lvl
	FROM cte c
	JOIN Employees e ON (e.manager_id = c.employee_id)
)
, tree AS (
  SELECT * FROM cte
)
, managers AS (
  SELECT t.employee_id AS r_m, t.employee_id, t.manager_id, t.salary, t.lvl
    FROM tree t
  UNION ALL
  SELECT m.r_m, t.employee_id, t.manager_id, t.salary, m.lvl
    FROM managers m
    JOIN tree t ON (t.manager_id = m.employee_id)
)
, pre AS (
    SELECT m.r_m AS employee_id, COUNT(m.employee_id) - 1 AS team_size, SUM(m.salary) AS budget
    FROM managers m
    GROUP BY m.r_m
)
SELECT p.employee_id, t.employee_name, t.lvl AS level, p.team_size, p.budget
    FROM pre p
    JOIN tree t ON (t.employee_id = p.employee_id)
    --JOIN Employees e ON (e.employee_id = p.employee_id)
    ORDER BY t.lvl, p.budget DESC

	
----------------------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------
-- Example 2: Fibonacci numbers - recursive CTE

-- 1.calculate fibonacci, give number of numbers
-- 2.calc distribution of leading numbers - in generate series


with recursive fibonacci as (
    select 1 as n, 0 as fibnumb, 1 as next_fib  
    union all
    select n + 1, next_fib, fibnumb + next_fib  
    from fibonacci
    where n < 7
)
select n, fibnumb, next_fib
from fibonacci;
