/*
 * database for headers, proxy etc reference tables
 */

DROP ROLE IF EXISTS parsers;
CREATE ROLE parsers LOGIN;

DROP DATABASE IF EXISTS parsers;
CREATE DATABASE parsers OWNER parsers;


DROP TRIGGER IF EXISTS user_agent_update_trg ON user_agent;
DROP FUNCTION IF EXISTS user_agent_update_func;


DROP TABLE IF EXISTS user_agent_log;
DROP TABLE IF EXISTS user_agent;


/*
 * table for storing and processing user-agents
 */
CREATE TABLE user_agent (
    user_agent_id   SERIAL,
    software        TEXT NOT NULL,
    title           TEXT NOT NULL UNIQUE,
    version         TEXT,
    os              TEXT,
    hardware        TEXT,
    popularity      TEXT,

    -- эти два параметра планируется использовать в дальнейшей аналитике применения user-agent
    -- к примеру, если errors>100 && successes==0, то данный user-agent имеет смысл исключить из базы
    successes       INTEGER NOT NULL DEFAULT 0, -- общее число успешных применений
    errors          INTEGER NOT NULL DEFAULT 0, -- общее число ошибок, при применении

    insert_tz       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    update_tz       TIMESTAMPTZ,

    PRIMARY KEY (user_agent_id)
);


-- функция и триггер для автоматического обновления поля update_tz
CREATE FUNCTION user_agent_update_func() RETURNS TRIGGER AS
$$
BEGIN
    NEW.update_tz = NOW();
    RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';


CREATE TRIGGER user_agent_update_trg
    BEFORE UPDATE
    ON user_agent
    FOR EACH ROW
    EXECUTE FUNCTION user_agent_update_func()
;


/*
 * table for logging errors when working with user-agents
 */
CREATE TABLE user_agent_log (
    user_agent_log_id SERIAL,

    user_agent_id INTEGER NOT NULL,
    log_tz TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    msg TEXT NOT NULL, -- error message

    FOREIGN KEY (user_agent_id) REFERENCES user_agent (user_agent_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    PRIMARY KEY (user_agent_log_id)
);


/*
 * функция для вставки user-agent без изменения счётчика при наличии такого же user-agent в базе
 * (без необходимости использовать ON CONFLICT DO NOTHING) и с возможностью получить значение
 * user_agent_id для подсчёта числа вставок новых user-agent
 */
DROP FUNCTION IF EXISTS user_agent_insert_func;
CREATE FUNCTION user_agent_insert_func(
    IN in_software      TEXT,
    IN in_title         TEXT,
    IN in_version       TEXT,
    IN in_os            TEXT,
    IN in_hardware      TEXT,
    IN in_popularity    TEXT
) RETURNS INTEGER AS
$$
DECLARE
    p_user_agent_id INTEGER;
BEGIN
    IF NOT EXISTS (SELECT title FROM user_agent WHERE title=in_title) THEN
        WITH cte AS (
            INSERT INTO user_agent (
                software,
                title,
                version,
                os,
                hardware,
                popularity
            ) VALUES (
                in_software,
                in_title,
                in_version,
                in_os,
                in_hardware,
                in_popularity
            ) RETURNING user_agent_id
        ) SELECT cte.user_agent_id INTO p_user_agent_id FROM cte;
    ELSE
        p_user_agent_id := 0;
    END IF;

    RETURN p_user_agent_id;
END;
$$ LANGUAGE 'plpgsql';


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
