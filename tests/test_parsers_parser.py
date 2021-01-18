import logging
import logging.config
import os
import subprocess
import time
import unittest

import requests

from etltools.local_settings import test_config
from etltools.parsers.parser import Parser, ParserError
from etltools.tests.parsers.server_data import server_data


class ParserTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # apply logging during testing
        logging.config.fileConfig(fname='test_logging.conf', disable_existing_loggers=False)
        cls.logger = logging.getLogger(os.path.basename(__file__))

        # start flask server
        cls.host_name = 'http://127.0.0.1:5000'
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        SERVER_FILE_NAME = os.path.join(BASE_DIR, 'parsers', 'server.py')
        cls.server = subprocess.Popen(
            ['python', '-m', 'flask', 'run']
            , env=os.environ | {'FLASK_APP': SERVER_FILE_NAME}
            , stdout=subprocess.PIPE
            , stderr=subprocess.PIPE
        )
        time.sleep(3) # it is necessary to maintain a minimum pause for a full server start
        cls.logger.info('Successfully started Flask test server')

    @classmethod
    def tearDownClass(cls):
        try:
            cls.server.terminate()
            cls.logger.info('Successfully terminated Flask test server')
        except Exception as ex:
            cls.logger.exception(f'Error while terminating Flask test server, {ex=}')

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

    def _test_get_html_ok(self):
        '''
        successfully downloaded html
        '''
        p = Parser(test_config)
        ok_url = self.__class__.host_name + '/ok'

        # should be successfully downloaded html
        self.assertTrue(p.get_html(ok_url))

        # check for html, err_msg
        self.assertTrue(('Ok', None), (p.html, p.err_msg))

    def _test_get_html_429_ok(self):
        '''
        successfully downloaded html after several attempts with error 429 Too Many Requestst
        '''
        pass

    def _test_get_html_429_fail(self):
        '''
        failed to download html due to exceeded download attempts with error 429 Too Many Requestst
        '''
        pass

    def test_get_html_unicode_decode_error(self):
        '''
        download html in encoding other than utf-8
        '''
        unicode_decode_error_url = self.__class__.host_name + '/unicode-decode-error'

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

    def _test_get_html_fail(self):
        '''
        other errors while downloading html
        '''
        pass
