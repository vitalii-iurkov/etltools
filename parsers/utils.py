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
        :return: integer number or None if can't correctly convert str to int
        :rtype: int

        :Example:

        str_to_int('123') -> 123
        str_to_int(' 1 234 567 ') -> 1234567
        str_to_int('1  230') -> None
        '''
        try:
            if not isinstance(line, (str,)) or not re.match(r'^[0-9]{1,3}(\s[0-9]{3})*$', line.strip()):
                raise ValueError()
            return int(re.sub(r'\s+', '', line))
        except:
            return None
