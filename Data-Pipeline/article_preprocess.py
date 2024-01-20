import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import numpy as np
from pretrained_models import SemanticEmbeddings, SentimentAnalysis, ToneAnalysis
embedding_model = SemanticEmbeddings()
sentiment_analysis = SentimentAnalysis()
tone_analysis = ToneAnalysis()


def gather_article_metadata(article, query_used_for_article_search):
    metadata = {}
    '''
    The metadata for each article is in the format of a dictionary with the following fields:

        url                     :   A link to view the article on a webpage as a string

        date_published          :   Format- datetime object

        author                  :   The individual or group that wrote the article

        publisher               :   The organization that published the article
        
        category                :   A categorization of the type of article
                                    Examples include "politics", "finance", "sports"

        topic                   :   A very short description of the topic that the article addresses
                                    Examples include "Israel-Gaza War", "President Trump's Immunity Claim"

        keywords                :   Key words that illustrate what subtopics the article touches on
                                    Examples include "Biden", "Qatar", "Yankees"

        polarity                :   Format- Float in [-1,1] where -1 is negative and 1 is positive

        subjectivity            :   Format- Float in [0,1] where 0 is objective and 1 is subjective

        semantic_embedding      :   Format- (1536,1) vector average of all word embeddings
    '''

    # we can gather the following simply from the Bing News Search API
    metadata['url'] = article['url'] if 'url' in article else "Not found"
    metadata['date_published'] = datetime.strptime(article['datePublished'].split(".")[0], "%Y-%m-%dT%H:%M:%S") if 'datePublished' in article else "Not found"
    metadata['publisher'] = article['provider'][0]['name'][:-11] if 'provider' in article else "Not found"
    metadata['category'] = article['category'] if 'category' in article else "Not found"
    metadata['keywords'] = [d['name'] for d in article['about']] if 'about' in article else [d['name'] for d in article['mentions']] if 'mentions' in article else "Not found"
    metadata['topic'] = query_used_for_article_search

    # we need the article contents to compute the rest of the metadata
    article_id = fetch_article_id(article)
    author, article_text = fetch_article_contents(article_id)

    # now we can load our pretrained tone, sentiment, and embedding models
    #tone = tone_analysis.categorize(article_text)
    sentiment = sentiment_analysis.get_sentiment_score(article_text)
    semantic_embedding = embedding_model.get_embedding(article_text)

    metadata['id'] = article_id
    metadata['author'] = author
    #metadata['tone'] = tone
    metadata['sentiment'] = sentiment
    metadata['semantic_embedding'] = semantic_embedding

    return metadata
    


def fetch_article_id(article):        
    pattern = re.compile(r'/ar-([A-Za-z0-9]+)')
    article_url = article['url']

    match = pattern.search(article_url)
    if match:
        article_id = match.group(1)
        return article_id
    else:
        raise Exception("No article ID found")



def fetch_article_contents(article_id):
    '''
    Returns article's author and contents of the article
    '''
    asset_url = "https://assets.msn.com/content/view/v2/Detail/en-us/" + article_id

    try:
        response = requests.get(asset_url)
        response.raise_for_status()
        data = response.json()
        html_content = data.get('body', 'No content found')

    except requests.RequestException as e:
        print(f"Error fetching article: {e}")
        return None
    
    if data.get('authors', False):
        author = data.get('authors', 'None')[0]['name']
    else:
        author = 'Not found'
    
    soup = BeautifulSoup(html_content, 'lxml')
    paragraphs = [p.get_text(separator=' ', strip=True) for p in soup.find_all('p')]
    #print(author)
    return author, '\n\n'.join(paragraphs)



if __name__=='__main__':
    article = {'name': 'Israel-Gaza live updates: 1 dead, 17 injured in car-ramming attacks near Tel Aviv', 'url': 'https://www.msn.com/en-us/news/world/israel-gaza-live-updates-1-dead-17-injured-in-car-ramming-attacks-near-tel-aviv/ar-AA1mZtCd', 'image': {'thumbnail': {'contentUrl': 'https://www.bing.com/th?id=OVFT.-sI3FRNvYQitjz3LsIUp9i&pid=News', 'width': 700, 'height': 393}}, 'description': "At least one person was killed and 17 others were injured on Monday afternoon in car-ramming attacks that took place in various locations across Ra'anana, Israel, authorities said.", 'about': [{'readLink': 'https://api.bing.microsoft.com/api/v7/entities/90eb9ff6-60ad-da43-d3fe-1ee3e3cb775a', 'name': 'Gaza Strip'}, {'readLink': 'https://api.bing.microsoft.com/api/v7/entities/7105fc08-1958-b454-5216-cd319a983ad0', 'name': 'Tel Aviv'}, {'readLink': 'https://api.bing.microsoft.com/api/v7/entities/1ffafed3-2b37-b871-c271-aa855d98449a', 'name': 'Israel'}], 'mentions': [{'name': 'Gaza Strip'}, {'name': 'Tel Aviv'}, {'name': 'Israel'}], 'provider': [{'_type': 'Organization', 'name': 'ABC on MSN.com', 'image': {'thumbnail': {'contentUrl': 'https://www.bing.com/th?id=ODF.-LMnifaGw_NvPvJr_0E9tA&pid=news'}}}], 'datePublished': '2024-01-16T17:07:37.0000000Z', 'category': 'World'}
    print(gather_article_metadata(article, 'Israel Gaza War'))