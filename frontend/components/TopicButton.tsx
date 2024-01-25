import React, { Dispatch, SetStateAction } from "react";
import { Topic } from "./Interfaces";

export default function TopicButton({
  topic,
  index,
  selectedIndex,
  setTopic,
}: {
  topic: string;
  index: number;
  selectedIndex: number;
  setTopic: Dispatch<SetStateAction<number>>;
}) {
  const isSelected = index === selectedIndex;

  return (
    <button
      className={`flex justify-center items-center min-h-0 min-w-0 flex-shrink-0 px-2 gap-2 rounded-[3px] transform transition duration-500 ${
        isSelected ? "bg-gray-300 font-bold" : "bg-gray-100 hover:bg-gray-300"
      }`}
      onClick={() => {
        setTopic(index);
      }}
    >
      <div className="order-0 flex-none flex-shrink-0">{topic}</div>
    </button>
  );
}
