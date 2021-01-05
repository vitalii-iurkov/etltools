# -*- coding: utf-8 -*-

# this module reads text files with user-agents from the `./parsers/ua/` subfolder
# and inserts them into PostgreSQL `parsers` database, `user_agent` table

import logging
import logging.config
import os
import subprocess

from etltools.local_settings import parsers_config
from etltools.pg_tools.pg_connector import PgConnector, PgConnectorError


def main():
    if os.name == 'posix':
        _ = subprocess.run('clear')
    else:
        print('\n' * 42)

    logging.config.fileConfig(fname='logging.conf', disable_existing_loggers=False)
    logger = logging.getLogger(os.path.basename(__file__))

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # print(f'{BASE_DIR=}')

    total = 0 # total added user-agents
    query = 'SELECT user_agent_insert_func(%s, %s, %s, %s, %s, %s);'

    with PgConnector(parsers_config) as db:
        fnames = os.listdir(os.path.join(BASE_DIR, 'ua'))
        field_width = len(str(len(fnames)))

        for idx, fname in enumerate(fnames):
            software = fname.removesuffix('.txt')
            print(f'{idx+1:{field_width}}/{len(fnames)} : {software=}')

            with open(os.path.join(BASE_DIR, 'ua', fname), 'r', encoding='utf-8') as f:
                for line in f:
                    title, version, os_type, hardware, popularity = line.strip().split('\t')

                    user_agent_id = db.execute(query, (software, title, version, os_type, hardware, popularity))

                    # if we get new user_agent_id then increase their total amount
                    if user_agent_id[0][0] > 0:
                       total += 1

            db.commit()

    print(f'New user-agents inserted : {total=}')


if __name__ == '__main__':
    main()
