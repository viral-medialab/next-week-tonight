from flask import Flask
import sys
import os

# Add your backend directory to the path
sys.path.append(os.path.abspath("backend"))

# Import your Flask app
from backend.news_broom import app

# This is the handler Vercel will use
def handler(request):
    """Handle a request to the Flask app."""
    # The serverless function handler should process the request
    # and return a response according to Vercel's specs
    return {
        "statusCode": 200,
        "body": "API endpoint is working"
    }