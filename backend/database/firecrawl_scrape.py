# Install with pip install firecrawl-py
from firecrawl import FirecrawlApp
from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime
from dotenv import load_dotenv
from tqdm import tqdm
import os
import sys
from dateutil import parser
from test.env import *


class ExtractSchema(BaseModel):
        article_text: str
        article_title: str
        # article_publish_date: str = 'N/A'
        # article_author: str = 'N/A'

def create_article_doc(firecrawl_output,event_id,topic_title,url,query_datetime):
     article_doc = {
        'article_publish_date': query_datetime,
        'event_id':event_id,
            'topic_title': topic_title,
            'news_title': firecrawl_output['article_title'],
            'news_url': url,
            'text': firecrawl_output['article_text']
     }
     return article_doc

app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)

def firecrawl_scrape(urls, output_folder="output", query=""):
    """
    Extract article data from a list of URLs using Firecrawl.
    
    Args:
        urls (list): List of URLs to extract data from
        output_folder (str): Folder to save the extracted articles
        query (str): The search query used to find these articles (for file naming)
        
    Returns:
        list: List of dictionaries containing extracted article data
    """
    data = []
    checked = set()
    fail_count = 0
    success_count = 0
    
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    for i in tqdm(range(len(urls)), desc="Extracting articles"):
        url = urls[i]
        if url in checked:
            continue
        checked.add(url)
        
        try:
            # Extract article data using Firecrawl
            output = app.extract([url], {
                'prompt': '',
                'schema': ExtractSchema.model_json_schema(),
            })['data']
            
            # Check if extraction was successful
            if not output['article_text']:
                raise Exception("No article text extracted")
            
            # Create article document
            article_data = {
                'news_title': output['article_title'],
                'news_url': url,
                'text': output['article_text']
            }
            
            # Save to text file
            safe_query = "".join(x for x in query if x.isalnum() or x.isspace()).replace(" ", "_")[:50]
            url_id = str(abs(hash(url)) % 10000)
            filename = f"{safe_query}_{url_id}.txt" if safe_query else f"article_{url_id}.txt"
            filepath = os.path.join(output_folder, filename)
            
            with open(filepath, "w", encoding="utf-8") as file:
                file.write(f"Title: {article_data['news_title']}\n")
                file.write(f"Source: {article_data['news_url']}\n\n")
                file.write(article_data['text'])
            
            # Add file path to the article data
            article_data['file_path'] = filepath
            
            # Add to results
            data.append(article_data)
            success_count += 1
            
        except Exception as e:
            fail_count += 1
            print(f"Failed to extract from {url}: {str(e) if str(e) else 'Unknown error'}")
            continue
    
    print(f"Extraction complete. Successfully extracted {success_count} articles.")
    if fail_count:
        print(f"Extraction failed for {fail_count} articles.")
    
    return data

def test_extraction(url):
    """
    Simple test function to extract content from a URL and print the results.
    """
    print(f"Testing extraction on: {url}")
    
    try:
        # Extract article data using Firecrawl
        output = app.extract([url], {
            'prompt': '',
            'schema': ExtractSchema.model_json_schema(),
        })['data']
        
        # Print results
        print("\nExtraction successful!")
        print(f"Title: {output['article_title']}")
        print(f"Text length: {len(output['article_text'])} characters")
        print(f"Text preview: {output['article_text'][:150]}...")
        
    except Exception as e:
        print(f"Extraction failed: {str(e)}")


# Simple test main function
if __name__ == "__main__":
    # Test URL - replace with any article URL you want to test
    test_url = "https://nlihc.org/news/nlihc-releases-gap-2025-shortage-affordable-homes"
    test_extraction(test_url)
