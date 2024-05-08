from generate_database import *
from query_utils import *
import time
'''
This script will serve to:

    - Populate the database with relevant, trending news
    - Clean user activity from over 7 days ago in the database

'''

topics = populate_database_by_recent_news(-1, 1, simple_return = True)
for i, topic in enumerate(topics):
    time1 = time.time()
    print(topic)
    #populate_database_by_topic(topic, 5, trending_topic=True, max_attempts = 30)
    client, db, collection = connect_to_mongodb(collection_to_open = 'trendingTopics')
    doc = collection.find_one({'topic': topic})
    doc_copy = collection.find_one({'topic': topic})
    article = doc_copy['articles'][0]
    article_id = get_article_id(article)
    article_contents = get_article_contents_from_id(article_id)
    # generate questions
    questions = generate_what_if_questions(article_contents)
    print(questions)
    questions_dict = {question: {} for question in questions}
    doc_copy['articles'][0]['questions'] = questions_dict
    for question in questions_dict:
        new_question = question
        new_question = new_question.replace("...", "What happens if")
        if new_question[0] == " ": new_question = new_question[1:]
        print(new_question)
        del doc_copy['articles'][0]['questions'][question]
        doc_copy['articles'][0]['questions'][new_question] = questions_dict[question]

    for question in questions:
        for polarity in [0,1,2]:
            for probability in [0,1,2]:
                normalized_polarity = polarity / 2
                normalized_probability = probability / 2
                out = q2a_workflow(article_contents, article_id, question, normalized_polarity, normalized_probability, verbose=True)
                article_title, article_body = out[-1][0], out[-1][1]
                doc_copy['articles'][0]['questions'][question][str(probability) + ';' + str(polarity)] = {'title': article_title, 'body': article_body}
                id, parent = save_generated_article_to_DB(title = article['title'], body = article['body'], parent = article_id, query = question)

    collection.find_one_and_replace(doc, doc_copy)
    time2 = time.time()
    print(f"\n\n\n\n\n\n\n\n\n\nREPLACED COLLECTION - CHECK TRENDING TOPICS MONGODB AT TOPIC: {topic.upper()}")
    print(f"This process took {time2-time1} total seconds. Moving on to the next topic...\n\n\n\n\n\n\n\n\n\n\n")
