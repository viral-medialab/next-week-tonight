/**
 * Given a video ID and a time in seconds, returns a Promise that resolves to a StoryboardFrame object representing the thumbnail image at that time.
 * @param videoId The ID of the YouTube video.
 * @param time The time in seconds.
 * @returns A Promise that resolves to a StoryboardFrame object representing the thumbnail image at the given time.
 */
export default async function timeToThumbnail(
    videoId: string,
    time: number
): Promise<StoryboardFrame> {
    // Create a new Storyboard object with the given video ID
    const storyboard = new Storyboard(`/api/youtube?videoId=${videoId}`);

    // Load the storyboard
    await storyboard.load();

    // Get the duration of the video in seconds
    const videoDuration = storyboard.videoDuration;

    // Calculate the relative time (between 0 and 1) of the given time
    const relativeTime = time / videoDuration;

    // Calculate the index of the frame at the given time
    const frameIndex = Math.floor(relativeTime * storyboard.frameCount);

    // Get the frame at the given index
    const frame = storyboard.getFrame(frameIndex);

    // Return the frame
    return frame; // returns {src, x, y, frameWidth, frameHeight}
}

// src\Coordinate.js

/**
 * Represents a coordinate with an x and y value.
 */
export class Coordinate {
    x: number;
    y: number;

    /**
     * Creates a new Coordinate object with the given x and y values.
     * @param x The x value.
     * @param y The y value.
     */
    constructor(x: number, y: number) {
        this.x = x;
        this.y = y;
    }
}

// src\Storyboard.js

/**
 * Represents a storyboard for a YouTube video.
 */
export class Storyboard {
    url: string;
    sheets: StoryboardSheet[] = [];
    frameCount: number = 0;
    frameRowLength: number = 0;
    frameWidth: number = 0;
    frameHeight: number = 0;
    exists: boolean = false;
    videoDuration: number = 0; // duration in seconds

    /**
     * Creates a new Storyboard object with the given URL.
     * @param url The URL of the storyboard.
     */
    constructor(url: string) {
        this.url = url;
    }

    /**
     * Loads the storyboard.
     */
    async load() {
        try {
            // Fetch the text of the storyboard URL
            const text = await (await fetch(this.url)).text();

            // Extract the storyboard specification renderer from the text
            let storyBoardSpecRenderer =
                /playerStoryboardSpecRenderer.*?(\{.+?\})/g.exec(text);

            // If the storyboard specification renderer is not found, return
            if (!storyBoardSpecRenderer) {
                return;
            }

            // Parse the specification URL from the storyboard specification renderer
            let specURL = JSON.parse(
                storyBoardSpecRenderer[1].replace(/\\(.)/g, "$1")
            ).spec;

            // Extract the specification information from the specification URL
            let spec =
                /(http.*?)\|.*?#M\$M#(.*?)\|(\d+)#(\d+)#(\d+)#(\d+)#(\d+)#\d+#M\$M#([^|]*).*?$/g.exec(
                    specURL
                ) as any[];

            // If the specification information is not found, return
            if (!spec) {
                return;
            }

            // Extract the frame width, frame height, frame count, frame row length, and frame row count from the specification information
            const frameW = spec[3] * 1;
            this.frameWidth = frameW;
            const frameH = spec[4] * 1;
            this.frameHeight = frameH;
            const frameCount = spec[5] * 1;
            this.frameCount = frameCount;
            const frameRowLength = spec[6] * 1;
            this.frameRowLength = frameRowLength;
            const frameRowCount = spec[7] * 1;
            const sigh = spec[8];

            // Construct the HTTP URL for the storyboard image
            const http = `${spec[1]
                .replace(/\\/g, "")
                .replace("$L", "2")}&sigh=${sigh}`;

            // Extract the duration of the video in seconds from the text
            const lengthReg = /\\?"approxDurationMs\\?":\s*\\?"(\d+)\\?"/.exec(
                text
            );
            if (!lengthReg) {
                return;
            }
            const length = (lengthReg[1] as any) / 1000; // in seconds
            this.videoDuration = length;

            // Load the storyboard sheets
            const sheets: any = [];
            const promises = [];
            for (
                let i = 0;
                i < Math.ceil(frameCount / frameRowLength / frameRowCount);
                i++
            ) {
                promises.push(
                    new Promise<void>((resolve, reject) => {
                        const img = new Image();
                        img.addEventListener("error", () => {
                            sheets[i] = undefined;
                            resolve();
                        });
                        img.addEventListener("load", () => {
                            sheets[i] = new StoryboardSheet(
                                img,
                                frameRowLength,
                                frameW,
                                frameH
                            );
                            resolve();
                        });
                        img.src = http.replace("$N", `M${i}`);
                    })
                );
            }
            await Promise.all(promises);
            this.sheets = sheets.filter((it: any) => it);
            // this.frameCount = this.sheets.reduce((sum,cur)=>sum+cur.frameCount,0);
            this.exists = true;
        } catch {
            this.exists = false;
        }
    }

    /**
     * Gets the frame at the given index.
     * @param index The index of the frame.
     * @returns A StoryboardFrame object representing the frame at the given index.
     */
    getFrame(index: number) {
        let nextFirstFrame = 0;
        let sheetIdx = -1;

        // Find the sheet that contains the frame at the given index
        while (sheetIdx + 1 < this.sheets.length && nextFirstFrame <= index) {
            nextFirstFrame += this.sheets[++sheetIdx].frameCount;
        }
        const sheet = this.sheets[sheetIdx];

        // Get the frame from the sheet
        return new StoryboardFrame(
            sheet,
            sheet.getFrame(index - (nextFirstFrame - sheet.frameCount))
        );
    }
}

