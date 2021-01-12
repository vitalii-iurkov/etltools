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
            query = "SELECT title FROM user_agent WHERE hardware='Computer' ORDER BY update_tz NULLS FIRST, title LIMIT 1;"
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
                # these errors are not related to getting User-Agent, so here it's assumed that we received the correct User-Agent
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
        if field_name == self.__class__.ERRORS_FIELD:
            self._title = None

    def insert_user_agents_from_files(self, dir_name: str) -> dict:
        '''
        insert User-Agents from text files into the database

        in:
            dir_name, str - absolute path to the directory with User-Agents text files

            text files with User-Agents should have the following format:
                file name : `software.txt`, for example `Chrome.txt`, `Internet Explorer.txt`
                User-Agent data in tab delimited format:
                    format string: `title	version	os_type	hardware	popularity`
                    for example:
                        `Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36	60	Windows	Computer	Very common`
                The data must be in the specified format, but the creator of the User-Agent files is responsible for their content

        out:
            total_stats {
                'lines': 0,     # total number of lines in all files
                'successes': 0, # total number of successful inserts into the database
                'passes': 0,    # total number of passes - if we already have the same User-Agent in the database
                'errors': 0,    # total number of lines with incorrect format in the files
            }, dict
        '''
        self.logger.info(self.log_msg('Started import from text files into the database'))

        if not os.path.exists(dir_name):
            msg = f"Path doesn't exist : {dir_name=}"
            self.logger.error(self.log_msg(msg))
            raise UserAgentError(msg)

        total_stats = {
            'lines': 0,
            'successes': 0,
            'passes': 0,
            'errors': 0,
        }
        query = 'SELECT user_agent_insert_func(%s, %s, %s, %s, %s, %s);'

        try:
            with PgConnector(self._config) as db:
                fnames = os.listdir(dir_name)

                # for each file in the given directory
                for idx, fname in enumerate(fnames):
                    software = fname.removesuffix('.txt')
                    print(f'{idx+1}/{len(fnames)} : {fname=}', end='')

                    # read text file and try to insert data to the database
                    file_stats = {key:0 for key in total_stats} # stats for the current file
                    self.logger.info(self.log_msg(f'Processing file `{fname}`'))
                    try:
                        with open(os.path.join(dir_name, fname), 'r', encoding='utf-8') as f:
                            for line in f:
                                file_stats['lines'] += 1

                                # try to parse line into five tab delimited values; simple syntax check
                                user_agent_data = (line := line.strip()).split('\t')
                                if len(user_agent_data) != len('title	version	os_type	hardware	popularity'.split('\t')):
                                    self.logger.warning(f'Incorrect input data format. Expected five tab delimited values. Got {line=}')
                                    file_stats['errors'] += 1
                                    continue # try to process next line in the file

                                # title, version, os_type, hardware, popularity = user_agent_data
                                # user_agent_id = db.execute(query, (software, title, version, os_type, hardware, popularity))
                                user_agent_id = db.execute(query, (software, *user_agent_data))

                                if user_agent_id[0][0] > 0: # if we got new user_agent_id then increase their total amount
                                    file_stats['successes'] += 1
                                else:
                                    file_stats['passes'] += 1
                    except Exception as ex:
                        msg = f'Error reading data from file {fname=}, {ex=}'
                        self.logger.error(self.log_msg(msg))
                        db.rollback()

                        print(f' - error')
                    else:
                        db.commit()
                        print(f' - ok, {file_stats=}')

                        for key, value in file_stats.items():
                            total_stats[key] += value

                    self.logger.info(self.log_msg(f'For file `{fname}`: {file_stats=}'))

        # we don't need to analyze errors separately here
        except Exception as ex:
            self.logger.exception(self.log_msg(ex))
            raise UserAgentError('Error') from ex

        self.logger.info(self.log_msg(f'Total stats for all processed files: {total_stats=}'))
        return total_stats.copy()
