from download_video_info_module import *
from transcription_module import *
from transcription_tokenizer_module import *
from embedding_module import *
from clustering_module import *
from video_segmentation_module import *
import whisper
import os
import pickle

"""
Initialize Whisper Transcription Model

The whisper_model variable is the OpenAI whisper model used to transcribe an audio file to text
"""

whisper_model = whisper.load_model("large")

"""
Run Backend Pipleine

The following method takes in a list of Youtube video URLs, runs the entire Liquid News Backed V1.0 pipeline on them, and stores them in the processed directory. 
"""


def run_liquid_news_pipeline(video_list, run_name):
    liquid_videos_data = {}
    for video_url in video_list:
        # Generate Path for Run in LiquidNews Folder
        os.mkdir(f"processed/{run_name}")

        # Generate Path for video storage and audio storage in the "../LiquidNews/Path" folder
        os.mkdir(f"processed/{run_name}/videos")
        os.mkdir(f"processed/{run_name}/audios")
        os.mkdir(f"processed/{run_name}/transcriptions")
        os.mkdir(f"processed/{run_name}/embeddings")
        os.mkdir(f"processed/{run_name}/clustor_clips")

        # Download the video, and audio and retrieve the metadata
        download_video(video_url, f"processed/{run_name}/videos")
        download_video_audio(video_url, f"processed/{run_name}/audios")
        title, id = get_video_information(video_url)

        # Initialize children dictionaries & store metadata
        liquid_videos_data[id] = {}
        liquid_videos_data[id]["metadata"] = {}
        liquid_videos_data[id]["caption_token_data"] = {}
        liquid_videos_data[id]["metadata"]["title"] = title

        # Transcribe audio and store it as SRT file in the drive
        transcription = audio_to_caption(
            f"processed/{run_name}/audios/{id}.mp3", "", whisper_model
        )
        with open(
            f"processed/{run_name}/transcriptions/{id}.srt",
            "w",
            encoding="utf-8",
        ) as srt:
            write_srt(transcription["segments"], file=srt)

        # Tokenize the transcription and store it in the liquid_videos_data dictionary.
        # (Note we use a hard-coded token size of 4 or V1.0. We plan to us ML to identify
        # the optimal one in future versions).
        # MODIFIES THE EXISTING liquid_videos_data VARIABLE
        caption_tokenizer(transcription["segments"], 2, id, liquid_videos_data)

        # Gets embedding for each token and downloads embeddings to drive for the future.
        # MODIFIES THE EXISTING liquid_videos_data VARIABLE
        embeddings = get_token_embedding(
            liquid_videos_data,
            id,
            2,
            f"processed/{run_name}/embeddings",
        )

        # Clusters the embeddings and updates their respective clustering in the liquid_videos_data dict
        # MODIFIES THE EXISTING liquid_videos_data VARIABLE
        get_clusterings(liquid_videos_data, id, 2)

        # Gets the associated topic title (string) for each cluster and stores it in the liquid_videos_data dict
        cluster_data = get_cluster_topic(liquid_videos_data, id)
        liquid_videos_data[id]["cluster_data"] = cluster_data

        # Identifies how to segment videos and then creates clips for each segment
        get_cluster_clips_windows(liquid_videos_data, id)
        create_cluster_clips(
            liquid_videos_data,
            id,
            f"processed/{run_name}/videos/{id}.mp4",
            f"processed/{run_name}/clustor_clips",
        )

        # Download the final liquid_videos_data dict for future use
        dump_path = f"processed/{run_name}/liquid_videos_data.pkl"
        afile = open(dump_path, "wb")
        pickle.dump(liquid_videos_data, afile)
        afile.close()


# run_liquid_news_pipeline(['https://www.youtube.com/watch?v=HB2mGo_0tgA&ab_channel=ABCNews'], "apple")
