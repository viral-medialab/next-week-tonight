from dotenv import load_dotenv
import os
import requests


# load environment variables from .env file


load_dotenv("../../vars.env")
load_dotenv("../vars.env")
load_dotenv("vars.env")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
BING_API_KEY = os.environ.get("BING_API_KEY")
MONGODB_URI_KEY = os.environ.get("MONGODB_URI_KEY")

if not OPENAI_API_KEY or not BING_API_KEY or not MONGODB_URI_KEY:
    raise Exception("At least one API keys was not located. Check that your vars.env file exists in the correct directory")


# making sure all keys are active


def check_openai_api_key(api_key):
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = requests.get("https://api.openai.com/v1/models", headers=headers)
        response.raise_for_status()  # Will raise an exception for 4XX/5XX responses
    except Exception as e:
        raise ValueError("OpenAI API key is invalid or expired.")


def check_bing_api_key(api_key):
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    try:
        response = requests.get("https://api.bing.microsoft.com/v7.0/search?q=OpenAI", headers=headers)
        response.raise_for_status()
    except Exception as e:
        raise ValueError("Bing API key is invalid or expired.")


def check_mongodb_uri(uri):
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)  # Short timeout
        client.admin.command('ping')
    except ConnectionFailure:
        raise ValueError("MongoDB connection failed. URI might be invalid or MongoDB service is unavailable.")


check_openai_api_key(OPENAI_API_KEY)
check_bing_api_key(BING_API_KEY)
check_mongodb_uri(MONGODB_URI_KEY)

print("All API keys and connections verified successfully.")