import os
import re
import subprocess
import time


class Utility:
    '''
    various additional methods
    '''
    @classmethod
    def time_spent_hms(cls, start_time: int) -> str:
        '''
        calculate duration of time from start_time in "HH:mm:ss" format

        in: start_time, int - start time in seconds
        out: duration of time from start_time in "HH:mm:ss" format
        '''
        s = int(time.time() - start_time)
        h = s // 3600
        m = s // 60 % 60
        s %= 60
        return f'Total time spent - {h:02}:{m:02}:{s:02}'

    @classmethod
    def string_to_filename(cls, line: str) -> str:
        '''
        simple string converter into a valid filename (only alphanumeric characters and underscores)

        in: line, str - any string
        out: a string of only alphanumeric characters and underscores
        '''
        res = re.sub(r'[\W]+', ' ', line.strip())
        res = re.sub(r'\s+', ' ', res)
        return res.strip()


if __name__ == '__main__':
    # some simple testings for Utility
    if os.name == 'posix':
        _ = subprocess.run('clear')
    else:
        print('\n' * 42)

    string_to_file_data = [
        ('dir1/dir2/dir3', 'dir1 dir2 dir3'),
        ('<some$ %text%  _with_ #non-alphanumeric !characters?> ', 'some text _with_ non alphanumeric characters'),
        ('Hello, World!...', 'Hello World'),
    ]

    print('Tests for Utility.string_to_filename():')
    for idx, (test_data, check_data) in enumerate(string_to_file_data):
        try:
            assert Utility.string_to_filename(test_data) == check_data, f"Utility.string_to_filename('{test_data}') != '{check_data}'"
        except AssertionError as ex:
            print(f'{idx+1}/{len(string_to_file_data)} error : {ex}')
        else:
            print(f'{idx+1}/{len(string_to_file_data)} ok')
