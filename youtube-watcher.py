# Packages used
import logging
import sys
import requests
from config import config
import json
from pprint import pformat
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.serialization import StringSerializer
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka import SerializingProducer

def fetch_playlist_items_page(google_api_key, youtube_playlist_id, page_token = None):
    # Get response data
    response = requests.get("https://www.googleapis.com/youtube/v3/playlistItems",
                            params = {
                                    "key": google_api_key,
                                    "playlistId": youtube_playlist_id,
                                    "part": "contentDetails",
                                    "page_token": page_token
                                    })
    # Parse JSON payload
    payload = json.loads(response.text)
    logging.debug("GOT %s", payload)

    return payload


def fetch_videos_page(google_api_key, video_id, page_token = None):
    # Get response data
    response = requests.get("https://www.googleapis.com/youtube/v3/videos",
                            params = {
                                        "key": google_api_key,
                                        "id": video_id,
                                        "part": "snippet,statistics",
                                        "page_token": page_token
                                    })0
    
    # Parse JSON payload
    payload = json.loads(response.text)
    logging.debug("GOT %s", payload)

    return payload


def fetch_playlist_items(google_api_key, youtube_playlist_id, page_token = None):
    # Call sub function which gives us the raw payload
    payload = fetch_playlist_items_page(google_api_key, youtube_playlist_id, page_token)

    # Get all items which it gives us - use generator "yield from" which works similar to for loop get items 
    yield from payload["items"]                 

    # If caller wants more, we continue getting next page but recursively
    next_page_token = payload.get("nextPageToken")  # Dict.get() gives a value if there is else None - prevents KeyError 
    if next_page_token is not None:
        yield from fetch_playlist_items(google_api_key, youtube_playlist_id, next_page_token)


def fetch_videos(google_api_key, youtube_playlist_id, page_token = None):
    # Call sub function which gives us the raw payload
    payload = fetch_videos_page(google_api_key, youtube_playlist_id, page_token)

    # Get all items which it gives us - use generator "yield from" which works similar to for loop get items 
    yield from payload["items"]                 

    # If caller wants more, we continue getting next page but recursively
    next_page_token = payload.get("nextPageToken")  # Dict.get() gives a value if there is else None - prevents KeyError 
    if next_page_token is not None:
        yield from fetch_videos(google_api_key, youtube_playlist_id, next_page_token)

def summarize_video(video):

    return {
        "video_id": video["id"],
        "title": video["snippet"]["title"],
        "views": int(video["statistics"].get("viewCount", 0)),       # If no key, return 0
        "likes": int(video["statistics"].get("likeCount", 0)),       # If no key, return 0
        "comments": int(video["statistics"].get("commentCount", 0))  # If no key, return 0
    }

def on_delivery(err, record):
    pass



def main():

    # Start logging and set up variables from config
    logging.info("START")  # Start logging
    google_api_key = config["google_api_key"]
    youtube_playlist_id = config['youtube_playlist_id']
    schema_registry_client = SchemaRegistryClient(config["schema_registry"])
    youtube_videos_value_schema = schema_registry_client.get_latest_version("youtube_videos-value")

    kafka_config = config["kafka"] | {
        "key.serializer": StringSerializer(),
        "value.serializer": AvroSerializer(
                schema_registry_client, 
                youtube_videos_value_schema.schema.schema_str
                ),
    }
    producer = SerializingProducer(kafka_config)

    # Run fetch function
    for video_item in fetch_playlist_items(google_api_key, youtube_playlist_id):
        video_id = video_item["contentDetails"]["videoId"]
        for video in fetch_videos(google_api_key, video_id):
            logging.info("GOT %s", pformat(summarize_video(video))) 

            producer.produce(
                topic = "youtube_videos",  # Same as your Kafka kSQLDB predefined topic
                key = video_id,
                value = {
                    "TITLE": video["snippet"]["title"],
                    "VIEWS": int(video["statistics"].get("viewCount", 0)),
                    "LIKES": int(video["statistics"].get("likeCount", 0)),
                    "COMMENTS": int(video["statistics"].get("commentCount", 0)),
                },
                on_delivery = on_delivery
            )
    producer.flush()

# Activate program
if __name__ == "__main__":
    logging.basicConfig(level = logging.INFO)
    sys.exit(main())

