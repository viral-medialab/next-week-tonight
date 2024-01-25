import pandas as pd
from os.path import exists
from random import randint
import fnmatch
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import matplotlib
from sklearn.cluster import KMeans
import numpy as np
from dotenv import load_dotenv

"""
Clustering Module

The following methods are used to cluster the tokens and then determine a topic for each cluster.
"""


def get_clusterings(liquid_videos_data, id, n_clusters):
    keys = list(liquid_videos_data[id]["caption_token_data"].keys())
    keys.sort()
    embeddings = [
        liquid_videos_data[id]["caption_token_data"][key]["embedding"] for key in keys
    ]
    kmeans = KMeans(n_clusters=n_clusters, init="k-means++", random_state=42)
    kmeans.fit(embeddings)
    labels = kmeans.labels_
    for i in range(len(labels)):
        liquid_videos_data[id]["caption_token_data"][keys[i]]["cluster"] = labels[i]


def get_cluster_topic(liquid_videos_data, id):
    cluster_data = {}
    for key in liquid_videos_data[id]["caption_token_data"]:
        if liquid_videos_data[id]["caption_token_data"][key]["cluster"] in cluster_data:
            cluster_data[liquid_videos_data[id]["caption_token_data"][key]["cluster"]][
                "summary"
            ] += liquid_videos_data[id]["caption_token_data"][key]["text"]
        else:
            cluster_data[
                liquid_videos_data[id]["caption_token_data"][key]["cluster"]
            ] = {"summary": liquid_videos_data[id]["caption_token_data"][key]["text"]}
    for cluster in cluster_data:
        summary = cluster_data[cluster]["summary"]
        prompt = f"key idea of this paragraph in three words. \n {summary}"

        load_dotenv()
        openai.api_key = os.getenv("OPEN_AI_API_KEY")

        key_topic = openai.Completion.create(
            engine="text-davinci-002",
            prompt=prompt,
            temperature=0.7,
            max_tokens=32,
            top_p=0.9,
        )
        key_topic = key_topic["choices"][0]["text"]
        key_topic = key_topic.replace(" ", "_")
        summary = cluster_data[cluster]["topic"] = key_topic
    return cluster_data
