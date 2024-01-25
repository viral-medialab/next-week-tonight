import { Dispatch, SetStateAction } from "react";
import { Topic } from "./Interfaces";
import TopicButtonWrapper from "./TopicButtonWrapper";
import { Tooltip, Button } from "@material-tailwind/react";
import Image from "next/image";

export default function VideoHeader({
  topics,
  setCurrentTopic,
  selectedIndex,
}: {
  selectedIndex: number;
  topics: string[];
  setCurrentTopic: Dispatch<SetStateAction<number>>;
}) {
  return (
    <div className="flex flex-col">
      <div className="flex flex-row items-center">
        <h3 className="text-xl">Current Topics</h3>
        <Tooltip
          content="Major catagories that encompass what is being talked about in the news"
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
          topics={topics}
          setTopic={setCurrentTopic}
        ></TopicButtonWrapper>
      </div>
    </div>
  );
}
