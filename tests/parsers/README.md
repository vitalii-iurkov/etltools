# Sample text files, database dumps and other data for testing `parsers` database.

# 1. create `parsers` database dump, schema only

```bash
pg_dump -h localhost -p 5432 -d parsers -U parsers -v --clean --if-exists --schema-only --no-owner > parsers_dump_schema_only.sql
```

# 2. create objects in `test` database

```bash
psql -h localhost -p 5432 -d test -U test -f parsers_dump_schema_only.sql
```
