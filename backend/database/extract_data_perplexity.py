import requests
from bs4 import BeautifulSoup
import re
import json
import time
import argparse
import os
from urllib.parse import quote_plus
import sys
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd
from tqdm import tqdm
from test.env import *
from database.extract_raw_text import extract_text_from_url, perplexity_text_extractor, BSoup_text_extractor

# Load environment variables from .env file
load_dotenv()

def get_perplexity_sources(query):
    """
    Get sources from Perplexity API for a given query, excluding YouTube videos and PDFs.
    
    Args:
        query (str): The user query to search with Perplexity
        
    Returns:
        list: A list of article URLs that can be used for data extraction
    """
    # Use the PERPLEXITY_API_KEY imported from test.env
    api_key = PERPLEXITY_API_KEY
    
    if not api_key:
        print("Error: PERPLEXITY_API_KEY not found in environment variables.")
        print("Please add your Perplexity API key to your vars.env file.")
        sys.exit(1)
    
    # Initialize the OpenAI client with Perplexity's base URL
    client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
    
    # Create a message with a prompt that asks for sources and avoids PDFs and videos
    messages = [
        {"role": "system", "content": "You are a helpful assistant focused on providing comprehensive news coverage. Your goal is to find and share as many high-quality news sources as possible for each query, with an emphasis on diversity across time periods. Include both historical archives and the latest news stories to give a complete picture. Focus only on reputable news sites, academic sources, and established media outlets. Do not include YouTube videos, PDFs, or social media. ALWAYS end your response with a clearly labeled 'Sources:' section containing a numbered list (1., 2., etc.) of ALL source URLs used, with each URL on its own line."},
        {"role": "user", "content": f"Please find and provide as many high-quality news sources as possible about this topic: {query}. I want extensive coverage from both historical archives and recent news stories. Include sources from major news outlets, academic institutions, and reputable media organizations spanning different time periods. Your response MUST end with a clearly labeled 'Sources:' section containing a numbered list of ALL source URLs used. Focus on finding diverse perspectives and coverage across different years and events. Do not include YouTube, PDFs, or social media sources."}
    ]
    
    try:
        print(f"Sending request to Perplexity API for query: {query}")
        
        # Make the API call
        response = client.chat.completions.create(
            model="sonar-pro",
            messages=messages,
        )
        
        # Extract the response text
        response_text = response.choices[0].message.content
        
        # Debug the raw response
        print("\n=== PERPLEXITY RAW RESPONSE ===")
        print(response_text)
        print("================================\n")
        
        # First attempt to find a sources section
        sources_section_patterns = [
            r'Sources:[\s\n]+((?:\d+\.\s+https?://[^\s\n]+[\s\n]*)+)',  # Original pattern
            r'Sources:[\s\n]+((?:\[\d+\]:\s*https?://[^\s\n]+[\s\n]*)+)',  # [1]: http://... format
            r'References:[\s\n]+((?:\d+\.\s+https?://[^\s\n]+[\s\n]*)+)',  # "References" instead of "Sources"
            r'Bibliography:[\s\n]+((?:\d+\.\s+https?://[^\s\n]+[\s\n]*)+)'  # "Bibliography" instead of "Sources"
        ]

        filtered_sources = []
        for pattern in sources_section_patterns:
            sources_match = re.search(pattern, response_text, re.IGNORECASE)
            if sources_match:
                # Extract the numbered list of sources
                sources_list = sources_match.group(1)
                # Extract each numbered URL
                url_patterns = [
                    r'\d+\.\s+(https?://[^\s\n]+)',  # 1. http://... format
                    r'\[\d+\]:\s*(https?://[^\s\n]+)'  # [1]: http://... format
                ]
                for url_pattern in url_patterns:
                    sources = re.findall(url_pattern, sources_list)
                    
                    # Filter out YouTube videos and PDFs
                    for source in sources:
                        # Clean up the URL (remove trailing punctuation or formatting)
                        clean_source = source.rstrip('.,;:"\'')
                        
                        # Skip YouTube videos
                        if 'youtube.com' in clean_source or 'youtu.be' in clean_source:
                            continue
                        # Skip PDFs
                        if clean_source.lower().endswith('.pdf'):
                            continue
                        # Add valid article sources
                        filtered_sources.append(clean_source)
        else:
            # If no sources section found, look for footnote references
            footnote_pattern = r'\[\d+\]\s*(https?://[^\s\n]+)'
            footnote_sources = re.findall(footnote_pattern, response_text)
            for source in footnote_sources:
                # Clean up the URL
                clean_source = source.rstrip('.,;:"\'')
                # Skip YouTube videos and PDFs
                if 'youtube.com' in clean_source or 'youtu.be' in clean_source or clean_source.lower().endswith('.pdf'):
                    continue
                # Add valid article sources
                filtered_sources.append(clean_source)
        
        # Remove duplicates
        filtered_sources = list(set(filtered_sources))
        
        return filtered_sources, response_text
    
    except Exception as e:
        print(f"Error making request to Perplexity API: {e}")
        return [], ""


