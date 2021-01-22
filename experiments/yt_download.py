# download YouTube playlists and videos
# used module https://pypi.org/project/pytube/

import os
import subprocess
import time

from pytube import Playlist, YouTube
from pytube.cli import on_progress

from etltools.experiments.utility import Utility


class YtDownload:
    class _Decorators:
        @classmethod
        def deco_downloader(cls, f):
            def wrapper(*args, downloads_dir: str, **kwargs):
                # clear screen
                if os.name == 'posix':
                    _ = subprocess.run('clear')
                else:
                    print('\n' * 42)

                # check for the directory
                if not os.path.exists(downloads_dir):
                    raise FileNotFoundError(f"Directory {downloads_dir} doesn't exist")

                start_time = time.time()
                result = f(*args, downloads_dir, **kwargs)
                print(Utility.time_spent_hms(start_time)) # print download duration

                return result

            return wrapper

    @classmethod
    @_Decorators.deco_downloader
    def download_videos(cls, downloads_dir: str, urls: list, pause_between_downloads: int=3) -> None:
        '''
        download videos from YouTube to specified directory

        in:
            downloads_dir, str - directory for saving video; must already be created
            urls, list - list of videos url
            pause_between_downloads, int - in seconds
        '''
        for idx, url in enumerate(urls):
            try:
                yt = YouTube(url)
                print(f'{idx+1}/{len(urls)}: {url}')

                yt.register_on_progress_callback(on_progress)
                yt.streams.filter(mime_type='video/mp4', progressive=True).order_by('resolution').desc().first().download(
                    output_path=downloads_dir
                    , filename_prefix=None
                    , skip_existing=True
                )
                print()
            except Exception as ex:
                print(f'{ex=}')

            time.sleep(pause_between_downloads) # pause before downloading the next video

    @classmethod
    @_Decorators.deco_downloader
    def download_playlist(cls, downloads_dir: str, pl_url: str, pause_between_downloads: int=3):
        '''
        download videos from YouTube Playlist to specified directory
        subdirectory for the playlist will be created

        in:
            downloads_dir, str - base directory for saving video; must already be created
            pl_url, str - YouTube playlist url
            pause_between_downloads, int - in seconds
        '''
        pl = Playlist(pl_url)
        PLAYLIST_SUBDIR = Utility.string_to_filename(pl.title)

        PL_DOWNLOADS_DIR = os.path.join(DOWNLOADS_DIR, PLAYLIST_SUBDIR)
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

            time.sleep(pause_between_downloads) # pause before downloading the next video


if __name__ == '__main__':
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DOWNLOADS_DIR = os.path.join(BASE_DIR, 'downloads')

    # use

    # <download playlist>
    # PLAYLIST_URL = ''
    # yt = YtDownload()
    # yt.download_playlist(
    #     downloads_dir=DOWNLOADS_DIR,
    #     pl_url=PLAYLIST_URL,
    #     pause_between_downloads=3
    # )

    # or

    # <download videos>
    # yt = YtDownload()
    # yt.download_videos(
    #     downloads_dir=DOWNLOADS_DIR,
    #     urls=[
    #         '',
    #     ],
    #     pause_between_downloads=3
    # )
