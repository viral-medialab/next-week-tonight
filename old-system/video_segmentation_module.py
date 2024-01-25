from os.path import exists
from random import randint
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import os
import fnmatch
import numpy as np
import pickle
import uuid

"""
Video Segmentation Module

The following module uses the cluster information from the cluster module to generate video clips for each cluster using the algorithm defined in the ```reduce_cluster_clip_windows``` method.
"""


def reduce_cluster_clip_windows(windows):
    clips = []
    start = windows[0][0]
    end = windows[0][1]
    for i in range(len(windows)):
        if windows[i][0] - end > 30:
            clips.append((start, end))
            start = windows[i][0]
            end = windows[i][1]
            if i == len(windows) - 1:
                clips.append(windows[i])
        else:
            end = windows[i][1]
            if i == len(windows) - 1:
                clips.append((start, end))
    return clips


def get_cluster_clips_windows(liquid_videos_data, id):
    clip_windows = sorted(list(liquid_videos_data[id]["caption_token_data"].keys()))
    for window in clip_windows:
        window_cluster = liquid_videos_data[id]["caption_token_data"][window]["cluster"]
        if "clip_windows" in liquid_videos_data[id]["cluster_data"][window_cluster]:
            liquid_videos_data[id]["cluster_data"][window_cluster][
                "clip_windows"
            ].append(window)
        else:
            liquid_videos_data[id]["cluster_data"][window_cluster]["clip_windows"] = [
                window
            ]
    for cluster in liquid_videos_data[id]["cluster_data"]:
        liquid_videos_data[id]["cluster_data"][cluster][
            "clip_windows"
        ] = reduce_cluster_clip_windows(
            liquid_videos_data[id]["cluster_data"][cluster]["clip_windows"]
        )


def create_cluster_clips(liquid_videos_data, id, video_path, output_path):
    # Create path for clips
    title = "".join(
        c for c in liquid_videos_data[id]["metadata"]["title"] if c.isalpha()
    )
    clips_ouput_path = f"{output_path}/{id}_{title}"
    if not os.path.exists(clips_ouput_path):
        os.makedirs(clips_ouput_path)

    # Create clips
    for clustor in liquid_videos_data[id]["cluster_data"]:
        print(liquid_videos_data[id]["cluster_data"][clustor]["clip_windows"])
        for clip_window in liquid_videos_data[id]["cluster_data"][clustor][
            "clip_windows"
        ]:
            topic_name = "".join(
                c
                for c in liquid_videos_data[id]["cluster_data"][clustor]["topic"]
                if c.isalpha()
            )
            output_clip_path = (
                f"{clips_ouput_path}/{clustor}_{topic_name}_{uuid.uuid1()}.mp4"
            )
            if not exists(output_clip_path):
                ffmpeg_extract_subclip(
                    video_path,
                    clip_window[0],
                    clip_window[1],
                    targetname=output_clip_path,
                )
