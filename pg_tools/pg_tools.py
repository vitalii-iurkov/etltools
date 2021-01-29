'''
set of various tools
'''

class PgToolsError(Exception):
    pass


class PgTools:

    @classmethod
    def list_to_array(cls, lst: list, dtype: str='str') -> str:
        '''
        convert Python list into PostgreSQL ARRAY data type

        :param lst: a list to convert
        :type lst: list or tuple
        :param dtype: data type of list elements, defaults to 'str'
        :type dtype: str, optional
        :raises TypeError: if `lst` isn't list or tuple
        :raises TypeError: if `dtype` not 'int', 'float' or 'str'
        :raises PgToolsError: resulting exception of any error, include TypeError
        :return: a string of PostgreSQL ARRAY data type
        :rtype: str

        :Example:

        >>> PgTools.list_to_array(['alpha ', 'beta ', 'gamma '], 'str')
        '{"alpha","beta","gamma"}'
        >>> PgTools.list_to_array([1, 2, 3, 4, 5], 'int')
        '{1,2,3,4,5}'
        '''
        try:
            if not isinstance(lst, (list, tuple)):
                raise TypeError(f'The object {lst} must be of type list or tuple.')

            if dtype == 'int':
                line = ','.join([str(int(value)) for value in lst])
            elif dtype == 'float':
                line = ','.join([str(float(value)) for value in lst])
            elif dtype == 'str':
                line = ','.join([f'"{str(value).strip()}"' for value in lst])
            else:
                raise TypeError(f"dtype must be 'int', 'float' or 'str'")

            line = '{' + line + '}'

            return line
        except Exception as ex:
            raise PgToolsError(f'Cannot convert Python object "{lst}" into PostgreSQL array.') from ex
