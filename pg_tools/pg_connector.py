# -*- coding: utf-8 -*-

# base class to connect to PostgreSQL

import logging
import os
from dataclasses import asdict

import psycopg2
import psycopg2.extensions

from etltools.pg_tools.db_config import DBConfig


class PgConnectorError(Exception):
    pass


class PgConnector:
    def __init__(self, config: DBConfig):
        '''
        in: config, DBConfig(hostname='localhost', port='5432', database='db_name', user='role_name', password='password')
        '''
        self.log_prefix = 'PgConnector'
        self.logger = logging.getLogger(os.path.basename(__file__))

        if isinstance(config, DBConfig):
            self.config = asdict(config)
        else:
            err_msg = f'[{self.log_prefix}] Incorrect connection configuration : {type(config)=}'
            self.logger.error(err_msg)
            raise PgConnectorError(err_msg)

        # this attribute is for logging purposes only
        self.conn_string = str(config)

        self.__conn = None
        self.__cur = None

    def __enter__(self):
        try:
            self.__conn = psycopg2.connect(**self.config)
            self.__cur = self.__conn.cursor()
        except Exception as ex:
            self.__conn = None
            self.__cur = None

            self.logger.exception(f'[{self.log_prefix}] connection={self.conn_string}, {ex=}')

            raise PgConnectorError(f'Error while connecting to database : {self.conn_string}') from ex
        else:
            self.logger.info(f'[{self.log_prefix}] Connection opened : {self.conn_string}')
            return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # if we have active connection and in transaction status
        if self.__conn and self.__conn.status != psycopg2.extensions.STATUS_READY:
            if exc_type: # if error, then rollback
                self.__conn.rollback()
                self.logger.warning(f'[{self.log_prefix}] The last transaction was canceled, {exc_type=}, {exc_val=}')
            else:
                try:
                    self.__conn.commit()
                except Exception as ex:
                    self.__conn.rollback()
                    self.logger.exception(f'[{self.log_prefix}] The last transaction was canceled, {ex=}')

        if self.__cur:
            self.__cur.close()
        if self.__conn:
            self.__conn.close()

        self.logger.info(f'[{self.log_prefix}] Connection closed : {self.conn_string}')

    def execute(self, query: str, args: tuple=None):
        '''
        in:
            query, str
            args, tuple
        '''
        result = None
        try:
            self.__cur.execute(query, args)

            # try to fetch results from query
            try:
                result = self.__cur.fetchall() # will work for 'SELECT...' and 'INSERT... RETURNING...'
            except:
                result = None

            self.logger.info(f'[{self.log_prefix}] Successfully executed {query=}, {args=}')
        except Exception as ex:
            self.logger.exception(f'[{self.log_prefix}] Error executing {query=}, {args=}')
            result = None

        return result

    def commit(self):
        '''
        commit open transaction
        '''
        if self.__conn.status == psycopg2.extensions.STATUS_READY:
            self.logger.info(f'[{self.log_prefix}] Nothing to commit')
        else:
            try:
                self.__conn.commit()
            except Exception as ex:
                self.__conn.rollback()
                self.logger.exception(f'[{self.log_prefix}] Error during commit, {ex=}. The transaction was canceled')
            else:
                self.logger.info(f'[{self.log_prefix}] Successfully committed')

    def rollback(self):
        '''
        rollback open transaction
        '''
        if self.__conn.status == psycopg2.extensions.STATUS_READY:
            self.logger.info(f'[{self.log_prefix}] Nothing to rollback')
        else:
            try:
                self.__conn.rollback()
            except Exception as ex:
                self.logger.exception(f'[{self.log_prefix}] Error during rollback, {ex=}')
                raise PgConnectorError(f'Error during rollback') from ex
            else:
                self.logger.info(f'[{self.log_prefix}] Successfully rollback')
