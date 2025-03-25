# Install with pip install firecrawl-py
from firecrawl import FirecrawlApp
from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime
from dotenv import load_dotenv
from tqdm import tqdm
import os
import sys
from dateutil import parser

load_dotenv("../../vars.env")
load_dotenv("../vars.env")
load_dotenv("vars.env")

firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
if not firecrawl_api_key:
        print("Error: FIRECRAWL_API_KEY not found in environment variables.")
        print("Please add your Firecrawl API key to your vars.env file.")
        sys.exit(1)


class ExtractSchema(BaseModel):
        article_text: str
        article_title: str
        # article_publish_date: str = 'N/A'
        # article_author: str = 'N/A'

def create_article_doc(firecrawl_output,event_id,topic_title,url,query_datetime):
    #  print(firecrawl_output['article_publish_date'],'\n')
    #  print(parser.parse(firecrawl_output['article_publish_date']))
     article_doc = {
        #original_event_datetime
        #article_data
        #event_id
        # 'article_publish_date': parser.parse(firecrawl_output['article_publish_date']),
        'article_publish_date': query_datetime,
        'event_id':event_id,
            'topic_title': topic_title,
            'news_title': firecrawl_output['article_title'],
            'news_url': url,
            # 'domain': article.get('domain', ''),
            # 'language': article.get('language', ''),
            # 'source_country': article.get('sourcecountry', ''),
            'text': firecrawl_output['article_text']
     }
    #  print("articledoc", article_doc)
     return article_doc

app = FirecrawlApp(api_key=firecrawl_api_key)
def firecrawl_scrape(urls,event_id,topic_title,query_datetime):
    data = []
    checked = set()
    fail_count = 0
    for i in tqdm (range (len(urls)), desc="Loading..."):
        url = urls[i]
        if url in checked:
            continue
        checked.add(url)
        try:
            output = app.extract([url], {
                'prompt': '',
                'schema': ExtractSchema.model_json_schema(),
            })['data']
            if not output['article_text']:
                raise Exception
            data.append(create_article_doc(output,event_id,topic_title,url,query_datetime))
        except:
            fail_count+=1
            continue
    print("Extraction complete.")
    if fail_count:
        print(f"Extraction for {fail_count} articles failed.")
    return data
# print(datetime.strptime('2025-01-15T19:30:58.540Z', '%Y-%m-%dT%H:%M:%S.%fZ'))
# print(firecrawl_scrape(['https://www.usatoday.com/story/news/politics/2025/03/12/trump-doge-federal-layoffs-timeline/82240271007/','https://www.nytimes.com/2025/03/12/us/politics/trump-crackdown-dissent.html'],0,'trump'))