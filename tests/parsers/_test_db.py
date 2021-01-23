# Object for working with test database

import os
import subprocess

from etltools.local_settings import test_config
from etltools.pg_tools.pg_connector import PgConnector, PgConnectorError
from etltools.parsers.user_agent import UserAgent, UserAgentError


class TestDB:
    '''
    create / recreate test database and insert test data
    '''
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DUMP_FILE_NAME = 'parsers_dump_schema_only.sql'
    USER_AGENT_TEST_DATA_DIR = 'user_agent_test_data/'

    @classmethod
    def create_schema(cls):
        '''
        create / recreate test database from dump file
        '''
        # drop all objects in the test database
        with PgConnector(test_config) as db:
            _ = db.execute('DROP OWNED BY test CASCADE;')

        # restore objects from dump file
        with PgConnector(test_config) as db:
            _ = subprocess.run(
                ['psql', '-f', os.path.join(cls.BASE_DIR, cls.DUMP_FILE_NAME)]
                , env=os.environ | {
                    'PGHOST'        : test_config.host,
                    'PGPORT'        : test_config.port,
                    'PGDATABASE'    : test_config.database,
                    'PGUSER'        : test_config.user,
                    'PGPASSWORD'    : test_config.password,
                }
                , stdout=subprocess.PIPE
                , stderr=subprocess.PIPE
            )

    @classmethod
    def user_agent_insert_test_data(cls) -> dict:
        '''
        insert test data from files
        '''
        ua = UserAgent(test_config)
        res_stats = ua.insert_user_agents_from_files(os.path.join(cls.BASE_DIR, cls.USER_AGENT_TEST_DATA_DIR))

        return res_stats

    @classmethod
    def user_agent_truncate_table(cls):
        '''
        truncate table user_agent
        '''
        with PgConnector(test_config) as db:
            _ = db.execute('TRUNCATE TABLE user_agent RESTART IDENTITY CASCADE;')

    @classmethod
    def user_agent_reset_successes_errors(cls):
        '''
        set successes and errors in user_agent table to 0
        '''
        with PgConnector(test_config) as db:
            _ = db.execute('UPDATE user_agent SET successes=0, errors=0;')


if __name__ == '__main__':
    TestDB.create_schema()
    TestDB.user_agent_insert_test_data()
    # TestDB.user_agent_truncate_table()
    TestDB.user_agent_reset_successes_errors()
