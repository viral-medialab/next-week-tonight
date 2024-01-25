import React, { Dispatch, SetStateAction } from "react";
import Image from "next/image";
import GridItem from "./GridItem";
import { Subtopic } from "./Interfaces";

export default function LandscapeGrid({
  currentSubtopic,
  setCurrentSubtopicClip,
  selectedClipIndex,
}: {
  currentSubtopic: Subtopic;
  setCurrentSubtopicClip: Dispatch<SetStateAction<number>>;
  selectedClipIndex: number;
}) {
  return (
    <div className="grid grid-cols-2 gap-10 overflow-y-scroll scrollbar-hide pt-3 h-auto px-6 pb-[5vh]">
      {currentSubtopic.clips.map((data, index) => (
        <GridItem
          title={data.title}
          source={data.source}
          videoId={data.videoId}
          start={data.start}
          thumbnail={data.thumbnail}
          key={index}
          index={index}
          currentSubtopicClipIndex={selectedClipIndex}
          setCurrentSubtopicClip={setCurrentSubtopicClip}
        />
      ))}
    </div>
  );
}
