# download YouTube playlists
# https://pypi.org/project/pytube/

import os
import subprocess
import time

from pytube import Playlist
from pytube.cli import on_progress


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(BASE_DIR, 'downloads')

PLAYLIST_URL = 'https://www.youtube.com/playlist?list=PL9AH2TSQVitKwjq57nIPIbTwGAtyvL2Ao'


def time_spent(start_time):
    s = int(time.time() - start_time)
    h = s // 3600
    m = s // 60 % 60
    s %= 60

    return f'{h:02}:{m:02}:{s:02}'


def main():
    if os.name == 'posix':
        _ = subprocess.run('clear')
    else:
        print('\n' * 42)

    start_time = time.time()

    pl = Playlist(PLAYLIST_URL)

    PL_DOWNLOADS_DIR = os.path.join(DOWNLOADS_DIR, pl.title)
    if os.path.exists(PL_DOWNLOADS_DIR):
        msg = f'Directory {PL_DOWNLOADS_DIR} already exists'
        print(msg)
        # raise FileExistsError(msg)
    else:
        os.mkdir(PL_DOWNLOADS_DIR)

    for idx, video in enumerate(pl.videos):
        try:
            video.register_on_progress_callback(on_progress)
            yt = video.streams.filter(mime_type='video/mp4', progressive=True).order_by('resolution').desc().first()
            # yt = video.streams.get_by_itag(18)
            print(f'{idx+1}/{len(pl)}: url={video.watch_url}')

            yt.download(
                output_path=PL_DOWNLOADS_DIR
                , filename_prefix=None
                , skip_existing=True
            )
            print()
        except Exception as ex:
            print(f'{ex=}')

        time.sleep(30)

    print(f'Total time spent {time_spent(start_time)}')


if __name__ == '__main__':
    main()
