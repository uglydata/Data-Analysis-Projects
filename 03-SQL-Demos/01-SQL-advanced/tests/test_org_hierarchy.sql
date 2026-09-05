-- ============================================================
-- Test: org-hierarchy recursive CTE (mirrors "Example 1" / option 1
-- in ../SQL_recursion.sql) against known-by-hand expected values.
--
-- Run with:
--   psql -v ON_ERROR_STOP=1 -f test_org_hierarchy.sql
-- Exits non-zero (via RAISE EXCEPTION) if any assertion fails, which
-- is what the CI workflow (.github/workflows/sql-tests.yml) checks.
-- ============================================================

DROP TABLE IF EXISTS test_results;
DROP TABLE IF EXISTS employees;

CREATE TABLE employees (
    employee_id INT PRIMARY KEY,
    employee_name varchar,
    manager_id int,
    salary int,
    department varchar
);

INSERT INTO employees (employee_id, employee_name, manager_id ,salary ,department) VALUES
(1, 'Alice', null, 12000, 'Executive'),
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
(13, 'Ivy3', 9, 2000, 'Engineering');

-- materialize the same query as SQL_recursion.sql option 1
with recursive levels as (
    select 1 as level, employee_id, employee_name, manager_id, salary, department
    from employees
    where manager_id is null
    union all
    select d.level + 1, e.employee_id, e.employee_name, e.manager_id, e.salary, e.department
    from employees e
        join levels d on e.manager_id = d.employee_id
),
hierarchy as (
    select manager_id, employee_id, salary from employees where manager_id is not null
),
teams as (
    select manager_id, employee_id, salary from hierarchy
    union all
    select h.manager_id, e.employee_id, e.salary
    from hierarchy h
        join teams e on h.employee_id = e.manager_id
)
select
    d.employee_id,
    d.employee_name,
    d.level,
    coalesce(count(t.employee_id), 0) as team_size,
    d.salary + coalesce(sum(t.salary), 0) as budget
into temp test_results
from levels d
    left join teams t on d.employee_id = t.manager_id
group by d.employee_id, d.employee_name, d.level, d.salary;

-- ------------------------------------------------------------
-- assertions - values hand-computed from the employee data above
-- ------------------------------------------------------------
DO $$
DECLARE
    v_budget numeric;
    v_team_size int;
BEGIN
    -- Alice (CEO): controls the entire org
    SELECT budget, team_size INTO v_budget, v_team_size FROM test_results WHERE employee_id = 1;
    IF v_budget <> 159100 OR v_team_size <> 12 THEN
        RAISE EXCEPTION 'Alice (id=1): expected budget=159100 team_size=12, got budget=% team_size=%', v_budget, v_team_size;
    END IF;

    -- Bob: David + Eva + Hank (David's subordinate) report to him
    SELECT budget, team_size INTO v_budget, v_team_size FROM test_results WHERE employee_id = 2;
    IF v_budget <> 99600 OR v_team_size <> 3 THEN
        RAISE EXCEPTION 'Bob (id=2): expected budget=99600 team_size=3, got budget=% team_size=%', v_budget, v_team_size;
    END IF;

    -- Frank: Ivy + her 3 direct reports + Judy report to him
    SELECT budget, team_size INTO v_budget, v_team_size FROM test_results WHERE employee_id = 6;
    IF v_budget <> 29000 OR v_team_size <> 5 THEN
        RAISE EXCEPTION 'Frank (id=6): expected budget=29000 team_size=5, got budget=% team_size=%', v_budget, v_team_size;
    END IF;

    -- Eva: individual contributor, no reports
    SELECT budget, team_size INTO v_budget, v_team_size FROM test_results WHERE employee_id = 5;
    IF v_budget <> 7600 OR v_team_size <> 0 THEN
        RAISE EXCEPTION 'Eva (id=5): expected budget=7600 team_size=0, got budget=% team_size=%', v_budget, v_team_size;
    END IF;

    RAISE NOTICE 'org hierarchy test: all assertions passed';
END $$;
