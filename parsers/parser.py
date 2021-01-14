# -*- coding: utf-8 -*-

# Parser implementation

import logging
import logging.config
import os
import subprocess
import time

import requests

from etltools.additions.logger import Logger
from etltools.local_settings import parsers_config
from etltools.parsers.user_agent import UserAgent, UserAgentError


class ParserError(Exception):
    pass


class Parser(Logger):
    '''
    base class for downloading and preprocessing html pages
    '''

    def __init__(self):
        super().__init__(name=os.path.basename(__file__), log_prefix=self.__class__.__name__)

        self.html = None # str object to store downloaded html pages
        self.err_msg = None # error message for get_html() method

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

    def get_html(self, url: str, attempts_total: int=10, pause_duration: int=0, pause_increment: int=1) -> bool:
        '''
        download html from given url and store it in self.html

        in:
            url, str - url where to download html
            attempts_total, int - total number of attempts to download html from url
            pause_duration, int - start pause in seconds before GET request
            pause_increment, int - increment in seconds for pause before each next attempt

        out: bool
            True - successfully downloaded html
            False - error while downloading html
        '''
        self.html = None
        self.err_msg = None

        ua = UserAgent(parsers_config)

        # attempts to download html
        for attempt in range(1, attempts_total+1):
            self.logger.info(self.log_msg(f'Request GET {attempt=} for {url=}'))

            # pause before attempt and then increment this pause for the next attempt
            time.sleep(pause_duration)
            pause_duration += pause_increment

            try:
                headers = {
                    'user-agent': ua.title,
                }
                # use `mitmproxy` for debugging purposes
                # proxies = {
                #     'http': 'http://127.0.0.1:8080',
                #     'https': 'http://127.0.0.1:8080',
                # }
                response = requests.get(
                    url
                    , headers=headers
                    # , proxies=proxies
                )
                if response.status_code == 200:
                    self.logger.info(self.log_msg(f'Successfully downloaded html from {url=}'))
                    self.html = response.content.decode('utf-8')
                    self.err_msg = None
                    ua.update_usage(UserAgent.SUCCESSES_FIELD)

                    break
                elif response.status_code == 429: # Too Many Requests; try again
                    self.logger.warning(self.log_msg(f'429 Too Many Requests {url=}'))
                    self.err_msg = '429'
                    ua.update_usage(UserAgent.ERRORS_FIELD)

                    continue
                else:
                    self.logger.error(self.log_msg(f'Error downloading html from {url=}'))
                    self.html = None
                    self.err_msg = response.status_code
            except UserAgentError as ex:
                self.logger.exception(self.log_msg(f'{ex=}'))
            except Exception as ex:
                self.logger.exception(self.log_msg(f'{ex=}'))
                raise ParserError(f'Error for {url=}') from ex

        if self.html:
            return True # successfully downloaded html
        else:
            return False # error while downloading html

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

    logging.config.fileConfig(fname='logging.conf', disable_existing_loggers=False)
    # logger = logging.getLogger(os.path.basename(__file__))

    p = Parser()

    print(p.get_html('http://example.com/'))
    print(p.html)


if __name__ == '__main__':
    main()
