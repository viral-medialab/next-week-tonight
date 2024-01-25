import re
import tenacity
import time
import openai
import logging
from transformers import GPT2Tokenizer


# Define a retry decorator with a rate limiter
@tenacity.retry(
    wait=tenacity.wait_fixed(1),
    stop=tenacity.stop_after_delay(60),
    before_sleep=tenacity.before_sleep,
)
def safe_request(
    prompt: str, max_tokens: int, top_p: int, chat: bool
) -> dict[str, any]:
    """
    Send a request to the OpenAI API using the specified prompt, and handle rate limit errors by logging them
    and sleeping for the recommended number of seconds before trying again.

    Parameters:
    - prompt: The prompt to use in the OpenAI API request.

    Returns:
    - response: A dictionary containing the response from the OpenAI API.

    Raises:
    - openai.error.RateLimitError: If the request encounters a rate limit error.
    """
    try:
        if chat:
            response = openai.ChatCompletion.create(
                model="gpt-4-0314",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant who has a strong preference for being ubiased and concise.",
                    },
                    {
                        "role": "system",
                        "content": "When asked for a response in JSON you must prioratize sending a response that is complete and correctly formated over sending a response that is correct.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
                top_p=top_p,
                max_tokens=max_tokens,
            )
            return response
        else:
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                temperature=0,
                top_p=top_p,
                max_tokens=max_tokens,
            )
            return response
    except openai.error.RateLimitError as e:
        logging.info(f"Encountered RateLimitError: {e}", e)
        logging.info(f"Sleeping for {e.wait_seconds} seconds.")
        time.sleep(e.wait_seconds)


def bullet_request(prompt: str) -> dict[str, any]:
    """
    Send a request to the OpenAI API using the specified prompt, and handle rate limit errors by logging them
    and sleeping for the recommended number of seconds before trying again.

    Parameters:
    - prompt: The prompt to use in the OpenAI API request.

    Returns:
    - response: A dictionary containing the response from the OpenAI API.

    Raises:
    - openai.error.RateLimitError: If the request encounters a rate limit error.
    """
    try:
        response = openai.ChatCompletion.create(
            # model="gpt-3.5-turbo-0301",
            model="gpt-4",
            # model="gpt-4-0314",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant who has a strong preference for being ubiased and concise.",
                },
                {
                    "role": "system",
                    "content": "When asked for a response in JSON you must prioratize sending a response that is complete and correctly formated over sending a response that is correct.",
                },
                {
                    "role": "user",
                    "content": 'Generate bullet point summaries for this transcription return them as JSON formatted as {"0": "", "1":"",...}. \n'
                    + prompt,
                },
            ],
            # max_tokens=1200,
        )
        return response
    except openai.error.RateLimitError as e:
        logging.info(f"Encountered RateLimitError: {e}", e)
        logging.info(f"Sleeping for {e.wait_seconds} seconds.")
        time.sleep(e.wait_seconds)


def string_cleaner(input_str: str) -> str:
    """
    Cleans the input string by performing the following operations:
    1. Remove all special HTML characters and whitespace.
    2. Strip leading and trailing spaces.
    3. Remove multiple consecutive spaces and replace with a single space.
    4. Keep only letters, numbers, and punctuation.
    5. Remove consecutive '>>' or '<<' symbols.
    6. Remove all '>' and '<' symbols.

    Args:
        input_str (str): The string to be cleaned.

    Returns:
        str: The cleaned string.
    """
    # Remove special HTML characters and whitespace
    cleaned_str = re.sub(r"<[^>]*>", "", input_str)
    cleaned_str = re.sub(
        r"[^\S\n]+", " ", cleaned_str
    )  # remove all whitespace except newline

    # Strip leading and trailing spaces
    cleaned_str = cleaned_str.strip()

    # Remove multiple consecutive spaces and replace with a single space
    cleaned_str = re.sub(r"\s+", " ", cleaned_str)

    # Keep only letters, numbers, and punctuation
    cleaned_str = re.sub(r"[^\w\s\.\,]", "", cleaned_str)

    # Remove consecutive '>>' or '<<' symbols
    cleaned_str = re.sub(r"(>>+|<<+)", "", cleaned_str)

    # Remove all '>' and '<' symbols
    cleaned_str = cleaned_str.replace(">", "").replace("<", "")

    return cleaned_str


