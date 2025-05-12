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
import requests
import wikipediaapi
from bs4 import BeautifulSoup


class ExtractSchema(BaseModel):
        article_text: str
        article_title: str
        article_publish_date: str = 'N/A'
        article_author: str = 'N/A'

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

def extract_full_wikipedia_article(url):
    """Extract complete text from a Wikipedia article"""
    try:
        # Extract the article title from the URL properly
        if '/wiki/' in url:
            # Handle URL encoded characters
            title = url.split("/wiki/")[-1].replace("_", " ")
            # Handle special URL encoding
            title = requests.utils.unquote(title)
            
            # If there's a section anchor, remove it
            if '#' in title:
                title = title.split('#')[0]
                
            print(f"Extracted Wikipedia title: {title}")
            
            # Use Wikipedia API to get full content
            wiki_wiki = wikipediaapi.Wikipedia(
                'NewsProcessor (yourname@example.com)',  # Add a user agent
                'en'
            )
            page = wiki_wiki.page(title)
            
            if page.exists():
                # Build a structured version with sections
                full_text = f"# {page.title}\n\n"
                
                # Add summary
                full_text += f"{page.summary}\n\n"
                
                # Add each section and its content
                for section in page.sections:
                    full_text += _process_wiki_section(section, 2)
                
                article_data = {
                    'news_title': page.title,
                    'news_url': url,
                    'text': full_text,
                    'extraction_method': 'Wikipedia API'
                }
                return article_data
            else:
                print(f"Wikipedia page not found for title: {title}")
        return None
    except Exception as e:
        print(f"Error extracting Wikipedia article: {str(e)}")
        return None

def _process_wiki_section(section, level=2):
    """Helper function to process Wikipedia sections recursively"""
    # Create section heading with appropriate number of #
    section_text = f"{'#' * level} {section.title}\n\n"
    
    # Add section content
    if section.text:
        section_text += f"{section.text}\n\n"
    
    # Process subsections recursively
    for subsection in section.sections:
        section_text += _process_wiki_section(subsection, level + 1)
    
    return section_text

def firecrawl_extract_only(url):
    """
    Extract article data from a URL using multiple extraction methods in order of preference.
    
    Args:
        url (str): URL to extract data from
        
    Returns:
        dict or None: Dictionary with extracted article data, or None if extraction failed
    """
    print(f"Extracting content from: {url}")
    
    # Try Wikipedia extractor first for Wikipedia URLs
    if 'wikipedia.org/wiki/' in url.lower():
        print("Using Wikipedia API extractor...")
        wiki_data = extract_full_wikipedia_article(url)
        if wiki_data and len(wiki_data['text']) > 200:
            print(f"Wikipedia extraction successful: {len(wiki_data['text'])} characters")
            return wiki_data
        else:
            print("Wikipedia API extraction failed or returned insufficient content")
    
    # Try Firecrawl next
    try:
        print("Using Firecrawl extractor...")
        # Create an appropriate prompt based on the source type
        prompt = "Extract the complete text of this article, including all paragraphs, sections, and important information. Be thorough and comprehensive."
        
        # Extract article data using Firecrawl
        output = app.extract([url], {
            'prompt': prompt,
            'schema': ExtractSchema.model_json_schema(),
            'max_tokens': 32768
        })['data']
        
        # Check if extraction was successful
        if output['article_text'] and len(output['article_text'].strip()) > 200:
            article_data = {
                'news_title': output['article_title'],
                'news_url': url,
                'text': output['article_text'],
                'extraction_method': 'Firecrawl'
            }
            print(f"Firecrawl extraction successful: {len(article_data['text'])} characters")
            return article_data
        else:
            print("Firecrawl returned insufficient content, trying BeautifulSoup")
            
    except Exception as e:
        print(f"Firecrawl extraction failed: {str(e)}")
    
    # Try BeautifulSoup as a last resort
    print("Using BeautifulSoup extractor...")
    bs_data = extract_text_with_beautifulsoup(url)
    if bs_data:
        print(f"BeautifulSoup extraction successful: {len(bs_data['text'])} characters")
        return bs_data
    
    print("All extraction methods failed")
    return None

