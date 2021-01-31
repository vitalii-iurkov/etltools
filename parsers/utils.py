import re


class Utils:
    '''
    some utilities for cleaning and transforming text data
    '''

    @classmethod
    def clear_string_from_spaces(self, line: str) -> str:
        '''
        transform any space symbol to ' ' symbol and delete from string all repeating spaces

        :param line: source string
        :type line: str
        :return: processed string
        :rtype: str
        '''
        return re.sub(r'\s+', ' ', line.strip())

    @classmethod
    def str_to_int(cls, line: str) -> int:
        '''
        simple converter from string to an integer, supports only strings of digits and spaces

        :param line: source string
        :type line: str
        :return: integer number
        :rtype: int
        '''
        try:
            return int(re.sub(r'\s+', '', line))
        except:
            return None
