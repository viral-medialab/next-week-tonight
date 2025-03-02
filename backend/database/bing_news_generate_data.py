import requests
import sys
from pathlib import Path
#from llm.sentiment import SentimentModel
# Add the project root directory to Python path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))
from backend.llm.openai_utils import *
from backend.database.database_utils import *
from backend.api.article_utils import *
from backend.test.env import *
from backend.llm.prompts import *
from datetime import datetime, timedelta
import json



# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).parent.parent))

#sentiment_model = SentimentModel()

def populate_database_by_recent_news(num_articles_to_store = 2, num_topics = 20, simple_return = False, offset=0):
    url = "https://api.bing.microsoft.com/v7.0/news"  # Changed to general news endpoint
    headers = {'Ocp-Apim-Subscription-Key': BING_API_KEY}
    query_params = {"count": num_topics*2, 
                    "q": "Breaking Global US News",
                    "mkt": "en-US", 
                    "offset": 0}
    response = requests.get(url, headers=headers, params = query_params)
    response.raise_for_status()
    results = response.json()['value']

    context = trending_topics_prompt
    query =  "News headlines and descriptions (separated by semicolons): "
    for article in results:
        query = query + article['name'] + article['description'] + '; '
    topics = query_chatgpt([context], [query[:-2]])[1:-1].replace(' "','').replace('"','').split(",")

    if simple_return:
        return topics

    successful_topics = 0
    for topic in topics:
        if successful_topics < num_topics:
            print("NOW EXAMINING HEADLINES IN ", topic.upper())
            if populate_database_by_topic(topic, num_articles_to_store // num_topics, trending_topic=True):
                successful_topics += 1




def populate_database_by_topic(topic, num_articles_to_store=10, summary=None, date=None, trending_topic=False, max_attempts = 30):
    client, db, collection = connect_to_mongodb()

    num_articles_stored = 0
    offset = 0
    if trending_topic:
        entry = {'topic': topic, 'articles': []}
    attempts = 0
    while num_articles_stored < num_articles_to_store and attempts < max_attempts:
        articles = find_articles_by_topic(topic, offset, num_articles_to_store=min(5*num_articles_to_store,100))
        articles = filter_msn_articles(articles)
        for article in articles:
            try:
                cur_article_id = get_article_id(article)
                cur_article_url = article['url']
                if collection.count_documents({'id': cur_article_id}) == 0 and collection.count_documents({'url': cur_article_url}) == 0:
                    metadata = gather_article_metadata(article, topic, sentiment_model)
                    result = collection.insert_one(metadata)
                    if trending_topic:
                        entry['articles'].append(metadata)
                    num_articles_stored += 1
                    print(f"Document added. The document ID is: {result.inserted_id}")
            
            except Exception as e:
                print(f"An error occurred: {e}")
                continue

        offset += min(5*num_articles_to_store,100)
        attempts += 1

    if trending_topic:
        article_count = len(entry['articles'])
        if article_count >= 6:
            result = db['trendingTopics'].insert_one(entry)
            article_count = len(entry['articles'])
            print(f"Trending topic with {article_count} articles added to DB, the document id is {result.inserted_id}")
            return True
        else:
            return False


def extract_keywords_from_summary(summary):
    prompt = f"""
    Extract 5-10 key terms or phrases from the following summary. These terms should be most relevant for searching news articles about the incident. Return the keywords as a comma-separated list.

    Summary: {summary}
    """
    response = query_chatgpt(["You are a helpful assistant."], [prompt])
    keywords = [keyword.strip() for keyword in response.split(',')]
    return keywords

def calculate_freshness(date_str):
    try:
        input_date = datetime.strptime(date_str, "%Y-%m-%d")
        today = datetime.now()
        delta = today - input_date
        
        if delta.days <= 1:
            return "Day"
        elif delta.days <= 7:
            return "Week"
        elif delta.days <= 31:
            return "Month"
        else:
            return None  # Bing API doesn't support freshness beyond a month
    except ValueError:
        print(f"Invalid date format. Please use YYYY-MM-DD. Defaulting to no freshness filter.")
        return None

def find_articles_by_topic(topic, summary=None, date=None, category=None, offset=0, num_articles_to_store=10):
    api_endpoint = "https://api.bing.microsoft.com/v7.0/news/search"

    # Extract keywords from summary if provided
    summary_keywords = extract_keywords_from_summary(summary) if summary else None

    # Construct the query string
    query = topic + ' site:msn.com'
    if summary_keywords:
        query += f' {" ".join(summary_keywords)}'

    query_params = {
        "q": query,
        "count": num_articles_to_store,
        "mkt": "en-US",
        "offset": offset,
        "sortBy": "Relevance",  # Always sort by date
    }

    if date:
        freshness = calculate_freshness(date)
        if freshness:
            query_params["freshness"] = freshness
    if category:
        query_params["category"] = category

    headers = {
        "Ocp-Apim-Subscription-Key": BING_API_KEY
    }

    try:
        response = requests.get(api_endpoint, headers=headers, params=query_params)
        response.raise_for_status()
        results = response.json()
    except Exception as e:
        print(f"Generate database Error: {e}")
        return []

    articles = results.get('value', [])

    print(f"Found {len(articles)} articles on {topic} with offset {offset}")
    if summary_keywords:
        print(f"Using keywords: {', '.join(summary_keywords)}")
    if date:
        print(f"Using freshness: {freshness if freshness else 'No freshness filter applied'}")
    print("Articles sorted by latest first")

    return articles

# def main(args):
#     '''
#     Adds articles to the database depending on user specification

#     >> python generate_dataset.py 100 "Israel Gaza War"
#     Now adding 100 articles on Israel Gaza war into the database

#     >> python generate_dataset.py 100 10
#     Now adding 100 articles on 10 trending topics into the database
#     '''
#     if len(args) != 3:
#         print("Usage: \npython generate_dataset.py <amount_of_articles> <topic> , or\n python generate_dataset.py <amount_of_articles> <num_topics>")
#         sys.exit(1)

#     if args[2].isdigit():
#         amount_of_articles = int(args[1])
#         num_topics = int(args[2])
#         print(f"Now adding {amount_of_articles} articles on {num_topics} trending topics into the database.")
#         populate_database_by_recent_news(amount_of_articles, num_topics)
#     else:
#         amount_of_articles = int(args[1])
#         topic = args[2]
#         print(f"Now adding {amount_of_articles} articles on {topic} into the database.")
#         populate_database_by_topic(topic, amount_of_articles, True)

def get_multi_line_input(prompt):
    print(prompt)
    print("(Type your summary and press Enter twice to finish)")
    lines = []
    while True:
        line = input()
        if line:
            lines.append(line)
        else:
            break
    return ' '.join(lines)

def get_user_input():
    print("Please provide the following information:")
    topic = input("Topic (required): ").strip()
    if not topic:
        print("Topic is required. Exiting.")
        sys.exit(1)
    
    date = input("Date (optional, format YYYY-MM-DD): ").strip()
    summary = get_multi_line_input("Summary (optional):")
    
    while True:
        num_articles = input("Number of articles (optional, default is 10): ").strip()
        if not num_articles:
            num_articles = 10
            break
        try:
            num_articles = int(num_articles)
            if num_articles > 0:
                break
            else:
                print("Please enter a positive number.")
        except ValueError:
            print("Please enter a valid number.")
    
    return {
        "topic": topic,
        "date": date if date else None,
        "summary": summary if summary else None,
        "number_of_articles": num_articles
    }

def main():
    '''
    Adds articles to the database based on user input.

    Usage: python generate_database.py
    '''
    user_input = get_user_input()
    
    print("\nProcessing with the following parameters:")
    print(json.dumps(user_input, indent=2))
    
    # Call the function to populate the database
    populate_database_by_topic(
        topic=user_input["topic"],
        num_articles_to_store=user_input["number_of_articles"],
        date=user_input["date"],
        summary=user_input["summary"]
    )


if __name__=='__main__':
    main()