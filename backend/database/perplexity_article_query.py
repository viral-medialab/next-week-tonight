from openai import OpenAI
def perplexity_article_query(topic):
    """
    :param news_url: The url of the article to search
    :type news_url: str
    :returns: A tuple with the summarized text from the article url and a score of the summary: (score,text)
    """
    YOUR_API_KEY = "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"
    messages = [
        {
        "role": "system",
        "content": (
            "You are an artificial intelligence assistant with the sole purpose of providing news articles given a topic."
        ),
        },
        {
            "role": "user",
            "content": (
                f"Provide 10 news urls from any news source given the following topic. Return only the urls with no other words or line breaks, separated by commas: {topic}."
            ),
        }
    ]
    
    client = OpenAI(api_key=YOUR_API_KEY, base_url="https://api.perplexity.ai")

    response = client.chat.completions.create(
        model="sonar-pro",
        messages=messages,
    )
    
    # print(response.choices[0].message.content)
    # print(news_url, score.choices[0].message.content)
    urls = response.choices[0].message.content
    urls = urls.split(",")
    print(urls)
    return urls
# perplexity_text_extractor("California Wild Fires")