from ctypes import POINTER
import json
import os
import re
from bson import json_util
import requests



from pathlib import Path
import urllib

# from mutagen.mp3 import MP3
from mutagen.flac import MutagenError
# from requests.api import get

from app.models import AllSongs, Folders, Artists
from app.configs import default_configs

from flask import Blueprint, request, send_from_directory

from app.helpers import (
    all_songs_instance,
    get_folders,
    getTags,
    # music_dirs,
    PORT,
    convert_to_json,
    remove_duplicates,
    save_image,
    isValidFile,
    getFolderContents,
    create_config_dir,
    extract_thumb,
    home_dir
)

bp = Blueprint('api', __name__, url_prefix='')

artist_instance = Artists()
folder_instance = Folders()

def main_whatever():
    create_config_dir()
    # extract_thumb("/home/cwilvx/Music/a.flac")
    extract_thumb("/home/cwilvx/Music/a.mp3")

main_whatever()

@bp.route('/search')
def search_by_title():
    if not request.args.get('q'):
        query = "mexican girl"
    else:
        query = request.args.get('q')

    songs = all_songs_instance.find_song_by_title(query)
    all_songs = convert_to_json(songs)
    songs = remove_duplicates(all_songs)

    return {'songs': songs}


@bp.route('/populate')
def populate():
    folders = []

    for dir in default_configs['dirs']:
        entries = os.scandir(dir)

        # base_url = "http://localhost:{}{}".format(
        #     PORT,
        #     dir
        # )
        # print(base_url)

        for entry in entries:
            if entry.is_dir():
                folders.append(entry.path)

    for folder in folders:
        for entry in os.scandir(folder):
            if entry.is_file() and isValidFile(entry.name):
                try:
                    getTags(entry.path, folder)
                except MutagenError:
                    pass
    return "heheee"




@bp.route('/file')
def get_file():
    file_id = request.args.get('id')

    song_obj = all_songs_instance.get_song_by_id(file_id)
    json_song = json.dumps(song_obj, default=json_util.default)
    loaded_song = json.loads(json_song)

    filepath = loaded_song['filepath'].split('/')[-1]
    print(filepath)

    return send_from_directory(loaded_song['folder'], filepath)

        # folder_name = urllib.parse.unquote(folder)

        # dir = music_dir + folder_name

        # for path in Path(folder).rglob('*.flac'):
        #     print("processing: " + path.name)

            # image_absolute_path = folder_name + '/.thumbnails/' + \
            #     path.name.replace('.flac', '.jpg')
            # image_path = music_dir + image_absolute_path

            # if os.path.exists(image_path):
            #     url_compatible_image_url = urllib.parse.quote(
            #         image_absolute_path)
            #     image_url = 'http://localhost:{}/{}'.format(
            #         PORT, url_compatible_image_url)
            # try:
            #     audio = FLAC(path)
            #     file_path = path.resolve().as_posix()
            #     audio_url = 'http://localhost:{}/{}'.format(
            #         PORT, urllib.parse.quote(file_path))
            #     getTags(audio_url, audio, image_url, folder)

            # except(KeyError, MutagenError):
            #     pass

        # for path in Path(dir).rglob('*.mp3'):
        #     print("processing: " + path.name)
        #     image_absolute_path = folder_name + '/.thumbnails/' + \
        #         path.name.replace('.mp3', '.jpg')
        #     image_path = music_dir + image_absolute_path

        #     if os.path.exists(image_path):
        #         url_compatible_image_url = urllib.parse.quote(
        #             image_absolute_path)
        #         image_url = 'http://localhost:{}/{}'.format(
        #             PORT, url_compatible_image_url)

        #     try:
        #         audio = MP3(path)
        #         audio_url = 'http://localhost:{}/{}'.format(
        #             PORT, urllib.parse.quote(file_path))
        #         getTags(audio_url, audio, image_url, folder)
        #     except(IndexError, MutagenError):
        #         pass

    # return {'data': 'completed'}


