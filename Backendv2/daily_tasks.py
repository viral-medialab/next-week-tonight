from generate_database import *
from query_utils import *
from database_utils import *
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
    topics = populate_database_by_recent_news(-1, 1, simple_return=True, offset=3)
    client, db, collection = connect_to_mongodb(collection_to_open='trendingTopics')
    
    for topic in topics:
        topic = topic.replace("\n ", "")
        print(f"Now performing on topic: {topic}")
        populate_database_by_topic(topic, 5, trending_topic=True, max_attempts=30)
        
        doc = collection.find_one({'topic': topic})
        if doc:
            print(f"Topic '{topic}' successfully added to the database.")
        else:
            print(f"Failed to add topic '{topic}' to the database.")
    
    return topics

def generate_questions_for_topics(topics):
    client, db, collection = connect_to_mongodb(collection_to_open='trendingTopics')
    
    for topic in topics:
        doc = collection.find_one({'topic': topic})
        if not doc or not doc['articles']:
            print(f"No articles found for topic: {topic}")
            continue
        
        article = doc['articles'][0]
        article_id = get_article_id(article)
        article_contents = get_article_contents_from_id(article_id)
        
        questions = generate_what_if_questions(article_contents)
        new_questions = []
        print(f"Found questions for top article: {questions}")
        for question in questions:
            new_question = question.replace("...", "What happens if").strip()
            print(f"Replaced old question [{question}] with new question [{new_question}] for formatting purposes")
            new_questions.append(new_question)
        
        questions_dict = {question: {} for question in new_questions}
        doc['articles'][0]['questions'] = questions_dict
        collection.find_one_and_replace({'_id': doc['_id']}, doc)
        print(f"Updated questions for topic: {topic}")

def generate_articles_for_questions(topics):
    client, db, collection = connect_to_mongodb(collection_to_open='trendingTopics')
    
    for topic in topics:
        doc = collection.find_one({'topic': topic})
        if not doc or not doc['articles'] or 'questions' not in doc['articles'][0]:
            print(f"No questions found for topic: {topic}")
            continue
        
        article = doc['articles'][0]
        article_id = get_article_id(article)
        article_contents = get_article_contents_from_id(article_id)
        questions = doc['articles'][0]['questions']
        
        for question in questions:
            for polarity in [0, 1, 2]:
                for probability in [0, 1, 2]:
                    out = q2a_workflow(article_contents, article_id, question, polarity, probability, verbose=True)
                    article_title, article_body = out[-1][0], out[-1][1]
                    id, parent = save_generated_article_to_DB(title=article_title, body=article_body, parent=article_id, query=question)
                    
                    article_key = f'article{polarity * 3 + probability}'
                    questions[question][article_key] = {
                        'title': article_title,
                        'body': article_body,
                        'id': id,
                        'parent': parent,
                        "probability": probability,
                        "polarity": polarity
                    }
        
        collection.find_one_and_replace({'_id': doc['_id']}, doc)
        print(f"Generated articles for topic: {topic}")

def main():
    topics = populate_trending_topics()
    generate_questions_for_topics(topics)
    generate_articles_for_questions(topics)
    print("Job complete")

if __name__ == '__main__':
    main()
