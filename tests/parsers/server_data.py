# server data for Flask test server and for tests in test_parsers_parser.py

import os
import subprocess
from dataclasses import dataclass


# default Flask test server configuration
@dataclass
class ServerConfig:
    protocol: str = 'http'
    host: str = '127.0.0.1'
    port: str = '5000'
    app: str = 'server.py'

    def url(self) -> str:
        return f'{self.protocol}://{self.host}:{self.port}'


server_config = ServerConfig()

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


if __name__ == '__main__':
    # some simple tests for ServerConfig class
    if os.name == 'posix':
        _ = subprocess.run('clear')
    else:
        print('\n' * 42)

    server_config_test_data = [
        ({'protocol': 'http', 'host': '127.0.0.1', 'port': '5000', 'app': 'server.py'}, 'http://127.0.0.1:5000'),
        ({'protocol': 'http', 'host': 'localhost', 'port': '8000', 'app': 'server.py'}, 'http://localhost:8000'),
        ({'protocol': 'http', 'host': '192.168.0.120', 'port': '5050', 'app': 'server.py'}, 'http://192.168.0.120:5050'),
    ]

    print('Testing ServerConfig class:')
    for idx, (test_data, url) in enumerate(server_config_test_data):
        print(f'{idx+1}/{len(server_config_test_data)} : ', end='')
        try:
            test_server_config = ServerConfig(**test_data)
            assert test_server_config.url() == url, f"{test_server_config=}\ntest_server_config.url()='{test_server_config.url()}'\n{url=}"
        except AssertionError as ex:
            print('Error')
            print(ex)
        else:
            print('Ok')
