# Install with pip install firecrawl-py
from firecrawl import FirecrawlApp
from pydantic import BaseModel, Field
from typing import Any, Optional, List
from datetime import datetime, timedelta

class ExtractSchema(BaseModel):
        article_text: str
        article_title: str
        article_publish_date: str
        article_author: str = 'N/A'
def create_article_doc(firecrawl_output,event_id,topic_title,url):
     extracted_date = [int(t) for t in datetime(firecrawl_output['article_publish_date'])[:10].split("-")]+[0,0,0,0,0,0]
     article_doc = {
        #original_event_datetime
        #article_data
        #event_id
        'original_event_datetime': datetime(*extracted_date),
        'event_id':event_id,
        'article_data': {
            'topic_title': topic_title,
            'news_title': firecrawl_output['article_title'],
            'news_url': url,
            # 'domain': article.get('domain', ''),
            # 'language': article.get('language', ''),
            # 'source_country': article.get('sourcecountry', ''),
            'seen_date': firecrawl_output['article_publish_date'],
            'text': firecrawl_output['article_text']
                        },  
                            }
     return article_doc

app = FirecrawlApp(api_key='fc-312aa443d7114da6b7ffffd079d2de44')
def firecrawl_scrape(urls,event_id,topic_title):
    data = []
    for url in urls:
        try:
            output = app.extract([url], {
                'prompt': '',
                'schema': ExtractSchema.model_json_schema(),
            })['data']
            data.append(create_article_doc(output,event_id,topic_title,url))
        except:
            continue
    return data
print(firecrawl_scrape(['https://www.usatoday.com/story/news/politics/2025/03/12/trump-doge-federal-layoffs-timeline/82240271007/','https://www.nytimes.com/2025/03/12/us/politics/trump-crackdown-dissent.html'],0,'trump'))