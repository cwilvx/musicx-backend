import os
import hashlib
from pathlib import Path
import urllib

from mutagen.mp3 import MP3
from mutagen.flac import FLAC, MutagenError

from app.models import Folders

from flask import Blueprint

bp = Blueprint('api', __name__, url_prefix='')

def getMP3Tags(full_path, audio, array):
    absolute_path = full_path.replace(music_dir,'')

    try:
        # artist = audio['TPE1'][0]
        artist = audio.getall('artist')[0]
        print(artist)
    except IndexError:
        artist = 'Unknown'

    try:
        title = audio['TIT2'][0]
    except IndexError:
        title = 'Unknown'

    try:
        album = audio['TALB'][0]
    except IndexError:
        album = "Unknown"

    try:
        genre = audio['TCON'][0]
    except:
        genre = 'Unknown'

    tags = {
        'filepath': absolute_path,
        'title': title,
        'artist': artist,
        'album': album,
        'genre': genre,
        'length': audio.info.length,
        'bitrate': audio.info.bitrate,
    }
    array.append(tags)


def getFLACTags(full_path, audio, array):
    absolute_path = full_path.replace(music_dir,'')
    tags = {
        'filepath': absolute_path,
        'title': audio['title'][0],
        'artist': audio['artist'][0],
        'album': audio['album'][0],
        'genre': audio['genre'][0],
        'length': audio.info.length,
        'bitrate': audio.info.bitrate,
    }
    array.append(tags)


def noTags(path, array):
    full_path = path.resolve().as_posix()
    absolute_path = full_path.replace(music_dir,'')

    array.append(absolute_path)


music_dir = os.environ.get("music_dir")
PORT = os.environ.get("PORT")


@bp.route('/update_folders')
def index():

    return "Hello, World!"

@bp.route("/")
def get_folders():
    folders = os.listdir(music_dir)
    folders_array = []

    for folder in folders:
        folder_obj = {
            'name': folder,
            'url': urllib.parse.quote_plus(folder),
        }

        folders_array.append(folder_obj)

    return {
        'server_port': 'http://localhost:{}'.format(PORT),
        'all_folders': folders_array
        }


@bp.route("/<folder>")
def get_files(folder):
    folder_name = urllib.parse.unquote_plus(folder)
    dir = music_dir + folder_name

    folder_files = []

    for path in Path(dir).rglob('*.flac'):
        try:
            audio = FLAC(path)
            full_path = path.resolve().as_posix()
            getFLACTags(full_path, audio, folder_files)
            print(audio['artist'])

        except(KeyError, MutagenError):
            noTags(path, folder_files)

    for path in Path(dir).rglob('*.mp3'):
        try:
            audio = MP3(path)
            full_path = path.resolve().as_posix()
            getMP3Tags(full_path, audio, folder_files)
        except(KeyError):
            noTags(path)
    
    count = len(folder_files)
    return {'count': count,'all_files': folder_files, 'folder_name': folder_name}
