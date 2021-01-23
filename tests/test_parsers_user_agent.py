import logging
import logging.config
import os
import random
import subprocess
import time
from dataclasses import asdict

import unittest

from etltools.pg_tools.db_config import DBConfig
from etltools.local_settings import test_config
from etltools.parsers.user_agent import UserAgent, UserAgentError
from etltools.pg_tools.pg_connector import PgConnector, PgConnectorError
from etltools.tests.parsers._test_db import TestDB


class UserAgentTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        '''
        the `test` database and the role `test` must be created in advance by the commands:
            `CREATE ROLE test LOGIN PASSWORD 'some_password';`
            `CREATE DATABASE test OWNER test;`

        add next line to `pg_hba.conf` configuration file if needed:
            `host test test md5`
        '''
        # apply logging during testing
        logging.config.fileConfig(fname='test_logging.conf', disable_existing_loggers=False)
        cls.logger = logging.getLogger(os.path.basename(__file__))

        # create / recreate test database schema
        TestDB.create_schema()

    def setUp(self):
        # tuncate table user_agent before each test case
        TestDB.user_agent_truncate_table()

    def test_property_title_no_db_connection(self):
        '''
        get User-Agent by default if there is no connection to the database (incorrect configuration parameters or the database is not available)
        '''
        # Unix timestamp as a fake database name to make configuration parameters incorrect
        config = DBConfig(**(asdict(test_config) | {'database': str(time.time())}))

        ua = UserAgent(config)
        self.assertEqual(ua.title, ua.DEFAULT_USER_AGENT_TITLE)

    def test_property_title_empty_user_agent_table(self):
        '''
        get User-Agent by default if there is an empty user_agent table
        '''
        ua = UserAgent(test_config)
        self.assertEqual(ua.title, ua.DEFAULT_USER_AGENT_TITLE)

    def test_insert_user_agents_from_file(self):
        '''
        read text files with User-Agents and write them into the database
        '''

        # in the test data we expect to find four text files:
        #   `Chrome.txt` - 19 lines, 19 correct User-Agent lines
        #   `Firefox.txt` - 11 lines, 11 correct User-Agent lines
        #   `Incorrect User Agents File.txt` - 4 lines, 4 incorrect User-Agent lines
        #   `Internet Explorer.txt`- 20 lines, 16 correct User-Agent lines, 4 incorrect User-Agent lines
        #   `User Agent Copies.txt` - 8 lines, 8 correct User-Agent lines, 8 elements that are already in the rest of the files
        test_stats = {
            'lines'     : 62,
            'successes' : 46,
            'passes'    : 8,
            'errors'    : 8,
        }

        res_stats = TestDB.user_agent_insert_test_data()

        self.assertEqual(test_stats, res_stats)

    def test_get_next_user_agent_from_the_database(self):
        '''
        get next User-Agent from the database
        '''
        # insert User-Agent test data
        _ = TestDB.user_agent_insert_test_data()
        ua = UserAgent(test_config)

        # get one User-Agent with raw SQL query
        with PgConnector(test_config) as db:
            res_title = db.execute("SELECT title FROM user_agent WHERE hardware='Computer' ORDER BY update_tz NULLS FIRST, title LIMIT 1;")[0][0]

        # compare User-Agents
        self.assertEqual(res_title, ua.title)

    def test_update_usage_successes_errors(self):
        '''
        test increasing successes and errors
        '''
        # expected values
        check_data = {
            'new_titles'    : 0, # how many times we expect to get a new User-Agent from the database
            'successes'     : 0,
            'errors'        : 0,
        }
        # test results
        test_data = check_data.copy()

        # insert User-Agent test data from text files
        _ = TestDB.user_agent_insert_test_data()
        ua = UserAgent(test_config)

        prev_title = None
        increase_new_titles = True # increase the number of new titles if we have an error or at the beginning of a loop

        for _ in range(100):
            if increase_new_titles:
                check_data['new_titles'] += 1
                increase_new_titles = False

            # here we expect to get a new User-Agent title (at the beginning of a loop or after an error)
            _ = ua.title # "process" titles
            if prev_title is None or prev_title != ua.title:
                test_data['new_titles'] += 1
                prev_title = ua.title

            # simulate random User-Agent usage
            if random.random() < 0.75: # successes
                check_data['successes'] += 1

                ua.update_usage(ua.SUCCESSES_FIELD)
            else: # errors
                check_data['errors'] += 1
                increase_new_titles = True

                ua.update_usage(ua.ERRORS_FIELD)

        # get test results from the database
        with PgConnector(test_config) as db:
            test_data['successes'], test_data['errors'] = db.execute('SELECT SUM(successes), SUM(errors) FROM user_agent;')[0]

        self.assertEqual(check_data, test_data)

    def test_update_usage_update_tz(self):
        '''
        test User-Agent usage without increasing successes or errors, only change update_tz
        '''
        # insert User-Agent test data from text files
        _ = TestDB.user_agent_insert_test_data()
        ua = UserAgent(test_config)

        # update `successes` and `errors` with random values
        # update only first 80% of rows to have NULL values in `update_tz` fields for the rest of rows
        update_successes_errors_query = (
            'UPDATE user_agent SET successes=(100.0 * RANDOM())::integer, errors=(20.0 * RANDOM())::integer '
            '    WHERE user_agent_id < (SELECT (0.80 * MAX(user_agent_id))::integer FROM user_agent);'
        )
        with PgConnector(test_config) as db:
            _ = db.execute(query=update_successes_errors_query)

        query = 'SELECT successes, errors, update_tz FROM user_agent WHERE title=%s;'
        with PgConnector(test_config) as db:
            for _ in range(100): # total number of tests
                title = ua.title # get new (if first loop iteration) or next UserAgent

                before_successes, before_errors, before_update_tz = db.execute(query=query, args=(title,))[0]
                ua.update_usage(field_name=UserAgent.UPDATE_TZ_FIELD)
                after_successes, after_errors, after_update_tz = db.execute(query=query, args=(title,))[0]

                # before and after successes and errors should be equal
                self.assertEqual((before_successes, before_errors), (after_successes, after_errors))

                # before_update_tz and after_update_tz should not be equal
                self.assertNotEqual(before_update_tz, after_update_tz)

                # get next UserAgent - it should be different from the previous one
                self.assertNotEqual(title, ua.title)

                time.sleep(0.01) # take a short pause
