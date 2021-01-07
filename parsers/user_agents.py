# -*- coding: utf-8 -*-

# UserAgent implementation

import logging
import logging.config
import os
import subprocess

from psycopg2.extensions import quote_ident

from etltools.additions.logger_mixin import LoggerMixin
from etltools.local_settings import parsers_config
from etltools.pg_tools.db_config import DBConfig
from etltools.pg_tools.pg_connector import PgConnector, PgConnectorError


class UserAgentError(Exception):
    pass


class UserAgent(LoggerMixin):
    # User-Agent is returned by default if there is no database connection
    DEFAULT_USER_AGENT_TITLE = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'

    def __init__(self, config: DBConfig):
        super().__init__(name=os.path.basename(__file__), log_prefix=self.__class__.__name__)

        self._title = None # User-Agent title

        # some hardcode - we plan to use here only PostgreSQL RDBMS (PgConnector class);
        # if we use here, for example, Redis, we need to move this check to another level (to the connector class)
        if isinstance(config, DBConfig):
            self._config = config
        else:
            msg = f'Incorrect `config` datatype : {type(config)=}'
            self.logger.error(self.log_msg(msg))
            raise UserAgentError(msg)

    @property
    def title(self):
        if self._title is None:
            # get next random User-Agent; only for desktop apps : hardware = 'Computer'
            query = "SELECT title FROM user_agent WHERE hardware='Computer' ORDER BY update_tz NULLS FIRST;"
            try:
                with PgConnector(self._config) as db:
                    self._title = db.execute(query)[0][0]
                self.logger.info(self.log_msg(f'New User-Agent received : {self._title}'))
            except PgConnectorError as ex:
                self._title = None
                self.logger.exception(self.log_msg(f'Error getting User-Agent from the database : {ex=}'))
            except Exception as ex:
                self.logger.exception(self.log_msg(f'{ex=}'))

        if self._title is not None:
            return self._title
        else:
            return self.__class__.DEFAULT_USER_AGENT_TITLE

    def increase_successes(self):
        self.__increase_field('successes')

    def increase_errors(self):
        self.__increase_field('errors')
        self._title = None # next time we want to get a new User-Agent

    def __increase_field(self, field_name: str):
        '''
        increase `successes` or `errors` for active User-Agent

        in: field_name, str - must be in ('successes', 'errors')
        '''
        # SQL injection ?
        if field_name not in ('successes', 'errors'):
            msg = f'Error: {field_name=}'
            self.logger.error(self.log_msg(msg))
            raise UserAgentError(msg)

        # if we don't have User-Agent value from the database, then pass this step
        if self._title is None:
            self.logger.warning(self.log_msg(f'No User-Agent to increase `{field_name}`.'))
            return

        query = 'UPDATE user_agent SET {field_name}={field_name}+1 WHERE title=%s;'.format(field_name=quote_ident(field_name))
        try:
            with PgConnector(self._config) as db:
                _ = db.execute(query, (self._title, ))
            self.logger.info(self.log_msg(f'Increased `{field_name}` for User-Agent : {self._title}'))
        except PgConnectorError as ex:
            # error during interacting with the database
            self.logger.exception(self.log_msg(f'Error increasing `{field_name}` for User-Agent : {self._title}, {ex=}'))
        except Exception as ex:
            self.logger.exception(self.log_msg(f'Error : {ex=}'))


def insert_user_agents_from_files():
    '''
    функция добавления User-Agent из файлов в базу данных
    потом ее перенести как @classmethod в UserAgent
    '''
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # print(f'{BASE_DIR=}')

    total = 0 # total added user-agents
    query = 'SELECT user_agent_insert_func(%s, %s, %s, %s, %s, %s);'

    with PgConnector(parsers_config) as db:
        fnames = os.listdir(os.path.join(BASE_DIR, 'ua'))
        field_width = len(str(len(fnames)))

        for idx, fname in enumerate(fnames):
            software = fname.removesuffix('.txt')
            print(f'{idx+1:{field_width}}/{len(fnames)} : {software=}')

            with open(os.path.join(BASE_DIR, 'ua', fname), 'r', encoding='utf-8') as f:
                for line in f:
                    title, version, os_type, hardware, popularity = line.strip().split('\t')

                    user_agent_id = db.execute(query, (software, title, version, os_type, hardware, popularity))

                    # if we get new user_agent_id then increase their total amount
                    if user_agent_id[0][0] > 0:
                       total += 1

            db.commit()

    print(f'New user-agents inserted : {total=}')


def main():
    if os.name == 'posix':
        _ = subprocess.run('clear')
    else:
        print('\n' * 42)

    logging.config.fileConfig(fname='logging.conf', disable_existing_loggers=False)
    logger = logging.getLogger(os.path.basename(__file__))

    # parsers_config.database = '1234'
    ua = UserAgent(parsers_config)

    print(ua.title)
    # ua.increase_successes()
    # ua.increase_errors()


if __name__ == '__main__':
    main()
