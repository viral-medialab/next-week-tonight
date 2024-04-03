from generate_database import *
from database_utils import *
'''
This script will serve to:

    - Populate the trending topics database with relevant, trending news
    - (Maybe) Clean user activity from over 7 days ago in the database

'''

if __name__ == '__main__':
    clear_trending_topics()
    populate_database_by_recent_news(num_articles_to_store = 100, num_topics = 10)
