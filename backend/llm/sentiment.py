from transformers import AutoModelForSequenceClassification
from transformers import AutoTokenizer
from scipy.special import softmax

'''
Stores all pretrained models to be called only when needed for less unnecessary computing.
For example, sentiment analysis is only needed to generate the database so we do not
call it for user query processing.
'''



class SentimentModel:
    def __init__(self):
        MODEL = f"cardiffnlp/twitter-roberta-base-sentiment"

        self.tokenizer = AutoTokenizer.from_pretrained(MODEL)
        self.model = AutoModelForSequenceClassification.from_pretrained(MODEL)
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
