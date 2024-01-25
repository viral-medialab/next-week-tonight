import React, { Dispatch, SetStateAction } from "react";
import Image from "next/image";

export default function ClipHeatMap({ colors }: { colors: string[] }) {
  return (
    <div className="absolute bottom-12 right-24 w-[8%] aspect-[5/6] px-4 py-6  bg-white bg-opacity-80 border border-gray-200 rounded-[10px]">
      <div className="relative w-full aspect-[5/6]  overflow-y-scroll scrollbar-hide">
        <div className="grid grid-cols-3 w-full h-full gap-2">
          {colors.map((color, index) => (
            <div
              className="aspect-video"
              style={{ backgroundColor: color }}
              key={index}
            ></div>
          ))}
        </div>
      </div>
    </div>
  );
}
