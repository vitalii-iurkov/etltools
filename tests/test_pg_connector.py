# -*- coding: utf-8 -*-

import unittest

from local_settings import test_config
from pg_tools.db_config import DBConfig
from pg_tools.pg_connector import PgConnector, PgConnectorError


class PgConnectorTest(unittest.TestCase):

    def setUp(self):
        self.ddl_drop = 'DROP TABLE IF EXISTS test;'
        self.ddl_create = (
            'CREATE TABLE test ('
            '  test_id SERIAL PRIMARY KEY, '
            '  amount INTEGER NOT NULL '
            ');'
        )
        self.dml_insert_data = 'INSERT INTO test (amount) SELECT s1.n FROM generate_series(1, 10000) AS s1(n);'
        self.dml_select_data = 'SELECT SUM(amount) FROM test;'
        self.select_result = sum(range(1, 10000+1))

    def tearDown(self):
        pass

    def test_incorrect_connection_configuration_type(self):
        self.assertRaises(
            PgConnectorError,
            PgConnector,
            "host='localhost' port='5432' database='test' user='test' password='12345'"
        )

    def test_incorrect_connection_configuration(self):
        with self.assertRaises(PgConnectorError):
            with PgConnector(DBConfig(host='localhost', port='5432', database='test', user='test', password='12345')) as db:
                pass

    def test_ddl_dml(self):
        with PgConnector(test_config) as db:
            db.cur.execute(self.ddl_drop)
            db.cur.execute(self.ddl_create)
            db.conn.commit()
            db.cur.execute(self.dml_insert_data)
            db.conn.commit()
            db.cur.execute(self.dml_select_data)
            result = db.cur.fetchall()[0][0]
            db.cur.execute(self.ddl_drop)

            self.assertEqual(result, self.select_result)
