/*
 * database for user-agents, proxies etc reference tables
 */

DROP ROLE IF EXISTS parsers;
CREATE ROLE parsers LOGIN;

DROP DATABASE IF EXISTS parsers;
CREATE DATABASE parsers OWNER parsers;
