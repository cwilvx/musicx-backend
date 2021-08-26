import os
from pathlib import Path

from mutagen.mp3 import MP3
from mutagen.mp3 import HeaderNotFoundError

from mutagen.flac import FLAC, FLACNoHeaderError, MutagenError
# import mutagen.flac.error as error

music_dir = "/home/cwilvx/Music"

def get_tags():
    for folder in music_dir:
        dir = music_dir + folder

        for path in Path(dir).rglob('*.mp3'):
            print(path.name)
            try:
                tags = MP3(path)
                tag = {
                    'filename': path.name,
                    'title': tags['TIT2'].text[0],
                    'artist': tags['TPE1'].text[0],
                    'album': tags['TALB'].text[0],
                    'length': tags.info.length,
                    'bitrate': tags.info.bitrate,
                }
                print(tag)
            except(HeaderNotFoundError, KeyError):
                print("No tags found")

# get_tags()
                # print(tags['TALB']
# get_tags()

def get_flac_tags():
    for folder in music_dir:
        dir = music_dir + folder

        for path in Path(dir).rglob('*.flac'):
            print(path.name)
            try:
                tags = FLAC(path)
                tag = {
                    'filename': path.name,
                    'title': tags['title'][0],
                    'artist': tags['artist'][0],
                    'album': tags['album'][0],
                    'length': tags.info.length,
                    'bitrate': tags.info.bitrate,
                }
                print(tag)
            except(FLACNoHeaderError, KeyError, MutagenError):
                print("No tags found")

get_flac_tags()