# `parsers_database_ddl.sql`

SQL code for creating `parsers` database and role `parsers`.

# User-Agent files and objects

```
+ user_agent_ddl.sql
+ user_agent_dml.sql
+ user_agent.py
    + `UserAgentError(Exception)`               : class
    + `UserAgent(Logger)`                       : class
        + DEFAULT_USER_AGENT_TITLE              : class attribute
        + SUCCESSES_FIELD                       : class attribute
        + ERRORS_FIELD                          : class attribute
        + title                                 : property
        + _config                               : property
        + update_usage(...)                     : method
        + insert_user_agents_from_files(...)    : method
```

# `for_testings_only`

This directory contains additional files and instructions for preparing for unit testing.