@bp.route("/")
def get_folders():
    folders = []
    files = []
    
    for entry in os.scandir(home_dir):
        if entry.is_dir():
            dir_name = entry.name
            if not dir_name.startswith("."):
                folders.append(entry.path)
        elif entry.is_file():
            if isValidFile(entry.name):
                files.append(entry.path)

    return {'folders': folders, 'files': files}


@bp.route("/<folder>")
def get_files(folder):
    folder_name = urllib.parse.unquote(folder)

    songs_obj = all_songs_instance.find_songs_by_folder(folder_name)
    songs = convert_to_json(songs_obj)
    # remove_duplicates(songs)

    for song in songs:
        song['artists'] = song['artists'].split(', ')

    count = len(songs)
    return {'count': count, 'all_files': songs, 'folder_name': folder_name, 'url_safe_name': folder}


@bp.route("/<folder>/artists")
def get_folder_artists(folder):
    folder_name = urllib.parse.unquote(folder)

    songs = all_songs_instance.find_songs_by_folder(folder_name)
    songs_array = convert_to_json(songs)
    without_duplicates = remove_duplicates(songs_array)

    artists = []

    for song in without_duplicates:
        this_artists = song['artists'].split(', ')

        for artist in this_artists:
            if artist not in artists:
                artists.append(artist)

    final_artists = []

    for artist in artists[:15]:
        artist_obj = artist_instance.find_artists_by_name(artist)

        if artist_obj != []:
            final_artists.append(convert_to_json(artist_obj))

    return {'artists': final_artists}



@bp.route("/populate/images")
def populate_images():
    if not os.path.exists(music_dir + '.thumbnails'):
        os.makedirs(music_dir + '.thumbnails')

    all_songs = all_songs_instance.get_all_songs()
    songs_array = convert_to_json(all_songs)
    remove_duplicates(songs_array)

    artists = []

    for song in songs_array:
        this_artists = song['artists'].split(', ')

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
                image_path = data['data'][0]['picture_xl']
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
        else:
            artist_obj = {
                'name': artist,
                'image': 'http://localhost:{}/{}'.format(PORT, urllib.parse.quote(absolute_path))
            }

            artist_instance.insert_artist(artist_obj)
            print('already exists for: {}'.format(artist))

    artists_in_db = artist_instance.get_all_artists()
    artists_in_db_array = convert_to_json(artists_in_db)

    return {'artists': artists_in_db_array}


@bp.route("/artist")
def getArtistData():
    artist = urllib.parse.unquote(request.args.get('q'))
    # artist = "Bob Marley"
    artist_obj = artist_instance.find_artists_by_name(artist)
    artist_obj_json = convert_to_json(artist_obj)
    print(artist_obj_json)

    def getArtistSongs():
        songs = all_songs_instance.find_songs_by_artist(artist)
        songs_array = convert_to_json(songs)

        return songs_array

    artist_songs = getArtistSongs()
    songs = remove_duplicates(artist_songs)

    def getArtistAlbums():
        artist_albums = []
        albums_with_count = []

        albums = all_songs_instance.find_songs_by_album_artist(artist)
        albums_array = convert_to_json(albums)

        for song in songs:
            song['artists'] = song['artists'].split(', ')

        for song in albums_array:
            if song['album'] not in artist_albums:
                artist_albums.append(song['album'])

        for album in artist_albums:
            count = 0
            length = 0

            for song in artist_songs:
                if song['album'] == album:
                    count = count + 1
                    length = length + song['length']

            album_ = {
                "title": album,
                "count": count,
                "length": length
            }

            albums_with_count.append(album_)

        return albums_with_count

    return {'artist': artist_obj_json, 'songs': songs, 'albums': getArtistAlbums()}


@bp.route("/tree")
def getFolderTree():
    requested_dir = request.args.get('folder')
    dir_content = os.scandir(requested_dir)

    folders = []
    files = []

    for entry in dir_content:
        if entry.is_dir():
            folders.append(entry.path)
        if entry.is_file():
            if isValidFile(entry.name) == True:
                files.append(getFolderContents(entry.path, requested_dir))

    dir_content.close()

    return {"requested": requested_dir, "files": files, "folders": folders}




# @bp.route('/folder')
