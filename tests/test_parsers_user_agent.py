# -*- coding: utf-8 -*-

import logging
import logging.config
import os
import subprocess
import time
from dataclasses import asdict

import unittest

from etltools.pg_tools.db_config import DBConfig
from etltools.local_settings import test_config
from etltools.parsers.user_agent import UserAgent, UserAgentError


class UserAgentTest(unittest.TestCase):
    def setUp(self):
        # apply logging during testing
        logging.config.fileConfig(fname='test_logging.conf', disable_existing_loggers=False)
        self.logger = logging.getLogger(os.path.basename(__file__))

        # recreate full data schema in the test database (without any data in it)
        # depends on `../parsers/for_testings_only` directory and files
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        schema_file_name = 'parsers_dump_20210106_schema_only.sql' # dump file to recreate data schema
        fname = os.path.join(BASE_DIR, '..', 'parsers/for_testings_only', schema_file_name)

        _ = subprocess.run(
            ["psql", "-f", fname],
            stdout=subprocess.PIPE,
            env=os.environ | {
                'PGHOST': test_config.host,
                'PGPORT': test_config.port,
                'PGDATABASE': test_config.database,
                'PGUSER': test_config.user,
                'PGPASSWORD': test_config.password,
            }
        )

    def tearDown(self):
        pass

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
