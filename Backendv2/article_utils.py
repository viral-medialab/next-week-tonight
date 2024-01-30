import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from openai_utils import *
'''
Provides all utility functions for analyzing articles
'''




def gather_article_metadata(article, query_used_for_article_search, sentiment_model):
    metadata = {}
    '''
    The metadata for each article is in the format of a dictionary with the following fields:

        url                     :   A link to view the article on a webpage as a string

        date_published          :   Format- datetime object

        author                  :   The individual or group that wrote the article

        publisher               :   The organization that published the article

        word_count              :   The word count of the article.
        
        category                :   A categorization of the type of article
                                    Examples include "politics", "finance", "sports"

        topic                   :   A very short description of the topic that the article addresses
                                    Examples include "Israel-Gaza War", "President Trump's Immunity Claim"

        keywords                :   Key words that illustrate what subtopics the article touches on
                                    Examples include "Biden", "Qatar", "Yankees"

        polarity                :   Format- Float in [-1,1] where -1 is negative and 1 is positive

        subjectivity            :   Format- Float in [0,1] where 0 is objective and 1 is subjective

        semantic_embedding      :   Format- (1536,1) vector average of all word embeddings

        image                   :   Refer to https://learn.microsoft.com/en-us/rest/api/cognitiveservices-bingsearch/bing-news-api-v7-reference#thumbnail
                                    for information on format
    '''

    # we can gather the following simply from the Bing News Search API
    metadata['url'] = article['url'] if 'url' in article else "Not found"
    metadata['date_published'] = datetime.strptime(article['datePublished'].split(".")[0], "%Y-%m-%dT%H:%M:%S") if 'datePublished' in article else "Not found"
    metadata['publisher'] = article['provider'][0]['name'][:-11] if 'provider' in article else "Not found"
    metadata['category'] = article['category'] if 'category' in article else "Not found"
    metadata['keywords'] = [d['name'] for d in article['about']] if 'about' in article else [d['name'] for d in article['mentions']] if 'mentions' in article else "Not found"
    metadata['topic'] = query_used_for_article_search
    metadata['image'] = article['image'] if 'image' in article else "Not found"

    # we need the article contents to compute the rest of the metadata
    article_id = get_article_id(article)
    author, article_text = get_article_contents_from_id(article_id, return_author=True)

    # now we can load our pretrained tone, sentiment, and embedding models
    # tone = tone_analysis.categorize(article_text)
    sentiment = sentiment_model.get_sentiment_score(article_text)
    semantic_embedding = get_embedding(article_text)

    metadata['word_count'] = len(article_text.replace("\n\n", " ").split(" "))
    metadata['id'] = article_id
    metadata['author'] = author
    #metadata['tone'] = tone
    metadata['sentiment'] = sentiment
    metadata['semantic_embedding'] = semantic_embedding

    return metadata




def get_article_id(article):        
    pattern = re.compile(r'/ar-([A-Za-z0-9]+)')
    article_url = article if type(article) == str else article['url']
    match = pattern.search(article_url)
    if match:
        article_id = match.group(1)
        return article_id
    else:
        raise Exception("No article ID found")




def get_article_contents_from_id(article_id, return_author = False):
    # Returns author and article contents
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
    if return_author:
        return author, '\n\n'.join(paragraphs)
    else:
        return '\n\n'.join(paragraphs)
    


def get_article_contents_for_website(article_id):
    # Returns author and article contents
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
    
    if data.get('title', False):
        title = data.get('title', 'None')
    else:
        title = 'No Title'

    return title, author, html_content




def filter_msn_articles(articles):
    return [article for article in articles if 'msn.com' in article['url']]