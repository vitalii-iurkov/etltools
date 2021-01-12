# -*- coding: utf-8 -*-

# base class to connect to PostgreSQL

import logging
import os
from dataclasses import asdict

import psycopg2
import psycopg2.extensions

from etltools.additions.logger import Logger
from etltools.pg_tools.db_config import DBConfig


class PgConnectorError(Exception):
    pass


class PgConnector(Logger):
    def __init__(self, config: DBConfig):
        '''
        in: config, DBConfig(hostname='localhost', port='5432', database='db_name', user='role_name', password='password')
        '''
        super().__init__(name=os.path.basename(__file__), log_prefix=self.__class__.__name__)

        if isinstance(config, DBConfig):
            self.config = asdict(config)
        else:
            msg = f'Incorrect connection configuration : {type(config)=}'
            self.logger.error(self.log_msg(msg))
            raise PgConnectorError(msg)

        # this attribute is for logging purposes only
        self.conn_string = str(config)

        self._conn = None
        self._cur = None

    def __enter__(self):
        try:
            self._conn = psycopg2.connect(**self.config)
            self._cur = self._conn.cursor()
        except Exception as ex:
            self._conn = None
            self._cur = None

            self.logger.exception(self.log_msg(f'Connection error : {self.conn_string}, {ex=}'))

            raise PgConnectorError(f'Error while connecting to the database : {self.conn_string}') from ex
        else:
            self.logger.info(self.log_msg(f'Connection opened : {self.conn_string}'))
            return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # if we have active connection and in transaction status
        if self._conn and self._conn.status != psycopg2.extensions.STATUS_READY:
            if exc_type: # if error, then rollback
                self._conn.rollback()
                self.logger.warning(self.log_msg(f'The last transaction was canceled, {exc_type=}, {exc_val=}'))
            else:
                try:
                    self._conn.commit()
                except Exception as ex:
                    self._conn.rollback()
                    self.logger.exception(self.log_msg(f'The last transaction was canceled, {ex=}'))

        if self._cur:
            self._cur.close()
        if self._conn:
            self._conn.close()

        self.logger.info(self.log_msg(f'Connection closed : {self.conn_string}'))

    def execute(self, query: str, args: tuple=None):
        '''
        in:
            query, str
            args, tuple
        '''
        result = None
        try:
            self._cur.execute(query, args)

            # try to fetch results from query
            try:
                result = self._cur.fetchall() # will work for 'SELECT...' and 'INSERT... RETURNING...'
            except:
                result = None

            self.logger.info(self.log_msg(f'Successfully executed {query=}, {args=}'))
        except Exception as ex:
            self.logger.exception(self.log_msg(f'Error executing {query=}, {args=}; {ex=}'))
            result = None

        return result

    def commit(self):
        '''
        commit open transaction
        '''
        if self._conn.status == psycopg2.extensions.STATUS_READY:
            self.logger.info(self.log_msg('Nothing to commit'))
        else:
            try:
                self._conn.commit()
            except Exception as ex:
                self._conn.rollback()
                self.logger.exception(self.log_msg(f'Error during commit, {ex=}. The transaction was canceled'))
            else:
                self.logger.info(self.log_msg('Successfully committed'))

    def rollback(self):
        '''
        rollback open transaction
        '''
        if self._conn.status == psycopg2.extensions.STATUS_READY:
            self.logger.info(self.log_msg('Nothing to rollback'))
        else:
            try:
                self._conn.rollback()
            except Exception as ex:
                self.logger.exception(self.log_msg(f'Error during rollback, {ex=}'))
                raise PgConnectorError(f'Error during rollback') from ex
            else:
                self.logger.warning(self.log_msg('Successfully rolled back'))
