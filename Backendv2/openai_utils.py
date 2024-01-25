from openai import OpenAI
from env import *
'''
Provides all utility functions relating to the OpenAI API, including
generating responses using an OpenAI LLM model and creating embeddings
using OpenAI's embedding models.
'''


client = OpenAI(
    api_key=OPENAI_API_KEY,
)




def query_chatgpt(contexts, queries):
    if len(queries) > 1:
        contexts += ["Note: The input will be split by semicolons. Answer each prompt separately and return your answer also split by semicolons. For example, if I asked you to solve arithmetic problems and my input was '2+2;4+5', your answer should be '4;9'."]
    messages = []
    for context in contexts:
        messages.append({"role": "system", "content": context})
    final_query = ""
    for query in queries:
        final_query += query + ";"
    messages.append({"role": "user", "content": final_query[:-1]})
    response = client.chat.completions.create(
        messages=messages,
        model="gpt-4",
    )

    out = response.choices[0].message.content.split(";")
    if len(out) > 1:
         return out
    return out[0]




def get_embedding(text, engine = 'text-embedding-ada-002'):
        """
        Get the embedding for the given text using OpenAI's Embedding API.

        :param text: The text to embed.
        :param engine: The embedding engine to use.
        :return: Embedding vector.
        """
        text = text.replace("\n", " ")
        return client.embeddings.create(input = [text], model=engine).data[0].embedding