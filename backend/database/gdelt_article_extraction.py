from gdeltdoc import GdeltDoc, Filters, repeat
from datetime import datetime, timedelta
import pandas as pd
from database_utils import connect_to_mongodb
from extract_article_text import extract_text_from_url
from datetime import datetime
from perplexity_article_query import perplexity_article_query
from firecrawl_scrape import firecrawl_scrape
import argparse
import sys
from dateutil import parser

class GDELTNewsRetriever:
    def __init__(self, collection_name='GDELT_test2'):
        self.collection_name = collection_name
        self.client, self.db, self.collection = connect_to_mongodb(collection_name)
        self.gdelt = GdeltDoc()

    def fetch_gdelt_articles(self, events, max_articles_per_event=10):
        perplexity_urls = []
        for event in events:
            # Use just the first two important words from the title
            # Common English stop words including prepositions
            stop_words = {'a', 'an', 'and', 'at', 'by', 'for', 'from', 'in', 'of', 'on', 
                         'or', 'the', 'to', 'with', 'near', 'at', 'into', 'during', 'including',
                         'until', 'against', 'among', 'throughout', 'despite', 'towards', 'upon'}

            # Split title, remove punctuation, convert to lowercase, and filter out stop words
            search_terms = [event['topic_title']]
            #search_query = ' '.join(search_terms)
            
            if type(event['published_datetime']) == str:
                event_datetime = datetime.fromisoformat(event['published_datetime'])
            else:
                event_datetime = event['published_datetime']
            start_date = (event_datetime - timedelta(days=3)).strftime('%Y-%m-%d')
            end_date = (event_datetime + timedelta(days=3)).strftime('%Y-%m-%d')

            domains = [
                'straitstimes.com', 'channelnewsasia.com', 'todayonline.com', 'nytimes.com', 'cnn.com', 'reuters.com', 'bloomberg.com'
            ]

            filters = Filters(
                keyword=search_terms,
                start_date=start_date,
                end_date=end_date,
                num_records=max_articles_per_event,
                domain=domains,
                country='US'
                # language=['en']
                #repeat=repeat(1, "Singapore")
            )
            print(f'Searching for article urls from query: {event['topic_title']}...')
            #Query perplexity for article urls
            perplexity_urls = perplexity_article_query(f'{event['topic_title']}, {event['published_datetime']}')
            # perplexity_urls = []

            try:
                #SEARCH FOR ARTICLES
                articles = self.gdelt.article_search(filters)
                print(f"Found {len(perplexity_urls)+len(articles)} articles.\nExtracting article text (this may take a few minutes)...")
                article_urls = articles['url'].tolist()
                for p_url in perplexity_urls:
                    article_urls.append(p_url)
            
                if article_urls:
                    mongo_articles = []
                    unique_id = self.generate_event_id(event['topic_title'])
            
                    #Extracts additional article information and article text from the perplexity urls          
                    mongo_articles=firecrawl_scrape(article_urls,unique_id,event['topic_title'],event_datetime)


                    #Try to insert the article data into the collection
                    if mongo_articles:
                        try:
                            self.collection.insert_many(mongo_articles, ordered=False)
                            print(f"Inserted {len(mongo_articles)} articles into collection {self.collection_name} for topic: {event['topic_title']}")
                        except Exception as e:
                            print(f"Some articles may be duplicates. Error: {e}")

            except Exception as e:
                print(f"Error processing {event['topic_title']}: {e}")

    #Generates an id for the given search term using the time to make it unique
    #Will change later
    def generate_event_id(self,topic_title):
        dt=datetime.now()
        time_id = ""
        for val in str(dt):
            if val.isnumeric(): 
                time_id += val 
        search_id = str(ord(topic_title[0]))
        #Max length for an int in mongodb is 8bytes
        return int(time_id[0:14])
    
    def export_to_csv(self, output_file='gdelt_news_articles.csv'):
        # Specify only the fields you want to retrieve
        fields = {
            'topic_title': 1,
            'news_title': 1,
            'news_url': 1,
            'source_country': 1,
            '_id': 0  # Explicitly exclude _id
        }
        df = pd.DataFrame(list(self.collection.find({}, fields)))
        df.to_csv(output_file, index=False)
        print(f"Exported articles to {output_file}")

    def export_to_db(self,mongo_collection=None):
        if not mongo_collection:
            mongo_collection = self.collection

        """
        fields = {
            'topic_title': 1,
            'news_title': 1,
            'news_url': 1,
            'source_country': 1,
            '_id': 0  # Explicitly exclude _id
        }"""
        #collect article text (separate function?)

        """
        Send to the collection with:
        topic_title
        news_title
        source_country
        news_url?
        article_text
        seen_date (IS SEEN_DATE ARTICLE PUBLISHED DATE)?

        """
        #save to mongodb
                    # mongo_articles = []
                    # for _, article in articles.iterrows():
                    #     if article.get('url'):
                    #         article_doc = {
                    #             'topic_title': event['topic_title'],
                    #             'original_event_datetime': event['published_datetime'],
                    #             'news_title': article.get('title', ''),
                    #             'news_url': article.get('url', ''),
                    #             'domain': article.get('domain', ''),
                    #             'language': article.get('language', ''),
                    #             'source_country': article.get('sourcecountry', ''),
                    #             'seen_date': article.get('seendate', '')
                    #         }
                    #         mongo_articles.append(article_doc)

                    # if mongo_articles:
                    #     try:
                    #         self.collection.insert_many(mongo_articles, ordered=False)
                    #         print(f"Retrieved {len(mongo_articles)} articles for: {event['topic_title']}")
                    #     except Exception as e:
                    #         print(f"Some articles may be duplicates. Error: {e}")
        return
    def close_connection(self):
        if hasattr(self, 'client') and self.client:
            self.client.close()

