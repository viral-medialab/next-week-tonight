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
    query = sys.argv[2]
    
    article = fetch_article_contents(fetch_article_id(msn_article_url))
    AI_generated_questions, relevant_articles, preds, out = q2a_workflow(article, query, 6)
    save_to_file([query, article, AI_generated_questions, relevant_articles, preds, out], 'out_CLI_2.txt')



if __name__ == "__main__":
    process_input()


#example CL prompt: 
    '''
    
    /Users/allenbaranov/opt/anaconda3/envs/news/bin/python Backend/RAG/CLI.py https://www.msn.com/en-us/news/politics/trump-is-clearly-annoyed-by-nikki-haley-s-decision-to-stay-in-the-presidential-race/ar-BB1hc4Nf "Who will win the general election in 2024?"

    '''
