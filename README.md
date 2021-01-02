# Description

Some tools for data processing.

# Project structure

+ parsers :
    + base_parser.py
        + BaseParser
    + user_agents.py
        + UserAgent
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


# Additional

## unittest

Run tests and exclude from output information about all Exceptions and Traceback.

```
python -m unittest discover -v -b
```
