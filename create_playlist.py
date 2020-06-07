import random
import json
import requests
from exceptions import ResponseException
from secrets import spotify_user_id, spotify_token


def is_sunny(response_json):
    return response_json["valence"] > 0.5 and response_json["danceability"] > 0.6


def is_rainy(response_json):
    return response_json["valence"] < 0.4 and response_json["energy"] < 0.4


class CreatePlaylist:

    def __init__(self, weather):
        self.user_id = spotify_user_id
        self.spotify_token = spotify_token
        self.weather = weather
        self.weather_corr = {"sunny": is_sunny, "rainy": is_rainy}

    def create_playlist(self):
        print(".")
        request_body = json.dumps({
            "name": "Your {} day playlist".format(self.weather),
            "description": "Some songs to fit this {} day".format(self.weather),
            "public": True
        })

        query = "https://api.spotify.com/v1/users/{}/playlists".format(self.user_id)
        response = requests.post(
            query,
            data=request_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(self.spotify_token)
            }
        )
        response_json = response.json()
        #playlist id
        return response_json["id"]

    def get_spotify_uri(self, song_name, artist):

        query = "https://api.spotify.com/v1/search?q=track%3A{}%20artist%3A{}&type=track".format(song_name, artist)

        uri_response = requests.get(
            query,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(self.spotify_token)
            }
        )

        response_json = uri_response.json()
        songs = response_json["tracks"]["items"]
        uri = songs[0]["uri"]

        return uri

    def add_songs_to_playlist(self, selection_size):
        print(".")
        # create playlist
        playlist_id = self.create_playlist()
        uris = self.get_random_songs_from_library(selection_size)

        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id)

        uri_data = json.dumps(uris)

        add_response = requests.post(
            query,
            data=uri_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(self.spotify_token),
            }
        )

        # check for valid response status
        if add_response.status_code != 201:
            raise ResponseException(add_response.status_code)

        response_json = add_response.json()
        return response_json

    def get_random_songs_from_library(self, selection_size):
        song_list = []
        prev = []
        print(".")
        i = 0
        while i < 10:
            offset = random.randrange(0, selection_size)
            while offset in prev:
                offset = random.randrange(0, selection_size)
            prev.append(offset)

            query = "https://api.spotify.com/v1/me/tracks?limit=1&offset={}".format(offset)

            get_response = requests.get(
                query,
                headers={
                    "Authorization": "Bearer {}".format(self.spotify_token)
                }
            )

            if get_response.status_code != 200:
                raise ResponseException(get_response.status_code)

            response_json = get_response.json()
            songs = response_json["items"]
            song = songs[0]['track']['uri']

            song_id = song[14::]

            feature_query = "https://api.spotify.com/v1/audio-features/{}".format(song_id)

            feature_response = requests.get(
                feature_query,
                headers={
                    "Authorization": "Bearer {}".format(self.spotify_token)
                }
            )

            feature_response_json = feature_response.json()

            if not self.weather_corr[self.weather](feature_response_json):
                continue

            song_list.append(songs[0]['track']['uri'])

            i += 1

        return song_list


if __name__ == '__main__':
    weather = input("What's the weather like today? ")
    cp = CreatePlaylist(weather)
    if weather == "rainy":
        pickmeup = input("Do you need a pick me up? y/n ")
        if pickmeup == "y":
            weather = "sunny"

    saved_num = int(input("How many songs do you have saved? "))
    cp.add_songs_to_playlist(saved_num)
    print("Done")
