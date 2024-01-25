import React, { Dispatch, SetStateAction } from "react";
import { Topic } from "./Interfaces";
import TopicButton from "./TopicButton";

export default function TopicButtonWrapper({
  topics,
  selectedTopicIndex,
  setTopic,
}: {
  topics: string[];
  selectedTopicIndex: number;
  setTopic: Dispatch<SetStateAction<number>>;
}) {
  if (!topics) return null;
  return (
    <div className="flex flex-row flex-wrap items-start gap-6 pb-6">
      {topics.map((text, index) => (
        <TopicButton
          topic={text}
          key={index}
          index={index}
          selectedIndex={selectedTopicIndex}
          setTopic={setTopic}
        />
      ))}
    </div>
  );
}
