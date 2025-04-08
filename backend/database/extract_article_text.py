from bs4 import BeautifulSoup
from urllib.request import urlopen
import requests
from openai import OpenAI
from firecrawl import FirecrawlApp
from pydantic import BaseModel
from typing import Any
from dotenv import load_dotenv
import os
import sys
from tqdm import tqdm

load_dotenv("../../vars.env")
load_dotenv("../vars.env")
load_dotenv("vars.env")


perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")

def perplexity_text_extractor(news_url):
    """
    :param news_url: The url of the article to search
    :type news_url: str
    :returns: A tuple with the summarized text from the article url and a score of the summary: (score,text)
    """
    messages = [
        {
        "role": "system",
        "content": (
            "You are an artificial intelligence assistant with the sole purpose of summarizing the plain text from webpage urls."
        ),
        },
        {
            "role": "user",
            "content": (
                f"Summarize the plain text from the following url: {news_url}."
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

    score_message = [
        {
        "role": "system",
        "content": (
            "You are an artificial intelligence assistant with the sole purpose of analyzing summaries of article text."
        ),
        }
        ,
        {
            "role": "user",
            "content": (
                f"Score the summary provided from a scale of 0 to 5 with 0 being a bad summary of the original article or a failed extraction, and 5 being a perfect summary. Respond only with a score: {response.choices[0].message.content}"
            ),
        }
    ]
    score = client.chat.completions.create(
        model="sonar-pro",
        messages=score_message,
    )

    return (score.choices[0].message.content,response.choices[0].message.content)


class ExtractSchema(BaseModel):
        article_text: str
app = FirecrawlApp(api_key=firecrawl_api_key)
if not firecrawl_api_key:
        print("Error: FIRECRAWL_API_KEY not found in environment variables.")
        print("Please add your Firecrawl API key to your vars.env file.")
        sys.exit(1)

def firecrawl_text_extractor(url):
    try:
        output = app.extract([url], {
            'prompt': '',
            'schema': ExtractSchema.model_json_schema(),
        })['data']['article_text']
        return output
    except:
        return
def BSoup_text_extractor(news_url):
    """
    :param news_url: The url of the article to search
    :type news_url: str
    :returns: The extracted text from the url, None if not found
    """
    try:
        html = urlopen(news_url).read()
    except:
        try:
            html = requests.get(news_url).text
        except:
            return None
        
    soup = BeautifulSoup(html, features="html.parser")

    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.extract()    # rip it out

    # get text
    text = soup.get_text()

    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())

    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))

    # drop blank lines
    text = ' '.join(chunk for chunk in chunks if chunk)
    return text
    #maybe remove the white space by taking the # of adjacent words in a radius is a way to remove the unecessary text while staying universal
    #another option is to search for specific html body tags where I know article text will be
    #   works well if I have a limited # of news sources
    #   WHAT ARE THE NEWS SOURCES WE ACCESS?
    #   NYT, wallstreet journal, bbc

def extract_text_from_url(article_data):
        article_urls = article_data['url'].tolist()
        output_text = []
        for i in tqdm (range (len(article_urls)), desc="Loading..."):
            # #check if the url is present
            # if not news_url:
            #     continue

            #Try to summarize using Perplexity API Chat completion
            # print("Accessing text using Perplexity API")
            # article_text = perplexity_text_extractor(news_url)

            # #article_text returns in the form (score, text). Extraction failed if score is less than 2.
            # if article_text[0].isnumeric() and int(article_text[0]) < 2:
            #     print(f"Perplexity text extraction returned a score of {article_text[0]}. Extracting text with Beautiful Soup.")

            #     #If extraction fails, resort to extraction using BeautifulSoup
            #     article_text = BSoup_text_extractor(news_url)
            # print("---> Firecrawl extraction...")
            news_url = article_urls[i]
            article_text = firecrawl_text_extractor(news_url)
            #If both BeautifulSoup and Perplexity fail, store Extraction Failed, which can be purged later
            if not article_text:
                article_text = "Extraction Failed"
            #Append the final result
            output_text.append(article_text)        
        return output_text
        