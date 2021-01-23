# server data for Flask test server and for tests in test_parsers_parser.py

host_name = 'http://127.0.0.1:5000'

# function_name: {url: str, server_message: str, status_code: int}
server_data = {
    'ok': {
        'url': '/ok',
        'msg': 'ok',
        'status_code': 200,
    },
    'unicode_decode_error': {
        'url': '/unicode_decode_error',
        'msg': 'Привет, Мир!'.encode('cp1251'),
        'status_code': 200,
    },
}
