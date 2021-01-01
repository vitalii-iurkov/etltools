# -*- coding: utf-8 -*-

# base class to connect to PostgreSQL

import logging
import os
from dataclasses import asdict

import psycopg2
import psycopg2.extensions

from pg_tools.db_config import DBConfig


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

        self.conn = None
        self.cur = None

    def __enter__(self):
        try:
            self.conn = psycopg2.connect(**self.config)
            self.cur = self.conn.cursor()
        except Exception as ex:
            self.conn = None
            self.cur = None

            self.logger.exception(f'[{self.log_prefix}] connection={self.conn_string}, {ex=}')

            raise PgConnectorError(f'Error while connecting to database : {self.conn_string}') from ex
        else:
            self.logger.info(f'[{self.log_prefix}] Successfully connected to database : {self.conn_string}')
            return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # if we have active connection and in transaction status
        if self.conn and self.conn.status != psycopg2.extensions.STATUS_READY:
            if exc_type: # if error, then rollback
                self.conn.rollback()
                self.logger.warning(f'[{self.log_prefix}] The last transaction was canceled, {exc_type=}, {exc_val=}')
            else:
                try:
                    self.conn.commit()
                except Exception as ex:
                    self.conn.rollback()
                    self.logger.exception(f'[{self.log_prefix}] The last transaction was canceled, {ex=}')

        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

        self.logger.info(f'[{self.log_prefix}] Connection closed : {self.conn_string}')
