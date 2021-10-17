from ctypes import POINTER
import json
import os
import re
from bson import json_util
import requests
from progress.bar import Bar


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
    convert_one_to_json,
    # get_folders,
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
    home_dir, app_dir,
    run_fast_scandir
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

    albums = all_songs_instance.find_songs_by_album(query)
    all_songs.append(convert_to_json(albums))

    artists = all_songs_instance.find_songs_by_artist(query)
    all_songs.append(convert_to_json(artists))

    songs = remove_duplicates(all_songs)

    return {'songs': songs}


@bp.route('/populate')
def populate():
    files = run_fast_scandir(home_dir, [".flac", ".mp3"])[1]

    bar = Bar('Processing', max=len(files))
    for file in files:
        file_in_db_obj = all_songs_instance.find_song_by_path(file)
        song_obj = convert_one_to_json(file_in_db_obj)

        try:
            image = song_obj['image']
        except:
            image = None
        
        if image is None:
            try:
                getTags(file)
            except MutagenError:
                pass

        if image is not None and not os.path.exists(image):
            
            extract_thumb(file)

        bar.next()
    
    bar.finish()

    return {"info": "done"}

@bp.route('/file')
def get_file():
    file_id = request.args.get('id')

    song_obj = all_songs_instance.get_song_by_id(file_id)
    json_song = json.dumps(song_obj, default=json_util.default)
    loaded_song = json.loads(json_song)

    filepath = loaded_song['filepath'].split('/')[-1]

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


# @bp.route("/")
# def get_folders():
#     folders = []
#     files = []
    
#     for entry in os.scandir(home_dir):
#         if entry.is_dir():
#             dir_name = entry.name
#             if not dir_name.startswith("."):
#                 folders.append(entry.path)
#         elif entry.is_file():
#             if isValidFile(entry.name):
#                 files.append(entry.path)

#     return {'folders': folders, 'files': files}


# @bp.route("/<folder>")
# def get_files(folder):
#     folder_name = urllib.parse.unquote(folder)

#     songs_obj = all_songs_instance.find_songs_by_folder(folder_name)
#     songs = convert_to_json(songs_obj)
#     # remove_duplicates(songs)

#     for song in songs:
#         song['artists'] = song['artists'].split(', ')

#     count = len(songs)
#     return {'count': count, 'all_files': songs, 'folder_name': folder_name, 'url_safe_name': folder}


@bp.route("/folder/artists")
def get_folder_artists():
    dir = request.args.get('dir')

    songs = all_songs_instance.find_songs_by_folder(dir)
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
    all_songs = all_songs_instance.get_all_songs()
    songs_array = convert_to_json(all_songs)
    remove_duplicates(songs_array)

    artists = []

    for song in songs_array:
        this_artists = song['artists'].split(', ')

        for artist in this_artists:
            if artist not in artists:
                artists.append(artist)

    bar = Bar('Processing images', max=len(artists))
    for artist in artists:
        file_path = app_dir + '/images/artists/' + artist + '.jpg'

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
                        'name': artist
                    }

                    artist_instance.insert_artist(artist_obj)
                except:
                    pass
        else:
            pass

        bar.next()

    bar.finish()

    artists_in_db = artist_instance.get_all_artists()
    artists_in_db_array = convert_to_json(artists_in_db)

    return {'sample': artists_in_db_array[:25]}


@bp.route("/artist")
def getArtistData():
    artist = urllib.parse.unquote(request.args.get('q'))
    artist_obj = artist_instance.find_artists_by_name(artist)
    artist_obj_json = convert_to_json(artist_obj)

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
        if entry.is_dir() and not entry.name.startswith('.'):
            folders.append(entry.path)
        if entry.is_file():
            if isValidFile(entry.name) == True:
                songs_array = all_songs_instance.find_songs_by_folder(requested_dir)
                songs = convert_to_json(songs_array)
                files = songs

    dir_content.close()

    return {"requested": requested_dir, "files": files, "folders": folders}




# @bp.route('/folder')
