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

    -- these two parameters are for analytics purposes for the User-Agent
    -- for example, if errors>100 && successes==0, then exclude this user-agent from the query results
    successes       INTEGER NOT NULL DEFAULT 0, -- total number of successful usages of the User-Agent
    errors          INTEGER NOT NULL DEFAULT 0, -- total number of error usages of the User-Agent

    insert_tz       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    update_tz       TIMESTAMPTZ,

    PRIMARY KEY (user_agent_id)
);


/*
 * function and trigger to autorefresh field `update_tz`
 */
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
 * table for logging errors when working with User-Agents
 * (this table is populated with data only from the client applications)
 */
CREATE TABLE user_agent_log (
    user_agent_log_id   SERIAL,

    user_agent_id       INTEGER NOT NULL,
    log_tz              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    msg                 TEXT NOT NULL, -- error message

    FOREIGN KEY (user_agent_id) REFERENCES user_agent (user_agent_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    PRIMARY KEY (user_agent_log_id)
);


/*
 * additional function to insert User-Agent (without `ON CONFLICT DO NOTHING`)
 * returns `user_agent_id` for new User-Agent or 0 if this User-Agent is already in the table
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
            ) RETURNING user_agent_id -- get new User-Agent `user_agent_id`
        ) SELECT cte.user_agent_id INTO p_user_agent_id FROM cte;
    ELSE
        p_user_agent_id := 0; -- User-Agent is already in the table
    END IF;

    RETURN p_user_agent_id;
END;
$$ LANGUAGE 'plpgsql';
