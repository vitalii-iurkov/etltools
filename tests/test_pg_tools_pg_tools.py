import unittest

from etltools.pg_tools.pg_tools import PgTools, PgToolsError


class PgToolsTest(unittest.TestCase):

    def test_list_to_array(self):
        '''
        successful convertions from Python lists into PostgreSQL ARRAY data type
        '''
        test_data = [
            (['alpha ', 'beta ', 'gamma '], 'str', '{"alpha","beta","gamma"}'),
            ([1, 2, 3, 4, 5], 'int', '{1,2,3,4,5}'),
            ([1.123, 2.7, 3.14, 4.5, 5.585], 'int', '{1,2,3,4,5}'),
            ([1.123, 2.7, 3.14, 4.5, 5.585], 'float', '{1.123,2.7,3.14,4.5,5.585}'),
            ([3.14, 2.81, 1.67], 'str', '{"3.14","2.81","1.67"}'),
        ]

        for idx, (lst, dtype, result) in enumerate(test_data):
            with self.subTest(idx=idx, lst=lst, dtype=dtype, result=result):
                self.assertEqual(PgTools.list_to_array(lst=lst, dtype=dtype), result)

    def test_list_to_array_pg_tools_error(self):
        '''
        error converting Python object into PostgreSQL ARRAY data type
        '''
        test_data = [
            ([(3.14, 12.2), (2.81, 5.17), (1.67, 9.01)], 'tuple', '{"(3.14, 12.2)","(2.81, 5.17)","(1.67, 9.01)"}'),
            ('abcd', 'str', '{"abcd"}'),
            (42, int, '{42}'),
            ({"height": 20, "width": 16}, 'dict', '{"height": 20, "width": 16}'),
        ]

        for idx, (lst, dtype, result) in enumerate(test_data):
            with self.subTest(idx=idx, lst=lst, dtype=dtype, result=result):
                with self.assertRaises(PgToolsError):
                    _ = PgTools.list_to_array(lst=lst, dtype=dtype)
