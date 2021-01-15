import logging
import logging.config
import os
import unittest

from etltools.parsers.parser import Parser, ParserError


class ParserTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # apply logging during testing
        logging.config.fileConfig(fname='test_logging.conf', disable_existing_loggers=False)
        cls.logger = logging.getLogger(os.path.basename(__file__))

    def test_pages_url_all_urls(self):
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

        p = Parser()

        pages_url_idx = 0
        for page_url in p.pages_url(**pages_url_args):
            with self.subTest(check_page_url=pages_url[pages_url_idx], test_page_url=page_url):
                self.assertEqual(pages_url[pages_url_idx], page_url)
            pages_url_idx += 1

    def test_pages_url_from_to_urls(self):
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

        p = Parser()

        pages_url_idx = pages_url_args['from_page'] - 1
        for page_url in p.pages_url(**pages_url_args):
            with self.subTest(check_page_url=pages_url[pages_url_idx], test_page_url=page_url):
                self.assertEqual(pages_url[pages_url_idx], page_url)
            pages_url_idx += 1
