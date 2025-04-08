from openai import OpenAI
import sys
from dotenv import load_dotenv
import os

load_dotenv("../../vars.env")
load_dotenv("../vars.env")
load_dotenv("vars.env")
perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")

def perplexity_article_query(topic):
    """
    :param news_url: The url of the article to search
    :type news_url: str
    :returns: A tuple with the summarized text from the article url and a score of the summary: (score,text)
    """
    
    messages = [
        {
        "role": "system",
        "content": (
            "You are an artificial intelligence assistant with the sole purpose of providing news articles given a topic."
        ),
        },
        {
            "role": "user",
            "content": (
                f"Provide 10 news urls from any news source given the following topic published within 1 week of the following date. Return only the urls with no other words or line breaks, separated by commas: {topic}."
            ),
        }
    ]
    if not perplexity_api_key:
        print("Error: PERPLEXITY_API_KEY not found in environment variables.")
        print("Please add your Perplexity API key to your vars.env file.")
        sys.exit(1)
    client = OpenAI(api_key=perplexity_api_key, base_url="https://api.perplexity.ai")

    response = client.chat.completions.create(
        model="sonar-pro",
        messages=messages,
    )
    urls = response.choices[0].message.content
    urls = urls.split(",")
    return urls

# print(perplexity_article_query("California Wild Fires, 2025-01-14T02:20:00+08:00"))