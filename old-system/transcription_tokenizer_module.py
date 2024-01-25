"""
Transcription Tokenizer

The following caption_tokenizer method breaks down the transcription for a given video into a token based on sentence length. The user inputs the ```num_sentences_per_token``` parameter to determine the token size used for embedding
"""


def caption_tokenizer(segments, num_sentences_per_token, id, liquid_videos_data):
    index = 0
    token = ""
    sentence_count = num_sentences_per_token
    start = segments[0]["start"]
    while index < len(segments) - 1:
        if (
            any(
                punctuation in segments[index]["text"]
                for punctuation in [".", "?", "!"]
            )
            and sentence_count == 1
        ):
            token += segments[index]["text"]
            key = (start, segments[index]["end"])
            liquid_videos_data[id]["caption_token_data"][key] = {"text": token}
            sentence_count = num_sentences_per_token
            start = segments[index + 1]["start"]
            token = ""
        elif (
            any(
                punctuation in segments[index]["text"]
                for punctuation in [".", "?", "!"]
            )
            and sentence_count > 1
        ):
            token += segments[index]["text"]
            sentence_count -= 1
        else:
            token += segments[index]["text"]
        index += 1

    token += segments[index]["text"]
    key = (start, segments[index]["end"])
    liquid_videos_data[id]["caption_token_data"][key] = {"text": token}
