import sys
from ..predictions.query_utils import *
from ..api.article_utils import *



def process_input():
    if len(sys.argv) not in [3,4]:
        print("Usage: \npython query_CLI.py <MSN_article_URL> <user_query>, or \npython query_CLI.py <MSN_article_URL> <user_query> <out_file>")
        sys.exit(1)
    
    msn_article_url = sys.argv[1]
    query = sys.argv[2]
    article_id = get_article_id(msn_article_url)
    article = get_article_contents_from_id(article_id)
    AI_generated_questions, relevant_articles, scenarios, out = q2a_workflow(article, query, 1, verbose = False)
    if len(sys.argv) == 4:
        out_file = sys.argv[3]
        save_to_file([query, article, AI_generated_questions, relevant_articles, scenarios, out], 'Outputs/'+out_file)
    else:
        save_to_file([query, article, AI_generated_questions, relevant_articles, scenarios, out], 'Outputs/out_article.txt')



if __name__ == "__main__":
    process_input()


#example CL prompt: 
    '''

    /Users/allenbaranov/opt/anaconda3/envs/news/bin/python backend/query_CLI.py https://www.msn.com/en-us/news/politics/trump-is-clearly-annoyed-by-nikki-haley-s-decision-to-stay-in-the-presidential-race/ar-BB1hc4Nf "What happens if Trump wins the general election?"

    '''
