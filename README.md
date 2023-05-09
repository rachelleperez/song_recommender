# Creating a Mood-based Workout Playlist (Spotify)

### App Description
* This simple app takes in a Spotify Song Link (URL) that best describes what mood the user is into and outputs a playlist of 20 workout songs
* There are ~5K song candidates extracted from Spotify's API from all playlists listed as [Popular Workout Playlists](https://open.spotify.com/genre/section0JQ5IMCbQBLsb9HwPKg2Us) 
* Song features for candidates are loaded in a BigQuery table to be manually refreshed periodically
* Song recommendations are based on content-based filtering. 
* Songs in Bigquery are extracted and each song is given a similarity score to input song via cosine distance.
* The songs most similar to song selected are printed.

### Data Warehouse
The data for all song candidates is generatated via the python script `source_tracks.py` and saved in a BigQuery table.

### User Behavior:
* Data In: Spotify Song Link (URL)
* Data Out: 20 Similar Spotify songs

### Tech Tools
* Spotify API, via Spotipy Python library
* BigQuery, via google.cloud Python library and BigQuery console
* SKLearn's Cosine Similarity, via sklearn.metrics.pairwise library
* Additional Python Libraries: Pandas, Re (Regex), OS

### Next Steps

This is an MVP project. It's basic structure including selection of data tools is effectively implemented. Below are some possible improvements:
* Create a UI
* Dynamically generate workout playlist uris via web parsing
* Partition BQ table by date to save past versions of song candidates
* Move to cloud