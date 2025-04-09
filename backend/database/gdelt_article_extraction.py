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
import os  # Added for folder creation

class GDELTNewsRetriever:
    def __init__(self, collection_name='GDELT_test2', folder="articles"):
        self.collection_name = collection_name
        self.folder = folder
        # Create folder if it doesn't exist
        os.makedirs(folder, exist_ok=True)
        self.client, self.db, self.collection = connect_to_mongodb(collection_name)
        self.gdelt = GdeltDoc()

    def save_text_to_file(self, text, topic_title, url, unique_id):
        """
        Save extracted text to a file.
        
        Args:
            text (str): The text to save
            topic_title (str): The topic title (used for file naming)
            url (str): The source URL (used for file naming)
            unique_id (str): A unique identifier for the article
        
        Returns:
            str: The path to the saved file
        """
        # Create a safe filename from the topic title
        safe_topic = "".join(x for x in topic_title if x.isalnum() or x.isspace()).rstrip()
        safe_topic = safe_topic.replace(" ", "_")[:50]  # Limit length
        
        # Create a unique filename using the unique_id and a hash of the URL
        url_hash = str(abs(hash(url)) % 10000)
        filename = f"{safe_topic}_{unique_id}_{url_hash}.txt"
        
        filepath = os.path.join(self.folder, filename)
        
        # Save text to file
        with open(filepath, "w", encoding="utf-8") as file:
            file.write(f"Source: {url}\n\n")
            file.write(text)
        
        return filepath

    def fetch_gdelt_articles(self, events, max_articles_per_event=10):
        perplexity_urls = []
        for event in events:
            # Use just the first two important words from the title
            # Common English stop words including prepositions
            stop_words = {'a', 'an', 'and', 'at', 'by', 'for', 'from', 'in', 'of', 'on', 
                         'or', 'the', 'to', 'with', 'near', 'at', 'into', 'during', 'including',
                         'until', 'against', 'among', 'throughout', 'despite', 'towards', 'upon'}

            # Split title, remove punctuation, convert to lowercase, and filter out stop words
            search_terms = [event['topic_title']]  # Use the topic title as search term
            
            # Get current datetime for the query
            event_datetime = datetime.now()
            
            print(f"Searching for article urls from query: {event['topic_title']}...")
            # Query perplexity for article urls
            perplexity_urls = perplexity_article_query(f"{event['topic_title']}")
            
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
                # No GDELT search for now
                article_urls = perplexity_urls
                #SEARCH FOR ARTICLES
                articles = self.gdelt.article_search(filters)
                print(f"Found {len(perplexity_urls)+len(articles)} articles.\nExtracting article text (this may take a few minutes)...")
                article_urls = articles['url'].tolist()
                for p_url in perplexity_urls:
                    article_urls.append(p_url)
            
                if article_urls:
                    mongo_articles = []
                    unique_id = self.generate_event_id(event['topic_title'])
                    
                    # Extracts additional article information and article text from the perplexity urls
                    print(f"Extracting text from {len(article_urls)} articles...")
                    firecrawl_results = firecrawl_scrape(article_urls, unique_id, event['topic_title'], event_datetime)
                    
                    # Debug the structure of firecrawl_results
                    print(f"Got {len(firecrawl_results)} results from firecrawl_scrape")
                    
                    # Save each article's text to a file
                    saved_count = 0
                    for i, result in enumerate(firecrawl_results):
                        # Print keys to debug
                        print(f"Result {i+1} keys: {result.keys()}")
                        
                        if 'article_text' in result and result['article_text']:
                            try:
                                filepath = self.save_text_to_file(
                                    result['article_text'], 
                                    event['topic_title'], 
                                    result['news_url'], 
                                    unique_id
                                )
                                result['text_filepath'] = filepath
                                print(f"Saved article text to {filepath}")
                                saved_count += 1
                            except Exception as save_error:
                                print(f"Error saving article to file: {save_error}")
                        else:
                            print(f"Article {i+1} has no article_text field or it's empty")
                    
                    print(f"Saved {saved_count} articles to folder: {self.folder}")
                    mongo_articles += firecrawl_results

                    # Try to insert the article data into the collection
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
    retriever = None
    try:
        argparser = argparse.ArgumentParser(description='Get article sources from Perplexity API and extract text')
        argparser.add_argument('--query', type=str, help='The query to search for')
        argparser.add_argument('--collection', type=str, help='Collection to save extracted article data')
        argparser.add_argument('--folder', type=str, default='articles', help='Folder to save extracted text files')
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

        events = [{
            "topic_title": query
        }]
        
        retriever = GDELTNewsRetriever(collection_name=collection, folder=args.folder)
        retriever.fetch_gdelt_articles(events)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if retriever:
            retriever.close_connection()

if __name__ == "__main__":
    main()