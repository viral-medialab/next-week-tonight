import sys
import requests
from bs4 import BeautifulSoup
import re
from augmented_generation import *



def process_input():
    if len(sys.argv) not in [3,4]:
        print("Usage: <script_name> <MSN_article_URL> <user_query> or <script_name> <MSN_article_URL> <user_query> <out_file>")
        sys.exit(1)
    
    msn_article_url = sys.argv[1]
    query = sys.argv[2]
    article = fetch_article_contents(fetch_article_id(msn_article_url))
    AI_generated_questions, relevant_articles, preds, out = q2a_workflow(article, query, 6)
    if len(sys.argv) == 4:
        out_file = sys.argv[3]
        save_to_file([query, article, AI_generated_questions, relevant_articles, preds, out], 'Outputs/'+out_file)
    else:
        save_to_file([query, article, AI_generated_questions, relevant_articles, preds, out], 'Outputs/out_article.txt')



if __name__ == "__main__":
    process_input()


#example CL prompt: 
    '''
    
    /Users/allenbaranov/opt/anaconda3/envs/news/bin/python Backend/RAG/CLI.py https://www.msn.com/en-us/news/politics/trump-is-clearly-annoyed-by-nikki-haley-s-decision-to-stay-in-the-presidential-race/ar-BB1hc4Nf "Who will win the general election in 2024?"

    '''
