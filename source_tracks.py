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

# Define the Spotify playlist URL

playlist_urls = [ #TODO: possible improvement, return all playlist uris from Populat Workout Playlist in Spotify: https://open.spotify.com/genre/section0JQ5IMCbQBLsb9HwPKg2Us
    'https://open.spotify.com/playlist/37i9dQZF1DWU13kKnk03AP', #Daily lift
    'https://open.spotify.com/playlist/37i9dQZF1DX5gQonLbZD9s', #Pumped Pop
    'https://open.spotify.com/playlist/37i9dQZF1DWSJHnPb1f0X3', #Cardio
    'https://open.spotify.com/playlist/37i9dQZF1DX5n5gZBZb0AT', #gymcore
    'https://open.spotify.com/playlist/37i9dQZF1DX76Wlfdnj7AP', # Beast Mode
    'https://open.spotify.com/playlist/37i9dQZF1DXdMm3yYbD7IO', #90s Workout
    'https://open.spotify.com/playlist/37i9dQZF1DX8CwbNGNKurt', #Throwback Workout
    'https://open.spotify.com/playlist/37i9dQZF1DWTDafB3skWPN', #Feelin Accomplished
    'https://open.spotify.com/playlist/37i9dQZF1DX4esiqDZ1sjJ', #Jock Jams
    'https://open.spotify.com/playlist/37i9dQZF1DX70RN3TfWWJh', #Workout 
    'https://open.spotify.com/playlist/37i9dQZF1DX35oM5SPECmN', #Run Wild
    'https://open.spotify.com/playlist/37i9dQZF1DX4eRPd9frC1m', #Hype
    'https://open.spotify.com/playlist/37i9dQZF1DX32NsLKyzScr', #Power Hour
    'https://open.spotify.com/playlist/37i9dQZF1DX0HRj9P7NxeE', #Workout Twerkout
    'https://open.spotify.com/playlist/37i9dQZF1DX9ZKyQHcEFXZ', #Perreo Workout
    'https://open.spotify.com/playlist/37i9dQZF1DX76t638V6CA8', #Rap Workout
    'https://open.spotify.com/playlist/37i9dQZF1DWYNSm3Z3MxiM', #Classic Rock Workout
    'https://open.spotify.com/playlist/37i9dQZF1DX7DBYY9PSkix', #Country Cardio
    'https://open.spotify.com/playlist/37i9dQZF1DX9oh43oAzkyx', #Beast Mode Hip Hop
    'https://open.spotify.com/playlist/37i9dQZF1DXe6bgV3TmZOL', #Adrenaline Workout
    'https://open.spotify.com/playlist/37i9dQZF1DWWPcvnOpPG3x', #Run This Town
    'https://open.spotify.com/playlist/37i9dQZF1DWUVpAXiEPK8P', #Power Workout
    'https://open.spotify.com/playlist/37i9dQZF1DX5rpMp3b5vWv', #Laced Up
    'https://open.spotify.com/playlist/37i9dQZF1DX8dTWjpijlub', #Trophy Room
    'https://open.spotify.com/playlist/37i9dQZF1DWZY6U3N4Hq7n', #80s Workout
    'https://open.spotify.com/playlist/37i9dQZF1DX3ZeFHRhhi7Y', #Wor K Out
    'https://open.spotify.com/playlist/37i9dQZF1DWYK2yx0OW9Kj', #Workout Latino
    'https://open.spotify.com/playlist/37i9dQZF1DX2SzDYPXnP1a', #Beast Mode Country
    'https://open.spotify.com/playlist/37i9dQZF1DXdURFimg6Blm', #Beast Mode Dance
    'https://open.spotify.com/playlist/37i9dQZF1DWZUTt0fNaCPB', #Running to Rock
    'https://open.spotify.com/playlist/37i9dQZF1DX4osfY3zybD2', #Retro Running
    'https://open.spotify.com/playlist/37i9dQZF1DX35X4JNyBWtb', #Energy Booster: Dance
    'https://open.spotify.com/playlist/37i9dQZF1DXdc2CX1rMGAc', #Beast Mode Latin
    'https://open.spotify.com/playlist/37i9dQZF1DWY3PJWG3ogmJ', #Extreme Metal Workout
    'https://open.spotify.com/playlist/37i9dQZF1DWSnRSDTCsoPk', #Energy Booster: KPop
    'https://open.spotify.com/playlist/37i9dQZF1DWZq91oLsHZvy', #Indie x Running
    'https://open.spotify.com/playlist/37i9dQZF1DX36TRAnIL92N', #Techno Workout
    'https://open.spotify.com/playlist/37i9dQZF1DXadOVCgGhS7j', #Fun Run
    'https://open.spotify.com/playlist/37i9dQZF1DX9IamZDvvtyh', #Training Montage
    'https://open.spotify.com/playlist/37i9dQZF1DX0hWmn8d5pRe', #Born to Run 150 BPM
    'https://open.spotify.com/playlist/37i9dQZF1DWXmQEAjlxGhi', #Latin Cardio
    'https://open.spotify.com/playlist/37i9dQZF1DXbFRZSqP41al', #Rock  Your Body
    'https://open.spotify.com/playlist/37i9dQZF1DX2BCKQiTaN5o', #Michelle Obama's Workout
    'https://open.spotify.com/playlist/37i9dQZF1DX0wiundViT27', #Rock Me Up
    'https://open.spotify.com/playlist/37i9dQZF1DX45xYefy6tIi', #The Rockstars of Racing ESPN
    'https://open.spotify.com/playlist/37i9dQZF1DX5OrO2Jxuvdn', #Country Workout
    'https://open.spotify.com/playlist/37i9dQZF1DWYLzS1pepUTD', #WWE Make an Entrance
    'https://open.spotify.com/playlist/37i9dQZF1DX9BXb6GsGCLl', #Powerwalk!
    'https://open.spotify.com/playlist/37i9dQZF1DWV3VLITCZusq', #Pop Run Walk
    'https://open.spotify.com/playlist/37i9dQZF1DXdVyc8LtLi96', #Sunrise Yoga
    'https://open.spotify.com/playlist/37i9dQZF1DX7cmFV9rWM0u', #Zumba Beats
    'https://open.spotify.com/playlist/37i9dQZF1DX0BZrbvIqxCd', #Punk Rock Workout
    'https://open.spotify.com/playlist/37i9dQZF1DWZqUHC2tviPw', #Trap Workout Beats
    'https://open.spotify.com/playlist/37i9dQZF1DWXUtxBFupUW9', #Body and Soul
    'https://open.spotify.com/playlist/37i9dQZF1DXcdGxYPVUKPf', #Dwayne Johnson Iron Paradise Tour
    'https://open.spotify.com/playlist/37i9dQZF1DX8E1Op3UZWf0', #Morning Run
    'https://open.spotify.com/playlist/37i9dQZF1DWTofcvJ2Dvma', #Vinyasa Flow
    'https://open.spotify.com/playlist/37i9dQZF1DXcCEH5EfTtzp', #Lactic Acid Run
    'https://open.spotify.com/playlist/37i9dQZF1DWZvpVE2NxPV2', #Hatha Yoga
    'https://open.spotify.com/playlist/37i9dQZF1DX3PKEfo9uS5R', #Pilates Lounge    
    'https://open.spotify.com/playlist/37i9dQZF1DX4FJyIpen2Yf', #Hip Hop Yoga
    'https://open.spotify.com/playlist/37i9dQZF1DX6scD2GXri65', #Hardstyle Gym
    'https://open.spotify.com/playlist/37i9dQZF1DWUI1rlvkdQnb', #Cool Down
    'https://open.spotify.com/playlist/37i9dQZF1DWYMTWCt2y4ZJ', #Sun Salutation
    'https://open.spotify.com/playlist/37i9dQZF1DX7R7Bjxm48PR', #Piano Yoga
    'https://open.spotify.com/playlist/37i9dQZF1DX8kehMXAAgpt', #The Real Beast Mode
    'https://open.spotify.com/playlist/37i9dQZF1DXcTpoGQmyr2B', #Acoustic Pilates
    'https://open.spotify.com/playlist/37i9dQZF1DX9qyeQZ6gM81', #Polly wants to sing-along
    'https://open.spotify.com/playlist/37i9dQZF1DX8SaiEt4OVJw', #Locker Room

]

