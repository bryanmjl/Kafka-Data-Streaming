# Kafka Data Streaming
This is a project which makes use of ```confluent_kafka``` to stream real-time data from a YouTube playlist to my own Telegram account. Specifically, this is the breakdown of the data pipeline:
1. Check up some playlist to see which videos are on a YouTube playlist 
2. Look up the videos to check their statistics such as likes, comments, etc
3. Stream these video statistics using Confluent Apache Kafka and send downstream to my own telegram account via a Telegram bot
    - Bot alerts me each time there is a change in view, likes, etc
4. This can be potentially used for any marketing company which needs to track views and likes of their client's videos into a form of dashboard for them

# Documentation
1. ```config.py``` - this file is hidden from Github and you would need to set up your own configuration details
    - Create a google API key at: https://developers.google.com/youtube/v3/getting-started
    - Select your own ```youtube_playlist_id```
    - Kafka bootstrap servers found at "Confluence Cluster settings" -> "Bootstrap Server"
    - sasl username - Cluster API key
    - sasl.password - Cluster API secret (secret referring to password)
    - schema_registry is for defining your schema and what columns to hold (see query #1 under ```queries.sql```)
        - url - schema registry API endpoint
        - basic.auth.user.info - [API credentials key: API credentials credential] (This is for your schema registry) 
3. An example of how raw YouTube data API for playlist items looks like:
    - ``
    {'kind': 'youtube#playlistItemListResponse', 'etag': 'eQzUlK3ml3m6C9ar17Z_9S8datg', 'nextPageToken': 'EAAaBlBUOkNBVQ', 'items': [{'kind': 'youtube#playlistItem', 'etag': 'ZQ2zbEB330tpTZ79CUVXcX1sXWA', 'id': 'UExyMy1iRWkxTjRraEtabTJ1NlE4cE9MTy1XTlpyS0RIbi41QTY1Q0UxMTVCODczNThE', 'contentDetails': {'videoId': '3AZFMT0LNAU', 'videoPublishedAt': '2022-10-19T10:57:14Z'}}
    ``
4. Set up your own Kafka instance at https://www.confluent.io/confluent-cloud/?utm_medium=sem&utm_source=google&utm_campaign=ch.sem_br.brand_tp.prs_tgt.confluent-brand_mt.xct_rgn.apac_lng.eng_dv.all_con.confluent-cloud&utm_term=confluent%20cloud&creative=&device=c&placement=&gclid=CjwKCAjwrJ-hBhB7EiwAuyBVXQBHHczoRUUnX0FuXpfe8kQ7nNs7gFWSdMNdM-9xSzNoHZC0wmCgeBoCqNQQAvD_BwE
    - Create your own environment
    - Within that environment, create a cluster
    - Set up your own schema registry (if needed)
    - Set up your own ksqlDB (database cluster) and run query #1 in 
    - Define your avro schema queries within your own ksqlDB and define it as a topic on its own
5. Creating Streams vs Creating tables in KSQL
    - Streams as time series of events whereas Tables as current state of a given key 
    - More info at https://developer.confluent.io/learn-kafka/ksqldb/streams-and-tables/#:~:text=Streams%20are%20unbounded%20series%20of,want%20to%20use%20the%20data.
6. Configuring telegram bot to send information from Confluent Kafka to Telegram
    - Create telegram connector via connectors -> ```http sink``` on Confluent connectors
    - Create a telegram bot by going to your telegram account -> "BotFather"
    - Go to your new bot and type "/start" and some random message
    - Find out your telegram bot chat id by running the following command in ```git bash```
        - ```curl https://api.telegram.org/bot(YOUR BOT NAME)/getUpdates```
    - ```Create stream telegram outbox``` for configuring all video statistics differences into telegram bot eventually (see ```queries.sql```)

# Contents of project
1. ```youtube-watcher.py``` 
    - Main file for tracking changes from a Youtube video
    - ```fetch_playlist_items_page``` is for getting all playlist items in raw JSON payload
    - ```fetch_playlist_items``` gets item details of each videos in each page 
    - ```fetch_videos_page``` querys raw information about a video
    - ```fetch_videos``` querys video information
        - We first use ```fetch_playlist_items_page``` to get all information about a playlist
        - We then get the video_id from  ```fetch_playlist_items```
        - Feed the video_id into ```fetch_videos_page``` to get raw JSON payload of a video content
        - ```fetch_videos``` allow us to get the actual video information from there
    - ```summarize_video``` for formatting nicely list of items we want in a dictionary format from ```fetch_videos```
    - ```main```() - executes the program and uploads new data onto KsqlDB
2. ```queries.sql``` - useful kSQL queries to use to create relevant schemas and tables in KSQL Confluent UI web page
    - ```youtube_videos``` as a stream for querying all youtube videos in a specified playlist
    - ```youtube_changes``` as a table for querying changes in video statistics over a period of time
    - ```telegram_outbox``` as a stream for sending streamed data into telegram bot created 


# Reference
1. Youtube kafka guide: 
    - https://www.youtube.com/watch?v=jItIQ-UvFI4
