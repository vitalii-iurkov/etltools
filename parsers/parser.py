# Parser implementation

import copy
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

    def __init__(self, parsers_config: 'DBConfig'):
        '''
        in: parsers_config, DBConfig - configuration to connect to `parsers` database
        '''
        super().__init__(name=os.path.basename(__file__), log_prefix=self.__class__.__name__)

        self.parsers_config = copy.deepcopy(parsers_config)

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

    def get_html(self, url: str, attempts_total: int=10, pause_duration: int=0, pause_increment: int=1, decode_errors: str='strict') -> bool:
        '''
        download html from given url and store it in self.html

        in:
            url, str - url where to download html
            attempts_total, int - total number of attempts to download html from the given url
            pause_duration, int (in seconds) - start pause before GET request
            pause_increment, int (in seconds) - increment for pause before each next attempt
            decode_errors, str - how to handle decoding errors; possible values are 'strict', 'ignore', 'replace'

        out: bool
            True - successfully downloaded html
            False - error while downloading html
        '''
        self.html = None
        self.err_msg = None

        if decode_errors not in ('strict', 'ignore', 'replace'):
            decode_errors = 'strict'

        ua = UserAgent(self.parsers_config)

        # attempts to download html
        for attempt in range(1, attempts_total+1):
            self.logger.info(self.log_msg(f'Request GET {attempt=}, {pause_duration=} seconds, {url=}'))

            # pause before attempt and then increment this pause for the next attempt
            time.sleep(pause_duration)
            pause_duration += pause_increment

            try:
                headers = {
                    'User-Agent': ua.title, # get new or next after error/update User-Agent
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
                    # , verify=False # enable https over http
                )
                if response.status_code == 200:
                    self.html = response.content.decode(encoding='utf-8', errors=decode_errors)
                    self.err_msg = None
                    self.logger.info(self.log_msg(f'Successfully downloaded html from {url=}'))
                    ua.update_usage(UserAgent.SUCCESSES_FIELD)
                elif response.status_code == 429: # Too Many Requests; try again
                    self.err_msg = '429'
                    self.logger.warning(self.log_msg(f'429 Too Many Requests {url=}'))
                    ua.update_usage(UserAgent.ERRORS_FIELD) # next attempt we will take new User-Agent
                else: # if we received any other status code except 200 or 429
                    self.err_msg = response.status_code
                    self.logger.error(self.log_msg(f'Error downloading html from {url=}, status code={response.status_code}'))

                    # here, in general, we do not know what led to the error and, just in case, we make a mark
                    # about the use of this User-Agent, so that next time we can take another User-Agent,
                    # since the error could also occur due to the incorrectness of the User-Agent itself
                    ua.update_usage(UserAgent.UPDATE_TZ_FIELD)
            except UserAgentError as ex:
                # here, this exception should not have an affect on getting html
                # so, if we successfully received the html, we can exit the loop without error
                self.logger.exception(self.log_msg(f'{ex=}'))
            except UnicodeDecodeError as ex:
                self.html = None
                self.err_msg = 'UnicodeDecodeError'
                self.logger.exception(self.log_msg(f'Cannot decode binary content to text format in utf-8, {url=}, {ex=}'))
            except Exception as ex:
                self.logger.exception(self.log_msg(f'{ex=}'))
                raise ParserError(f'Error for {url=}') from ex

            # exit the loop if we don't have an error "429 Too Many Requests"
            if self.err_msg != '429':
                break
        else:
            self.logger.error(self.log_msg(f'Failed to download html from {url=} due to error 429 Too Many Requests'))

        if self.html:
            return True # successfully downloaded html
        else:
            return False # error while downloading html

    def parse_catalog_html(self):
        '''
        parse html catalog page
        should be implemented in child classes
        '''
        raise NotImplementedError

    def parse_item_html(self):
        '''
        parse html item page
        should be implemented in child classes
        '''
        raise NotImplementedError
