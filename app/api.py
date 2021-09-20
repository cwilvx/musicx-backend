import os
import json
import requests
from io import BytesIO
from PIL import Image

from bson import json_util

from pathlib import Path
import urllib

from mutagen.mp3 import MP3
from mutagen.flac import FLAC, MutagenError

from app.models import Folders, Artists, AllSongs

from flask import Blueprint, request

bp = Blueprint('api', __name__, url_prefix='')

artist_instance = Artists()
folder_instance = Folders()
all_songs_instance = AllSongs()


music_dir = os.environ.get("music_dir")
PORT = os.environ.get("PORT")


def getTags(full_path, audio, image_path, folder):
    try:
        artist = audio['artist'][0]
    except KeyError:
        try:
            artist = audio['TPE1'][0]
        except:
            artist = 'Unknown'
    except IndexError:
        artist = 'Unknown'

    try:
        title = audio['title'][0]
    except KeyError:
        try:
            title = audio['TIT2'][0]
        except:
            title = 'Unknown'
    except IndexError:
        title = 'Unknown'

    try:
        album = audio['album'][0]
    except KeyError:
        try:
            album = audio['TALB'][0]
        except:
            album = "Unknown"
    except IndexError:
        album = "Unknown"

    try:
        genre = audio['genre'][0]
    except KeyError:
        try:
            genre = audio['TCON'][0]
        except:
            genre = "Unknown"
    except IndexError:
        genre = "Unknown"
    artists_array = []

    for artist in artist.split(', '):
        artists_array.append(artist)

    tags = {
        'filepath': full_path.replace(music_dir, ''),
        'folder': folder,
        'title': title,
        'artists': artists_array,
        'album': album,
        'genre': genre,
        'length': round(audio.info.length),
        'bitrate': audio.info.bitrate,
        'image': image_path
    }
    all_songs_instance.insert_song(tags)


def convert_to_json(array):
    songs = []

    for song in array:
        json_song = json.dumps(song, default=json_util.default)
        songs.append(json.loads(json_song))

    return songs


def remove_duplicates(array):
    if len(array) != 0 and len(array) != 1:
        index = 1
        test_song = array[index]
    else:
        index = 0

    for song in array:
        if index < len(array) and len(array) != 0 and len(array) != 1:
            if song['title'] == test_song['title'] and song['album'] == test_song['album'] and song['artists'] == test_song['artists']:
                array.remove(song)
                index = index + 1

    return array


@bp.route('/search')
def search_by_title():
    if not request.args.get('q'):
        query = "mexican girl"
    else:
        query = request.args.get('q')

    songs = all_songs_instance.find_song_by_title(query)
    all_songs = convert_to_json(songs)
    # remove_duplicates(all_songs)

    return {'songs': all_songs}


@bp.route('/populate')
def populate():
    folders = os.listdir(music_dir)

    for folder in folders:
        folder_name = urllib.parse.unquote(folder)

        dir = music_dir + folder_name

        for path in Path(dir).rglob('*.flac'):
            print("processing: " + path.name)
            image_absolute_path = folder_name + '/.thumbnails/' + \
                path.name.replace('.flac', '.jpg')
            image_path = music_dir + image_absolute_path

            if os.path.exists(image_path):
                url_compatible_image_url = urllib.parse.quote(
                    image_absolute_path)
                image_url = 'http://localhost:{}/{}'.format(
                    PORT, url_compatible_image_url)
            try:
                audio = FLAC(path)
                file_path = path.resolve().as_posix()
                audio_url = 'http://localhost:{}/{}'.format(
                    PORT, urllib.parse.quote(file_path))
                getTags(audio_url, audio, image_url, folder)

            except(KeyError, MutagenError):
                pass

        for path in Path(dir).rglob('*.mp3'):
            print("processing: " + path.name)
            image_absolute_path = folder_name + '/.thumbnails/' + \
                path.name.replace('.mp3', '.jpg')
            image_path = music_dir + image_absolute_path

            if os.path.exists(image_path):
                url_compatible_image_url = urllib.parse.quote(
                    image_absolute_path)
                image_url = 'http://localhost:{}/{}'.format(
                    PORT, url_compatible_image_url)

            try:
                audio = MP3(path)
                audio_url = 'http://localhost:{}/{}'.format(
                    PORT, urllib.parse.quote(file_path))
                getTags(audio_url, audio, image_url, folder)
            except(IndexError, MutagenError):
                pass

    return {'data': 'completed'}


@bp.route("/")
def get_folders():
    folders = os.listdir(music_dir)
    folders_array = []

    for folder in folders:
        if os.path.isdir(music_dir + folder):
            folder_obj = {
                'name': folder,
                'url': urllib.parse.quote(folder),
            }

            folders_array.append(folder_obj)
    return {
        'server_port': 'http://localhost:{}'.format(PORT),
        'type': 'folder',
        'all_folders': folders_array
    }


@bp.route("/<folder>")
def get_files(folder):
    folder_name = urllib.parse.unquote(folder)

    songs_obj = all_songs_instance.find_songs_by_folder(folder_name)
    songs = convert_to_json(songs_obj)
    # remove_duplicates(songs)

    count = len(songs)
    return {'count': count, 'all_files': songs, 'folder_name': folder_name, 'url_safe_name': folder}


@bp.route("/<folder>/artists")
def get_folder_artists(folder):
    folder_name = urllib.parse.unquote(folder)

    songs = all_songs_instance.find_songs_by_folder(folder_name)
    songs_array = convert_to_json(songs)

    artists = []

    for song in songs_array:
        this_artists = song['artists']

        for artist in this_artists:
            if artist not in artists:
                artists.append(artist)

    final_artists = []

    for artist in artists[0: 9]:
        artist_obj = artist_instance.find_artists_by_name(artist)

        final_artists.append(convert_to_json(artist_obj))

    return {'artists': final_artists}


def save_image(url, path):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    img.save(path, 'JPEG')


@bp.route("/populate/images")
def populate_images():
    if not os.path.exists(music_dir + '.thumbnails'):
        os.makedirs(music_dir + '.thumbnails')

    all_songs = all_songs_instance.get_all_songs()
    songs_array = convert_to_json(all_songs)
    remove_duplicates(songs_array)

    artists = []

    for song in songs_array:
        this_artists = song['artists']

        for artist in this_artists:
            if artist not in artists:
                artists.append(artist)

    for artist in artists:
        file_path = music_dir + '.thumbnails/' + artist + '.jpg'
        absolute_path = '.thumbnails/' + artist + '.jpg'

        if not os.path.exists(file_path):
            url = 'https://api.deezer.com/search/artist?q={}'.format(artist)
            response = requests.get(url)
            data = response.json()

            try:
                image_path = data['data'][0]['picture_medium']
            except:
                image_path = None
            
            if image_path is not None:
                try:
                    save_image(image_path, file_path)
                    artist_obj = {
                        'name': artist,
                        'image': 'http://localhost:{}/{}'.format(PORT, urllib.parse.quote(absolute_path))
                    }

                    artist_instance.insert_artist(artist_obj)
                    print('saved image for: {}'.format(artist))
                except:
                    print("error saving image for {}".format(artist))

    artists_in_db = artist_instance.get_all_artists()
    artists_in_db_array = convert_to_json(artists_in_db)

    return {'artists': artists_in_db_array}