/**
 * Represents a sheet in a storyboard for a YouTube video.
 */
export class StoryboardSheet {
    img: HTMLImageElement;
    frameCount: number;
    frameRowLength: number;
    frameWidth: number;
    frameHeight: number;

    /**
     * Creates a new StoryboardSheet object with the given image, frame row length, frame width, and frame height.
     * @param img The image of the sheet.
     * @param frameRowLength The number of frames in each row of the sheet.
     * @param frameWidth The width of each frame.
     * @param frameHeight The height of each frame.
     */
    constructor(
        img: HTMLImageElement,
        frameRowLength: number,
        frameWidth: number,
        frameHeight: number
    ) {
        this.img = img;
        this.frameCount =
            Math.floor(img.width / frameWidth) *
            Math.floor(img.height / frameHeight);
        this.frameRowLength = frameRowLength;
        this.frameWidth = frameWidth;
        this.frameHeight = frameHeight;
    }

    /**
     * Gets the frame at the given index.
     * @param index The index of the frame.
     * @returns An object representing the frame at the given index, with properties x, y, width, and height.
     */
    getFrame(index: number) {
        const row = Math.floor(index / this.frameRowLength);
        const col = index % this.frameRowLength;
        const x = col * this.frameWidth;
        const y = row * this.frameHeight;
        return { x, y, width: this.frameWidth, height: this.frameHeight };
    }
}

/**
 * Represents a frame in a storyboard for a YouTube video.
 */
export class StoryboardFrame {
    sheet: StoryboardSheet;
    coordinate: Coordinate;

    /**
     * Gets the source URL of the image for the frame.
     */
    get src() {
        return this.sheet.img.src;
    }

    /**
     * Gets the x coordinate of the frame.
     */
    get x() {
        return this.coordinate.x;
    }

    /**
     * Gets the y coordinate of the frame.
     */
    get y() {
        return this.coordinate.y;
    }

    /**
     * Creates a new StoryboardFrame object with the given sheet and coordinate.
     * @param sheet The sheet containing the frame.
     * @param coordinate The coordinate of the frame.
     */
    constructor(sheet: StoryboardSheet, coordinate: Coordinate) {
        this.sheet = sheet;
        this.coordinate = coordinate;
    }
}