# Extract track and features

all_track_features ={}  # dict of track : Features. Dict ensures no repeated uris

p_counter = 0
for playlist_url in playlist_urls:
    print("PLAYLIST COUNTER: ", p_counter)
    # Get the playlist ID from the URL
    playlist_id = playlist_url.split('/')[-1]


    # Retrieve the track URIs from the playlist
    results = sp.playlist_tracks(playlist_id)
    tracks = results['items']
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])

  # Extract the uris and features 
  
    t_counter = 0
    for track in tracks:
        print("TRACK COUNTER: ", t_counter)
        uri = track['track']['uri']
        if uri is None: #nothing returned
            t_counter += 1
            continue
        features = sp.audio_features(uri)[0]
        if features is None: #nothing returned
            t_counter += 1
            continue
        # track_metadata = sp.track(uri) # Metadata to be retrieved only to surface data to user
        # if track_metadata is None: #nothing returned
        #     t_counter += 1
        #     continue
        # if track_metadata['name'] is None: 
        #     t_counter += 1
        #     continue
        # features['name'] = track_metadata['name'] #update
        # if track_metadata['artists'][0]['name'] is None:
        #     t_counter += 1
        #     continue
        # features['artist'] = track_metadata['artists'][0]['name']
        all_track_features[uri] = features     
        t_counter += 1

    p_counter += 1

print("EXTRACTED FEATURES")    

# PUT IN BQ TABLE

# settings
bigquery_client = bigquery.Client()
table_ref = bigquery_client.dataset(dataset).table(bq_table)
table = bigquery_client.get_table(table_ref)

# Prepares rows
rows_to_insert = []
for value in all_track_features.values():
    track_features = value
    rows_to_insert.append((track_features['uri'], track_features['danceability'], track_features['energy'], track_features['key'], track_features['loudness'], track_features['mode'], track_features['speechiness'], track_features['acousticness'], track_features['instrumentalness'], track_features['liveness'], track_features['valence'], track_features['tempo'], track_features['duration_ms'], track_features['time_signature']))
rows_df = pd.DataFrame(rows_to_insert, columns=['uri', 'danceability', 'energy','key','loudness','mode','speechiness','acousticness','instrumentalness','liveness','valence','tempo','duration_ms','time_signature'])

#load into BQ (update config so that table is overwritten and not just appended)
job_config = bigquery.LoadJobConfig()
job_config.write_disposition = 'WRITE_TRUNCATE'
job_config.source_format = bigquery.SourceFormat.CSV
job_config.autodetect = True
job_config.ignore_unknown_values = True

job = bigquery_client.load_table_from_dataframe(rows_df, f'{project}.{dataset}.{bq_table}', job_config=job_config)
job.result()  # Wait for the job to complete.

print("CANDIDATES SAVED IN BQ")    