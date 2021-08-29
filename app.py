import os
from pathlib import Path
from mutagen.mp3 import MP3
from mutagen.flac import FLAC, FLACNoHeaderError, MutagenError

from flask import Flask
from flask_cors import CORS


def getMP3Tags(full_path, audio, array):
    absolute_path = full_path.replace(music_dir,'')

    try:
        artist = audio['TPE1'][0]
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


app = Flask(__name__)
CORS(app)

music_dir = os.environ.get("music_dir")
PORT = os.environ.get("PORT")

@app.route("/")
def get_folders():
    folders = os.listdir(music_dir)
    return {
        'home_folder': music_dir,
        'server_port': 'http://localhost:{}'.format(PORT),
        'all_folders': folders
        }


@app.route("/<folder>")
def get_files(folder):
    dir = music_dir + folder
    folder_files = []

    for path in Path(dir).rglob('*.flac'):
        try:
            audio = FLAC(path)
            full_path = path.resolve().as_posix()
            getFLACTags(full_path, audio, folder_files)

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
    return {'count': count,'all_files': folder_files}

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8080, debug=False)

