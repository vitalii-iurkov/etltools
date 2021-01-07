# -*- coding: utf-8 -*-

# UserAgent implementation

import logging
import logging.config
import os
import subprocess

from psycopg2.extensions import quote_ident

from etltools.additions.logger_mixin import LoggerMixin
from etltools.local_settings import parsers_config
from etltools.local_settings import test_config
from etltools.pg_tools.db_config import DBConfig
from etltools.pg_tools.pg_connector import PgConnector, PgConnectorError


class UserAgentError(Exception):
    pass


class UserAgent(LoggerMixin):
    # User-Agent is returned by default if there is no database connection
    DEFAULT_USER_AGENT_TITLE = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'

    # columns in the `user_agent` table to update the number of success/error usage
    SUCCESSES_FIELD = 'successes'
    ERRORS_FIELD = 'errors'

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
        '''
        get the current User-Agent or get random User-Agent from the database
        '''
        # get next random User-Agent; only for desktop apps : hardware = 'Computer'
        # `self._title is None` only in two cases:
        #     1. the initial value
        #     2. after error while using the User-Agent
        if self._title is None:
            query = "SELECT title FROM user_agent WHERE hardware='Computer' ORDER BY update_tz NULLS FIRST;"
            try:
                with PgConnector(self._config) as db:
                    self._title = db.execute(query)[0][0]
                self.logger.info(self.log_msg(f'New User-Agent received : {self._title}'))
            except PgConnectorError as ex:
                self._title = None
                self.logger.exception(self.log_msg(f'Error getting User-Agent from the database : {ex=}'))
            except IndexError as ex: # there is no rows in the `user_agent` table for this query (can be an empty table)
                self._title = None
                self.logger.warning(self.log_msg(f'There are no rows in the response to the query. Is the `user_agent` table empty? {ex=}'))
            except Exception as ex:
                self.logger.exception(self.log_msg(f'{ex=}'))

        if self._title is not None:
            return self._title
        else: # if we can't get the User-Agent from the database
            return self.__class__.DEFAULT_USER_AGENT_TITLE

    def update_usage(self, field_name: str):
        '''
        increase `successes` or `errors` for active User-Agent after its usage

        in: field_name, str - must be
            SUCCESSES_FIELD
            or
            ERRORS_FIELD
        '''
        # SQL injection ?
        if field_name not in (self.__class__.SUCCESSES_FIELD, self.__class__.ERRORS_FIELD):
            msg = f'Error: {field_name=}; must be `{self.__class__.__name__}.SUCCESSES_FIELD` or `{self.__class__.__name__}.ERRORS_FIELD`'
            self.logger.error(self.log_msg(msg))
            raise UserAgentError(msg)

        # if we don't have User-Agent value from the database, then pass this step
        if self._title is None:
            self.logger.warning(self.log_msg(f'No User-Agent to increase `{field_name}`.'))
            return

        try:
            with PgConnector(self._config) as db:
                query = 'UPDATE user_agent SET {field_name}={field_name}+1 WHERE title=%s;'.format(field_name=quote_ident(field_name, db._conn))
                _ = db.execute(query, (self._title, ))
            self.logger.info(self.log_msg(f'Increased `{field_name}` for User-Agent : {self._title}'))
        except PgConnectorError as ex:
            # error during interacting with the database
            self.logger.exception(self.log_msg(f'Error increasing `{field_name}` for User-Agent : {self._title}, {ex=}'))
        except Exception as ex:
            self.logger.exception(self.log_msg(f'Error : {ex=}'))

        # next time we want to get a new User-Agent
        if field_name == 'errors':
            self._title = None

    def insert_user_agents_from_files(self, dir_name: str) -> int:
        '''
        insert User-Agents from text files into the database

        in: dir_name, str - absolute path to the directory with User-Agent text files

        out: int - total number of successfully inserted User-Agents
        '''
        if not os.path.exists(dir_name):
            msg = f"Path doesn't exists : {dir_name=}"
            self.logger.error(self.log_msg(msg))
            raise UserAgentError(msg)

        total = 0 # total number of successfully inserted User-Agents
        query = 'SELECT user_agent_insert_func(%s, %s, %s, %s, %s, %s);'

        try:
            with PgConnector(self._config) as db:
                fnames = os.listdir(os.path.join(dir_name, 'ua'))
                field_width = len(str(len(fnames)))

                for idx, fname in enumerate(fnames):
                    software = fname.removesuffix('.txt')
                    print(f'{idx+1:{field_width}}/{len(fnames)} : {software=}')

                    with open(os.path.join(dir_name, 'ua', fname), 'r', encoding='utf-8') as f:
                        for line in f:
                            title, version, os_type, hardware, popularity = line.strip().split('\t')

                            user_agent_id = db.execute(query, (software, title, version, os_type, hardware, popularity))

                            # if we get new user_agent_id then increase their total amount
                            if user_agent_id[0][0] > 0:
                                total += 1

                    db.commit()
        except Exception as ex:
            self.logger.exception(self.log_msg(ex))
            raise UserAgentError('Error') from ex

        return total


def main():
    if os.name == 'posix':
        _ = subprocess.run('clear')
    else:
        print('\n' * 42)

    logging.config.fileConfig(fname='logging.conf', disable_existing_loggers=False)
    logger = logging.getLogger(os.path.basename(__file__))

    # parsers_config.database = '1234'
    # ua = UserAgent(parsers_config)
    ua = UserAgent(test_config)
    print(ua.title)


if __name__ == '__main__':
    main()
