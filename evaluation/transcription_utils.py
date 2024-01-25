from tenacity import sleep
import youtube_dl
import requests
import os

ydl_opts = {
    "format": "bestaudio/best",
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ],
    "ffmpeg-location": "./",
    "outtmpl": "./audio/%(id)s.%(ext)s",
    "retries": 3,  # number of times to retry the entire download
    "fragment_retries": 10,  # number of times to retry individual fragments
}

transcript_endpoint = "https://api.assemblyai.com/v2/transcript"
upload_endpoint = "https://api.assemblyai.com/v2/upload"

headers_auth_only = {"authorization": os.environ.get("AAI_KEY")}
headers = {
    "authorization": os.environ.get("AAI_KEY"),
    "content-type": "application/json",
}
CHUNK_SIZE = 5242880
ROOT = "./audio/"
ROOT_J = "./json/"


def get_vid(link):
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(link)


def read_file(filename):
    with open(filename, "rb") as _file:
        while True:
            data = _file.read(CHUNK_SIZE)
            if not data:
                break
            yield data


def transcribe_from_link(link):
    link = link.strip()
    meta = get_vid(link)
    save_location = ROOT + f'{meta["id"]}.mp3'
    duration = meta["duration"]
    print("Saved mp3 to", save_location)

    upload_response = requests.post(
        upload_endpoint, headers=headers_auth_only, data=read_file(save_location)
    )

    audio_url = upload_response.json()["upload_url"]
    print("Uploaded to", audio_url)

    transcript_request = {
        "audio_url": audio_url,
    }

    transcript_response = requests.post(
        transcript_endpoint, json=transcript_request, headers=headers
    )
    transcript_id = transcript_response.json()["id"]
    polling_endpoint = transcript_endpoint + "/" + transcript_id
    print("Transcribing at", polling_endpoint)
    polling_response = requests.get(polling_endpoint, headers=headers)
    while polling_response.json()["status"] != "completed":
        sleep(30)
        try:
            polling_response = requests.get(polling_endpoint, headers=headers)
        except:
            print("Expected wait time:", duration * 2 / 5, "seconds")
            print("After wait time is up, call poll with id", transcript_id)
            return transcript_id
    print("Transcript completed")

    sentence_endpoint = f"{transcript_endpoint}/{transcript_id}/sentences"
    sentence_response = requests.get(sentence_endpoint, headers=headers)

    sentence_response_json = sentence_response.json()
    transcription_json = polling_response.json()

    return sentence_response_json, transcription_json
