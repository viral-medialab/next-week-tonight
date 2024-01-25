import { Dispatch, SetStateAction } from "react";
import TopicButtonWrapper from "./TopicButtonWrapper";
import { Tooltip, Button } from "@material-tailwind/react";
import Image from "next/image";

export default function LandscapeHeader({
  subtopics,
  setCurrentSubtopic,
  selectedIndex,
}: {
  selectedIndex: number;
  subtopics: string[];
  setCurrentSubtopic: Dispatch<SetStateAction<number>>;
}) {
  return (
    <div className="flex flex-col pl-6">
      <div className="flex flex-row items-center">
        <h3 className="text-xl">Subtopics</h3>
        <Tooltip
          content="Subtopics that correspond the the topic selected on the left"
          placement="right"
        >
          <Image
            src="/info.svg"
            alt={"source"}
            width={20}
            height={20}
            className="ml-2"
          />
        </Tooltip>
      </div>
      <div className="pt-4">
        <TopicButtonWrapper
          selectedTopicIndex={selectedIndex}
          setTopic={setCurrentSubtopic}
          topics={subtopics}
        ></TopicButtonWrapper>
      </div>
    </div>
  );
}
