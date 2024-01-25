import os
import numpy as np
from datetime import datetime
from os.path import exists
import openai
from tenacity import retry, wait_random_exponential, stop_after_attempt
from dotenv import load_dotenv

load_dotenv()

"""
Embedding Module

The following methods are used to get the embeddings for each token using the GPT-3 text-similarity-davinci-001 model. 
"""


openai.api_key = os.getenv("OPEN_AI_API_KEY")


@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def get_embedding(text: str, engine="text-similarity-davinci-001"):
    return openai.Embedding.create(input=[text], engine=engine)["data"][0]["embedding"]


def get_token_embedding(
    liquid_videos_data, id, num_sentences_per_token, directory_path
):
    embeddings = []
    for key in liquid_videos_data[id]["caption_token_data"]:
        embedding = get_embedding(
            liquid_videos_data[id]["caption_token_data"][key]["text"]
        )
        liquid_videos_data[id]["caption_token_data"][key]["embedding"] = embedding
    os.makedirs(
        os.path.dirname(
            f"{directory_path}/embedding_tokensize_{num_sentences_per_token}/{id}_embedding.text"
        ),
        exist_ok=True,
    )
    np.savetxt(
        f"{directory_path}/embedding_tokensize_{num_sentences_per_token}/{id}_embedding.text",
        embeddings,
    )
    return embeddings
