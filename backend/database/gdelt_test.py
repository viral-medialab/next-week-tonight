

from gdeltdoc import GdeltDoc, Filters, repeat
from datetime import datetime, timedelta
import pandas as pd
from database_utils import connect_to_mongodb

class GDELTNewsRetriever:
    def __init__(self, collection_name='GDELT'):
        self.client, self.db, self.collection = connect_to_mongodb(collection_name)
        self.gdelt = GdeltDoc()

    def fetch_gdelt_articles(self, events, max_articles_per_event=10):
        for event in events:
            # Use just the first two important words from the title
            # Common English stop words including prepositions
            stop_words = {'a', 'an', 'and', 'at', 'by', 'for', 'from', 'in', 'of', 'on', 
                         'or', 'the', 'to', 'with', 'near', 'at', 'into', 'during', 'including',
                         'until', 'against', 'among', 'throughout', 'despite', 'towards', 'upon'}

            # Split title, remove punctuation, convert to lowercase, and filter out stop words
            search_terms = "Los Angeles wildfire"
            print(search_terms)
            #search_query = ' '.join(search_terms)
            
            event_datetime = datetime.fromisoformat(event['published_datetime'])
            start_date = (event_datetime - timedelta(days=1)).strftime('%Y-%m-%d')
            end_date = (event_datetime + timedelta(days=5)).strftime('%Y-%m-%d')

            domains = [
                'nytimes.com', 'cnn.com', 'reuters.com', 'bloomberg.com', 'bbc.com'
            ]

            filters = Filters(
                keyword=search_terms,
                start_date=start_date,
                end_date=end_date,
                num_records=max_articles_per_event,
                domain=domains,
                country=['US']
                #language=['en']
                #repeat=repeat(1, "Singapore")
            )

            try:
                articles = self.gdelt.article_search(filters)
                
                print(articles)
                if not articles.empty:
                    #save to csv 
                    if not articles.empty:
                        # Create filename using topic title (sanitized) and date
                        safe_title = "".join(x for x in event['topic_title'] if x.isalnum() or x.isspace()).rstrip()
                        date_str = datetime.fromisoformat(event['published_datetime']).strftime('%Y%m%d')
                        filename = f"articles_{safe_title}_{date_str}.csv"
                        
                        # Save to CSV
                        articles.to_csv(f'{filename}', index=False)
                        print(f"Saved {len(articles)} articles to {filename}")

                    #save to mongodb
                    mongo_articles = []
                    for _, article in articles.iterrows():
                        if article.get('url'):
                            article_doc = {
                                'topic_title': event['topic_title'],
                                'original_event_datetime': event['published_datetime'],
                                'news_title': article.get('title', ''),
                                'news_url': article.get('url', ''),
                                'domain': article.get('domain', ''),
                                'language': article.get('language', ''),
                                'source_country': article.get('sourcecountry', ''),
                                'seen_date': article.get('seendate', '')
                            }
                            mongo_articles.append(article_doc)

                    if mongo_articles:
                        try:
                            self.collection.insert_many(mongo_articles, ordered=False)
                            print(f"Retrieved {len(mongo_articles)} articles for: {event['topic_title']}")
                        except Exception as e:
                            print(f"Some articles may be duplicates. Error: {e}")

            except Exception as e:
                print(f"Error processing {event['topic_title']}: {e}")

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

    def close_connection(self):
        if hasattr(self, 'client') and self.client:
            self.client.close()

def main():
    events = [
        # {
        #     "topic_title": "CrowdStrike Outage Singapore",
        #     "published_datetime": "2024-07-19T16:10:00+08:00",
        # },
        {
            "topic_title": "Los Angeles wildfire",
            "published_datetime": "2025-01-07T12:51:00+08:00",
        },
        # {
        #     "topic_title": "Oil Tanker Collision near Singapore",
        #     "published_datetime": "2024-07-20T02:20:00+08:00",
        # },
        # {
        #     "topic_title": "Singapore Airlines Severe Turbulence",
        #     "published_datetime": "2024-05-30T00:00:00+00:00",
        # },
        # {
        #     "topic_title": "Fire in Singapore Data Centre",
        #     "published_datetime": "2024-09-10T23:47:00+08:00",
        # }
           
    ]

    retriever = None
    try:
        retriever = GDELTNewsRetriever()
        retriever.fetch_gdelt_articles(events)
        retriever.export_to_csv()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if retriever:
            retriever.close_connection()

if __name__ == "__main__":
    main()