def main():
    # events = [
    #     # {
    #     #     "topic_title": "CrowdStrike Outage Singapore",
    #     #     "published_datetime": "2024-07-19T16:10:00+08:00",
    #     # },
    #     # {
    #     #     "topic_title": "Soil Erosion Causes Water Overflow at Bukit Batok Town Park",
    #     #     "published_datetime": "2021-07-19T12:51:00+08:00",
    #     # },
    #     {
    #         "topic_title": "Los Angeles forest fires",
    #         "published_datetime": "2025-01-14T02:20:00+08:00",
    #     },
    #     # {
    #     #     "topic_title": "Oil Tanker Collision near Singapore",
    #     #     "published_datetime": "2024-07-20T02:20:00+08:00",
    #     # },
    #     # {
    #     #     "topic_title": "Singapore Airlines Severe Turbulence",
    #     #     "published_datetime": "2024-05-30T00:00:00+00:00",
    #     # },
    #     # {
    #     #     "topic_title": "Fire in Singapore Data Centre",
    #     #     "published_datetime": "2024-09-10T23:47:00+08:00",
    #     # }
           
    # ]

    retriever = None
    try:
        argparser = argparse.ArgumentParser(description='Get article sources from Perplexity API and extract text')
        argparser.add_argument('--query', type=str, help='The query to search for')
        argparser.add_argument('--date', type=str, default=datetime.now(), help='Approximate article publish date')
        argparser.add_argument('--collection', type=str, help='Collection to save extracted article data')
        args = argparser.parse_args()
        
        if args.query:
            query = args.query
        else:
            # If no query argument provided, prompt for input
            query = input("Enter your query for articles: ")
        
        if args.collection:
            collection = args.collection
        else:
            # If no collection argument provided, prompt for input
            collection = input("Enter the collection name: ")

        if not collection:
            print("No collection provided. Exiting.")
            sys.exit(1)
        try:
            date = parser.parse(args.date)
        except:
            print("Invalid date format. Please enter in the format YYYY-MM-DD. Exiting.")
            sys.exit(1)


        events = [{
            "topic_title": query,
            "published_datetime": date,
        }]
        retriever = GDELTNewsRetriever(collection_name=collection)
        retriever.fetch_gdelt_articles(events)
        # retriever.export_to_csv()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if retriever:
            retriever.close_connection()

if __name__ == "__main__":
    main()