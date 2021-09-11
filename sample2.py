from io import BytesIO

from mutagen.mp3 import MP3
from mutagen.id3 import ID3
from mutagen.flac import FLAC

from PIL import Image

song_path = "/home/cwilvx/Music/a.flac"

track = FLAC(song_path)
# tags = ID3(song_path)

pic = track.pictures[0]
img = Image.open(BytesIO(pic.data))
# image = Image.open(BytesIO(pic))
img.save("/home/cwilvx/Music/a.jpg")