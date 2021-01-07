#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# get lines from `parsers_dump_20210106_sample_user_agents_data.sql` dump file
# and write them into separate text files in `ua_sample_data` subdirectory

import os
import shutil


USER_AGENTS_DIR = 'ua_sample_data'
USER_AGENTS_SAMPLE_DATA_FILE = 'parsers_dump_20210106_sample_user_agents_data.sql'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# delete and recreate USER_AGENTS_DIR directory
if os.path.exists(os.path.join(BASE_DIR, USER_AGENTS_DIR)):
    shutil.rmtree(os.path.join(BASE_DIR, USER_AGENTS_DIR))

os.mkdir(os.path.join(BASE_DIR, USER_AGENTS_DIR))


ua = []
with open(os.path.join(BASE_DIR, USER_AGENTS_SAMPLE_DATA_FILE), 'r', encoding='utf-8') as f:
    for line in f:
        software, line = line.strip().split('\t', 1)

        # use `software` field as file name
        fname = os.path.join(BASE_DIR, USER_AGENTS_DIR, f'{software}.txt')
        with open(fname, 'a', encoding='utf-8') as ofs:
            ofs.write(line + '\n')
