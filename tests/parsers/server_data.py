# server data for Flask test server and for tests in test_parsers_parser.py

# function_name: {server_message: str, status_code: int}
server_data = {
    'unicode_decode_error': {'msg': 'Привет, Мир!'.encode('cp1251'), 'status_code': 200},
}
