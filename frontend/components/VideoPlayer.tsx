import React from "react";
import ReactPlayer from "react-player";

interface VideoPlayerProps {
  url: string;
  width?: string;
  height?: string;
  start: number;
  end: number;
}

export default function VideoPlayer(props: VideoPlayerProps) {
  const config = {
    youtube: {
      playerVars: {
        start: props.start,
        end: props.end,
      },
    },
  };

  return (
    <div className="h-[50vh]">
      <ReactPlayer
        url={props.url}
        height="100%"
        width="100%"
        config={config}
        controls={false}
        style={{ objectFit: "contain" }}
      />
    </div>
  );
}
