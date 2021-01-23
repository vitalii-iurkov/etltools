from flask import Flask

from etltools.tests.parsers.server_data import server_data


app = Flask(__name__)


@app.route('/ok')
def response_ok():
    return server_data['ok']['msg'], server_data['ok']['status_code']

@app.route(server_data['unicode_decode_error']['url'])
def unicode_decode_error():
    return server_data['unicode_decode_error']['msg'], server_data['unicode_decode_error']['status_code']


if __name__ == '__main__':
    app.run()
