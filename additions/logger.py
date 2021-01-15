# add logging functionality to other classes

import logging


class Logger:
    '''
    add logging functionality
    '''
    def __init__(self, name: str, log_prefix: str):
        '''
        in:
            name, str - name of the file, for example, os.path.basename(__file__)
            log_prefix, str - for example, self.__class__.__name__
        '''
        self.logger = logging.getLogger(name)
        self.log_prefix = log_prefix

    def log_msg(self, msg: str):
        return f'[{self.log_prefix}] ' + msg
