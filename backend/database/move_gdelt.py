from generate_database import *
from predictions.query_utils import *
from database.database_utils import *
import time
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).parent.parent))
'''
This script will serve to:

    - Populate the database with relevant, trending news
    - Delete previous trending topics
    - Refreshes articles in storage (any expired articles get cleared)

Topics are found using populate_database_by_recent_news in generate_database.py

Questions are generated using generate_what_if_questions in query_utils.py

Articles are generated using q2a_workflow in query_utils.py

'''

def populate_trending_topics_from_gdelt(topic_title):
    client, db, gdelt_collection = connect_to_mongodb("GDELT")
    
    # Use aggregation to find all unique topics in the articles collection
    # pipeline = [
    #     {"$group": {"_id": "$topic"}}
    # ]
    # unique_topics = collection.aggregate(pipeline)
    
    trending_topics_collection = db['trendingTopics']
    gdelt_articles = list(gdelt_collection.find({"topic_title": topic_title}))
    if not gdelt_articles:
        print(f"No articles found in GDELT for topic: {topic_title}")
        return
    

    new_topic = {
        "topic": article['news_title'],
        "articles": [
            {
                "url": article['news_url'],
                "date_published": article['original_event_datetime'],
                "publisher": article['domain'],
                "category": "",
                "keywords": "",
                "topic": article['news_title'],
                "image": "",
                "word_count": "",
                "id": get_article_id(article['news_url']),
                "author": "",
                "sentiment": "",
                "semantic_embedding": "",
                "questions": [],
                "prompts": [],
            }
            for article in gdelt_articles
        ]
    }
    trending_topics_collection.insert_one(new_topic)

    print(f"Created new topic '{topic_title}' with {len(gdelt_articles)} articles")

def get_article_id(article):        
    pattern = re.compile(r'/ar-([A-Za-z0-9]+)')
    article_url = article if type(article) == str else article['url']
    match = pattern.search(article_url)
    if match:
        article_id = match.group(1)
        return article_id
    else:
        raise Exception("No article ID found")
    
def get_article_contents_from_id(news_url, return_author = False):
    # Returns author and article contents
    asset_url = news_url

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
    # TODO fix LXML library
    if return_author:
        return author, '\n\n'.join(paragraphs)
    else:
        return '\n\n'.join(paragraphs)
    

def generate_questions_for_topics(topics):
    client, db, collection = connect_to_mongodb(collection_to_open='trendingTopics')
    
    for topic in topics:
        doc = collection.find_one({'topic': topic})
        if not doc or not doc['articles']:
            print(f"No articles found for topic: {topic}")
            continue
        
        updated = False
        for article in doc['articles']:
            # Skip if questions already exist
            if 'questions' in article and article['questions']:
                print(f"Questions already exist for article ID {get_article_id(article)}. Skipping.")
                continue
            
            article_id = get_article_id(article)
            article_contents = get_article_contents_from_id(article['news_url'])
            
            questions = generate_what_if_questions(article_contents)
            new_questions = []
            print(f"Found questions for article ID {article_id}: {questions}")
            for question in questions:
                new_question = question.replace("...", "What happens if").strip()
                print(f"Replaced old question [{question}] with new question [{new_question}] for formatting purposes")
                new_questions.append(new_question)
            
            # Add new questions
            questions_dict = {question: {} for question in new_questions}
            article['questions'] = questions_dict
            updated = True
        
        # Update the entire document only if changes were made
        if updated:
            collection.find_one_and_replace({'_id': doc['_id']}, doc)
            print(f"Updated questions for articles without existing questions in topic: {topic}")
        else:
            print(f"No updates needed for topic: {topic}. All articles already have questions.")

def generate_articles_for_questions(topics):
    client, db, collection = connect_to_mongodb(collection_to_open='trendingTopics')
    
    for topic in topics:
        doc = collection.find_one({'topic': topic})
        if not doc or not doc['articles'] or 'questions' not in doc['articles'][0]:
            print(f"No questions found for topic: {topic}")
            continue
        
        #first article in the topic
        article = doc['articles'][0]
        article_id = get_article_id(article)
        article_contents = get_article_contents_from_id(article['news_url'])
        questions = doc['articles'][0]['questions']
        
        for question in questions:
            for yscale in [0, 1, 2]:
                for xscale in [0, 1, 2]:
                    out = q2a_workflow(article_contents, article_id, question, xscale, yscale, verbose=True)
                    article_title, article_body = out[-1][0], out[-1][1]
                    id, parent = save_generated_article_to_DB(title=article_title, body=article_body, parent=article_id, query=question)
                    
                    article_key = f'article{yscale * 3 + xscale}'
                    questions[question][article_key] = {
                        'title': article_title,
                        'body': article_body,
                        'id': id,
                        'parent': parent,
                        "probability": xscale,
                        "impact": yscale
                    }
        
        collection.find_one_and_replace({'_id': doc['_id']}, doc)
        print(f"Generated articles for topic: {topic}")

def get_all_trending_topics():
    # Connect to the MongoDB database
    client, db, collection = connect_to_mongodb(collection_to_open='trendingTopics')
    
    # Retrieve all topics from the trendingTopics collection
    topics_cursor = collection.find({}, {"topic": 1, "_id": 0})
    
    # Extract topics into a list
    topics = [doc['topic'] for doc in topics_cursor]
    
    return topics

def main():
    populate_trending_topics_from_gdelt() # populates trendingtopics from articles collection
    print("Populated trending topics complete")
    topics = get_all_trending_topics()
    #generate_questions_for_topics(topics) # right not, this generates "what if" questions for the first article in the topic. 
    #generate_articles_for_questions(topics)
    

if __name__ == '__main__':
    main()
