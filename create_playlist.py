# source for code example (without user auth): https://github.com/spotipy-dev/spotipy
# to run: py data_upload.py from same directory


import spotipy
from spotipy.oauth2 import SpotifyClientCredentials # downloaded with py -m pip install spotipy
import spotipy.util as util
import pandas as pd
from google.cloud import bigquery
from sklearn.metrics.pairwise import cosine_similarity #scikit-learn and sklearn are the same library. sklearn is just an alias for scikit-learn
import os
import numpy as np
import re

###### SETTINGS

# Spotify API credentials (hide?)
CLIENT_ID = "2d78b09918524458b4fcc776b822673c"
CLIENT_SECRET = "10859191e6a34ac8afe7b7639a644d69"

# Initialize Spotipy client
sp = spotipy.Spotify(auth_manager=spotipy.SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET))

'''
Free BQ Tier
- process up to 1 TB of data per month for free.
- up to 10 GB of storage, 1 GB of querying per day, and 10 GB of streaming inserts per day.

Steps to fix authentication issue
- Google Cloud Console (https://console.cloud.google.com/).
- Create a new project or select an existing one.
- Click on the "Activate Cloud Shell" button at the top right corner of the page. This will open a terminal window with the Cloud SDK installed.
- Run the following command in the terminal to set the default project: gcloud config set project <your-project-id>
- Run the following command to authenticate your ADC:gcloud auth application-default login
- This will open a web page where you can sign in with your Google account and grant permission to access your resources.

'''

###### BQ SETTINGS

project = 'song-recommender-385801'
dataset = 'api_in'
bq_table = 'track_features'

###### ENV SETTINGS

import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '../song-recommender-385801-353a937bd051.json'

###### PROGRAM

# Extracts the track URI from a Spotify share URL
def get_track_uri(url):
    match = re.search(r'track\/(\w+)', url)
    if match:
        track_id = match.group(1)
        track_uri = f"spotify:track:{track_id}"
        return track_uri
    else:
        raise ValueError("Invalid Spotify share URL")


# get track audio features for a given track
def get_track_audio_features(track_uri, sp):
    track_id = track_uri.split(':')[-1]
    track_features = sp.audio_features(tracks=[track_id])[0]
    track_row = (track_features['uri'], track_features['danceability'], track_features['energy'], track_features['key'], track_features['loudness'], track_features['mode'], track_features['speechiness'], track_features['acousticness'], track_features['instrumentalness'], track_features['liveness'], track_features['valence'], track_features['tempo'], track_features['duration_ms'], track_features['time_signature'])
    return track_row

# get track properties for a given track, for display
def get_track_properties(track_uri):
    track_properties = {} # {'name': x, 'artist': x}
    track_metadata = sp.track(track_uri)
    track_properties['name'] = track_metadata['name'] 
    track_properties['artist'] = track_metadata['artists'][0]['name']
    return track_properties


# Gets similar tracks from BigQuery table using content-based filtering
def get_similar_track_uris(track_uri):
    
    client = bigquery.Client()

    # Retrieve previously inserted track features
    query = f"""
        SELECT *
        FROM `{project}.{dataset}.{bq_table}`
    """

    candidates_df = client.query(query).to_dataframe() #all candidates ONLY

    # Generate input_track_fatures and save on df
    input_track_features = get_track_properties(track_uri, sp)
    input_track_df = pd.DataFrame(input_track_features, columns=['uri', 'danceability', 'energy','key','loudness','mode','speechiness','acousticness','instrumentalness','liveness','valence','tempo','duration_ms','time_signature'])

    # combine track features

    df = pd.concat(input_track_df, candidates_df)

    # Calculates similarity
    input_track_features = df[df['uri'] == track_uri].iloc[0][1:] #starting from 2nd column
    df['similarity'] = df[df['uri'] != track_uri].iloc[:, 1:].apply(lambda x: cosine_similarity([input_track_features, x])[0][1], axis=1)
    similar_tracks = df.sort_values(by='similarity', ascending=False).head(20)

    # Creates list of uris
    track_uris = similar_tracks['uri'].tolist()

    return track_uris

# display info
def display_similar_songs (track_uris):
    # extract metadata
    metadata = {}
    for uri in track_uris:
        metadata[uri] = get_track_properties(track_uri) #returns {'name': x, 'artist': x}

    # display output
    track_num = 1
    for uri, meta in metadata:
        print(f"Track: {track_num}: {meta['name']} by {meta['artist']} ({uri})")
        track_num += 1

# display info
def display_input_song (uri):
    # extract metadata
    meta = get_track_properties(uri) #returns {'name': x, 'artist': x}
    print(f"You entered this song: {meta['name']} by {meta['artist']} ({uri})")


# Examples to test
track_uri_1 = 'spotify:track:6v0UJD4a2FtleHeSYVX02A?si=3d28829c47ba4fb7'  
track_url_1 = 'https://open.spotify.com/track/6v0UJD4a2FtleHeSYVX02A?si=0095b201771d4357' # I Love Wine by Adele
track_url_2 = 'https://open.spotify.com/track/6UZS3KgNc0NF13bbtQTzD6?si=b0a8bb86665544e9' #The Jump off Lil Kim


print("WELCOME TO THIS APP!")
print("ENTER A SPOTIFY SONG LINK THAT MATCHES THE MOOD OF YOUR WORKOUT TO GET THE IDEAL WORKOUT PLAYLIST BASED ON SIMILAR SONGS")
print()
print('Enter a Spotify Song Link (URL):')

# Extract url and print input song
track_url = input().strip() # remove leading and trailing spaces
track_uri = get_track_uri(track_url)
display_input_song (track_uri)
print()

#Extract similar songs and display them
similar_track_uris = get_similar_track_uris(track_uri)
print("Here is your workout playlist!")
display_similar_songs (similar_track_uris)
print()
print("GOODBYE!)")
