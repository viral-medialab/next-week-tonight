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

def repopulate_trendingtopics_database():
    topics = populate_database_by_recent_news(-1, 1, simple_return=True, offset=3)  # generates a list of topics, not the actual articles yet

    for i, topic in enumerate(topics):
        # first, saves articles into the db
        time1 = time.time()
        topic = topic.replace("\n ", "")
        print(f"Now performing on topic: {topic}")
        populate_database_by_topic(topic, 3, trending_topic=True, max_attempts=30)  # locates actual articles

        # finds newly saved articles in mongodb
        client, db, collection = connect_to_mongodb(collection_to_open='trendingTopics')
        doc = collection.find_one({'topic': topic})
        doc_copy = collection.find_one({'topic': topic})
        article = doc_copy['articles'][0]
        article_id = get_article_id(article)
        article_contents = get_article_contents_from_id(article_id)

        # generate questions
        questions = generate_what_if_questions(article_contents)
        new_questions = []
        print(f"Found questions for top article: {questions}")
        for question in questions:
            new_question = question
            new_question = new_question.replace("...", "What happens if")
            if new_question[0] == " ":
                new_question = new_question[1:]
            print(f"Replaced old question [{question}] with new question [{new_question}] for formatting purposes")
            new_questions.append(new_question)
        questions_dict = {question: {} for question in new_questions}
        doc_copy['articles'][0]['questions'] = questions_dict

        # generates articles for every question
        for question in new_questions:
            for polarity in [0]:
                for probability in [0]:
                    normalized_polarity = polarity / 2
                    normalized_probability = probability / 2
                    article_pol_prob = str(probability) + ';' + str(polarity)

                    out = q2a_workflow(article_contents, article_id, question, normalized_polarity, normalized_probability, verbose=True)
                    article_title, article_body = out[-1][0], out[-1][1]
                    id, parent = save_generated_article_to_DB(title=article_title, body=article_body, parent=article_id, query=question)
                    doc_copy['articles'][0]['questions'][question][article_pol_prob] = {'title': article_title, 'body': article_body, 'id': id, 'parent': parent}

        collection.find_one_and_replace(doc, doc_copy)
        time2 = time.time()
        print(f"\n\nCheck MongoDB at topic: {topic}")
        print(f"This process took {time2 - time1} total seconds. Moving on to the next topic...\n\n")

def main():
    ready_to_replace_old_topics = True

    clear_all_expired_articles()

    if ready_to_replace_old_topics:
        clear_trending_topics()

    repopulate_trendingtopics_database()

    print("Job complete")

if __name__ == '__main__':
    main()