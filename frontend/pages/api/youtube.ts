import { NextApiRequest, NextApiResponse } from "next";
import fetch from "node-fetch";

export default async (req: NextApiRequest, res: NextApiResponse) => {
  const { videoId } = req.query;
  const thumbnailUrl = `https://www.youtube.com/watch?v=${videoId}`;

  try {
    const response = await fetch(thumbnailUrl);
    const data = await response.buffer();

    res.setHeader("Content-Type", response.headers.get("content-type") as any);
    res.setHeader("Cache-Control", "public, max-age=3600");
    res.end(data);
  } catch (error) {
    console.error(error);
    res.status(500).end();
  }
};