def extract_text_with_beautifulsoup(url):
    """More robust text extraction using BeautifulSoup"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'iframe']):
            element.decompose()
        
        # Extract title
        title = soup.title.string if soup.title else "No title found"
        
        # Extract main content based on common article containers
        main_content = None
        for container in ['article', 'main', '.content', '.post', '.entry', '#content', '.article-content']:
            if main_content:
                break
                
            if container.startswith('.') or container.startswith('#'):
                main_content = soup.select_one(container)
            else:
                main_content = soup.find(container)
        
        # If no specific container found, use body as fallback
        if not main_content:
            main_content = soup.body
        
        # Extract text, preserving some structure
        text = ""
        for element in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li']):
            if element.name.startswith('h'):
                level = int(element.name[1])
                text += f"{'#' * level} {element.get_text().strip()}\n\n"
            else:
                text += f"{element.get_text().strip()}\n\n"
        
        # Clean up the text
        text = text.replace('\n\n\n', '\n\n').strip()
        
        if len(text) < 100:  # If text is too short, try more aggressive extraction
            text = '\n\n'.join([p.get_text().strip() for p in soup.find_all('p') if len(p.get_text().strip()) > 20])
        
        article_data = {
            'news_title': title,
            'news_url': url,
            'text': text,
            'extraction_method': 'BeautifulSoup'
        }
        
        return article_data if len(text) > 200 else None
        
    except Exception as e:
        print(f"BeautifulSoup extraction failed for {url}: {str(e)}")
        return None

def test_all_extractors(url):
    """Test all extraction methods and print results"""
    print(f"\n=== TESTING EXTRACTION ON: {url} ===\n")
    
    if 'wikipedia.org/wiki/' in url.lower():
        print("\n--- TESTING WIKIPEDIA EXTRACTOR ---")
        wiki_data = extract_full_wikipedia_article(url)
        if wiki_data:
            print(f"Title: {wiki_data['news_title']}")
            print(f"Text length: {len(wiki_data['text'])} characters")
            print(f"Text preview: {wiki_data['text'][:150]}...\n")
        else:
            print("Wikipedia extraction failed\n")
    
    print("\n--- TESTING FIRECRAWL EXTRACTOR ---")
    try:
        output = app.extract([url], {
            'prompt': "Extract the complete text of this article",
            'schema': ExtractSchema.model_json_schema(),
        })['data']
        print(f"Title: {output['article_title']}")
        print(f"Text length: {len(output['article_text'])} characters")
        print(f"Text preview: {output['article_text'][:150]}...\n")
    except Exception as e:
        print(f"Firecrawl extraction failed: {str(e)}\n")
    
    print("\n--- TESTING BEAUTIFULSOUP EXTRACTOR ---")
    bs_data = extract_text_with_beautifulsoup(url)
    if bs_data:
        print(f"Title: {bs_data['news_title']}")
        print(f"Text length: {len(bs_data['text'])} characters")
        print(f"Text preview: {bs_data['text'][:150]}...\n")
    else:
        print("BeautifulSoup extraction failed\n")
    
    print("\n--- TESTING COMBINED EXTRACTOR ---")
    result = firecrawl_extract_only(url)
    if result:
        print(f"Method chosen: {result['extraction_method']}")
        print(f"Title: {result['news_title']}")
        print(f"Text length: {len(result['text'])} characters")
        print(f"Text preview: {result['text'][:150]}...\n")
    else:
        print("All extraction methods failed\n")


# Add this to the main function in firecrawl_scrape.py to test
if __name__ == "__main__":
    # Specific test for the problematic URL
    problem_url = "https://en.wikipedia.org/wiki/Indo-Pakistani_wars_and_conflicts"
    print("\n\nTESTING PROBLEMATIC URL:")
    result = firecrawl_extract_only(problem_url)
    
    if result:
        print(f"Extraction method: {result.get('extraction_method')}")
        print(f"Title: {result.get('news_title')}")
        print(f"Text length: {len(result.get('text', ''))} characters")
        print(f"Text preview: {result.get('text', '')[:200]}...")
        
        # Test writing to file directly
        with open("test_extraction.txt", "w", encoding="utf-8") as f:
            f.write(f"Title: {result.get('news_title')}\n")
            f.write(f"Source: {problem_url}\n\n")
            f.write(result.get('text', ''))
        
        # Check the written file
        file_size = os.path.getsize("test_extraction.txt")
        print(f"File saved with {file_size} bytes")