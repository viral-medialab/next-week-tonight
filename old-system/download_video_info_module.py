from pytube import YouTube
import youtube_dl

"""
Video Download and Information Retrieval Module

The following three methods are used to download a video from Youtube, download the audio file for a respective Youtube video, and get the metadata associated with the video (i.e., name, video_id)
"""


def get_video_information(video_link):
    title, id = None, None
    ydl_opts_info = {"skip_download": True}
    with youtube_dl.YoutubeDL(ydl_opts_info) as ydl:
        title = ydl.extract_info(video_link, download=False).get("title", None)
        id = ydl.extract_info(video_link, download=False).get("id", None)
    return title, id


def download_video(video_link, output_path, skip_download=False):
    ydl_opts = {
        "writesubtitles": True,
        "writeautomaticsub": True,
        "skip_download": skip_download,
        "subtitleslangs": ["en"],
        "outtmpl": f"{output_path}/%(id)s.%(ext)s",
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_link])


def download_video_audio(video_link, output_path, skip_download=False):
    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "outtmpl": f"{output_path}/%(id)s.%(ext)s",
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_link])
