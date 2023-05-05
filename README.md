## Song Recommender (Spotify)

### App Description
* This simple app takes in a Spotify Song Link (URL) that best describes what the user is into and outputs a playlist of 20 songs to consider. 
* Song candidates were chosen via a simple search in Spotify via its Web API.
* Song features are loaded in a BigQuery table
* Song recommendations are based on content-based filtering. 
* Songs in Bigquery are extracted and each song is given a similarity score via cosine distance.
* The songs most similar to song selected are printed.

### User Behavior:
* Data In: Spotify Song Link (URL)
* Data Out: 10 Simlar Spotify songs

### Next Steps

This is an MVP project that could be improved both in its selection of candidates and UI. However, it's basic structure including selection of data tools is effectively implemented.