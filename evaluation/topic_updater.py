import datetime
import os
import pymongo
from pymongo.database import Database
import openai
import json
from openai.embeddings_utils import cosine_similarity, get_embedding
from pathlib import Path
from utils import *
import numpy as np
from sklearn import manifold
from matplotlib import pyplot as plt
from scipy.optimize import linear_sum_assignment
from numpy import dot
from numpy.linalg import norm
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from bson.objectid import ObjectId
import pprint

openai.api_key = os.environ.get("OPENAI_API_KEY")
MONGO_CLIENT = os.environ.get("MONGO_CLIENT")

client = pymongo.MongoClient(MONGO_CLIENT)
db = client["LiquidEvaluation"]
metadata_collection = db["metadata"]
topics_collection = db["topics"]


# Define a function to calculate cosine similarity between two vectors
def cosine_similarity(a, b):
    return dot(a, b) / (norm(a) * norm(b))


def get_segment_embedding():
    client = pymongo.MongoClient(MONGO_CLIENT)
    db = client["LiquidEvaluation"]

    filter = {"segments": {"$elemMatch": {"embedding": {"$exists": False}}}}

    for doc in db["metadata"].find(filter):
        segment_index = 0
        for segment in doc["segments"]:
            try:
                db["metadata"].update_one(
                    {"_id": doc["_id"]},
                    {
                        "$set": {
                            f"segments.{segment_index}.embedding": get_embedding(
                                f'{segment["title"]} : {segment["segment_transcription"]}',
                                "text-embedding-ada-002",
                            )
                        }
                    },
                )
            except Exception as e:
                logging.error(
                    f"Failed to uploaded updated metadata with topic for segment : {segment['_id']} ",
                    e,
                )
            segment_index += 1


def sort_clips_via_avg_embedding(subtopic):
    # Compute the average segment embedding for the clip array
    embeddings = []
    for clip in subtopic["clips"]:
        if "embedding" in clip:
            embeddings.append(clip["embedding"])
    if len(embeddings) > 0:
        avg_embedding = np.mean(embeddings, axis=0)
    else:
        avg_embedding = None

    # Compute the cosine similarity between the average embedding and each clip's segment embedding
    for clip in subtopic["clips"]:
        if "embedding" in clip:
            if avg_embedding is not None:
                clip_embedding = clip["embedding"]
            else:
                clip_embedding = avg_embedding
            clip["cosine_similarity"] = cosine_similarity(
                [avg_embedding.reshape((-1, 1))], np.array([clip_embedding])
            )[0][0]

            # Sort the clips based on cosine similarity to the average embedding
            subtopic["clips"].sort(
                key=lambda x: x.get("cosine_similarity", [0])[0], reverse=True
            )
            for clip in subtopic["clips"]:
                if "cosine_similarity" in clip:
                    del clip["cosine_similarity"]
                if "embedding" in clip:
                    del clip["embedding"]
    return subtopic


def set_subtopics():
    client = pymongo.MongoClient(MONGO_CLIENT)
    db = client["LiquidEvaluation"]
    topics = [doc["topic"] for doc in db["topics"].find()]
    for topic in topics:
        subtopics = {}
        for doc in db["metadata"].find(
            {"segments": {"$exists": True}, "topic": {"$eq": topic}}
        ):
            for segment in doc["segments"]:
                if segment["subtopic"] not in subtopics:
                    subtopics[segment["subtopic"]] = {"clips": []}

        for doc in db["metadata"].find(
            {"segments": {"$exists": True}, "topic": {"$eq": topic}}
        ):
            for segment in doc["segments"]:
                clip = {}
                clip["videoId"] = doc["videoId"]
                clip["channelTitle"] = doc["channelTitle"]
                clip["title"] = segment["title"]
                clip["start_timestamp"] = segment["start_timestamp"]
                clip["end_timestamp"] = segment["end_timestamp"]
                clip["segment_transcription"] = segment["segment_transcription"]
                clip["thumbnail"] = doc["thumbnails"]["default"]["url"]
                clip["embedding"] = segment["embedding"]
                subtopics[segment["subtopic"]]["clips"].append(clip)

        for subtopic in subtopics:
            modifed_subtopic = sort_clips_via_avg_embedding(subtopics[subtopic])
            subtopics[subtopic] = modifed_subtopic

        try:
            db["topics"].update_one(
                {"topic": {"$eq": topic}}, {"$set": {"subtopics": subtopics}}
            )
        except Exception as e:
            logging.error(
                f"Failed to uploaded updated topics with subtopics : {topic} ",
                e,
            )


def set_clip_bullets():
    client = pymongo.MongoClient(MONGO_CLIENT)
    db = client["LiquidEvaluation"]
    for topicDoc in db["topics"].find():
        print(f"current topics:  {topicDoc['topic']}")
        topicDoc_Id = topicDoc["_id"]
        subtopicObj = topicDoc["subtopics"]
        for subtopic in subtopicObj:
            print(f"current subtopic:  {subtopic}")
            print(
                f"There are this many clips for this subtopic: {len(subtopicObj[subtopic]['clips'])}"
            )
            current_clip = 0
            for clip in subtopicObj[subtopic]["clips"]:
                if "bullets" in clip:
                    # Skip clips that already have bullets
                    print(
                        f"Skipping clip: {current_clip} because it already has bullets"
                    )
                    continue
                print(f"We are on this clip: {current_clip}")
                current_clip += 1
                try:
                    clip_transcription = clip["segment_transcription"]
                    bullets = bullet_request(clip_transcription)
                    response_json_text = bullets["choices"][0]["message"]["content"]
                    cleaned_response_json_text = response_json_text[
                        response_json_text.find("{") :
                    ]
                    response_dict = json.loads(cleaned_response_json_text)
                    bullet_list = list(response_dict.values())
                    clip["bullets"] = bullet_list
                    try:
                        print(f"Added bullets to clip in topic: {topicDoc['topic']}")
                        db["topics"].update_one(
                            {"_id": topicDoc_Id}, {"$set": {"subtopics": subtopicObj}}
                        )
                    except Exception as e:
                        logging.error(
                            f"Failed to uploaded updated topics with subtopics : {topicDoc['topic']} ",
                            e,
                        )
                except Exception as e:
                    logging.error(
                        f"Failed to get bullets for clip: {clip['title']} ",
                        e,
                    )
                    continue


get_segment_embedding()
set_subtopics()
set_clip_bullets()
