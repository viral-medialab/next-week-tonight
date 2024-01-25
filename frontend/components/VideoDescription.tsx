import React, { useRef, useEffect } from "react";
import Image from "next/image";
import { Tooltip, Button } from "@material-tailwind/react";

interface VideoDescriptionProps {
  source_name: string;
  source_description: string;
  title: string;
  bullets: string[];
}

export default function VideoDescription(props: VideoDescriptionProps) {
  const descriptionRef = useRef<HTMLDivElement>(null);
  const maxHeightRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (descriptionRef.current && maxHeightRef.current) {
      descriptionRef.current.style.height = `${
        maxHeightRef.current.clientHeight * 0.85
      }px`;
    }
  }, []);

  return (
    <div className="flex flex-col w-full pt-4 h-[35vh]">
      <div className="text-xl font-bold text-black">
        <h1>{props.title}</h1>
      </div>
      <div className="flex flex-row text-lg font-[500] text-[#CFCFCF]">
        <Tooltip content="Video Source" placement="left">
          <Image
            src="/link.svg"
            alt={"source"}
            width={22}
            height={18}
            className="mr-1"
          />
        </Tooltip>
        <h1>{props.source_name}</h1>
      </div>
      <div className="flex justify-end flex-row">
        <Tooltip
          content="Summarized bullet points for the video clip"
          placement="left"
        >
          <Image
            src="/info.svg"
            alt={"source"}
            width={20}
            height={20}
            className="pb-4"
          />
        </Tooltip>
      </div>
      <div className="text-sm text-black px-6 py-4 bg-gray-100 rounded-lg overflow-scroll scrollbar-hide">
        <div ref={maxHeightRef} className="max-h-[70%]">
          {props.bullets.length > 0 ? (
            <ul className="list-disc list-inside space-y-2">
              {props.bullets.map((bullet, index) => (
                <li key={index}>{bullet}</li>
              ))}
            </ul>
          ) : (
            <p>{props.source_description}</p>
          )}
        </div>
        <div ref={descriptionRef} className="h-[15%]"></div>
      </div>
    </div>
  );
}
