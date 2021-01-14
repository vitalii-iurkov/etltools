# directories and files

+ ~dir~ `ua_sample_data` - directory for script `split_sample_data_into_txt_files.py` (clear data from real database)


# algorithm to create `user_agent` table in `test` database for unit testings

## **notes** : for unit testing we need only steps 1, 2, 4 and create `test` database

## 1. create `parsers` database dump, schema only

```bash
pg_dump -h localhost -p 5432 -d parsers -U parsers -v --clean --if-exists --schema-only --no-owner > parsers_dump_schema_only.sql
```

## 2. get sample data from `parsers` database, `user_agent` table

```bash
psql -h localhost -p 5432 -d parsers -U postgres --tuples-only --no-align --field-separator=$'\t' -f export_random_user_agents.sql -o parsers_dump_20210106_sample_user_agents_data.sql
```

## 3. create objects in `test` database

```bash
psql -h localhost -p 5432 -d test -U test -f parsers_dump_schema_only.sql
```

## 4. insert sample data into text files in `ua_sample_data` subdirectory

```bash
./split_sample_data_into_txt_files.py
```

## 5. execute `UserAgent.insert_user_agents_from_files(...)` to insert data from sample text files into `test` database