def save_text_to_file(text, query, url, folder="graphrag/ragtest/input", is_perplexity_response=False):
    """
    Save extracted text to a file.
    
    Args:
        text (str): The text to save
        query (str): The original query (used for file naming)
        url (str): The source URL (used for file naming)
        folder (str): The folder to save the file in
        is_perplexity_response (bool): Whether this is the main Perplexity response
    
    Returns:
        str: The path to the saved file
    """
    # Create folder if it doesn't exist
    os.makedirs(folder, exist_ok=True)
    
    # Create a safe filename from the query and URL
    safe_query = "".join(x for x in query if x.isalnum() or x.isspace()).rstrip()
    safe_query = safe_query.replace(" ", "_")[:50]  # Limit length
    
    # Get a unique identifier from the URL or use "response" for the main perplexity response
    if is_perplexity_response:
        filename = f"{safe_query}_perplexity_response.txt"
    else:
        url_id = str(abs(hash(url)) % 10000)
        filename = f"{safe_query}_{url_id}.txt"
    
    filepath = os.path.join(folder, filename)
    
    # Save text to file
    with open(filepath, "w", encoding="utf-8") as file:
        if not is_perplexity_response:
            file.write(f"Source: {url}\n\n")
        file.write(text)
    
    return filepath


def main():
    """
    Main function that takes user input, gets sources from Perplexity,
    extracts text from those sources, and saves the text to files.
    """
    parser = argparse.ArgumentParser(description='Get article sources from Perplexity API and extract text')
    parser.add_argument('--query', type=str, help='The query to search for')
    parser.add_argument('--folder', type=str, default='input', help='Folder to save extracted text files')
    args = parser.parse_args()
    
    if args.query:
        query = args.query
    else:
        # If no query argument provided, prompt for input
        query = input("Enter your query for Perplexity: ")
    
    if not query:
        print("No query provided. Exiting.")
        sys.exit(1)
    
    # Get sources from Perplexity
    sources, perplexity_response = get_perplexity_sources(query)
    
    # Save the Perplexity response
    if perplexity_response:
        filepath = save_text_to_file(perplexity_response, query, "", folder=args.folder, is_perplexity_response=True)
        print(f"Saved Perplexity's response to {filepath}")
    
    if sources:
        print(f"\nFound {len(sources)} sources:")
        for i, source in enumerate(sources, 1):
            print(f"{i}. {source}")
        
        # Extract and save text from each source
        print("\nExtracting text from sources...")
        successful_extractions = 0
        
        # Create a DataFrame to pass to extract_text_from_url
        sources_df = pd.DataFrame({'url': sources})
        
        # Extract text using the functions from extract_raw_text.py
        article_texts = extract_text_from_url(sources_df)
        
        # Save each extracted text to a file
        for i, (source, text) in enumerate(zip(sources, article_texts)):
            # Check if extraction was successful
            if isinstance(text, tuple):  # If text is a tuple (score, content) from perplexity_text_extractor
                score, content = text
                if score.isnumeric() and int(score) >= 2:
                    text_to_save = content
                    extraction_method = f"Perplexity (score: {score})"
                    successful = True
                else:
                    # Text was not good enough, but was already handled by extract_text_from_url
                    text_to_save = content
                    extraction_method = f"Perplexity with low score ({score}), fallback to BeautifulSoup"
                    successful = True
            elif text != "Extraction Failed":
                text_to_save = text
                extraction_method = "BeautifulSoup"
                successful = True
            else:
                text_to_save = "Could not extract text from this source."
                extraction_method = "Failed"
                successful = False
            
            # Save the text (even if failed, to keep record)
            filepath = save_text_to_file(text_to_save, query, source, folder=args.folder)
            
            if successful:
                successful_extractions += 1
                print(f"✓ Extracted text from {source} using {extraction_method} and saved to {filepath}")
            else:
                print(f"✗ Could not extract text from {source}")
        
        print(f"\nExtraction complete. Successfully extracted text from {successful_extractions} out of {len(sources)} sources.")
    else:
        print("No valid sources found for your query.")


if __name__ == "__main__":
    main()
