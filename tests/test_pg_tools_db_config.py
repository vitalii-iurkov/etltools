# -*- coding: utf-8 -*-

import logging
import logging.config
import os
import unittest

from etltools.pg_tools.db_config import DBConfig


class DBConfigTest(unittest.TestCase):

    def setUp(self):
        # apply logging during testing
        logging.config.fileConfig(fname='test_logging.conf', disable_existing_loggers=False)
        self.logger = logging.getLogger(os.path.basename(__file__))

    def test_repr(self):
        test_data = [
            (
                "DBConfig(host='localhost', port='5432', database='test', user='test')",
                DBConfig(host='localhost', port='5432', database='test', user='test', password='*****').__repr__(),
            ),
            (
                "DBConfig(host='replica-srv', port='5435', database='sensors', user='manager')",
                DBConfig(host='replica-srv', port='5435', database='sensors', user='manager', password='*****').__repr__(),
            ),
        ]

        for expected_value, received_value in test_data:
            with self.subTest(expected_value=expected_value, received_value=received_value):
                self.assertEqual(expected_value, received_value)

    def test_str(self):
        test_data = [
            (
                "test@localhost:5432/test",
                str(DBConfig(host='localhost', port='5432', database='test', user='test', password='*****')),
            ),
            (
                "manager@replica-srv:5435/sensors",
                str(DBConfig(host='replica-srv', port='5435', database='sensors', user='manager', password='*****')),
            ),
        ]

        for expected_value, received_value in test_data:
            with self.subTest(expected_value=expected_value, received_value=received_value):
                self.assertEqual(expected_value, received_value)
