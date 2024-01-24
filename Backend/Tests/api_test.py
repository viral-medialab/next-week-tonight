from dotenv import load_dotenv
import os
from pymongo.mongo_client import MongoClient
from openai import OpenAI


load_dotenv("../../vars.env")
load_dotenv("vars.env")
openai_api = os.environ.get("OPENAI_API")
print(openai_api)