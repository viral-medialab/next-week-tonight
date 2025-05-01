import os
import json
import time
import pandas as pd
import anthropic
from tqdm import tqdm
from dotenv import load_dotenv
from backend.test.env import *

# Load environment variables from .env file
load_dotenv()

# Initialize Claude client
client = anthropic.Anthropic(
    api_key=ANTHROPIC_API_KEY
)

def load_response_pairs(filepath):
    """Load the file containing questions and response pairs."""
    # This function will depend on your file format
    # For example, if using JSON:
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data

def get_llm_evaluation(question, response_a, response_b):
    """Call Claude API to evaluate the response pair."""
    
    prompt = f"""
[SYSTEM INSTRUCTIONS]
You are an expert evaluator tasked with comparing two research tool responses to the same question. You will judge which response is better based on specific criteria. Your assessment should be fair, detailed, and objective.

[TASK DESCRIPTION]
Compare the following two responses to this research question: 

QUESTION:
{question}

RESPONSE A:
{response_a}

RESPONSE B:
{response_b}

[EVALUATION CRITERIA]
Please evaluate the responses based on these criteria:
1. Helpfulness: Does the response directly answer the question and provide useful information?
2. Factual Accuracy: Is the information provided correct and well-supported?
3. Comprehensiveness: Does the response cover the important aspects of the topic?
4. Clarity: Is the response well-organized, coherent, and easy to understand?
5. Source Quality: Are the sources cited credible and relevant?

[OUTPUT FORMAT]
For each criterion, rate both responses on a scale of 1-5 and explain your rating.
Then provide an overall winner (A, B, or Tie) with justification.

Helpfulness:
Response A: [1-5] [Explanation]
Response B: [1-5] [Explanation]

Factual Accuracy:
Response A: [1-5] [Explanation]
Response B: [1-5] [Explanation]

Comprehensiveness:
Response A: [1-5] [Explanation]
Response B: [1-5] [Explanation]

Clarity:
Response A: [1-5] [Explanation]
Response B: [1-5] [Explanation]

Source Quality:
Response A: [1-5] [Explanation]
Response B: [1-5] [Explanation]

OVERALL WINNER: [A/B/Tie]
JUSTIFICATION: [Detailed explanation of overall assessment]
"""

    try:
        response = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=4000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text
    except Exception as e:
        print(f"Error calling Claude API: {e}")
        return None

def save_evaluation_results(results, output_filepath):
    """Save evaluation results to file."""
    # Depending on your needs, you might save as JSON, CSV, or other format
    with open(output_filepath, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Optionally also save as CSV for easier analysis
    df = pd.DataFrame(results)
    csv_path = output_filepath.replace('.json', '.csv')
    df.to_csv(csv_path, index=False)
    print(f"Results saved to {output_filepath} and {csv_path}")

def parse_evaluation_results(evaluation_text):
    """Parse the evaluation to extract scores and winner."""
    try:
        # Extract scores (this is a simple parser, might need refinement)
        scores = {}
        for criterion in ["Helpfulness", "Factual Accuracy", "Comprehensiveness", "Clarity", "Source Quality"]:
            for response in ["A", "B"]:
                pattern = f"Response {response}: ([1-5])"
                import re
                match = re.search(pattern, evaluation_text)
                if match:
                    scores[f"{criterion.lower()}_response_{response.lower()}"] = int(match.group(1))
        
        # Extract winner
        winner_match = re.search(r"OVERALL WINNER: ([A|B|Tie])", evaluation_text)
        winner = winner_match.group(1) if winner_match else "Unknown"
        
        return {
            "scores": scores,
            "winner": winner,
            "full_evaluation": evaluation_text
        }
    except Exception as e:
        print(f"Error parsing evaluation: {e}")
        return {
            "scores": {},
            "winner": "Error",
            "full_evaluation": evaluation_text
        }

def main():
    input_filepath = "backend/eval/sample_comparisons.json"  # Updated path
    output_filepath = "backend/eval/evaluation_results.json"  # Updated path
    
    # Load data
    data = load_response_pairs(input_filepath)
    
    results = []
    
    # Process each question-response pair
    for item in tqdm(data):
        question = item["question"]
        response_a = item["response_a"]
        response_b = item["response_b"]
        
        print(f"Evaluating: {question[:50]}...")
        
        # Get evaluation from Claude
        evaluation = get_llm_evaluation(question, response_a, response_b)
        
        # Parse the evaluation
        parsed_evaluation = parse_evaluation_results(evaluation) if evaluation else None
        
        # Add to results
        if evaluation:
            results.append({
                "question": question,
                "evaluation": evaluation,
                "parsed": parsed_evaluation
            })
            
            # Print a brief summary
            if parsed_evaluation and "winner" in parsed_evaluation:
                print(f"Winner: {parsed_evaluation['winner']}")
        
        # Add delay to avoid rate limits
        time.sleep(0.5)
    
    # Save results
    save_evaluation_results(results, output_filepath)

if __name__ == "__main__":
    main() 