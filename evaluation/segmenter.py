import os
import pprint
import pymongo
import openai
import re
from transformers import GPT2Tokenizer
import json
import tenacity
import time
from utils import *
import logging

openai.api_key = os.environ.get("OPENAI_API_KEY")
MONGO_CLIENT = os.environ.get("MONGO_CLIENT")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)


def get_segment_timestamps(segments, captions):
    if len(segments) == 1:
        first_topic_shift = segments[0]["shift_phrase"]
        start, start_index = None, None

        for n in range(len(captions)):
            if string_comparer(first_topic_shift, captions[n]["text"]):
                start = captions[n]["start"]
                start_index = n
                break

        segments[0]["start_timestamp"] = start
        segments[0]["start_index"] = start_index
        segments[0]["end_index"] = len(captions) - 1
        segments[0]["end_timestamp"] = captions[-1]["end"]
        segments[0]["segment_transcription"] = get_segment_transcript(
            start_index, len(captions) - 1, captions
        )
        return segments

    for i in range(len(segments) - 1):
        first_topic_shift = segments[i]["shift_phrase"]
        second_topic_shift = segments[i + 1]["shift_phrase"]
        start, start_index, end, end_index = None, None, None, None

        for j in range(len(captions)):
            if string_comparer(first_topic_shift, captions[j]["text"]):
                start = captions[j]["start"]
                start_index = j
                break

        for k in range(len(captions)):
            if string_comparer(second_topic_shift, captions[k]["text"]):
                end = captions[k]["start"]
                end_index = k
                break

        segments[i]["start_timestamp"] = start
        segments[i]["end_timestamp"] = end
        segments[i]["start_index"] = start_index
        segments[i]["end_index"] = end_index
        segments[i]["segment_transcription"] = get_segment_transcript(
            start_index, end_index, captions
        )
        if i == (len(segments) - 2):
            segments[-1]["start_index"] = end_index
            segments[-1]["start_timestamp"] = end
            segments[-1]["end_index"] = len(captions) - 1
            segments[-1]["end_timestamp"] = captions[-1]["end"]
            segments[-1]["segment_transcription"] = get_segment_transcript(
                end_index, len(captions) - 1, captions
            )
    return segments


def get_video_segments(video):
    transcript = video["transcription"]
    captions = video["sentence_captions"]
    segment_primer = 'Identify when there is a major topic change and return the segment in the following JSON format: {"0":  {"title": "" ,  "shift_phrase":""}}. The title is a word/phrase to describe the segment. The shift_phrase must be a SINGLE UNIQUE SENTENCE in which the shift occurs. The shift_phrase MUST be verbatim what is said in the transcript and must appear in the order they come in the text. The segmentation must be broader and have fewer segmentations when possible.'
    prompt = segment_primer + "\n" + transcript
    response = safe_request(prompt, 1200, 0.75, True)
    response_json_text = response["choices"][0]["message"]["content"]
    cleaned_response_json_text = response_json_text[response_json_text.find("{") :]
    response_dict = json.loads(cleaned_response_json_text)
    segments_with_timestamps = []
    segments = list(response_dict.values())
    segments_with_timestamps.extend(get_segment_timestamps(segments, captions))
    return segments_with_timestamps


def segmenter_main():
    # Connect to Mongo Channels Collection
    client = pymongo.MongoClient(MONGO_CLIENT)
    db = client["LiquidEvaluation"]
    metadata_collection = db["metadata"].find(
        {
            "$and": [
                {"segments": {"$exists": False}},
                {"sentence_captions": {"$exists": True, "$ne": []}},
            ]
        }
    )
    query_count = db["metadata"].count_documents(
        {
            "$and": [
                {"segments": {"$exists": False}},
                {"sentence_captions": {"$exists": True, "$ne": []}},
            ]
        }
    )

    # Success Tracking
    succesful_count = 0
    logging.info(
        f"There are {query_count} docs ready to be proccessed for segments. \n"
    )

    for video in metadata_collection:
        try:
            segments_with_timestamps = get_video_segments(video)
            db.get_collection("metadata").update_one(
                {"videoId": video["videoId"]},
                {
                    "$set": {
                        "segments": segments_with_timestamps,
                    }
                },
            )
            logging.info(f"Succefuly added segments for video: {video['videoId']} \n")
            succesful_count += 1
        except Exception as e:
            logging.error(
                f"Failed to added segments for video: {video['videoId']} due to ", e
            )
    logging.info(
        f"{succesful_count} of {query_count} docs were succesfully proccessed for segments. \n"
    )


segmenter_main()
