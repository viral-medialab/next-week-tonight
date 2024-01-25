from sqlite3 import Date
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import pymongo
from datetime import datetime, timedelta
import os
from utils import *
import logging
from datetime import datetime, timedelta
import pprint
from transcription_utils import transcribe_from_link 

# configure the root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
MONGO_CLIENT = os.environ.get("MONGO_CLIENT")
PLAYLIST_ID = 'PLvZ_pPHZ6kBz_Y5XG5XXblPype55nRAIa'

def get_videos_metadata(playlist_id, max_results):
    """
    Makes a YouTube Data API call to retrieve video information for a given playlist

    Args:
        playlist_id (str): The ID of the YouTube playlist to retrieve video information for
        max_results (int): The maximum number of videos to retrieve

    Returns:
        dict: The YouTube API response JSON/dict for the retrieved videos
    """

    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

        playlist_item_request = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=max_results,
        )

        playlist_item_response = playlist_item_request.execute()
        video_ids = []

        for item in playlist_item_response["items"]:
            video_ids.append(item["snippet"]["resourceId"]["videoId"])

        videos_request = youtube.videos().list(
            part="snippet",
            id=",".join(video_ids),
        )

        return videos_request.execute()
    except Exception as e:
        logging.error(
            f"Failed to properly retrieve metadata for videos from playlist {playlist_id}",
            e,
        )
        return None

def update_metadata(youtube_response):
    id = youtube_response["id"]
    snippet = youtube_response["snippet"]
    snippet['videoId'] = id

    # Only delete keys in the snippet dictionary if they exist
    if 'localized' in snippet:
        del snippet['localized']
    if 'liveBroadcastContent' in snippet:
        del snippet['liveBroadcastContent']
    if 'categoryId' in snippet:
        del snippet['categoryId']
    if 'defaultAudioLanguage' in snippet:
        del snippet['defaultAudioLanguage']

    video_url = f"https://www.youtube.com/watch?v={id}"
    try:
        sentences, transcription = transcribe_from_link(video_url)
        snippet['transcription'] = transcription['text']
        snippet['sentence_captions'] = [{'text':s['text'], 'start':s['start'], 'end':s['end']} for s in sentences['sentences']]
    except Exception as e:
        logging.info(f"Failed to transcribe video {video_url}", e)
        return None
    return snippet

def write_metadata_to_db(metadata, db, collection_name="metadata"):
    """
    Updates YouTube videos 'snippet' with captions and transcriptions
    """
    collection = db.get_collection(collection_name)
    # Upload if video is not a duplicate
    if not collection.find_one({"videoId": metadata["videoId"]}):
        try:
            collection.insert_one(metadata)
            logging.info(f'Succesfully uploaded metadata for video : {metadata["videoId"]} \n')
        except Exception as e:
            logging.error(
                f'Failed to upload metadata for video : {metadata["videoId"]}', e
            )

def youtube_importer_main():
    # Connect to Mongo Database
    client = pymongo.MongoClient(MONGO_CLIENT)
    db = client["LiquidEvaluation"]
    collection = db.get_collection('metadata')
    video_metadata = get_videos_metadata(PLAYLIST_ID, 20)
    for video in video_metadata['items']:
        if not collection.find_one({"videoId": video["id"]}):
            updated_metadata = update_metadata(video)
            write_metadata_to_db(updated_metadata, db)
        else:
            logging.info(f'Video already proccesed: {video["id"]}')

youtube_importer_main()