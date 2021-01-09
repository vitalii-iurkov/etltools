# Description

Some tools for data processing.

# Project structure

+ parsers :
    + base_parser.py
        + BaseParser
    + user_agents.py
        + UserAgent
    + (postgresql db) parsers
        + user_agent
        + user_agent_log
        + user_agent_insert_func(...)
+ pg_tools :
    + db_config.py
        + DBConfig
    + pg_connector.py
        + PgConnector
        + PgConnectorError
+ tests :
    + test_db_config.py
        + DBConfigTest
    + test_pg_connector.py
        + PgConnectorTest
+ logging.conf
+ test_logging.conf


# Additional for development purproses

## unittest

Run tests and exclude from output information about all Exceptions and Traceback.

```
clear && python -m unittest discover -v -b
```

## for VS Code 

### `.vscode/settings.json`

```
{
    "python.languageServer": "Jedi",
}
```

### Unresolved import warnings ( - doesn't work)

https://github.com/microsoft/python-language-server/blob/master/TROUBLESHOOTING.md#unresolved-import-warnings
