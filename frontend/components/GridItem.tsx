import React, {
    Dispatch,
    SetStateAction,
    useEffect,
    useRef,
    useState,
} from "react";
import Image from "next/image";
import timeToThumbnail from "@/utils/timeToThumbnail";

const GRID_ITEM_WIDTH = "11.11vw";
const GRID_ITEM_HEIGHT = "14.44vh";

interface GridItemInfo {
    title: string;
    source: string;
    key: number;
    thumbnail: string;
    start: number;
    index: number;
    videoId: string;
    setCurrentSubtopicClip: Dispatch<SetStateAction<number>>;
    currentSubtopicClipIndex: number;
}

export default function GridItem(itemInfo: GridItemInfo) {
    const [thumbnailAtTime, setThumbnailAtTime] = useState<string>("");
    const gridItemRef = useRef<HTMLDivElement>(null);
    const imgRef = useRef<HTMLImageElement>(null);

    useEffect(() => {
        const getThumbnailAtTime = async () => {
            const thumbnailAtTime = await timeToThumbnail(
                itemInfo.videoId,
                itemInfo.start
            );
            console.log("thumbnailAtTime", thumbnailAtTime);

            /* 
    ------------------------------
   |
   |
   |
   |
    ------------------------------
    
    */
            let scaleFactor = 0;
            if (gridItemRef.current && imgRef.current) {
                const gridItemHeight = gridItemRef.current.clientHeight;
                const gridItemWidth = gridItemRef.current.clientWidth;
                let newImageWidth = 0;
                let newImageHeight = 0;
                let frameWidth = 0;
                let frameHeight = 0;

                console.log(
                    "gridItemHeight",
                    gridItemHeight,
                    "gridItemWidth",
                    gridItemWidth
                );

                if (
                    gridItemWidth / gridItemHeight <
                    thumbnailAtTime.sheet.frameWidth /
                        thumbnailAtTime.sheet.frameHeight
                ) {
                    newImageWidth = Math.round(
                        (gridItemWidth / thumbnailAtTime.sheet.frameWidth) *
                            thumbnailAtTime.sheet.img.width
                    );

                    newImageHeight = Math.round(
                        (gridItemWidth / thumbnailAtTime.sheet.frameWidth) *
                            thumbnailAtTime.sheet.img.height
                    );
                    frameWidth = gridItemWidth;
                    frameHeight = Math.round(
                        (gridItemWidth / thumbnailAtTime.sheet.frameWidth) *
                            thumbnailAtTime.sheet.frameHeight
                    );
                    gridItemRef.current.style.height = `${frameHeight}px`;
                    console.log(
                        "frameWidth",
                        frameWidth,
                        "frameHeight",
                        frameHeight,
                        "newImageWidth",
                        newImageWidth,
                        "newImageHeight",
                        newImageHeight
                    );
                    scaleFactor =
                        gridItemWidth / thumbnailAtTime.sheet.frameWidth;
                } else {
                    newImageWidth = Math.round(
                        (gridItemHeight / thumbnailAtTime.sheet.frameHeight) *
                            thumbnailAtTime.sheet.img.width
                    );
                    newImageHeight = Math.round(
                        (gridItemHeight / thumbnailAtTime.sheet.frameHeight) *
                            thumbnailAtTime.sheet.img.height
                    );
                    frameWidth = Math.round(
                        (gridItemHeight / thumbnailAtTime.sheet.frameHeight) *
                            thumbnailAtTime.sheet.frameWidth
                    );
                    frameHeight = gridItemHeight;
                    scaleFactor =
                        gridItemHeight / thumbnailAtTime.sheet.frameHeight;
                }
                imgRef.current.style.width = `${newImageWidth}px`;
                imgRef.current.style.top = `${
                    -1 * thumbnailAtTime.y * scaleFactor
                }px`;
                imgRef.current.style.left = `${
                    -1 * thumbnailAtTime.x * scaleFactor
                }px`;
                console.log(
                    "thumbnailAtTime.x",
                    thumbnailAtTime.x,
                    "thumbnailAtTime.y",
                    thumbnailAtTime.y
                );

                console.log("thumbnailAtTime", thumbnailAtTime);
                setThumbnailAtTime(thumbnailAtTime.src);
            }
        };
        getThumbnailAtTime();
    }, [itemInfo.videoId, itemInfo.start, gridItemRef.current, imgRef.current]);

    return (
        <div
            className={`flex flex-col w-full rounded-[10px] transform transition duration-500 hover:scale-105 shadow-xl hover:selected ${
                itemInfo.currentSubtopicClipIndex === itemInfo.index
                    ? "selected @layer selected"
                    : ""
            }`}
            key={itemInfo.key}
            onClick={() => {
                itemInfo.setCurrentSubtopicClip(itemInfo.index);
            }}
        >
            <div ref={gridItemRef} className="relative overflow-hidden h-full">
                <img
                    ref={imgRef}
                    src={thumbnailAtTime || itemInfo.thumbnail}
                    alt=""
                    className=" relative object-cover max-w-none rounded-t-[10px]"
                />
            </div>
            <div className="pt-2 px-2 rounder-b-[10px]">
                <h3
                    className="font-medium text-sm overflow-hidden line-clamp-2 overflow-ellipsis"
                    title={itemInfo.title}
                >
                    {itemInfo.title}
                </h3>
                <div className="flex flex-row py-1">
                    <Image
                        src="/link.svg"
                        alt={"source"}
                        width={15}
                        height={10}
                        className="mr-1"
                    />
                    <h4 className="font-medium text-xs">{itemInfo.source}</h4>
                </div>
            </div>
        </div>
    );
}
