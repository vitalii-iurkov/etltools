/*
 * various DML code for testing purposes
 */
SELECT * FROM user_agent;


SELECT
    hardware,
    COUNT(*) AS total
FROM user_agent
GROUP BY hardware
ORDER BY total DESC, hardware
;


SELECT title FROM user_agent ORDER BY update_tz NULLS FIRST, title;


-- show updated rows; for debugging purposes
SELECT
    user_agent_id,
    title,
    successes,
    errors,
    update_tz
FROM user_agent
WHERE 1=2
    OR (update_tz IS NOT NULL)
    OR (successes+errors>0)
ORDER BY update_tz;


(SELECT * FROM user_agent WHERE hardware='Computer' AND software IN ('Chrome', 'Firefox') ORDER BY RANDOM() LIMIT 20)
UNION
(SELECT * FROM user_agent WHERE hardware!='Computer' AND software IN ('Chrome', 'Firefox') ORDER BY RANDOM() LIMIT 10)
ORDER BY software, user_agent_id;


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
