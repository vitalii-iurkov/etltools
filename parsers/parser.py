# -*- coding: utf-8 -*-

import os
import subprocess

from etltools.additions.logger import Logger


class ParserError(Exception):
    pass


class Parser(Logger):
    def __init__(self):
        pass


def main():
    if os.name == 'posix':
        _ = subprocess.run('clear')
    else:
        print('\n' * 42)

    print(os.name)


if __name__ == '__main__':
    main()
