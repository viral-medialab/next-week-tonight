import os
from pymongo import MongoClient
import json

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['your_database']
collection = db['your_collection']

# Create input directory if it doesn't exist
input_dir = 'input'
os.makedirs(input_dir, exist_ok=True)

# Retrieve documents from MongoDB
documents = collection.find({})

# Process each document and save as a text file
for i, doc in enumerate(documents):
    # Format the document as needed
    content = f"ID: {doc.get('_id')}\n"
    
    # Add all fields from the document
    for key, value in doc.items():
        if key != '_id':
            content += f"{key}: {value}\n"
    
    # Save to file
    with open(os.path.join(input_dir, f"document_{i}.txt"), 'w', encoding='utf-8') as f:
        f.write(content)

print(f"Processed {i+1} documents from MongoDB to the input directory") 