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

###### TESTING LIBRARIES

# example - prints name of 10 weezer songs
# results = sp.search(q='weezer', limit=20)
# for idx, track in enumerate(results['tracks']['items']):
#     print(idx, track['name'])

# testing - pandas works
# s = pd.Series([1, 3, 5, 6, 8])
# print(s)    

# testing - sklearn works?
# import numpy as np
# X = np.array([1,2])
# Y = np.array([2,2])
# Z = np.array([2,4])

# cos_sim = cosine_similarity([X], [Y,Z])
# print(cos_sim)

# cos_sim = cosine_similarity([X, Y, Z])
# print(cos_sim)
# print()


###### BQ SETTINGS

# PROJECT_ID = 'song-recommender-385801'
# DATASET_ID = 'song-recommender-385801.api_in'
# TABLE_ID  ='song-recommender-385801.api_in.test'
project = 'song-recommender-385801'
dataset = 'api_in'
bq_table = 'track_features'

import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '../song-recommender-385801-353a937bd051.json'

# Extracts the track URI from a Spotify share URL
def get_track_uri(url):
    match = re.search(r'track\/(\w+)', url)
    if match:
        track_id = match.group(1)
        track_uri = f"spotify:track:{track_id}"
        return track_uri
    else:
        raise ValueError("Invalid Spotify share URL")


# Authenticates with Spotify API and get track features for a given track
def get_track_features(track_uri, sp):
    track_id = track_uri.split(':')[-1]
    track_features = sp.audio_features(tracks=[track_id])[0]
     # name, artist
    track_metadata = sp.track(track_uri)
    track_features['name'] = track_metadata['name'] 
    track_features['artist'] = track_metadata['artists'][0]['name']
    return track_features

# Gets a list of similar tracks from Spotify based on a given track URI. Short-lists of 50 candidates
def get_similar_tracks(track_uri, sp):
  
    search_results_features = []

    # add input track features
    input_track_features = get_track_features(track_uri, sp)
    search_results_features.append(input_track_features)

    # Define search query for similar tracks (TODO: improve criteria)
    #search_query = f'artist:{input_track_features["artist"]} track:{input_track_features["name"]}' # example: "Adele I Drink Wine"
    search_query = f'{input_track_features["artist"]} {input_track_features["name"]}' # example: "Adele I Drink Wine"
    search_results = sp.search(q=search_query, type='track', limit=50) # 50: LIMIT
    
    # Get track features for search results
    for track in search_results['tracks']['items']:
        track_features = get_track_features(track['uri'], sp)
        search_results_features.append(track_features)
    
    return search_results_features

# Inserts track features into BigQuery table
def insert_track_features(track_features_list):
    
    # settings
    bigquery_client = bigquery.Client()
    table_ref = bigquery_client.dataset(dataset).table(bq_table)
    table = bigquery_client.get_table(table_ref)

    # Prepares rows
    rows_to_insert = []
    for i in range(len(track_features_list)):
      track_features = track_features_list[i]
      rows_to_insert.append((track_features['uri'], track_features['name'], track_features['artist'], track_features['danceability'], track_features['energy'], track_features['key'], track_features['loudness'], track_features['mode'], track_features['speechiness'], track_features['acousticness'], track_features['instrumentalness'], track_features['liveness'], track_features['valence'], track_features['tempo'], track_features['duration_ms'], track_features['time_signature']))
    rows_df = pd.DataFrame(rows_to_insert, columns=['uri', 'name', 'artist', 'danceability', 'energy','key','loudness','mode','speechiness','acousticness','instrumentalness','liveness','valence','tempo','duration_ms','time_signature'])
    
    #load into BQ (update config so that table is overwritten and not just appended)
    job_config = bigquery.LoadJobConfig()
    job_config.write_disposition = 'WRITE_TRUNCATE'
    job_config.source_format = bigquery.SourceFormat.CSV
    job_config.autodetect = True
    job_config.ignore_unknown_values = True

    job = bigquery_client.load_table_from_dataframe(rows_df, f'{project}.{dataset}.{bq_table}', job_config=job_config)
    job.result()  # Wait for the job to complete.


# Gets similar tracks from BigQuery table using content-based filtering
def get_similar_tracks_from_bq(track_uri):
    
    client = bigquery.Client()

    # Retrieve previously inserted track features
    query = f"""
        SELECT *
        FROM `{project}.{dataset}.{bq_table}`
    """

    df = client.query(query).to_dataframe()

    # Calculates similarity
    input_track_features = df[df['uri'] == track_uri].iloc[0][3:] #starting from 4th column
    df['similarity'] = df[df['uri'] != track_uri].iloc[:, 3:].apply(lambda x: cosine_similarity([input_track_features, x])[0][1], axis=1)
    similar_tracks = df.sort_values(by='similarity', ascending=False).head(20)

    # Creates lists to index through them in print
    track_names = similar_tracks['name'].tolist()
    track_artists = similar_tracks['artist'].tolist()
    track_uris = similar_tracks['uri'].tolist()

    # Prints playlist tracks
    for i in range(len(track_names)):
        print(f"Track: {i+1}: {track_names[i]} by {track_artists[i]} ({track_uris[i]})")

    return track_names, track_artists, track_uris


actual_track_uri = 'spotify:track:6v0UJD4a2FtleHeSYVX02A?si=3d28829c47ba4fb7'  
track_url = 'https://open.spotify.com/track/6v0UJD4a2FtleHeSYVX02A?si=0095b201771d4357'


print("WELCOME TO THIS APP! ENTER A SPOTIFY SONG LINK AND GET A PLAYLIST OF SIMILAR SONGS")
print()
print('Enter a Spotify Song Link (URL):')
track_url = input().strip() # remove leading and trailing spaces
track_uri = get_track_uri(track_url)
track_features = get_similar_tracks(track_uri, sp) #for all tracks
#print(track_features)
insert_track_features(track_features) #into BQ
print("Here is your playlist")
get_similar_tracks_from_bq(track_uri)
print("HOPE YOU ENJOYED YOUR PLAYLIST! GOODBYE ;)")