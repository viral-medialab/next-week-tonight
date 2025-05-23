from dotenv import load_dotenv
import os
import requests
from firecrawl import FirecrawlApp


load_dotenv("../../vars.env")
load_dotenv("../vars.env")
load_dotenv("vars.env")



OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
BING_API_KEY = os.environ.get("BING_API_KEY")
MONGODB_URI_KEY = os.environ.get("MONGODB_URI_KEY")
PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY")
FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
NEWSDATA_IO_API_KEY = os.environ.get("NEWSDATA_IO_API_KEY")


#print(PERPLEXITY_API_KEY,FIRECRAWL_API_KEY)
def test_openai_api(key):
    url = "https://api.openai.com/v1/embeddings"
    headers = {"Authorization": f"Bearer {key}"}
    data = {
        "input": "Hello world",
        "model": "text-embedding-ada-002"
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return True  # Return True if the request was successful
    except:
        return False


def test_bing_api(key):
    params = {"q": "Microsoft", "count": 10}
    headers = {"Ocp-Apim-Subscription-Key": key}
    response = requests.get("https://api.bing.microsoft.com/v7.0/search", params=params, headers=headers)
    return response.ok


def test_mongodb_uri(uri):
    from pymongo import MongoClient
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.server_info()  # Force connection on a request as the MongoClient constructor does not connect.
        return True
    except Exception as e:
        return False

def test_perplexity_api(key):
    from openai import OpenAI
    try:
        client = OpenAI(api_key=key, base_url="https://api.perplexity.ai")
        message = [
        {
        "role": "system",
        "content": (
            "You are an artificial intelligence assistant."
        ),
        
        },
        {
                "role": "user",
                "content": (
                    f"Respond with the current time."
                ),
            }
    ]
        response = client.chat.completions.create(
        model="sonar-pro",
        messages=message
        )
        return True
    except:
        return False

def test_firecrawl_api(key):
    if not key:
        return False
    try:
        app = FirecrawlApp(api_key=key)
        return True
    except ValueError:
        return False

def run_tests():
    results = {}
    results["OPENAI_API_KEY"] = test_openai_api(OPENAI_API_KEY) if OPENAI_API_KEY else False
    results["BING_API_KEY"] = test_bing_api(BING_API_KEY) if BING_API_KEY else False
    results["MONGODB_URI_KEY"] = test_mongodb_uri(MONGODB_URI_KEY) if MONGODB_URI_KEY else False
    results["PERPLEXITY_API_KEY"] = test_perplexity_api(PERPLEXITY_API_KEY) if PERPLEXITY_API_KEY else False
    results["FIRECRAWL_API_KEY"] = test_firecrawl_api(FIRECRAWL_API_KEY) if FIRECRAWL_API_KEY else False

    failed_keys = {key: "Failed" for key, result in results.items() if not result}
    if failed_keys:
        raise Exception(f"The following keys or URLs failed their tests: {failed_keys}")
    return results


try:
    test_results = run_tests()
    print("All API keys and URIs are working:", test_results)
except Exception as e:
    print(str(e))