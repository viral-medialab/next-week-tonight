'''
Pulls all API Keys and loads them into environment variables using the python OS library.
'''

from dotenv import load_dotenv
import os
load_dotenv("../../vars.env")
load_dotenv("vars.env")


OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
BING_API_KEY = os.environ.get("BING_API_KEY")
MONGODB_URI_KEY = os.environ.get("MONGODB_URI_KEY")

if not OPENAI_API_KEY or not BING_API_KEY or not MONGODB_URI_KEY:
    raise Exception("At least one API keys was not located. Check that your vars.env file exists in the NEXT-WEEK-TONIGHT directory")