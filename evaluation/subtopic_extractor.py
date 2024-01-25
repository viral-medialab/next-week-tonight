import datetime
import os
import pymongo
from pymongo.database import Database
import openai
import json
from openai.embeddings_utils import cosine_similarity, get_embedding
from pathlib import Path
from utils import *
import pprint

openai.api_key = os.environ.get("OPENAI_API_KEY")
MONGO_CLIENT = os.environ.get("MONGO_CLIENT")

client = pymongo.MongoClient(MONGO_CLIENT)
db = client["LiquidEvaluation"]
metadata_collection = db["metadata"]
topics_collection = db["topics"]


def get_subtopics(titles: list[str], topics: list[str]) -> dict[str, dict[str, str]]:
    topic_primer = 'Return a list of unique key categories for these titles along with a description of the category. The number of catagories must be significnalty shorter than the number of titles listed below.  Format the response as a completed JSON formated as {"0": {"topic", "", "topic_description": ""}}. The JSON absolutley must be complete and correctly formated so it can be used with the Python json.loads() method. The list should not contain any of the following catagories: \n + {topics}. The titles are the following: \n'
    for title in titles:
        topic_primer += title + "\n"
    response = openai.ChatCompletion.create(
        model="gpt-4-0314",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant who has a strong preference for being ubiased and concise.",
            },
            {
                "role": "system",
                "content": "When asked for a response in JSON you must prioratize sending a response that is complete and correctly formated over sending a response that is correct.",
            },
            {"role": "user", "content": topic_primer},
        ],
        temperature=0,
        top_p=0,
        # max_tokens=4000,
    )
    response_json_topics = response["choices"][0]["message"]["content"]
    response_json_topics_cleaned = response_json_topics[
        response_json_topics.find("{") :
    ]
    topics = json.loads(response_json_topics_cleaned)
    return topics


def get_subtopic_embbedings(
    topics: dict[str, dict[str, str]], db: Database
) -> dict[str, list[float]]:
    topic_embbedings = {
        topic["topic"]: get_embedding(
            f'{topic["topic"]}-{topic["topic_description"]}',
            "text-embedding-ada-002",
        )
        for topic in topics.values()
    }
    return topic_embbedings


def get_subtopic_to_segment(
    topic_embbedings: dict[str, list[float]], titles: list[str]
) -> dict[str, list[str]]:
    topics_to_videos = {}
    for title in titles:
        best_topic = None
        best_cosine = 0
        title_embedding = get_embedding(title, "text-embedding-ada-002")

        for topic in topic_embbedings:
            similarity = cosine_similarity(title_embedding, topic_embbedings[topic])
            if similarity > best_cosine:
                best_topic, best_cosine = topic, similarity

        if best_topic in topics_to_videos:
            topics_to_videos[best_topic].append(title)
        else:
            topics_to_videos[best_topic] = [title]
    return topics_to_videos


def subtopic_extractor_main() -> None:
    client = pymongo.MongoClient(MONGO_CLIENT)
    db = client["LiquidEvaluation"]

    topics = [doc["topic"] for doc in db["topics"].find()]
    for topic in topics:
        segment_titles = []
        for doc in db["metadata"].find({"segments": {"$exists": True}, "topic": topic}):
            for segment in doc["segments"]:
                segment_titles.append(segment["title"])

        subtopics = get_subtopics(segment_titles, topics)
        subtopic_embeddiings = get_subtopic_embbedings(subtopics, db)
        subtopic_to_segment = get_subtopic_to_segment(
            subtopic_embeddiings, segment_titles
        )

        segment_titles_to_topic = {}

        for subtopic in subtopic_to_segment:
            for segment_title in subtopic_to_segment[subtopic]:
                segment_titles_to_topic[segment_title] = subtopic

        for doc in db["metadata"].find({"segments": {"$exists": True}, "topic": topic}):
            index = 0
            for segment in doc["segments"]:
                try:
                    db["metadata"].update_one(
                        {"_id": doc["_id"]},
                        {
                            "$set": {
                                f"segments.{index}.subtopic": segment_titles_to_topic[
                                    segment["title"]
                                ]
                            }
                        },
                    )
                except Exception as e:
                    logging.error(
                        f"Failed to uploaded updated metadata with topic for segment : {segment['_id']} ",
                        e,
                    )
                index += 1


subtopic_extractor_main()
