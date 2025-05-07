import json
import os
import time
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment variables
api_key = os.getenv("OPENAI_API_KEY")

def ask_gpt_model(question, model_name):
    """Ask a question to a specified GPT model with web search enabled and return the response."""
    try:
        # Create client instance
        client = OpenAI(api_key=api_key)
        
        # Use chat completions API with web search
        response = client.responses.create(
            model="gpt-4o-mini",
            tools=[{"type": "web_search_preview"}],
            input=question
        )

        print(response.output_text)
        
        # Extract the response text from the response
        return response.output_text
    
    except Exception as e:
        print(f"Error querying {model_name}: {str(e)}")
        return f"Error: {str(e)}"

def generate_responses(model_name):
    """Generate responses for all questions using the specified model."""
    # Load test data
    with open('backend/eval/test_data.json', 'r') as f:
        test_data = json.load(f)
    
    results = {}
    
    for scenario in test_data['scenarios']:
        topic = scenario['topic']
        results[topic] = {}
        
        for question in scenario['questions']:
            print(f"Querying {model_name} for topic '{topic}' with question: {question[:50]}...")
            
            # Query the model
            response = ask_gpt_model(question, model_name)
            
            # Add a delay to avoid rate limiting
            time.sleep(1)
            
            # Store the response
            results[topic][question] = response
    
    return results

def save_responses(model_name, filename):
    """Generate and save responses to a JSON file."""
    responses = generate_responses(model_name)
    
    # Save responses to file
    with open(f'backend/eval/{filename}', 'w') as f:
        json.dump(responses, f, indent=2)
    
    print(f"Responses saved to backend/eval/{filename}")

def main():
    """Main function to generate samples from all models with web search enabled."""
    # Generate responses from GPT-4o with web search
    #save_responses("gpt-4o-search-preview", "gpt_4o_search_responses.json")
    
    # Generate responses from GPT-o4-mini with web search
    save_responses("gpt-4o-mini", "gpt_o4_mini_responses.json")
    
    # Generate responses from GPT-o3 with correct model ID
   # save_responses("o3-2025-04-16", "gpt_o3_responses.json")
    
    # Generate responses from GPT-4.1 with web search
    #save_responses("gpt-4.1", "gpt_4_1_responses.json")

if __name__ == "__main__":
    # Run the main function
    main()
