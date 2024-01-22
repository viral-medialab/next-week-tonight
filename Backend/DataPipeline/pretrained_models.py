from openai import OpenAI
import numpy as np
from transformers import pipeline
from transformers import TFAutoModelForSequenceClassification
from transformers import AutoTokenizer
import numpy as np
from scipy.special import softmax
from dotenv import load_dotenv
import os
load_dotenv("../../vars.env")



class SemanticEmbeddings:
    def __init__(self):
        self.engine = 'text-embedding-ada-002'
        self.api = os.environ.get("OPENAI_API")


    def get_embedding(self, text, engine = 'text-embedding-ada-002'):
        """
        Get the embedding for the given text using OpenAI's Embedding API.

        :param text: The text to embed.
        :param engine: The embedding engine to use.
        :return: Embedding vector.
        """
        client = OpenAI(
            #  This is the default and can be omitted
            api_key=self.api,
        )


        text = text.replace("\n", " ")
        return client.embeddings.create(input = [text], model=engine).data[0].embedding


    def similarity_score(self, x, y, verbose = True):
        x = np.array(x)
        y = np.array(y)
        sim_score = x.T@y / (np.linalg.norm(x) * np.linalg.norm(y))
        if verbose:
            print(f"Similarity between the two embeddings is: {sim_score:.4f}")
        return sim_score
        




class SentimentAnalysis:
    def __init__(self):
        MODEL = f"cardiffnlp/twitter-roberta-base-sentiment"

        self.tokenizer = AutoTokenizer.from_pretrained(MODEL)
        self.model = TFAutoModelForSequenceClassification.from_pretrained(MODEL)
        self.tokenizer.save_pretrained(MODEL)
        self.model.save_pretrained(MODEL)

        self.labels=['negative', 'neutral', 'positive']
    

    def get_sentiment_score(self, text):
        paragraphs = text.split("\n\n")
        out = 0
        for paragraph in paragraphs:
            try:
                encoded_input = self.tokenizer(paragraph, return_tensors='tf')
                output = self.model(encoded_input)
                scores = output[0][0].numpy()
                scores = softmax(scores)

                out = 0
                for l in range(3):
                    label = self.labels[l]
                    score = scores[l]
                    if label == 'positive':
                        out += score
                    if label == 'negative':
                        out -= score

            except:
                print("paragraph too large, moving on")

        return out / len(paragraphs)





class ToneAnalysis: 
    ''' We will take care of the tone analysis model later'''
    def __init__(self):
        pass


    def categorize(self, text):
        categories = ['informative','objective','serious','']





if __name__ == '__main__':
    '''
    Run this script as main to ensure any errors are not due to initialization of the models.
    '''
    a = SentimentAnalysis()
    b = SemanticEmbeddings()
    c = ToneAnalysis()
