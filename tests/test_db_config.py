# -*- coding: utf-8 -*-

import unittest

from pg_tools.db_config import DBConfig


class DBConfigTest(unittest.TestCase):

    def test_repr(self):
        self.assertEqual(
            DBConfig(host='localhost', port='5432', database='test', user='test', password='*****').__repr__(), 
            "DBConfig(host='localhost', port='5432', database='test', user='test')"
        )

    def test_str(self):
        self.assertEqual(
            str(DBConfig(host='localhost', port='5432', database='test', user='test', password='*****')), 
            'test@localhost:5432/test'
        )
