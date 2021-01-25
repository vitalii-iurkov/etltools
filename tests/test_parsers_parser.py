import logging
import logging.config
import os
import subprocess
import time
import unittest
from collections import namedtuple

import requests

from etltools.local_settings import test_config
from etltools.parsers.parser import Parser, ParserError
from etltools.pg_tools.pg_connector import PgConnector, PgConnectorError
from etltools.tests.parsers._test_db import TestDB
from etltools.tests.parsers.server_data import server_config, server_data


class ParserTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # apply logging during testing
        logging.config.fileConfig(fname='test_logging.conf', disable_existing_loggers=False)
        logging.captureWarnings(True)
        cls.logger = logging.getLogger(os.path.basename(__file__))

        # start flask server
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        cls.server = subprocess.Popen(
            ['python', '-m', 'flask', 'run']
            , env=os.environ | {
                'FLASK_APP': os.path.join(BASE_DIR, 'parsers', server_config.app),
                'FLASK_RUN_PORT': server_config.port,
            }
            , stdout=subprocess.PIPE
            , stderr=subprocess.PIPE
        )
        time.sleep(3) # it is necessary to maintain a minimum pause for a full server start
        cls.logger.info(f'Successfully started Flask test server {server_config.url()}')

        # create / recreate database schema and insert test data into parsers.user_agent
        TestDB.create_schema()
        _ = TestDB.user_agent_insert_test_data()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.server.terminate()
            cls.logger.info(f'Successfully terminated Flask test server {server_config.url()}')
        except Exception as ex:
            cls.logger.exception(f'Error while terminating Flask test server {server_config.url()}, {ex=}')

    def setUp(self):
        # reset User-Agents usages before each test
        TestDB.user_agent_reset_successes_errors()

    def _test_pages_url_all_urls(self):
        '''
        test all pages url from start_url to template_url.format(to_page)
        '''
        pages_url = [
            'https://www.somehost1.org/',
            'https://www.somehost1.org/page/2/',
            'https://www.somehost1.org/page/3/',
            'https://www.somehost1.org/page/4/',
            'https://www.somehost1.org/page/5/',
        ]
        pages_url_args = {
            'start_url'     : 'https://www.somehost1.org/',
            'template_url'  : 'https://www.somehost1.org/page/{}/',
            'from_page'     : 1,
            'to_page'       : len(pages_url),
        }

        p = Parser(test_config)

        pages_url_idx = 0
        for page_url in p.pages_url(**pages_url_args):
            with self.subTest(check_page_url=pages_url[pages_url_idx], test_page_url=page_url):
                self.assertEqual(pages_url[pages_url_idx], page_url)
            pages_url_idx += 1

    def _test_pages_url_from_to_urls(self):
        '''
        test only subset of pages url : from_page - to_page
        '''
        pages_url = [
            'https://somehost2.info/catalog',
            'https://somehost2.info/catalog?page=2',
            'https://somehost2.info/catalog?page=3', # from this url
            'https://somehost2.info/catalog?page=4',
            'https://somehost2.info/catalog?page=5',
            'https://somehost2.info/catalog?page=6',
            'https://somehost2.info/catalog?page=7', # to this url
            'https://somehost2.info/catalog?page=8',
        ]
        pages_url_args = {
            'start_url'     : 'https://somehost2.info/catalog',
            'template_url'  : 'https://somehost2.info/catalog?page={}',
            'from_page'     : 3,
            'to_page'       : 7,
        }

        p = Parser(test_config)

        pages_url_idx = pages_url_args['from_page'] - 1
        for page_url in p.pages_url(**pages_url_args):
            with self.subTest(check_page_url=pages_url[pages_url_idx], test_page_url=page_url):
                self.assertEqual(pages_url[pages_url_idx], page_url)
            pages_url_idx += 1

    def test_get_html_ok(self):
        '''
        successfully downloaded html
        '''
        p = Parser(test_config)
        ok_url = server_config.url() + server_data['ok']['url']

        # should be successfully downloaded html
        self.assertTrue(p.get_html(ok_url))

        # check for html, err_msg
        self.assertTrue((server_data['ok']['msg'], None), (p.html, p.err_msg))

        # check for successes, errors; should be +1 successes and +0 errors
        with PgConnector(test_config) as db:
            successes, errors = db.execute("SELECT SUM(successes), SUM(errors) FROM user_agent WHERE hardware='Computer';")[0]
        self.assertEqual((successes, errors), (1, 0))

    def _test_get_html_429_ok(self):
        '''
        successfully downloaded html after several attempts with error 429 Too Many Requestst
        '''
        pass

    def test_get_html_429_fail(self):
        '''
        failed to download html due to exceeded download attempts with error 429 Too Many Requestst
        '''
        ATTEMPTS_TOTAL = 3
        Row = namedtuple('Row', ['successes', 'errors', 'update_tz'])

        p = Parser(test_config)

        with PgConnector(test_config) as db:
            before = [
                Row(successes, errors, update_tz)
                for successes, errors, update_tz
                in db.execute("SELECT successes, errors, update_tz FROM user_agent WHERE hardware='Computer' ORDER BY user_agent_id;")
            ]

        result = p.get_html(
            url=server_config.url() + server_data['429_fail']['url']
            , attempts_total=ATTEMPTS_TOTAL
            , pause_duration=0
            , pause_increment=1
        )

        with PgConnector(test_config) as db:
            after = [
                Row(successes, errors, update_tz)
                for successes, errors, update_tz
                in db.execute("SELECT successes, errors, update_tz FROM user_agent WHERE hardware='Computer' ORDER BY user_agent_id;")
            ]

        # we shouldn't change total number of rows in the user_agent table
        self.assertEqual(len(after), len(before))

        # we shouldn't get any html
        self.assertFalse(result)

        # check for result values in html, err_msg
        self.assertEqual((p.html, p.err_msg), (None, '429'))

        # check for total number of successes and errors after the process
        before_successes_total = sum([row.successes for row in before])
        before_errors_total = sum([row.errors for row in before])

        after_successes_total = sum([row.successes for row in after])
        after_errors_total = sum([row.errors for row in after])

        self.assertEqual((before_successes_total, before_errors_total+ATTEMPTS_TOTAL), (after_successes_total, after_errors_total))

        # total number of row can be less than ATTEMPTS_TOTAL
        update_tz_compare = [
            after_row.update_tz>before_row.update_tz
            for before_row, after_row in zip(before, after)
            if after_row.update_tz != before_row.update_tz
        ]
        self.assertEqual(update_tz_compare, [True] * min(len(before), ATTEMPTS_TOTAL))

    def test_get_html_unicode_decode_error(self):
        '''
        download html in encoding other than utf-8
        '''
        unicode_decode_error_url = server_config.url() + server_data['unicode_decode_error']['url']

        p = Parser(test_config)

        test_data = [
            # (get_html_result, html, err_msg, decode_errors)
            (False, None, 'UnicodeDecodeError', 'strict'),
            (False, None, 'UnicodeDecodeError', 'some wrong decode parameter'), # same as 'strict'
            (True, server_data['unicode_decode_error']['msg'].decode('utf-8', errors='replace'), None, 'replace'),
            (True, server_data['unicode_decode_error']['msg'].decode('utf-8', errors='ignore'), None, 'ignore'),
        ]

        for get_html_result, html, err_msg, decode_errors in test_data:
            with self.subTest(get_html_result=get_html_result, html=html, err_msg=err_msg, decode_errors=decode_errors):
                self.assertEqual(get_html_result, p.get_html(url=unicode_decode_error_url, decode_errors=decode_errors))
                self.assertEqual((html, err_msg), (p.html, p.err_msg))

    def test_get_html_fail(self):
        '''
        other errors while downloading html, except for the 429 status code
        '''
        p = Parser(test_config)
        error_url = server_config.url() + '/error_url'

        # take all update_tz values from the user_agent table before the process
        with PgConnector(test_config) as db:
            before_update_tz = [row[0] for row in db.execute("SELECT update_tz FROM user_agent WHERE hardware='Computer' ORDER BY user_agent_id;")]

        # we shouldn't get any html from the given url
        self.assertFalse(p.get_html(error_url))

        # html is None, and err_mgs can be any status_code any error meggase
        self.assertEqual(p.html, None)
        self.assertNotEqual(p.err_msg, None)

        # we shouldn't get any databse changes except in only one update_tz
        with PgConnector(test_config) as db:
            successes, errors = db.execute("SELECT SUM(successes), SUM(errors) FROM user_agent WHERE hardware='Computer';")[0]
            after_update_tz = [row[0] for row in db.execute("SELECT update_tz FROM user_agent WHERE hardware='Computer' ORDER BY user_agent_id;")]
        self.assertEqual((successes, errors), (0, 0))

        # we should change only one value (update_tz) in one row
        self.assertEqual(len(before_update_tz), len(after_update_tz)) # total number of rows should be equal before and after the process
        compare = [after>before for before, after in zip(before_update_tz, after_update_tz) if before!=after]
        self.assertEqual(compare, [True]) # we should change only one row
