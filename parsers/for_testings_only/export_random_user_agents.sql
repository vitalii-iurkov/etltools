/*
 * get random 20 rows with `hardware='Computer'` and random 10 row with `hardware!='Computer'`
 */
WITH cte AS (
    (SELECT * FROM user_agent WHERE hardware='Computer' AND software IN ('Chrome', 'Firefox') ORDER BY RANDOM() LIMIT 20)
    UNION
    (SELECT * FROM user_agent WHERE hardware!='Computer' AND software IN ('Chrome', 'Firefox') ORDER BY RANDOM() LIMIT 10)
)
SELECT
    software,
    title,
    version,
    os,
    hardware,
    popularity
FROM cte
ORDER BY software, user_agent_id;
