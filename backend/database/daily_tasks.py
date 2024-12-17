from generate_database import *
from ..predictions.query_utils import *
from ..database.database_utils import *
import time
from transformers import AutoModelForSequenceClassification

# Replace TFAutoModelForSequenceClassification with AutoModelForSequenceClassification for PyTorch
MODEL = "model-name"  # specify your model name

class SentimentModel:
    def __init__(self):
        self.model = AutoModelForSequenceClassification.from_pretrained(MODEL)
        # other initializations if necessary

    # other methods if necessary

'''
This script will serve to:

    - Populate the database with relevant, trending news
    - Delete previous trending topics
    - Refreshes articles in storage (any expired articles get cleared)

Topics are found using populate_database_by_recent_news in generate_database.py

Questions are generated using generate_what_if_questions in query_utils.py

Articles are generated using q2a_workflow in query_utils.py

'''

def populate_trending_topics():
    client, db, collection = connect_to_mongodb()
    
    # Use aggregation to find all unique topics in the articles collection
    pipeline = [
        {"$group": {"_id": "$topic"}}
    ]
    unique_topics = collection.aggregate(pipeline)
    
    trending_topics_collection = db['trendingTopics']
    
    for topic in unique_topics:
        topic_name = topic['_id']
        print(f"Processing topic: {topic_name}")
        
        # Find all articles related to this topic
        articles = list(collection.find({"topic": topic_name}))
        
        if articles:
            # Check if the topic already exists in trendingTopics
            existing_entry = trending_topics_collection.find_one({"topic": topic_name})
            
            if existing_entry:
                # Merge new articles with existing ones
                existing_article_ids = {article['id'] for article in existing_entry['articles']}
                new_articles = [article for article in articles if article['id'] not in existing_article_ids]
                
                if new_articles:
                    # Update the existing entry with new articles
                    trending_topics_collection.update_one(
                        {"topic": topic_name},
                        {"$push": {"articles": {"$each": new_articles}}}
                    )
                    print(f"Updated topic '{topic_name}' with {len(new_articles)} new articles.")
                else:
                    print(f"No new articles to add for topic: {topic_name}")
            else:
                # Insert the new topic with its articles
                trending_topic_entry = {
                    "topic": topic_name,
                    "articles": articles
                }
                trending_topics_collection.insert_one(trending_topic_entry)
                print(f"Inserted topic '{topic_name}' with {len(articles)} articles into trendingTopics.")
        else:
            print(f"No articles found for topic: {topic_name}")

    print("Finished populating trending topics.")

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
            article_contents = get_article_contents_from_id(article_id)
            
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
        article_contents = get_article_contents_from_id(article_id)
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
    populate_trending_topics() # populates trendingtopics from articles collection
    print("Populated trending topics complete")
    topics = get_all_trending_topics()
    generate_questions_for_topics(topics) # right not, this generates "what if" questions for the first article in the topic. 
    #generate_articles_for_questions(topics)
    

if __name__ == '__main__':
    main()
