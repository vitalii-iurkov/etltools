import unittest

from etltools.parsers.utils import Utils


class UtilsTest(unittest.TestCase):

    def test_clear_string_from_spaces(self):
        '''
        transform any space symbol to ' ' symbol and delete from string all repeating spaces
        '''
        test_data = [
            ('Some\n\nmultiline\ntext\n\n', 'Some multiline text'),
            ('abc        123   \t\t poi  ', 'abc 123 poi'),
            ('    if status_code == 403:\n        break\n', 'if status_code == 403: break'),
        ]
        for idx, (line, result) in enumerate(test_data):
            with self.subTest(idx=idx, line=line, result=result):
                self.assertEqual(Utils.clear_string_from_spaces(line), result)

    def test_str_to_int(self):
        '''
        simple converter from string to an integer, supports only strings of digits and spaces
        '''
        test_data = [
            ('12 345 678', 12345678),
            ('3.14', None),
            (12, None),
            ('12e', None),
            ('123', 123),
        ]
        for idx, (line, result) in enumerate(test_data):
            with self.subTest(idx=idx, line=line, result=result):
                self.assertEqual(Utils.str_to_int(line), result)
