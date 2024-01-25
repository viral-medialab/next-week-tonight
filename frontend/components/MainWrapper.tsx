import React, { useEffect, useState } from "react";
import ClipHeatMap from "./ClipHeatMap";
import { Clip, LiquidData, Subtopic, Topic } from "./Interfaces";
import LandscapeGrid from "./LandscapeGrid";
import LandscapeHeader from "./LandscapeHeader";
import VideoDescription from "./VideoDescription";
import VideoHeader from "./VideoHeader";
import VideoPlayer from "./VideoPlayer";

export default function MainWrapper({ data }: { data: LiquidData }) {
  const [currentTopicIndex, setCurrentTopicIndex] = useState<number>(0);
  const [currentSubtopicIndex, setCurrentSubtopicIndex] = useState<number>(0);
  const [currentSubtopicClipIndex, setCurrentSubtopicClipIndex] =
    useState<number>(0);

  const [currentTopic, setCurrentTopic] = useState<Topic>(
    data.topics[currentTopicIndex]
  );
  const [currentSubtopic, setCurrentSubtopic] = useState<Subtopic>(
    currentTopic.subtopics[currentSubtopicIndex]
  );
  const [currentSubtopicClip, setCurrentSubtopicClip] = useState<Clip>(
    currentSubtopic.clips[currentSubtopicClipIndex]
  );

  useEffect(() => {
    setCurrentTopic(data.topics[currentTopicIndex]);
    setCurrentSubtopic(currentTopic.subtopics[currentSubtopicIndex]);
    setCurrentSubtopicClip(currentSubtopic.clips[currentSubtopicClipIndex]);
  }, [
    currentTopicIndex,
    currentSubtopicIndex,
    currentSubtopicClipIndex,
    data.topics,
    currentTopic.subtopics,
    currentSubtopic.clips,
  ]);

  useEffect(() => {
    setCurrentSubtopic(currentTopic.subtopics[currentSubtopicIndex]);
    setCurrentSubtopicClip(currentSubtopic.clips[currentSubtopicClipIndex]);
  }, [
    currentSubtopicIndex,
    currentSubtopicClipIndex,
    currentTopic.subtopics,
    currentSubtopic.clips,
  ]);
  console.log("currentSubtopicClip", currentSubtopicClip)
  return (
    <div className="flex flex-row">
      <div className="flex flex-col h-full w-[38.347vw] font-karrik-regular">
        <VideoHeader
          selectedIndex={currentTopicIndex}
          topics={data.topics
            .filter((topic) => topic.subtopics.length > 0)
            .map(({ topic }) => topic)}
          setCurrentTopic={setCurrentTopicIndex}
        />
        <div className="flex flex-col flex-1 h-full overflow-scroll scrollbar-hide">
          <VideoPlayer
            url={`https://www.youtube.com/v/${currentSubtopicClip.videoId}?start=${currentSubtopicClip.start}&end=${currentSubtopicClip.end}`}
            start={currentSubtopicClip.start}
            end={currentSubtopicClip.end}
          />
          <VideoDescription
            title={currentSubtopicClip.title}
            source_name={currentSubtopicClip.source}
            source_description={currentSubtopicClip.transcript}
            bullets={currentSubtopicClip.bullets}
          />
        </div>
      </div>
      <div className="w-[48.33vw] h-full pl-[7vw] font-karrik-regular">
        <LandscapeHeader
          selectedIndex={currentSubtopicIndex}
          subtopics={currentTopic.subtopics.map(({ subtopic }) => subtopic)}
          setCurrentSubtopic={setCurrentSubtopicIndex}
        />
        <div className="h-full overflow-scroll scrollbar-hide">
          <div className="pb-[12vh]">
            <LandscapeGrid
              currentSubtopic={currentSubtopic}
              setCurrentSubtopicClip={setCurrentSubtopicClipIndex}
              selectedClipIndex={currentSubtopicClipIndex}
            />
          </div>
        </div>
      </div>
      {/* <ClipHeatMap colors={colors} /> */}
    </div>
  );
}
