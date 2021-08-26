import os
from pathlib import Path
from mutagen.mp3 import MP3

from flask import Flask
from flask_cors import CORS


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
    print(dir)

    files = []

    for path in Path(dir).rglob('*.flac'):
        files.append(path.name)

    for path in Path(dir).rglob('*.mp3'):
        files.append(path.name)

    return {'all_files': files}


# @app.route("/tags")
def get_tags():
    folders = os.listdir(music_dir)

    for folder in folders:
        dir = music_dir + folder

        for path in Path(dir).rglob('*.flac'):
            print(path.name)
            tags = MP3(path)
            return tags
    
get_tags()

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8080, debug=True)

