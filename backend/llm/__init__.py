# In backend/database/__init__.py
from .sentiment import SentimentModel
from .openai_utils import *
# This makes these functions available directly from the database package
__all__ = ['SentimentModel', 'query_chatgpt']