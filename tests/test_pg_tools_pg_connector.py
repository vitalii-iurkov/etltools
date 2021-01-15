import logging
import logging.config
import os
import unittest
from dataclasses import asdict

from etltools.local_settings import test_config
from etltools.pg_tools.db_config import DBConfig
from etltools.pg_tools.pg_connector import PgConnector, PgConnectorError


class PgConnectorTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # apply logging during testing
        logging.config.fileConfig(fname='test_logging.conf', disable_existing_loggers=False)
        cls.logger = logging.getLogger(os.path.basename(__file__))

    def test_incorrect_connection_configuration_type(self):
        # test `str` and `dict` connection parameters
        test_data = [
            (PgConnectorError, PgConnector, str(test_config)),
            (PgConnectorError, PgConnector, asdict(test_config)),
        ]

        for exception, callable, args in test_data:
            with self.subTest(exception=exception, callable=callable, args=args):
                self.assertRaises(exception, callable, args)

    def test_incorrect_connection_configuration_data(self):
        configs = [
            asdict(test_config) | {'host':'fakehost'},
            asdict(test_config) | {'port':'3306'},
            asdict(test_config) | {'database':'fakedatabase'},
            asdict(test_config) | {'user':'fakeuser'},
            asdict(test_config) | {'password':'*****'},
        ]

        for config in configs:
            with self.subTest(config=config):
                with self.assertRaises(PgConnectorError):
                    with PgConnector(DBConfig(**config)) as db:
                        pass

    def test_ddl_dml(self):
        ddl_drop_table = 'DROP TABLE IF EXISTS test;'
        ddl_create_table = (
            'CREATE TABLE test ('
            '  test_id SERIAL PRIMARY KEY, '
            '  amount INTEGER NOT NULL '
            ');'
        )

        dml_insert_test_data = 'INSERT INTO test (amount) SELECT s1.n FROM generate_series(1, 10000) AS s1(n);'

        # for commit testing
        dml_select_sum = 'SELECT SUM(amount) FROM test;'
        select_sum_result = sum(range(1, 10000+1))

        # for rollback testing
        dml_select_count = 'SELECT COUNT(*) FROM test;'
        select_count_result = 0 # difference for count between before query `insert` and after rollback query `insert`

        with PgConnector(test_config) as db:
            # create test table
            db.execute(ddl_drop_table)
            db.execute(ddl_create_table)
            db.commit()

            # insert test data and rollback
            rollback_result = db.execute(dml_select_count)[0][0] # before inserting test data
            db.execute(dml_insert_test_data)
            db.rollback()
            rollback_result -= db.execute(dml_select_count)[0][0] # after rollback inserting test data

            # insert test data and commit
            db.execute(dml_insert_test_data)
            db.commit()
            commit_result = db.execute(dml_select_sum)
            if commit_result:
                commit_result = commit_result[0][0]

            # drop test table
            db.execute(ddl_drop_table)
            db.commit()

        test_data = [
            (select_count_result, rollback_result),
            (select_sum_result, commit_result),
        ]
        for expected_value, received_value in test_data:
            with self.subTest(expected_value=expected_value, received_value=received_value):
                self.assertEqual(expected_value, received_value)
