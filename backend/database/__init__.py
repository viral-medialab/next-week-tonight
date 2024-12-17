# In backend/database/__init__.py
from .database_utils import connect_to_mongodb, save_generated_article_to_DB

# This makes these functions available directly from the database package
__all__ = ['connect_to_mongodb', 'save_generated_article_to_DB']