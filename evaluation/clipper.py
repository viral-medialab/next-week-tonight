import os
import pymongo
import openai
import youtube_dl
import boto3
from botocore.exceptions import ClientError
import logging
import time

openai.api_key = os.environ.get("OPENAI_API_KEY")
MONGO_CLIENT = os.environ.get("MONGO_CLIENT")
PROJECT_PATH_EVAL = os.environ.get("PROJECT_PATH_EVAL")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME = "liquid-news"

print(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)


def download_video(video_id):
    """
    Download video from youtube using youtube-dl python library given a youtuve video-id
    """
    ydl_opts = {
        "ffmpeg-location": "./",
        "outtmpl": "./videos/%(id)s.%(ext)s",
        "retries": 3,  # number of times to retry the entire download
        "fragment_retries": 10,  # number of times to retry individual fragments
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"https://www.youtube.com/watch?v={video_id}"])


def create_segment_clips():
    """
    Create clips for each segment in the metadata collection and upload to S3,
    then update the metadata collection with the pre-signed URL for each segment
    """
    client = pymongo.MongoClient(MONGO_CLIENT)
    db = client["LiquidEvaluation"]
    metadata_collection = db["metadata"]
    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )

    for doc in metadata_collection.find({}):
        video_id = doc["videoId"]
        video_path = f"{PROJECT_PATH_EVAL}/videos/{video_id}.mp4"
        if not os.path.exists(video_path):
            download_video(video_id)

        for index, segment in enumerate(doc["segments"]):
            start_time_ms = segment["start_timestamp"]
            end_time_ms = segment["end_timestamp"]
            clip_filename = f"{video_id}-segment-{index}.mp4"
            clip_path = f"{PROJECT_PATH_EVAL}/clips/{clip_filename}"
            # Convert start time and end time from milliseconds to HH:MM:SS format
            start_time = time.strftime("%H:%M:%S", time.gmtime(start_time_ms / 1000))
            end_time = time.strftime("%H:%M:%S", time.gmtime(end_time_ms / 1000))

            if not os.path.exists(clip_path):
                # ffmpeg -i input.mp4 -ss 00:00:30 -to 00:00:35 -c copy output.mp4
                os.system(
                    f"ffmpeg -i {PROJECT_PATH_EVAL}/videos/{video_id}.mp4 -ss {start_time} -to {end_time} -c copy {clip_path}"
                )

            try:
                s3.upload_file(
                    clip_path,
                    BUCKET_NAME,
                    clip_filename,
                    ExtraArgs={"ContentType": "video/mp4"},
                )
                url = s3.generate_presigned_url(
                    "get_object",
                    Params={
                        "Bucket": BUCKET_NAME,
                        "Key": clip_filename,
                        "ResponseContentDisposition": "inline",
                    },
                    ExpiresIn=1209600,  # URL is valid for 2 weeks (1,209,600 seconds)
                )
                logging.info("Uploaded the following clip to S3: " + clip_filename)
                # Update the metadata collection with the pre-signed URL for the segment
                metadata_collection.update_one(
                    {
                        "videoId": video_id,
                        "segments.start_timestamp": start_time_ms,
                        "segments.end_timestamp": end_time_ms,
                    },
                    {"$set": {"segments.$.url": url}},
                )
                logging.info(
                    "Updated the metadata collection with the pre-signed URL for the segment : "
                    + clip_filename
                )
                # Delete the clip from the local machine
                os.remove(clip_path)
            except ClientError as e:
                print(f"Failed to upload {clip_filename}: {e}")

        # Delete the video from the local machine
        os.remove(f"{PROJECT_PATH_EVAL}/videos/{video_id}.mp4")


create_segment_clips()
