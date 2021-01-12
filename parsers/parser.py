# -*- coding: utf-8 -*-

# Parser implementation

import os
import subprocess

from etltools.additions.logger import Logger


class ParserError(Exception):
    pass


class Parser(Logger):
    '''
    base class for downloading and preprocessing html pages
    '''

    def __init__(self):
        super().__init__(name=os.path.basename(__file__), log_prefix=self.__class__.__name__)

        self.html = None # str object to store downloaded html pages

    def pages_url(self, start_url: str, template_url, from_page: int, to_page: int) -> str:
        '''
        generate pages url using start page url and template page url

        in:
            start_url, str - 'https://www.somehost.com/catalog/'
            template_url, str - 'https://www.somehost.com/catalog/?page={}', format string
            from_page, int
            to_page, int

        out: page_url, str
        '''
        for page_number in range(from_page, to_page+1):
            if page_number == 1:
                page_url = start_url
            else:
                page_url = template_url.format(page_number)

            self.logger.info(self.log_msg(f'Generated page url: {page_url}'))
            yield page_url

    def get_html(self, url: str):
        '''
        download html from given url and store it in self.html

        in: url, str - url where to download html
        '''
        raise NotImplementedError

    def parse_catalog_html(self):
        '''
        parse html catalog page
        '''
        raise NotImplementedError

    def parse_item_html(self):
        '''
        parse html item page
        '''
        raise NotImplementedError


def main():
    if os.name == 'posix':
        _ = subprocess.run('clear')
    else:
        print('\n' * 42)

    print(os.name)


if __name__ == '__main__':
    main()
