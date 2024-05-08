#from generate_database import *
from query_utils import *
from database_utils import *
from article_utils import *
import time


def main():
    #clear_all_expired_articles()
    #clear_trending_topics()
    topics = ["U.S. Sends Ukraine Weapons Seized From Iran",
                "Marjorie Taylor Greene Keeps Up Pressure on Speaker Johnson",
                "Parents of Michigan School Shooter Sentenced For Manslaughter",
                "Arizona Supreme Court Issues Near-Total Ban On Abortions",
                "Trump Hush Money Trial To Move Ahead Despite Bid To Delay",
                "Russia Foreign Minister Visits Beijing"]
    for i, topic in enumerate(topics):
        if i < 4: continue
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

def main_check():
    topic = "U.S. Sends Ukraine Weapons Seized From Iran"
    client, db, collection = connect_to_mongodb(collection_to_open = 'trendingTopics')
    doc_copy = collection.find_one({'topic': topic})
    article = doc_copy['articles'][0]
    print(article)


def manual_polish_1(): #random fix for one of the topics with irrelevant articles
    topic = "Marjorie Taylor Greene Keeps Up Pressure on Speaker Johnson"
    client, db, collection = connect_to_mongodb(collection_to_open = 'trendingTopics')
    doc = collection.find_one({'topic': topic})
    doc_copy = collection.find_one({'topic': topic})
    doc_copy['articles'] = [doc_copy['articles'][3]]
    collection.replace_one(doc, doc_copy)


def manual_polish_2(): # replaced ... with actual question
    #topics = ["U.S. Sends Ukraine Weapons Seized From Iran"]
    # topics = ["U.S. Sends Ukraine Weapons Seized From Iran",
    topics = [   "Marjorie Taylor Greene Keeps Up Pressure on Speaker Johnson",
                 "Parents of Michigan School Shooter Sentenced For Manslaughter",
                 "Arizona Supreme Court Issues Near-Total Ban On Abortions",
                 "Trump Hush Money Trial To Move Ahead Despite Bid To Delay",
                 "Russia Foreign Minister Visits Beijing"]
    client, db, collection = connect_to_mongodb(collection_to_open = 'trendingTopics')
    for topic in topics:
        doc = collection.find_one({'topic': topic})
        doc_copy = collection.find_one({'topic': topic})
        for question in doc['articles'][0]['questions']:
            new_question = question
            new_question = new_question.replace("...", "What happens if")
            if new_question[0] == " ": new_question = new_question[1:]
            print(new_question)
            del doc_copy['articles'][0]['questions'][question]
            doc_copy['articles'][0]['questions'][new_question] = doc['articles'][0]['questions'][question]
        collection.replace_one(doc, doc_copy)


def manual_polish_3rd(): # made new db entries for children articles
    #topics = ["U.S. Sends Ukraine Weapons Seized From Iran"]
    # topics = ["U.S. Sends Ukraine Weapons Seized From Iran",
    topics = [   "Marjorie Taylor Greene Keeps Up Pressure on Speaker Johnson",
                 "Parents of Michigan School Shooter Sentenced For Manslaughter",
                 "Arizona Supreme Court Issues Near-Total Ban On Abortions",
                 "Trump Hush Money Trial To Move Ahead Despite Bid To Delay",
                 "Russia Foreign Minister Visits Beijing"]
    client, db, collection = connect_to_mongodb(collection_to_open = 'trendingTopics')
    for topic in topics:
        doc = collection.find_one({'topic': topic})
        doc_copy = collection.find_one({'topic': topic})
        article_id = doc['articles'][0]['id']
        for question in doc['articles'][0]['questions']:
            #print(question)
            for article_pol_prob in doc['articles'][0]['questions'][question]:
                article = doc_copy['articles'][0]['questions'][question][article_pol_prob]
                #print(article)
                id, parent = save_generated_article_to_DB(title = article['title'], body = article['body'], parent = article_id, query = question)
                article['id'] = id
                article['parent'] = parent
                doc_copy['articles'][0]['questions'][question][article_pol_prob] = article
                #print(doc_copy['articles'][0]['questions'][question][article_pol_prob])
        #print(doc, doc_copy)
        result = collection.replace_one(doc, doc_copy) 
        print(result.matched_count)

def manual_polish_4(): # removed nested questions
    topics = ["U.S. Sends Ukraine Weapons Seized From Iran"]
    # topics = ["U.S. Sends Ukraine Weapons Seized From Iran",
    #             "Marjorie Taylor Greene Keeps Up Pressure on Speaker Johnson",
    #             "Parents of Michigan School Shooter Sentenced For Manslaughter",
    #             "Arizona Supreme Court Issues Near-Total Ban On Abortions",
    #             "Trump Hush Money Trial To Move Ahead Despite Bid To Delay",
    #             "Russia Foreign Minister Visits Beijing"]
    client, db, collection = connect_to_mongodb(collection_to_open = 'trendingTopics')
    for topic in topics:
        doc = collection.find_one({'topic': topic})
        doc_copy = collection.find_one({'topic': topic})
        article_id = doc['articles'][0]['id']
        for question in doc['articles'][0]['questions']:
            for nested_question in doc['articles'][0]['questions'][question]:
                articles = doc['articles'][0]['questions'][question][nested_question]
            doc_copy['articles'][0]['questions'][question] = articles
        collection.replace_one(doc, doc_copy)

if __name__ == '__main__':
    main()
    manual_polish_2()
    manual_polish_3rd()