from flask import Flask

from etltools.tests.parsers.server_data import server_data


app = Flask(__name__)


@app.route(server_data['ok']['url'])
def response_ok():
    return server_data['ok']['msg'], 200

@app.route(server_data['429_fail']['url'])
def response_429_fail():
    return server_data['429_fail']['msg'], 429

@app.route(server_data['unicode_decode_error']['url'])
def unicode_decode_error():
    return server_data['unicode_decode_error']['msg'], 200


if __name__ == '__main__':
    app.run()
