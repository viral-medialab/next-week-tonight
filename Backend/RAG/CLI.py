import sys
import requests
from bs4 import BeautifulSoup
import re
from augmented_generation import *



def process_input():
    if len(sys.argv) != 3:
        print("Usage: <script_name> <MSN_article_URL> <user_query>")
        sys.exit(1)
    
    msn_article_url = sys.argv[1]
    user_query = sys.argv[2]
    
    article_contents = fetch_article_contents(fetch_article_id(msn_article_url))
    AI_generated_questions, relevant_articles, out = q2a_workflow(article_contents, query, 10, just_preds=True)
    save_to_file([query, article, AI_generated_questions, relevant_articles, out], 'out_preds.txt')

    
    # Use the variables msn_article_url and user_query as needed
    print(f"MSN Article URL: {msn_article_url}")
    print(f"User Query: {user_query}")

if __name__ == "__main__":
    process_input()


#example CL prompt: 
    '''
    
    /Users/allenbaranov/opt/anaconda3/envs/news/bin/python Backend/RAG/CLI.py https://www.msn.com/en-us/news/politics/trump-is-clearly-annoyed-by-nikki-haley-s-decision-to-stay-in-the-presidential-race/ar-BB1hc4Nf "Who will win the general election in 2024?"

    '''
