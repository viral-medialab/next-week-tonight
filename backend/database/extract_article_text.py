from bs4 import BeautifulSoup
from urllib.request import urlopen
import requests
from openai import OpenAI
def perplexity_text_extractor(news_url):
    """
    :param news_url: The url of the article to search
    :type news_url: str
    :returns: The extracted text from the url
    """
    YOUR_API_KEY = "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"
    messages = [
        {
        "role": "system",
        "content": (
            "You are an artificial intelligence assistant with the sole purpose of extracting plain text from webpage urls."
        ),
        },
        {
            "role": "user",
            "content": (
                f"Extract the plain text from the following url: {news_url}. If you are unable to extract the text, respond only with the words 'Invalid Request'"
            ),
        }
    ]
    client = OpenAI(api_key=YOUR_API_KEY, base_url="https://api.perplexity.ai")

    response = client.chat.completions.create(
        model="sonar-pro",
        messages=messages,
    )
    print(type(response))
    print(response.choices[0].message.content)
    return response.choices[0].message.content

def BSoup_text_extractor(news_url):
    """
    :param news_url: The url of the article to search
    :type news_url: str
    :returns: The extracted text from the url, None if not found
    """
    try:
        html = urlopen(news_url).read()
    except:
        try:
            html = requests.get(news_url).text
        except:
            return None
        
    soup = BeautifulSoup(html, features="html.parser")

    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.extract()    # rip it out

    # get text
    text = soup.get_text()

    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())

    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))

    # drop blank lines
    text = ' '.join(chunk for chunk in chunks if chunk)
    return text
    #maybe remove the white space by taking the # of adjacent words in a radius is a way to remove the unecessary text while staying universal
    #another option is to search for specific html body tags where I know article text will be
    #   works well if I have a limited # of news sources
    #   WHAT ARE THE NEWS SOURCES WE ACCESS?
    #   NYT, wallstreet journal, bbc

def extract_text_from_url(article_data):
        article_urls = article_data['url'].tolist()
        output_text = []
        for news_url in article_urls:
            print("Accessing text using Perplexity API")
            article_text = perplexity_text_extractor(news_url)
            if article_text == "Invalid Request":
                print("Perplexity text extraction failed. Extracting text with Beautiful Soup")
                article_text = BSoup_text_extractor(news_url)
            output_text.append(article_text)        
        return output_text