def clean_captions(captions: list[dict]):
    """
    Cleans the text field of the captions array

     Args:
         captions (list[dict]): List of caption dictionaries with the following keys:
             "text" (str): Caption text.
             "start" (int): Start time of caption.
             "duration" (int): Duration of caption.

     Returns:
         list[dict]: List of caption dictionaries with the following keys:
             "text" (str): Full sentence caption text.
             "start" (int): Start time of caption.
             "duration" (int): Duration of caption.
    """

    for caption in captions:
        caption["text"] = string_cleaner(caption["text"])
    return captions


def sentence_captions_from_caption_phrases(captions: list[dict]):
    """
    Combines caption fragments into full sentences.

    Args:
        captions (list[dict]): List of caption dictionaries with the following keys:
            "text" (str): Caption text.
            "start" (int): Start time of caption.
            "duration" (int): Duration of caption.

    Returns:
        list[dict]: List of caption dictionaries with the following keys:
            "text" (str): Full sentence caption text.
            "start" (int): Start time of caption.
            "duration" (int): Duration of caption.
    """
    combined_captions = []
    sentence = captions[0]["text"] + " "
    duration = captions[0]["duration"]
    start = captions[0]["start"]

    for caption in captions[1:]:
        if start == None:
            start = caption["start"]
        if not re.match("^[A-Za-z][^?!.]*[?.!]['\"]?$", caption["text"]) is not None:
            sentence += caption["text"] + " "
            duration += caption["duration"]
        else:
            combined_captions.append(
                {
                    "text": sentence + caption["text"],
                    "duration": duration + caption["duration"],
                    "start": start,
                }
            )
            start = None
            sentence = ""
            duration = 0
    return combined_captions


def transcript_from_captions(captions: list[dict]):
    """
    Combines caption fragments into full sentences.

    Args:
        captions (list[dict]): List of caption dictionaries with the following keys:
            "text" (str): Caption text.
            "start" (int): Start time of caption.
            "duration" (int): Duration of caption.

    Returns:
        str: Single string combining all captions.on.
    """
    return "".join("".join([" " + c["text"] for c in captions]).splitlines())


def tokenize(text: str) -> list[int]:
    """
    Tokenizes the input text using the GPT2 tokenizer.

    Args:
        text (str): The input text to be tokenized.

    Returns:
        List[int]: A list of integers representing the tokenized text.
    """
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    return tokenizer.encode(text)


def find_punctuations(tokens: list[int]) -> list[int]:
    """
    Find the indices of punctuation tokens in a list of GPT-2 tokens.

    Args:
        tokens (List[int]): A list of integers representing GPT-2 tokens.

    Returns:
        List[int]: A list of integers representing the indices of punctuation tokens in the input list.
    """
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    punctuations = [".", "!", "?"]
    punctuation_indices = []
    for i in range(len(tokens)):
        if tokenizer.decode([tokens[i]]) in punctuations:
            punctuation_indices.append(i)
    return punctuation_indices


def get_segment_transcript(
    start_index: int, end_index: int, captions: list[dict[str, dict[str, int]]]
) -> str:
    """
    Returns the transcript for a segment of a video based on the start and end indices.

    Args:
        start_index (int): The index of the first caption in the segment.
        end_index (int): The index of the last caption in the segment.
        captions (List[Dict[str, Union[str, int]]]): A list of dictionaries containing the captions for the video. Each dictionary has keys "start" (start time in milliseconds), "duration" (duration in milliseconds), and "text" (the caption text).

    Returns:
        str: The transcript for the specified segment of the video.
    """
    transcirpt = ""
    for i in range(start_index, end_index + 1):
        transcirpt += re.sub(r">+ ", "", captions[i]["text"])
    return transcirpt


def string_comparer(a: str, b: str) -> bool:
    """
    Compares two strings after performing the following operations:
    1. Converts all strings to lowercase.
    2. Removes all spaces.
    3. Returns True if both strings have more than one word and one of them is a substring of the other, else False.

    Args:
        a (str): The first string to compare.
        b (str): The second string to compare.

    Returns:
        bool: True if one string is a substring of the other, else False.
    """

    # Convert both strings to lowercase and remove spaces
    a = a.lower().replace(" ", "")
    b = b.lower().replace(" ", "")

    return a in b or b in a
